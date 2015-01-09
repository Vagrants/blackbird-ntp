blackbird-ntp
===============

[![Build Status](https://travis-ci.org/Vagrants/blackbird-ntp.png?branch=development)](https://travis-ci.org/Vagrants/blackbird-ntp)

Get information of time synchronization by using 'ntpq'

```
     remote           refid      st t when poll reach   delay   offset  jitter
==============================================================================
*127.0.0.1       133.243.238.243  2 u   52   64  377    0.489    0.066   0.388
+127.0.0.2       133.243.238.163  2 u   54   64  377    0.505   -0.007   6.133
```

Data to be sent is as follows

* ntp version
* remote
* refid
* stratum
* peer
* poll
* reach
* delay (ms)
* offset (ms)
* jitter

## Install

You can install by pip.

```
$ pip install git+https://github.com/Vagrants/blackbird-ntp.git
```

Or you can also install rpm package from [blackbird repository](https://github.com/Vagrants/blackbird/blob/master/README.md).

```
$ sudo yum install blackbird-ntp --enablerepo=blackbird
```
