---
id: "4.5.13"
title: "Lambda Provisioned Concurrency Utilization"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-4.5.13 · Lambda Provisioned Concurrency Utilization

## Description

Provisioned concurrency is a fixed cost; low utilization wastes spend while high utilization risks cold starts on overflow—balance requires continuous measurement.

## Value

Provisioned concurrency is a fixed cost; low utilization wastes spend while high utilization risks cold starts on overflow—balance requires continuous measurement.

## Implementation

Collect `ProvisionedConcurrencyUtilization` for each alias or version with provisioned settings. Compare against provisioned units from tags or CloudFormation export. Alert when utilization is chronically low (cost optimization) or high (risk of throttling on burst beyond provisioned pool).

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_aws`.
• Ensure the following data sources are available: `sourcetype=aws:cloudwatch` (namespace `AWS/Lambda`).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Collect `ProvisionedConcurrencyUtilization` for each alias or version with provisioned settings. Compare against provisioned units from tags or CloudFormation export. Alert when utilization is chronically low (cost optimization) or high (risk of throttling on burst beyond provisioned pool).

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/Lambda" metric_name="ProvisionedConcurrencyUtilization"
| timechart span=5m avg(Average) as util by FunctionName, Resource
| where util < 0.2 OR util > 0.9
```

Understanding this SPL

**Lambda Provisioned Concurrency Utilization** — Provisioned concurrency is a fixed cost; low utilization wastes spend while high utilization risks cold starts on overflow—balance requires continuous measurement.

Documented **Data sources**: `sourcetype=aws:cloudwatch` (namespace `AWS/Lambda`). **App/TA** (typical add-on context): `Splunk_TA_aws`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:cloudwatch. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=aws, sourcetype="aws:cloudwatch". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by FunctionName, Resource** — ideal for trending and alerting on this use case.
• Filters the current rows with `where util < 0.2 OR util > 0.9` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (utilization by function/alias), Area chart (consumed vs provisioned concurrency), Table (FunctionName, util %, recommended units).

## SPL

```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/Lambda" metric_name="ProvisionedConcurrencyUtilization"
| timechart span=5m avg(Average) as util by FunctionName, Resource
| where util < 0.2 OR util > 0.9
```

## Visualization

Line chart (utilization by function/alias), Area chart (consumed vs provisioned concurrency), Table (FunctionName, util %, recommended units).

## References

- [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)
