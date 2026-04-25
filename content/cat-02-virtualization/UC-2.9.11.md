<!-- AUTO-GENERATED from UC-2.9.11.json — DO NOT EDIT -->

---
id: "2.9.11"
title: "OpenStack Control Plane RabbitMQ Queue Depth by Service"
criticality: "high"
splunkPillar: "IT Operations"
---

# UC-2.9.11 · OpenStack Control Plane RabbitMQ Queue Depth by Service

## Description

Deep AMQP queues mean async RPC backlogs across Nova, Neutron, and Cinder. Consumer drops predict widespread API timeouts.

## Value

Preserves API responsiveness during traffic spikes and upgrades.

## Implementation

Ingest per-queue metrics every minute. Page on depth SLO breach. Tie queues to owning service via naming convention.

## SPL

```spl
index=openstack (sourcetype="openstack:rabbitmq" OR sourcetype="rabbitmq:metrics") earliest=-1h
| eval depth=tonumber(messages_ready)+tonumber(messages_unacked)
| eval consumers=tonumber(consumer_count)
| where depth>5000 OR (consumers==0 AND depth>0)
| stats latest(depth) as qdepth, latest(consumers) as cons by vhost, queue
```

## Visualization

Timechart depth; table worst queues; consumer count sparkline.

## References

- [OpenStack Message Queue (Oslo.messaging)](https://docs.openstack.org/oslo.messaging/latest/)
