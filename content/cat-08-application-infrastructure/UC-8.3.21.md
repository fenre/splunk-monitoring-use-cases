---
id: "8.3.21"
title: "MSMQ Queue Depth Monitoring"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.3.21 · MSMQ Queue Depth Monitoring

## Description

Message queue buildup indicates application processing failures. Monitoring queue depth prevents message loss and detects downstream system outages.

## Value

Message queue buildup indicates application processing failures. Monitoring queue depth prevents message loss and detects downstream system outages.

## Implementation

Configure Perfmon input for MSMQ Service counters: Total Messages in all Queues, Total Bytes in all Queues, Sessions. Also monitor individual queue counters via `MSMQ Queue` object. Alert when queue depth exceeds baseline (messages accumulating). Monitor journal queue size for message delivery confirmations. Track dead-letter queue growth for undeliverable messages.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=Perfmon:MSMQ`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Configure Perfmon input for MSMQ Service counters: Total Messages in all Queues, Total Bytes in all Queues, Sessions. Also monitor individual queue counters via `MSMQ Queue` object. Alert when queue depth exceeds baseline (messages accumulating). Monitor journal queue size for message delivery confirmations. Track dead-letter queue growth for undeliverable messages.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=perfmon source="Perfmon:MSMQ Service" counter="Total Messages in all Queues"
| timechart span=5m avg(Value) as AvgQueueDepth by host
| foreach * [eval <<FIELD>>=round('<<FIELD>>', 0)]
```

Understanding this SPL

**MSMQ Queue Depth Monitoring** — Message queue buildup indicates application processing failures. Monitoring queue depth prevents message loss and detects downstream system outages.

Documented **Data sources**: `sourcetype=Perfmon:MSMQ`. **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: perfmon.

**Pipeline walkthrough**

• Scopes the data: index=perfmon. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by host** — ideal for trending and alerting on this use case.
• Iterates over multivalue fields with `foreach`.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Timechart (queue depth trend), Single value (current depth), Alert on queue growth exceeding threshold.

## SPL

```spl
index=perfmon source="Perfmon:MSMQ Service" counter="Total Messages in all Queues"
| timechart span=5m avg(Value) as AvgQueueDepth by host
| foreach * [eval <<FIELD>>=round('<<FIELD>>', 0)]
```

## Visualization

Timechart (queue depth trend), Single value (current depth), Alert on queue growth exceeding threshold.

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
