<!-- AUTO-GENERATED from UC-2.9.11.json — DO NOT EDIT -->

---
id: "2.9.11"
title: "OpenStack Control Plane RabbitMQ Queue Depth by Service"
status: "verified"
criticality: "high"
splunkPillar: "IT Operations"
---

# UC-2.9.11 · OpenStack Control Plane RabbitMQ Queue Depth by Service

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** IT Operations &middot; **Type:** Performance, Reliability &middot; **Status:** Verified

*We monitor the building blocks of your private cloud—computers, networks, disks, and logins—so new systems come up reliably and people are not locked out when something upstream hiccups.*

---

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

## Known False Positives

RabbitMQ depth can build during controller restarts, large image pushes, or backup-driven orchestration; some backlog may clear on its own after the surge ends.

## References

- [OpenStack Message Queue (Oslo.messaging)](https://docs.openstack.org/oslo.messaging/latest/)
