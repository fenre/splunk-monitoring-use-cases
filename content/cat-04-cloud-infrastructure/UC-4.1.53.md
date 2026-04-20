---
id: "4.1.53"
title: "CloudWatch Logs Subscription Filter Errors"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-4.1.53 · CloudWatch Logs Subscription Filter Errors

## Description

Subscription filter delivery failures mean logs are not reaching Lambda, Kinesis, or Firehose. Indicates quota, permission, or downstream failures.

## Value

Subscription filter delivery failures mean logs are not reaching Lambda, Kinesis, or Firehose. Indicates quota, permission, or downstream failures.

## Implementation

Create CloudWatch metric filter for subscription delivery errors if available, or monitor Kinesis/Firehose delivery errors. Alert when delivery errors spike. Check Lambda/Kinesis throttling and IAM permissions.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_aws`.
• Ensure the following data sources are available: CloudWatch Logs metric filters (IncomingLogEvents, DeliveryErrors), or destination-specific metrics.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Create CloudWatch metric filter for subscription delivery errors if available, or monitor Kinesis/Firehose delivery errors. Alert when delivery errors spike. Check Lambda/Kinesis throttling and IAM permissions.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/Logs" metric_name="DeliveryErrors"
| where Sum > 0
| timechart span=5m sum(Sum) by LogGroupName, FilterName
```

Understanding this SPL

**CloudWatch Logs Subscription Filter Errors** — Subscription filter delivery failures mean logs are not reaching Lambda, Kinesis, or Firehose. Indicates quota, permission, or downstream failures.

Documented **Data sources**: CloudWatch Logs metric filters (IncomingLogEvents, DeliveryErrors), or destination-specific metrics. **App/TA** (typical add-on context): `Splunk_TA_aws`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:cloudwatch. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=aws, sourcetype="aws:cloudwatch". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where Sum > 0` — typically the threshold or rule expression for this monitoring goal.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by LogGroupName, FilterName** — ideal for trending and alerting on this use case.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (log group, filter, errors), Line chart (delivery errors over time), Single value.

## SPL

```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/Logs" metric_name="DeliveryErrors"
| where Sum > 0
| timechart span=5m sum(Sum) by LogGroupName, FilterName
```

## Visualization

Table (log group, filter, errors), Line chart (delivery errors over time), Single value.

## References

- [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)
