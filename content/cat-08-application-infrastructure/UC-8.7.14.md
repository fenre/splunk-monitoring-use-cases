<!-- AUTO-GENERATED from UC-8.7.14.json — DO NOT EDIT -->

---
id: "8.7.14"
title: "ActiveMQ Broker Administrative Shutdown Audit"
status: "draft"
criticality: "medium"
splunkPillar: "Security"
---

# UC-8.7.14 · ActiveMQ Broker Administrative Shutdown Audit

> **Criticality:** Medium &middot; **Difficulty:** Beginner &middot; **Pillar:** Security &middot; **Type:** Compliance &middot; **Status:** Draft

*We use this to supplements change tickets with ground-truth timestamps for /ITGC style controls on messaging infrastructure.*

---

## Description

Broker stop sequences document who interrupted message flow—critical when proving whether downtime was malicious, mistaken, or maintenance.

## Value

Supplements change tickets with ground-truth timestamps for SOX/ITGC style controls on messaging infrastructure.

## Implementation

Ensure graceful shutdown emits identifiable log lines in your distribution. Correlate with privileged OS accounts and bastion session logs. Retain per records-management policy.

## SPL

```spl
index=messaging sourcetype="activemq:log"
| search "Stopping broker" OR "Stopped broker" OR "Shutting down" OR "JVM received" OR ("BrokerService" AND "stop")
| table _time, host, _raw
```

## Visualization

Timeline (shutdown events), Table (host, operator context if present), Single value (events per month).

## Known False Positives

Queues and broker metrics swing during rebalancing, replay, or maintenance. We align with change windows.

## References

- [Apache ActiveMQ — Security](https://activemq.apache.org/components/classic/documentation/security)
- [Apache ActiveMQ — Web Console](https://activemq.apache.org/components/classic/documentation/web-console)
