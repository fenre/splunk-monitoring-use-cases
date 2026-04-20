---
id: "4.1.68"
title: "SQS Dead Letter Queue Growth"
criticality: "high"
splunkPillar: "Observability"
---

# UC-4.1.68 · SQS Dead Letter Queue Growth

## Description

DLQ depth growth means poison messages or downstream outages; rate-of-change highlights incidents faster than static thresholds.

## Value

DLQ depth growth means poison messages or downstream outages; rate-of-change highlights incidents faster than static thresholds.

## Implementation

Tag DLQs consistently for `*dlq*` matching or use explicit dimension. Alert on positive growth over 1h or depth exceeding SLO. Replay with caution after root-cause.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_aws`.
• Ensure the following data sources are available: `sourcetype=aws:cloudwatch` (AWS/SQS — ApproximateNumberOfMessagesVisible on DLQ ARNs).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Tag DLQs consistently for `*dlq*` matching or use explicit dimension. Alert on positive growth over 1h or depth exceeding SLO. Replay with caution after root-cause.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/SQS" metric_name="ApproximateNumberOfMessagesVisible" QueueName="*dlq*"
| sort 0 _time
| streamstats window=12 global=f first(Average) as prev by QueueName
| eval growth=Average-prev
| where growth > 10
| table _time QueueName Average growth
```

Understanding this SPL

**SQS Dead Letter Queue Growth** — DLQ depth growth means poison messages or downstream outages; rate-of-change highlights incidents faster than static thresholds.

Documented **Data sources**: `sourcetype=aws:cloudwatch` (AWS/SQS — ApproximateNumberOfMessagesVisible on DLQ ARNs). **App/TA** (typical add-on context): `Splunk_TA_aws`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:cloudwatch. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=aws, sourcetype="aws:cloudwatch". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
• `streamstats` rolls up events into metrics; results are split **by QueueName** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **growth** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where growth > 10` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **SQS Dead Letter Queue Growth**): table _time QueueName Average growth

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (DLQ depth), Single value (growth rate), Table (queue, depth).

## SPL

```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/SQS" metric_name="ApproximateNumberOfMessagesVisible" QueueName="*dlq*"
| sort 0 _time
| streamstats window=12 global=f first(Average) as prev by QueueName
| eval growth=Average-prev
| where growth > 10
| table _time QueueName Average growth
```

## Visualization

Line chart (DLQ depth), Single value (growth rate), Table (queue, depth).

## References

- [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)
