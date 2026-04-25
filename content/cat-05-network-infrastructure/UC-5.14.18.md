<!-- AUTO-GENERATED from UC-5.14.18.json — DO NOT EDIT -->

---
id: "5.14.18"
title: "Varnish Backend Connection Reuse Signals"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.14.18 · Varnish Backend Connection Reuse Signals

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

## References

- [Vendor documentation](https://varnish-cache.org/docs/trunk/reference/varnishstat.html)
