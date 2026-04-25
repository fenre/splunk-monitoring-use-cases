<!-- AUTO-GENERATED from UC-4.1.47.json — DO NOT EDIT -->

---
id: "4.1.47"
title: "Glue Job Run Failures and Duration"
criticality: "high"
splunkPillar: "Observability"
---

# UC-4.1.47 · Glue Job Run Failures and Duration

## Description

Glue job failures break ETL pipelines. Duration trends support capacity and cost optimization.

## Value

Glue job failures break ETL pipelines. Duration trends support capacity and cost optimization.

## Implementation

Collect Glue metrics. Alert when JobRunFailureCount > 0. Track JobRunDuration for SLA and DPU tuning. Ingest job run events from EventBridge for run-level detail.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_aws`.
• Ensure the following data sources are available: CloudWatch Glue metrics (JobRunFailureCount, JobRunDuration), Glue job run history.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Collect Glue metrics. Alert when JobRunFailureCount > 0. Track JobRunDuration for SLA and DPU tuning. Ingest job run events from EventBridge for run-level detail.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/Glue" metric_name="JobRunFailureCount"
| where Sum > 0
| timechart span=1h sum(Sum) by JobName
```

Understanding this SPL

**Glue Job Run Failures and Duration** — Glue job failures break ETL pipelines. Duration trends support capacity and cost optimization.

Documented **Data sources**: CloudWatch Glue metrics (JobRunFailureCount, JobRunDuration), Glue job run history. **App/TA** (typical add-on context): `Splunk_TA_aws`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:cloudwatch. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=aws, sourcetype="aws:cloudwatch". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where Sum > 0` — typically the threshold or rule expression for this monitoring goal.
• `timechart` plots the metric over time using **span=1h** buckets with a separate series **by JobName** — ideal for trending and alerting on this use case.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (failures, duration by job), Table (job, failure count), Single value.

## SPL

```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/Glue" metric_name="JobRunFailureCount"
| where Sum > 0
| timechart span=1h sum(Sum) by JobName
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  where match(All_Changes.app, "(?i)glue|lambda|logs")
  by All_Changes.user All_Changes.status span=1h
| sort -count
```

## Visualization

Line chart (failures, duration by job), Table (job, failure count), Single value.

## References

- [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)
