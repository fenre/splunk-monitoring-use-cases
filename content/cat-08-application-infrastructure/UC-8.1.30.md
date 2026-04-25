<!-- AUTO-GENERATED from UC-8.1.30.json — DO NOT EDIT -->

---
id: "8.1.30"
title: "Kafka Broker Request Handler Pool Saturation"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.1.30 · Kafka Broker Request Handler Pool Saturation

## Description

Low `RequestHandlerAvgIdlePercent` means broker I/O threads are rarely idle, which usually precedes produce/fetch latency spikes and client timeouts during traffic bursts.

## Value

Surfaces broker CPU/request-thread exhaustion before clients see widespread timeouts, allowing scale-out or partition moves.

## Implementation

On a heavy forwarder with `Splunk_TA_kafka` and the JMX add-on, create a KafkaServerStats task per broker (remote JMX enabled). Poll every 60s. Normalize field names to match your JMX template (some builds alias attributes). Alert when the 15-minute rolling average stays below 0.20.

## SPL

```spl
index=kafka sourcetype="kafka:serverStats"
| where isnotnull(RequestHandlerAvgIdlePercent) AND RequestHandlerAvgIdlePercent < 0.20
| bin span=5m _time
| stats avg(RequestHandlerAvgIdlePercent) as avg_idle by _time, host
| where avg_idle < 0.20
```

## Visualization

Line chart (avg_idle by broker), Single value (worst broker), Table (brokers under threshold).

## References

- [Apache Kafka — monitoring](https://kafka.apache.org/documentation/#monitoring)
- [Configure JMX inputs for the Splunk Add-on for Kafka](https://docs.splunk.com/Documentation/AddOns/released/Kafka/ConfigureJMXinputs)
