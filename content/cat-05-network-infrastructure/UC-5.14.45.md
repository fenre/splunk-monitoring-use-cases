<!-- AUTO-GENERATED from UC-5.14.45.json — DO NOT EDIT -->

---
id: "5.14.45"
title: "Traefik Middleware Time Share of Request Duration"
status: "draft"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.14.45 · Traefik Middleware Time Share of Request Duration

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Performance &middot; **Status:** Draft

*We watch traefik middleware time share of request duration and catch issues early, before they turn into outages for the people who rely on the network.*

---

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

## Known False Positives

Edge cases: multi-vendor mixes and ad hoc feeds can include lab traffic and partial visibility that mimics issues until scopes are defined. Tuning tip: match this to «Traefik Middleware Time Share of Request Duration» and exclude change windows, scans, and lab VLANs you already expect.

## References

- [Vendor documentation](https://doc.traefik.io/traefik/observability/access-logs/)
