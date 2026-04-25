<!-- AUTO-GENERATED from UC-7.1.45.json — DO NOT EDIT -->

---
id: "7.1.45"
title: "Redis Rejected Connections Near Client Limit"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-7.1.45 · Redis Rejected Connections Near Client Limit

## Description

The rejected_connections counter increments when Redis hits maxclients. This is a production-critical signal of connection storms, pool leaks, or undersized limits.

## Value

Stops silent application failures where clients cannot connect during traffic spikes or after misconfigured pools.

## Implementation

Ingest INFO snapshots every minute. Use delta or per-poll rejected_connections if you emit counters cumulatively. Alert on any rejection or sustained client_util_pct above policy. Map host to cluster and application owners.

## SPL

```spl
index=middleware sourcetype="redis:info"
| eval client_util_pct=if(maxclients>0, round(connected_clients/maxclients*100,2), null())
| where rejected_connections > 0 OR client_util_pct > 85
| timechart span=5m max(rejected_connections) as rejected, max(client_util_pct) as util_pct by host
```

## Visualization

Single value (rejected_connections), Line chart (connected_clients vs maxclients), Table (clusters at risk).

## References

- [Redis INFO reference (maxclients, rejected_connections)](https://redis.io/docs/latest/commands/info/)
