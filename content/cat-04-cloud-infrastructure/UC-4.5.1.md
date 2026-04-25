<!-- AUTO-GENERATED from UC-4.5.1.json — DO NOT EDIT -->

---
id: "4.5.1"
title: "Lambda Invocation Errors and Failed Invocations"
criticality: "high"
splunkPillar: "Observability"
---

# UC-4.5.1 · Lambda Invocation Errors and Failed Invocations

## Description

Failed Lambda invocations surface runtime bugs, dependency outages, and misconfiguration before they silently drop user traffic or break downstream workflows.

## Value

Failed Lambda invocations surface runtime bugs, dependency outages, and misconfiguration before they silently drop user traffic or break downstream workflows.

## Implementation

Enable CloudWatch metric collection for the Lambda namespace (Errors, Invocations). Ingest via Splunk_TA_aws. Optionally correlate with Lambda application logs from CloudWatch Logs subscription. Alert when error rate exceeds policy (for example 1–5% sustained over 15 minutes).

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_aws`.
• Ensure the following data sources are available: `sourcetype=aws:cloudwatch` (namespace `AWS/Lambda`).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable CloudWatch metric collection for the Lambda namespace (Errors, Invocations). Ingest via Splunk_TA_aws. Optionally correlate with Lambda application logs from CloudWatch Logs subscription. Alert when error rate exceeds policy (for example 1–5% sustained over 15 minutes).

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/Lambda" metric_name="Errors"
| timechart span=5m sum(Sum) as errors by FunctionName
| join max=1 FunctionName type=left
    [ search index=aws sourcetype="aws:cloudwatch" namespace="AWS/Lambda" metric_name="Invocations"
    | timechart span=5m sum(Sum) as invocations by FunctionName ]
| eval error_rate=if(invocations>0, round(100*errors/invocations, 2), 0)
| where error_rate > 1
```

Understanding this SPL

**Lambda Invocation Errors and Failed Invocations** — Failed Lambda invocations surface runtime bugs, dependency outages, and misconfiguration before they silently drop user traffic or break downstream workflows.

Documented **Data sources**: `sourcetype=aws:cloudwatch` (namespace `AWS/Lambda`). **App/TA** (typical add-on context): `Splunk_TA_aws`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:cloudwatch. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=aws, sourcetype="aws:cloudwatch". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by FunctionName** — ideal for trending and alerting on this use case.
• Joins to a subsearch with `join` — set `max=` to match cardinality and avoid silent truncation.
• `eval` defines or adjusts **error_rate** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where error_rate > 1` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (errors and invocations over time by function), Single value (error rate %), Table (FunctionName, errors, invocations, error_rate).

## SPL

```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/Lambda" metric_name="Errors"
| timechart span=5m sum(Sum) as errors by FunctionName
| join max=1 FunctionName type=left
    [ search index=aws sourcetype="aws:cloudwatch" namespace="AWS/Lambda" metric_name="Invocations"
    | timechart span=5m sum(Sum) as invocations by FunctionName ]
| eval error_rate=if(invocations>0, round(100*errors/invocations, 2), 0)
| where error_rate > 1
```

## Visualization

Line chart (errors and invocations over time by function), Single value (error rate %), Table (FunctionName, errors, invocations, error_rate).

## References

- [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)
