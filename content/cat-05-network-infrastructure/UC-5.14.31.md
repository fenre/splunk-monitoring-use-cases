<!-- AUTO-GENERATED from UC-5.14.31.json — DO NOT EDIT -->

---
id: "5.14.31"
title: "Squid HTTP Status Code Distribution"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.14.31 · Squid HTTP Status Code Distribution

## Description

Spikes in 5xx often precede origin incidents visible here first.

## Value

Gives NOC a single pane for user-impacting web errors.

## Implementation

Separate `ERR_*` Squid codes from upstream HTTP for triage.

## SPL

```spl
index=proxy sourcetype="squid:access"
| eval sc=tonumber(status_code)
| where isnotnull(sc)
| bin sc span=100
| timechart span=1h count by sc
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## References

- [Vendor documentation](http://www.squid-cache.org/Doc/config/http_status_codes/)
