<!-- AUTO-GENERATED from UC-8.3.4.json — DO NOT EDIT -->

---
id: "8.3.4"
title: "Under-Replicated Partitions"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-8.3.4 · Under-Replicated Partitions

## Description

Under-replicated partitions mean data is at risk of loss if additional brokers fail. Immediate remediation is required.

## Value

Under-replicated partitions mean data is at risk of loss if additional brokers fail. Immediate remediation is required.

## Implementation

Poll Kafka broker JMX metrics. Alert immediately on any under-replicated partitions. Track duration of under-replication. Correlate with broker disk usage and network metrics to identify root cause.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk Connect for Kafka` (Splunkbase 3862), JMX.
• Ensure the following data sources are available: Kafka JMX (`UnderReplicatedPartitions`, `UnderMinIsrPartitionCount`).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll Kafka broker JMX metrics. Alert immediately on any under-replicated partitions. Track duration of under-replication. Correlate with broker disk usage and network metrics to identify root cause.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=kafka sourcetype="kafka:broker"
| where UnderReplicatedPartitions > 0
| stats sum(UnderReplicatedPartitions) as total_under_replicated by _time
| timechart span=5m max(total_under_replicated) as under_replicated
```

Understanding this SPL

**Under-Replicated Partitions** — Under-replicated partitions mean data is at risk of loss if additional brokers fail. Immediate remediation is required.

Documented **Data sources**: Kafka JMX (`UnderReplicatedPartitions`, `UnderMinIsrPartitionCount`). **App/TA** (typical add-on context): `Splunk Connect for Kafka` (Splunkbase 3862), JMX. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: kafka; **sourcetype**: kafka:broker. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=kafka, sourcetype="kafka:broker". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where UnderReplicatedPartitions > 0` — typically the threshold or rule expression for this monitoring goal.
• `stats` rolls up events into metrics; results are split **by _time** so each row reflects one combination of those dimensions.
• `timechart` plots the metric over time using **span=5m** buckets — ideal for trending and alerting on this use case.


Step 3 — Validate
Compare with the broker or gateway’s own UI or CLI (`kafka-consumer-groups`, RabbitMQ management, ActiveMQ console, or Traefik/Envoy access log on the node) for the same period.


Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Single value (under-replicated count — target: 0), Line chart (under-replicated over time), Table (affected topics/partitions).

## SPL

```spl
index=kafka sourcetype="kafka:broker"
| where UnderReplicatedPartitions > 0
| stats sum(UnderReplicatedPartitions) as total_under_replicated by _time
| timechart span=5m max(total_under_replicated) as under_replicated
```

## Visualization

Single value (under-replicated count — target: 0), Line chart (under-replicated over time), Table (affected topics/partitions).

## References

- [Splunkbase app 3862](https://splunkbase.splunk.com/app/3862)
