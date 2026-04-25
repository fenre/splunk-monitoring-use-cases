<!-- AUTO-GENERATED from UC-8.2.37.json — DO NOT EDIT -->

---
id: "8.2.37"
title: "ActiveMQ Transport Connector Accept Failure"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-8.2.37 · ActiveMQ Transport Connector Accept Failure

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

## References

- [Apache ActiveMQ — Configuring Transports](https://activemq.apache.org/components/classic/documentation/configuring-transports)
- [Apache ActiveMQ — Broker Configuration](https://activemq.apache.org/components/classic/documentation/broker-configuration)
