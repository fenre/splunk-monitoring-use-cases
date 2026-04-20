---
id: "4.1.54"
title: "Kinesis Data Stream Iterator Age and Throttling"
criticality: "high"
splunkPillar: "Observability"
---

# UC-4.1.54 · Kinesis Data Stream Iterator Age and Throttling

## Description

High iterator age means consumers are falling behind. Throttling indicates producers exceed shard capacity. Both cause lag and potential data loss.

## Value

High iterator age means consumers are falling behind. Throttling indicates producers exceed shard capacity. Both cause lag and potential data loss.

## Implementation

Collect Kinesis metrics. Alert when iterator age > 60 seconds (consumer lag). Alert on WriteProvisionedThroughputExceeded (add shards or reduce write rate). Monitor IncomingRecords/OutgoingRecords for throughput.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_aws`.
• Ensure the following data sources are available: CloudWatch Kinesis metrics (GetRecords.IteratorAgeMilliseconds, WriteProvisionedThroughputExceeded).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Collect Kinesis metrics. Alert when iterator age > 60 seconds (consumer lag). Alert on WriteProvisionedThroughputExceeded (add shards or reduce write rate). Monitor IncomingRecords/OutgoingRecords for throughput.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/Kinesis" metric_name="GetRecords.IteratorAgeMilliseconds"
| where Average > 60000
| timechart span=1m avg(Average) by StreamName
```

Understanding this SPL

**Kinesis Data Stream Iterator Age and Throttling** — High iterator age means consumers are falling behind. Throttling indicates producers exceed shard capacity. Both cause lag and potential data loss.

Documented **Data sources**: CloudWatch Kinesis metrics (GetRecords.IteratorAgeMilliseconds, WriteProvisionedThroughputExceeded). **App/TA** (typical add-on context): `Splunk_TA_aws`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:cloudwatch. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=aws, sourcetype="aws:cloudwatch". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where Average > 60000` — typically the threshold or rule expression for this monitoring goal.
• `timechart` plots the metric over time using **span=1m** buckets with a separate series **by StreamName** — ideal for trending and alerting on this use case.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (iterator age, throttles by stream), Table (stream, age ms), Single value (max lag).

## SPL

```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/Kinesis" metric_name="GetRecords.IteratorAgeMilliseconds"
| where Average > 60000
| timechart span=1m avg(Average) by StreamName
```

## Visualization

Line chart (iterator age, throttles by stream), Table (stream, age ms), Single value (max lag).

## References

- [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)
