---
id: "4.1.38"
title: "EventBridge Rule Invocation and Failed Invocations"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-4.1.38 · EventBridge Rule Invocation and Failed Invocations

## Description

Failed invocations mean downstream targets (Lambda, SQS, etc.) are not receiving events. Critical for event-driven architecture reliability.

## Value

Failed invocations mean downstream targets (Lambda, SQS, etc.) are not receiving events. Critical for event-driven architecture reliability.

## Implementation

Collect EventBridge metrics per rule. Alert on FailedInvocations > 0. Correlate with target service (e.g. Lambda errors, SQS rejections) for root cause.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_aws`.
• Ensure the following data sources are available: CloudWatch EventBridge metrics (Invocations, FailedInvocations, TriggeredRules).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Collect EventBridge metrics per rule. Alert on FailedInvocations > 0. Correlate with target service (e.g. Lambda errors, SQS rejections) for root cause.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/Events" metric_name="FailedInvocations"
| where Sum > 0
| timechart span=5m sum(Sum) by RuleName
```

Understanding this SPL

**EventBridge Rule Invocation and Failed Invocations** — Failed invocations mean downstream targets (Lambda, SQS, etc.) are not receiving events. Critical for event-driven architecture reliability.

Documented **Data sources**: CloudWatch EventBridge metrics (Invocations, FailedInvocations, TriggeredRules). **App/TA** (typical add-on context): `Splunk_TA_aws`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:cloudwatch. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=aws, sourcetype="aws:cloudwatch". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where Sum > 0` — typically the threshold or rule expression for this monitoring goal.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by RuleName** — ideal for trending and alerting on this use case.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (rule, failures), Line chart (invocations vs failures), Single value.

## SPL

```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/Events" metric_name="FailedInvocations"
| where Sum > 0
| timechart span=5m sum(Sum) by RuleName
```

## Visualization

Table (rule, failures), Line chart (invocations vs failures), Single value.

## References

- [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)
