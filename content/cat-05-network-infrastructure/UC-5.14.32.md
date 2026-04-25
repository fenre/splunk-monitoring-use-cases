<!-- AUTO-GENERATED from UC-5.14.32.json — DO NOT EDIT -->

---
id: "5.14.32"
title: "Squid Delay Pool Throttling Signals"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.14.32 · Squid Delay Pool Throttling Signals

## Description

Fair-use rules should be observable, not silent.

## Value

Supports regulatory bandwidth management.

## Implementation

Avoid verbose debug in prod; use short cache log notices or manager counters.

## SPL

```spl
index=proxy sourcetype="squid:cache"
| regex _raw="(?i)Delay pool|delay_pool"
| bin _time span=5m
| stats count by host, _time
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## References

- [Vendor documentation](http://www.squid-cache.org/Doc/config/delay_pools/)
