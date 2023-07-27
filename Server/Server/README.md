---
title: CMC Simulator README
description:
published: true
#date: 2021-07-01T22:13:55.842Z
tags:
editor: markdown
#dateCreated: 2021-07-01T22:13:55.842Z
---

# CMC Simulator README

This server code lets multiple ADCs connect to it.  Test code can access it on another port.

Source code: [cmc.py](/cmc/cmc.py)

```shell
setsid python3 ./cmc.py --log-config-file=cmc-log.conf >/dev/null 2>&1 < /dev/null &
```

Manual access
```
nc $(ho rms) 8806
10.250.0.4
!!!ADC not yet connected
!!!ADC connects
<SGN="####";ADN="10010001";FWV="1.21RC8_1.21RC8">

```