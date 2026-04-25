<!-- AUTO-GENERATED from UC-5.14.51.json — DO NOT EDIT -->

---
id: "5.14.51"
title: "Traefik Request Content-Length Distribution"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.14.51 · Traefik Request Content-Length Distribution

## Description

Big bodies stress buffers and may signal exfiltration.

## Value

Informs WAF and API gateway limits.

## Implementation

Use for large upload monitoring; pair with body size limits middleware.

## SPL

```spl
index=proxy sourcetype="traefik:access"
| eval cl=tonumber(RequestContentSize)
| where cl > 5000000
| bin cl span=1000000
| stats count by cl, RouterName
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## References

- [Vendor documentation](https://doc.traefik.io/traefik/observability/access-logs/#access-logs)
