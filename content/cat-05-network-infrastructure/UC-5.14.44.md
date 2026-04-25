<!-- AUTO-GENERATED from UC-5.14.44.json — DO NOT EDIT -->

---
id: "5.14.44"
title: "Traefik Service Health Check Failures"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.14.44 · Traefik Service Health Check Failures

## Description

Router health drives load balancing; silent failures hurt most.

## Value

Accelerates rollback when a deploy breaks probes.

## Implementation

Ship container stdout via sidecar; set log level INFO in prod.

## SPL

```spl
index=proxy sourcetype="traefik:log"
| regex _raw="(?i)(Health check failed|Status.*DOWN|Server.*Unhealthy)"
| stats count by service_name
| sort - count
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## References

- [Vendor documentation](https://doc.traefik.io/traefik/routing/services/#health-check)
