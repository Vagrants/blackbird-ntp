"""
blackbird ntp module

get information of time synchronization by using 'ntpq'
"""

__VERSION__ = '0.1.2'

import subprocess
import re

from blackbird.plugins import base


class ConcreteJob(base.JobBase):
    """
    This class is Called by "Executor".
    Get ntp information and send to backend.
    """

    def __init__(self, options, queue=None, logger=None):
        super(ConcreteJob, self).__init__(options, queue, logger)

    def build_items(self):
        """
        main loop
        """

        # ping item
        self.ping()

        # ntpq --version
        self.ntp_version()

        # ntpq -pn
        self.ntpq()

    def _enqueue(self, key, value):
        """
        set queue item
        """

        item = NTPItem(
            key=key,
            value=value,
            host=self.options['hostname']
        )
        self.queue.put(item, block=False)
        self.logger.debug(
            'Inserted to queue {key}:{value}'
            ''.format(key=key, value=value)
        )

    def ping(self):
        """
        send ping item
        """

        self._enqueue('blackbird.ntp.ping', 1)
        self._enqueue('blackbird.ntp.version', __VERSION__)

    def ntp_version(self):
        """
        detect version from 'ntpq --version'

        $ ntpq --version
        ntpq 4.2.6p5
        """

        ntp_version = 'Unknown'

        try:
            output = subprocess.Popen(
                [self.options['path'], '--version'],
                stdout=subprocess.PIPE
            ).communicate()[0]
            match = re.match(r'ntpq (\S+)', output.split('\n')[0])
            if match:
                ntp_version = match.group(1)

        except OSError:
            self.logger.debug(
                'can not exec "{0} --version", failed to get ntp version'
                ''.format(self.options['path'])
            )

        self._enqueue('ntp.version', ntp_version)

    def ntpq(self):
        """
        execute ntpq peer status
        """

        _cmd = [
            self.options['path'],
            '-c', 'hostnames no',
            '-c', 'timeout {to}'.format(to=self.options['timeout']),
            '-c', 'peer',
            self.options['host']
        ]

        try:
            output, stderr = subprocess.Popen(
                _cmd,
                stderr=subprocess.PIPE,
                stdout=subprocess.PIPE
            ).communicate()
        except OSError:
            self._enqueue('ntp.synchronized', 0)
            raise base.BlackbirdPluginError(
                'can not exec "{cmd}", failed to get ntp information'
                ''.format(cmd=' '.join(_cmd))
            )

        if stderr:
            self._enqueue('ntp.synchronized', 0)
            raise base.BlackbirdPluginError(
                'ntpq client error [{err}]'.format(err=stderr.strip())
            )

        peer_type = {
            'l': 'local',
            'u': 'unicast',
            'm': 'multicast',
            'b': 'broadcast',
        }

        # remove header 2 lines
        ntpq_pn = output.split('\n')[2:-1]

        for line in ntpq_pn:
            value = line.split()

            # synchronized
            if value[0].startswith('*'):
                self._enqueue('ntp.synchronized', 1)
                self._enqueue('ntp.remote', value[0][1:])
                self._enqueue('ntp.refid', value[1])
                self._enqueue('ntp.stratum', value[2])
                self._enqueue('ntp.peer', peer_type[value[3]])
                self._enqueue('ntp.poll', value[5])
                self._enqueue('ntp.reach', value[6])
                self._enqueue('ntp.delay', value[7])
                self._enqueue('ntp.offset', value[8])
                self._enqueue('ntp.jitter', value[9])

                # ok, no more loop
                return

        # there is no synchronized server
        self._enqueue('ntp.synchronized', 0)


# pylint: disable=too-few-public-methods
class NTPItem(base.ItemBase):
    """
    Enqued item.
    """

    def __init__(self, key, value, host):
        super(NTPItem, self).__init__(key, value, host)

        self._data = {}
        self._generate()

    @property
    def data(self):
        return self._data

    def _generate(self):
        self._data['key'] = self.key
        self._data['value'] = self.value
        self._data['host'] = self.host
        self._data['clock'] = self.clock


class Validator(base.ValidatorBase):
    """
    Validate configuration.
    """

    def __init__(self):
        self.__spec = None

    @property
    def spec(self):
        self.__spec = (
            "[{0}]".format(__name__),
            "path=string(default='/usr/sbin/ntpq')",
            "host=string(default='127.0.0.1')",
            "timeout=integer(0, 10000, default=1000)",
            "hostname=string(default={0})".format(self.detect_hostname()),
        )
        return self.__spec
