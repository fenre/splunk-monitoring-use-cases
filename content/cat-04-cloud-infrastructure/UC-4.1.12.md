<!-- AUTO-GENERATED from UC-4.1.12.json — DO NOT EDIT -->

---
id: "4.1.12"
title: "Lambda Error Rate Monitoring"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-4.1.12 · Lambda Error Rate Monitoring

## Description

Lambda errors affect serverless application reliability. Timeouts indicate functions need more memory/time. Throttling means concurrency limits are hit.

## Value

Lambda errors affect serverless application reliability. Timeouts indicate functions need more memory/time. Throttling means concurrency limits are hit.

## Implementation

Ingest CloudWatch metrics (namespace `AWS/Lambda`, metrics `Errors`, `Invocations`, `Throttles`) via the Splunk Add-on for AWS. Compute error rate as `Errors/Invocations` over a 5-minute window; alert when rate exceeds 5% AND invocations exceed 50 (to avoid low-traffic false positives). For throttles, alert on any non-zero value. Forward Lambda CloudWatch Logs for stack trace correlation.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_aws`.
• Ensure the following data sources are available: `sourcetype=aws:cloudwatch` (Lambda namespace), Lambda logs.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Ingest CloudWatch metrics (namespace `AWS/Lambda`, metrics `Errors`, `Invocations`, `Throttles`) via the Splunk Add-on for AWS. Compute error rate as `Errors/Invocations` over a 5-minute window; alert when rate exceeds 5% AND invocations exceed 50 (to avoid low-traffic false positives). For throttles, alert on any non-zero value. Forward Lambda CloudWatch Logs for stack trace correlation.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/Lambda" (metric_name="Errors" OR metric_name="Throttles" OR metric_name="Duration")
| timechart span=5m sum(Sum) by metric_name, FunctionName
```

Understanding this SPL

**Lambda Error Rate Monitoring** — Lambda errors affect serverless application reliability. Timeouts indicate functions need more memory/time. Throttling means concurrency limits are hit.

Documented **Data sources**: `sourcetype=aws:cloudwatch` (Lambda namespace), Lambda logs. **App/TA** (typical add-on context): `Splunk_TA_aws`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:cloudwatch. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=aws, sourcetype="aws:cloudwatch". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by metric_name, FunctionName** — ideal for trending and alerting on this use case.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (errors/invocations over time), Bar chart (top error functions), Single value (error rate %).

## SPL

```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/Lambda" (metric_name="Errors" OR metric_name="Throttles" OR metric_name="Duration")
| timechart span=5m sum(Sum) by metric_name, FunctionName
```

## CIM SPL

```spl
| tstats `summariesonly` max(Performance.cpu_load_percent) as peak
  from datamodel=Performance.Performance
  by Performance.object Performance.host span=1h
| where isnotnull(peak)
| sort - peak
```

## Visualization

Line chart (errors/invocations over time), Bar chart (top error functions), Single value (error rate %).

## References

- [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)
