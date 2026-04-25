<!-- AUTO-GENERATED from UC-5.14.47.json — DO NOT EDIT -->

---
id: "5.14.47"
title: "Traefik Default Router / Catch-All Traffic Spike"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.14.47 · Traefik Default Router / Catch-All Traffic Spike

## Description

Unexpected default-router hits expose config gaps.

## Value

Improves edge hygiene and security posture.

## Implementation

High catch-all volume may be scanners; pair with WAF and geo blocking.

## SPL

```spl
index=proxy sourcetype="traefik:access"
| where RouterName=="default@internal" OR match(RouterName, "(?i)dashboard@internal")
| bin _time span=5m
| stats count by ClientAddr, entryPointName, _time
| where count > 200
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## References

- [Vendor documentation](https://doc.traefik.io/traefik/routing/routers/)
