<!-- AUTO-GENERATED from UC-5.14.43.json — DO NOT EDIT -->

---
id: "5.14.43"
title: "Traefik Entrypoint Open Connections"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.14.43 · Traefik Entrypoint Open Connections

## Description

Connection growth predicts fds and memory pressure.

## Value

Supports right-sizing edge nodes.

## Implementation

Enable `--metrics.prometheus`; label series by entrypoint. Use OTel if multi-tenant.

## SPL

```spl
index=proxy sourcetype="traefik:metrics"
| search metric_name="*entrypoint*open_connections*" OR match(metric_name, "traefik_entrypoint_open_connections")
| eval v=tonumber(metric_value)
| timechart span=1m max(v) by entrypoint
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## References

- [Vendor documentation](https://doc.traefik.io/traefik/observability/metrics/prometheus/)
