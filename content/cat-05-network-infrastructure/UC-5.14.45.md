<!-- AUTO-GENERATED from UC-5.14.45.json — DO NOT EDIT -->

---
id: "5.14.45"
title: "Traefik Middleware Time Share of Request Duration"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.14.45 · Traefik Middleware Time Share of Request Duration

## Description

Auth and compression should not dominate latency budgets.

## Value

Guides middleware ordering and tuning.

## Implementation

If fields absent, export OpenTelemetry traces with span attributes for middleware.

## SPL

```spl
index=proxy sourcetype="traefik:access"
| eval mw=tonumber(MiddlewareDuration), total=tonumber(Duration)
| eval mw_pct=if(total>0, round(100*mw/total,1), null())
| where mw_pct > 25
| timechart span=5m perc95(mw_pct) by RouterName
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## References

- [Vendor documentation](https://doc.traefik.io/traefik/observability/access-logs/)
