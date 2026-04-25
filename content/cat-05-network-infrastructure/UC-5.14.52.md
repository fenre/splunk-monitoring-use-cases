<!-- AUTO-GENERATED from UC-5.14.52.json — DO NOT EDIT -->

---
id: "5.14.52"
title: "Traefik Weighted Round-Robin Backend Imbalance"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.14.52 · Traefik Weighted Round-Robin Backend Imbalance

## Description

Skewed weights waste capacity or overload canaries.

## Value

Keeps progressive delivery honest.

## Implementation

Validate dynamic weights from Consul/Kubernetes; investigate cold endpoints.

## SPL

```spl
index=proxy sourcetype="traefik:access"
| stats count by ServiceName, ServiceAddr
| eventstats sum(count) as tot by ServiceName
| eval share_pct=round(100*count/tot,2)
| where share_pct < 5 OR share_pct > 80
| table ServiceName, ServiceAddr, count, share_pct
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## References

- [Vendor documentation](https://doc.traefik.io/traefik/routing/services/#weighted-round-robin)
