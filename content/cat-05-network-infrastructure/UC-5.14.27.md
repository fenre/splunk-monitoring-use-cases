<!-- AUTO-GENERATED from UC-5.14.27.json — DO NOT EDIT -->

---
id: "5.14.27"
title: "Squid ICAP and eCAP Adaptation Failures"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.14.27 · Squid ICAP and eCAP Adaptation Failures

## Description

Adaptation failures look like random web errors to users.

## Value

Protects both security coverage and productivity.

## Implementation

Tune service timeouts; scale scanners horizontally when counts rise.

## SPL

```spl
index=proxy sourcetype="squid:cache"
| regex _raw="(?i)(ICAP|ECAP).*(?:fail|error|timeout)"
| bin _time span=5m
| stats count by _time, host
| where count > 10
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## References

- [Vendor documentation](http://www.squid-cache.org/Doc/config/icap_service/)
