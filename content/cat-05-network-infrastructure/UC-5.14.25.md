<!-- AUTO-GENERATED from UC-5.14.25.json — DO NOT EDIT -->

---
id: "5.14.25"
title: "Squid Cache Peer Selection and Failure Events"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.14.25 · Squid Cache Peer Selection and Failure Events

## Description

Peer flaps shift load unexpectedly across the mesh.

## Value

Stabilizes hierarchical cache designs.

## Implementation

Log `cache_peer` lines at appropriate debug level; aggregate to Splunk via UF.

## SPL

```spl
index=proxy sourcetype="squid:cache"
| regex _raw="(?i)(peer.*(?:DEAD|DOWN|FAILED)|DETECT UP|DETECT DOWN)"
| stats count by cache_peer
| sort - count
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## References

- [Vendor documentation](http://www.squid-cache.org/Doc/config/cache_peer/)
