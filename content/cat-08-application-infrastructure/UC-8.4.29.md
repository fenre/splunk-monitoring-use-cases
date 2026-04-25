<!-- AUTO-GENERATED from UC-8.4.29.json — DO NOT EDIT -->

---
id: "8.4.29"
title: "RabbitMQ File Descriptor Utilization"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.4.29 · RabbitMQ File Descriptor Utilization

## Description

High file-descriptor usage predicts `emfile` errors, connection drops, and cluster instability during connection storms.

## Value

Gives capacity teams time to raise `ulimit`, prune stale connections, or scale out before the broker refuses sockets.

## Implementation

Poll `/api/nodes` every minute. Confirm `fd_total` reflects the effective OS limit in your environment. Alert at 75% sustained; emergency page at 90%. Pair with connection churn dashboards.

## SPL

```spl
index=messaging sourcetype="rabbitmq:node"
| eval fd_pct=if(fd_total>0, round(fd_used/fd_total*100,1), null())
| where fd_pct > 75
| table _time, name, fd_used, fd_total, fd_pct
```

## Visualization

Gauge (fd_pct), Line chart (fd_used trend), Table (nodes over threshold).

## References

- [RabbitMQ — Networking and Connection Bloat](https://www.rabbitmq.com/docs/networking)
- [RabbitMQ — Alarms](https://www.rabbitmq.com/docs/alarms)
