<!-- AUTO-GENERATED from UC-8.1.87.json — DO NOT EDIT -->

---
id: "8.1.87"
title: "WildFly JMS Queue Depth and Consumer Lag"
status: "draft"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.1.87 · WildFly JMS Queue Depth and Consumer Lag

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance, Availability &middot; **Status:** Draft

*We help you prevent message loss scenarios and disk-full events on brokers embedded in WildFly.*

---

## Description

Deep JMS queues mean producers outpace consumers or consumers failed silently. Zero consumers with positive depth is especially dangerous.

## Value

Prevents message loss scenarios and disk-full events on brokers embedded in WildFly.

## Implementation

Enable messaging statistics on queues. Poll JMX every minute; alert on rising `MessageCount` with zero consumers.

## SPL

```spl
index=web sourcetype="jmx:jboss"
| search mbean="*jms*queue*" OR mbean="*messaging*server*"
| eval depth=tonumber(MessageCount) cons=tonumber(ConsumerCount)
| where depth > 1000 OR (depth > 0 AND cons == 0)
| table _time, host, mbean, depth, cons
```

## Visualization

Time series for pool/queue metrics, top stats for failures, event timeline for deploys.

## Known False Positives

Queues grow during consumer maintenance, slow consumers, or burst producer activity. Seasonal traffic can also create sustained backlog without a hard fault.

## References

- [WildFly Admin Guide](https://docs.wildfly.org/30/Admin_Guide.html#messaging-subsystem)
