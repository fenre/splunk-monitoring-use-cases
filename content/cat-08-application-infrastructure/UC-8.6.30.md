<!-- AUTO-GENERATED from UC-8.6.30.json — DO NOT EDIT -->

---
id: "8.6.30"
title: "Kafka Invalid Message Batch and Corrupt Record Errors"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-8.6.30 · Kafka Invalid Message Batch and Corrupt Record Errors

## Description

Broker-side parse and checksum errors usually mean poison messages, interrupted log segments, or incompatible producer serializers.

## Value

Stops extended data corruption incidents from spreading across consumers and guides engineers to the offending topic/partition quickly.

## Implementation

Collect broker logs from all replicas. Include partition/topic regex extractions where your distribution logs them. Auto-open incidents when any broker exceeds zero errors in 5 minutes for tier-0 topics.

## SPL

```spl
index=kafka sourcetype="kafka:serverLog"
| search "CorruptRecordException" OR "InvalidRecordException" OR "Record batch" OR "INVALID_RECORD" OR "checksum"
| rex "^\[[^\]]+\]\s+(?<log_level>\w+)"
| where log_level IN ("ERROR","WARN")
| stats count by host
| where count > 0
```

## Visualization

Timeline (corruption errors), Table (host, count), Single value (open error window).

## References

- [Apache Kafka — Message Format](https://kafka.apache.org/documentation/#messageformat)
- [Configure monitor inputs for the Splunk Add-on for Kafka](https://docs.splunk.com/Documentation/AddOns/released/Kafka/Configuremonitorinputs)
