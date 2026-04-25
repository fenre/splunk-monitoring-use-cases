<!-- AUTO-GENERATED from UC-5.14.13.json — DO NOT EDIT -->

---
id: "5.14.13"
title: "Varnish Grace and Keep Serving Stale Content Frequency"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.14.13 · Varnish Grace and Keep Serving Stale Content Frequency

## Description

Stale serving shields origins but can confuse content owners if unexplained.

## Value

Balances resilience versus freshness commitments.

## Implementation

Tune thresholds against editorial SLOs; document VCL `grace`/`keep`.

## SPL

```spl
index=proxy sourcetype="varnish:vsl"
| regex _raw="(?i)(grace|stale|hit-for-pass)"
| bin _time span=15m
| stats count by host, _time
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## References

- [Vendor documentation](https://varnish-cache.org/docs/trunk/users-guide/vcl-grace.html)
