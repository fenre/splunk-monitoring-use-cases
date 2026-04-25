<!-- AUTO-GENERATED from UC-8.5.24.json — DO NOT EDIT -->

---
id: "8.5.24"
title: "RabbitMQ Federation Link Health and Upstream Lag"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.5.24 · RabbitMQ Federation Link Health and Upstream Lag

## Description

Federation links carry traffic across clusters and regions; a link in the down state or a large `rabbitmq_federation_unacked_messages` value means upstream backlog is building and regional DR or hub-spoke routing is at risk. Correlating Prometheus federation metrics with broker logs speeds isolation of TLS, policy, or network faults.

## Value

Protects multi-site messaging topologies from partial outages that otherwise show up only as mysterious queue growth on downstream vhosts.

## Implementation

Enable `rabbitmq_prometheus` and scrape `/metrics` into Splunk; ensure label dimensions map to indexed fields (`vhost`, `upstream`). Alert on `rabbitmq_federation_link_up==0` for tier-1 links and tune unacked threshold by message size.

## SPL

```spl
index=messaging sourcetype="rabbitmq:metrics" earliest=-24h
| search metric_name="rabbitmq_federation_link_up" OR metric_name="rabbitmq_federation_unacked_messages"
| eval link_up=if(metric_name="rabbitmq_federation_link_up", coalesce(metric_value, value, gauge), null())
| eval unacked_upstream=if(metric_name="rabbitmq_federation_unacked_messages", coalesce(metric_value, value, gauge), null())
| eval vhost_dim=coalesce(vhost, federation_vhost, dimension_vhost)
| eval upstream_dim=coalesce(upstream, federation_upstream, dimension_upstream)
| where (isnotnull(link_up) AND link_up==0) OR (isnotnull(unacked_upstream) AND unacked_upstream > 10000)
| stats latest(link_up) as up latest(unacked_upstream) as unacked by host, vhost_dim, upstream_dim
| where up==0 OR unacked > 10000
| table host, vhost_dim, upstream_dim, up, unacked
```

## Visualization

Table (vhost, upstream, link_up, unacked messages), geomap or topology panel by site, line chart of unacked federation backlog.

## References

- [RabbitMQ — Federation](https://www.rabbitmq.com/docs/federation)
- [RabbitMQ — Prometheus plugin](https://www.rabbitmq.com/docs/prometheus)
