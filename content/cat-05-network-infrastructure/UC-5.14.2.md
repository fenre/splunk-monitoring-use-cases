<!-- AUTO-GENERATED from UC-5.14.2.json — DO NOT EDIT -->

---
id: "5.14.2"
title: "HAProxy Connection Retry and Redispatch Volume"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.14.2 · HAProxy Connection Retry and Redispatch Volume

## Description

Retries absorb brief faults but high volume masks systemic overload or brownouts.

## Value

Surfaces upstream instability that averages hide until SLAs break.

## Implementation

Extend `log-format` to include retry/redispatch counters; validate with `show stat`. Baseline per service.

## SPL

```spl
index=proxy sourcetype="haproxy:http"
| regex field=_raw "(?i)retry=(?<retry>\d+)"
| stats sum(retry) as retries by backend, server
| where retries > 100
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## References

- [Vendor documentation](https://docs.haproxy.org/2.8/configuration.html#log-format)
