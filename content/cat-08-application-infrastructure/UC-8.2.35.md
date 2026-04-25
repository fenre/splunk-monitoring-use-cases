<!-- AUTO-GENERATED from UC-8.2.35.json — DO NOT EDIT -->

---
id: "8.2.35"
title: "Kafka Broker Fatal Shutdown Detection"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-8.2.35 · Kafka Broker Fatal Shutdown Detection

## Description

FATAL/ERROR lines that include shutdown semantics indicate the broker process is exiting or an unrecoverable subsystem failed, which immediately impacts partition availability.

## Value

Triggers rapid incident response for broker loss before controller metrics and lag alarms cascade across the cluster.

## Implementation

Enable `kafka:serverLog` collection from `$KAFKA_HOME/logs` on every broker. Tune the `match` filters to your log vocabulary; add host-based suppressions for planned maintenance windows.

## SPL

```spl
index=kafka sourcetype="kafka:serverLog"
| rex "^\[[^\]]+\]\s+(?<log_level>\w+)"
| where log_level IN ("FATAL","ERROR") AND (match(_raw, "(?i)shutting\s+down") OR match(_raw, "(?i)fatal") OR match(_raw, "(?i)stopped"))
| stats count by host, log_level
| where count >= 1
```

## Visualization

Timeline (fatal/error shutdown events), Table (host, sample _time), Single value (brokers with events in window).

## References

- [Source types for the Splunk Add-on for Kafka](https://docs.splunk.com/Documentation/AddOns/released/Kafka/Sourcetypes)
- [Apache Kafka — broker configuration](https://kafka.apache.org/documentation/#brokerconfigs)
