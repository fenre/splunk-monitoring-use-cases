<!-- AUTO-GENERATED from UC-8.4.11.json — DO NOT EDIT -->

---
id: "8.4.11"
title: "AWS API Gateway 4xx/5xx Trends"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-8.4.11 · AWS API Gateway 4xx/5xx Trends

## Description

CloudWatch `4XXError`, `5XXError`, `Latency` per API stage. Single pane for serverless API frontends.

## Value

CloudWatch `4XXError`, `5XXError`, `Latency` per API stage. Single pane for serverless API frontends.

## Implementation

Enable detailed metrics per stage. Alert on 5XX >0 sustained or 4XX spike vs baseline. Join with Lambda logs for root cause.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_aws` CloudWatch.
• Ensure the following data sources are available: `AWS/ApiGateway` metrics, execution logs.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable detailed metrics per stage. Alert on 5XX >0 sustained or 4XX spike vs baseline. Join with Lambda logs for root cause.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/ApiGateway" metric_name IN ("4XXError","5XXError")
| timechart span=5m sum(Sum) as err by ApiName, Stage, metric_name
| where err > 0
```

Understanding this SPL

**AWS API Gateway 4xx/5xx Trends** — CloudWatch `4XXError`, `5XXError`, `Latency` per API stage. Single pane for serverless API frontends.

Documented **Data sources**: `AWS/ApiGateway` metrics, execution logs. **App/TA** (typical add-on context): `Splunk_TA_aws` CloudWatch. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:cloudwatch. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=aws, sourcetype="aws:cloudwatch". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by ApiName, Stage, metric_name** — ideal for trending and alerting on this use case.
• Filters the current rows with `where err > 0` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Compare with the API gateway or mesh admin (Kong, Apigee, AWS API Gateway, etc.) and a raw log tail for the same time range.


Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Stacked area (4xx vs 5xx), Line chart (error rate), Table (API, stage, errors).

## SPL

```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/ApiGateway" metric_name IN ("4XXError","5XXError")
| timechart span=5m sum(Sum) as err by ApiName, Stage, metric_name
| where err > 0
```

## CIM SPL

```spl
| tstats summariesonly=t count from datamodel=Web.Web by Web.status, Web.http_method, Web.dest span=5m | sort - count
```

## Visualization

Stacked area (4xx vs 5xx), Line chart (error rate), Table (API, stage, errors).

## References

- [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)
- [CIM: Web](https://docs.splunk.com/Documentation/CIM/latest/User/Web)
