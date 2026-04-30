<!-- AUTO-GENERATED from UC-5.14.35.json — DO NOT EDIT -->

---
id: "5.14.35"
title: "Squid Client Connection Load from cachemgr"
status: "draft"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.14.35 · Squid Client Connection Load from cachemgr

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Capacity, Security &middot; **Status:** Draft

*We watch squid client connection load from cachemgr and catch issues early, before they turn into outages for the people who rely on the network.*

---

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

## Known False Positives

Edge cases: multi-vendor mixes and ad hoc feeds can include lab traffic and partial visibility that mimics issues until scopes are defined. Tuning tip: match this to «Squid Client Connection Load from cachemgr» and exclude change windows, scans, and lab VLANs you already expect.

## References

- [Vendor documentation](http://www.squid-cache.org/Doc/config/max_filedescriptors/)
