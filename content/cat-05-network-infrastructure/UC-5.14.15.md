<!-- AUTO-GENERATED from UC-5.14.15.json — DO NOT EDIT -->

---
id: "5.14.15"
title: "Varnish ESI Fragment Error Rate"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.14.15 · Varnish ESI Fragment Error Rate

## Description

ESI failures create partial pages that are hard to spot in averages.

## Value

Speeds collaboration between CDN and app teams.

## Implementation

Limit verbose ESI debug to non-prod; aggregate counts in prod.

## SPL

```spl
index=proxy sourcetype="varnish:vsl"
| regex _raw="(?i)(ESI.*error|include.*failed)"
| stats count by host
| where count > 10
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## References

- [Vendor documentation](https://varnish-cache.org/docs/trunk/users-guide/esi.html)
