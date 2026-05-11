<!-- AUTO-GENERATED from UC-8.2.37.json — DO NOT EDIT -->

---
id: "8.2.37"
title: "ActiveMQ Transport Connector Accept Failure"
status: "draft"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-8.2.37 · ActiveMQ Transport Connector Accept Failure

> **Criticality:** Critical &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Availability &middot; **Status:** Draft

*We use this to surfaces partial outages — one OpenWire/AMQP/STOMP listener down — that JVM uptime checks miss.*

---

## Description

Connector-level WARN/ERROR lines (bind failures, accept loop stopped, I/O exceptions) mean clients cannot open new sessions on that transport even if the JVM is still running.

## Value

Surfaces partial outages—one OpenWire/AMQP/STOMP listener down—that JVM uptime checks miss.

## Implementation

Forward `activemq.log` from each broker. Normalize multi-line stack traces. Maintain a lookup of known maintenance hosts. Correlate with OS firewall and TLS keystore rotations.

## SPL

```spl
index=messaging sourcetype="activemq:log"
| search ("TransportConnector" OR "Connector") (ERROR OR WARN OR FATAL)
| search "failed" OR "stopped" OR "stopped accepting" OR "IOException"
| stats latest(_raw) as sample by host
| eval connector_down=1
```

## Visualization

Timeline (connector errors), Table (host, sample message), Single value (affected brokers).

## Known False Positives

Queues and broker metrics swing during rebalancing, replay, or maintenance. We align with change windows.

## References

- [Apache ActiveMQ — Configuring Transports](https://activemq.apache.org/components/classic/documentation/configuring-transports)
- [Apache ActiveMQ — Broker Configuration](https://activemq.apache.org/components/classic/documentation/)
