<!-- AUTO-GENERATED from UC-5.14.10.json — DO NOT EDIT -->

---
id: "5.14.10"
title: "Varnish Backend Health Probe and Fetch Failures"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.14.10 · Varnish Backend Health Probe and Fetch Failures

## Description

Probe failures starve users even when edge CPUs look idle.

## Value

Triggers fast failover or capacity before SLAs breach.

## Implementation

Enable backend polling; include `Backend` VSL tags in forwarded logs.

## SPL

```spl
index=proxy sourcetype="varnish:vsl"
| regex _raw="(?i)(Backend fetch failed|FetchError|no healthy backend)"
| stats count by backend
| sort - count
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## References

- [Vendor documentation](https://varnish-cache.org/docs/trunk/reference/vcl-backend-health.html)
