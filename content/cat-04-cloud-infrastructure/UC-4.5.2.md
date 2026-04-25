<!-- AUTO-GENERATED from UC-4.5.2.json — DO NOT EDIT -->

---
id: "4.5.2"
title: "Lambda Cold Start and Init Duration Latency"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-4.5.2 · Lambda Cold Start and Init Duration Latency

## Description

Cold starts add tail latency to user-facing APIs and batch jobs; tracking Init Duration guides memory tuning, provisioned concurrency, and VPC design.

## Value

Cold starts add tail latency to user-facing APIs and batch jobs; tracking Init Duration guides memory tuning, provisioned concurrency, and VPC design.

## Implementation

Collect the `InitDuration` CloudWatch metric for each function. For log-based validation, subscribe Lambda log groups to Splunk and parse `REPORT` lines for `Init Duration`. Baseline p95/p99 init time per function and alert when cold-start latency breaches SLO after deploys or scaling events.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_aws`.
• Ensure the following data sources are available: `sourcetype=aws:cloudwatch` (`InitDuration`), optional `sourcetype=aws:cloudwatchlogs` (Lambda REPORT lines).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Collect the `InitDuration` CloudWatch metric for each function. For log-based validation, subscribe Lambda log groups to Splunk and parse `REPORT` lines for `Init Duration`. Baseline p95/p99 init time per function and alert when cold-start latency breaches SLO after deploys or scaling events.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/Lambda" metric_name="InitDuration"
| timechart span=5m avg(Average) as avg_init_ms, max(Maximum) as max_init_ms by FunctionName
| where avg_init_ms > 500
```

Understanding this SPL

**Lambda Cold Start and Init Duration Latency** — Cold starts add tail latency to user-facing APIs and batch jobs; tracking Init Duration guides memory tuning, provisioned concurrency, and VPC design.

Documented **Data sources**: `sourcetype=aws:cloudwatch` (`InitDuration`), optional `sourcetype=aws:cloudwatchlogs` (Lambda REPORT lines). **App/TA** (typical add-on context): `Splunk_TA_aws`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:cloudwatch. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=aws, sourcetype="aws:cloudwatch". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by FunctionName** — ideal for trending and alerting on this use case.
• Filters the current rows with `where avg_init_ms > 500` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (avg/max Init Duration by function), Box plot or percentile overlay (if precomputed), Table (FunctionName, p95 init ms).

## SPL

```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/Lambda" metric_name="InitDuration"
| timechart span=5m avg(Average) as avg_init_ms, max(Maximum) as max_init_ms by FunctionName
| where avg_init_ms > 500
```

## Visualization

Line chart (avg/max Init Duration by function), Box plot or percentile overlay (if precomputed), Table (FunctionName, p95 init ms).

## References

- [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)
