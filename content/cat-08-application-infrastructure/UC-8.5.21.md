<!-- AUTO-GENERATED from UC-8.5.21.json — DO NOT EDIT -->

---
id: "8.5.21"
title: "RabbitMQ Policy and Operator Policy Change Events"
criticality: "medium"
splunkPillar: "IT Operations"
---

# UC-8.5.21 · RabbitMQ Policy and Operator Policy Change Events

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

## References

- [RabbitMQ — Policies](https://www.rabbitmq.com/docs/policies)
- [RabbitMQ — Logging](https://www.rabbitmq.com/docs/logging)
