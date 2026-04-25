<!-- AUTO-GENERATED from UC-5.14.35.json — DO NOT EDIT -->

---
id: "5.14.35"
title: "Squid Client Connection Load from cachemgr"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.14.35 · Squid Client Connection Load from cachemgr

## Description

Proxies fail open or drop sessions when fds exhaust.

## Value

Protects peak events like live streams and exams.

## Implementation

Poll during incidents; baseline diurnal curves. Correlate with SYN flood mitigations.

## SPL

```spl
index=proxy sourcetype="squid:info"
| regex _raw="(?i)Current active connections|client_http\.conns"
| rex field=_raw "(?<conns>\d{3,})"
| eval conns=tonumber(conns)
| where conns > 20000
| table _time, host, conns
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## References

- [Vendor documentation](http://www.squid-cache.org/Doc/config/max_filedescriptors/)
