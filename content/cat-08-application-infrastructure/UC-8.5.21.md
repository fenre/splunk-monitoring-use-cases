<!-- AUTO-GENERATED from UC-8.5.21.json — DO NOT EDIT -->

---
id: "8.5.21"
title: "RabbitMQ Policy and Operator Policy Change Events"
status: "draft"
criticality: "medium"
splunkPillar: "IT Operations"
---

# UC-8.5.21 · RabbitMQ Policy and Operator Policy Change Events

> **Criticality:** Medium &middot; **Difficulty:** Beginner &middot; **Pillar:** IT Operations &middot; **Type:** Change &middot; **Status:** Draft

*We use this to create an immutable our monitoring platform-backed audit trail when queue semantics shift without a matching ticket.*

---

## Description

Policy changes alter TTL, queue type, delivery limits, and federation behavior—high-impact operational events that should align with change management.

## Value

Creates an immutable Splunk-backed audit trail when queue semantics shift without a matching ticket.

## Implementation

Validate log verbosity includes policy changes in your RabbitMQ version. Deduplicate noisy HA events. Join against CMDB ownership for routing.

## SPL

```spl
index=messaging sourcetype="rabbitmq:log"
| search "policy" AND ("set" OR "applied" OR "updated" OR "cleared" OR "operator policy")
| table _time, host, _raw
```

## Visualization

Timeline (policy events), Table (recent changes), Single value (events per week).

## Known False Positives

Queues and broker metrics swing during rebalancing, replay, or maintenance. We align with change windows.

## References

- [RabbitMQ — Policies](https://www.rabbitmq.com/docs/policies)
- [RabbitMQ — Logging](https://www.rabbitmq.com/docs/logging)
