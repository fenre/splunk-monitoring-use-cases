<!-- AUTO-GENERATED from UC-5.14.18.json — DO NOT EDIT -->

---
id: "5.14.18"
title: "Varnish Backend Connection Reuse Signals"
status: "draft"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.14.18 · Varnish Backend Connection Reuse Signals

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance &middot; **Status:** Draft

*We watch varnish backend connection reuse signals and catch issues early, before they turn into outages for the people who rely on the network.*

---

## Description

Poor reuse increases latency and CPU on both sides.

## Value

Guides keep-alive and TLS session settings.

## Implementation

Low reuse may indicate TLS handshake storms toward origin.

## SPL

```spl
index=proxy sourcetype="varnish:stats"
| eval conn=tonumber(backend_conn), reuse=tonumber(backend_recycle)
| eval reuse_ratio=if(conn>0, round(100*reuse/conn,1), null())
| timechart span=15m avg(reuse_ratio) by host
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## Known False Positives

Edge cases: multi-vendor mixes and ad hoc feeds can include lab traffic and partial visibility that mimics issues until scopes are defined. Tuning tip: match this to «Varnish Backend Connection Reuse Signals» and exclude change windows, scans, and lab VLANs you already expect.

## References

- [Vendor documentation](https://varnish-cache.org/docs/trunk/reference/varnishstat.html)
