<!-- AUTO-GENERATED from UC-8.4.1.json — DO NOT EDIT -->

---
id: "8.4.1"
title: "API Error Rate by Endpoint"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-8.4.1 · API Error Rate by Endpoint

## Description

Per-endpoint error rates pinpoint failing services, enabling targeted debugging rather than broad investigation.

## Value

Per-endpoint error rates pinpoint failing services, enabling targeted debugging rather than broad investigation.

## Implementation

Forward API gateway access logs to Splunk. Parse endpoint, status code, latency, and consumer identity. Calculate error rates per endpoint. Alert when any endpoint exceeds error threshold. Break down by 4xx vs 5xx.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom log input, gateway access logs.
• Ensure the following data sources are available: API gateway access logs (Kong, Apigee, AWS API Gateway).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Forward API gateway access logs to Splunk. Parse endpoint, status code, latency, and consumer identity. Calculate error rates per endpoint. Alert when any endpoint exceeds error threshold. Break down by 4xx vs 5xx.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=api sourcetype="kong:access"
| eval is_error=if(status>=400,1,0)
| stats count, sum(is_error) as errors by request_uri, upstream_service
| eval error_rate=round(errors/count*100,2)
| where error_rate > 5
| sort -error_rate
```

Understanding this SPL

**API Error Rate by Endpoint** — Per-endpoint error rates pinpoint failing services, enabling targeted debugging rather than broad investigation.

Documented **Data sources**: API gateway access logs (Kong, Apigee, AWS API Gateway). **App/TA** (typical add-on context): Custom log input, gateway access logs. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: api; **sourcetype**: kong:access. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=api, sourcetype="kong:access". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **is_error** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by request_uri, upstream_service** so each row reflects one combination of those dimensions.
• `eval` defines or adjusts **error_rate** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where error_rate > 5` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Compare with the API gateway or mesh admin (Kong, Apigee, AWS API Gateway, etc.) and a raw log tail for the same time range.


Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (endpoints with error rates), Bar chart (error rate by endpoint), Line chart (error rate trend per endpoint).

## SPL

```spl
index=api sourcetype="kong:access"
| eval is_error=if(status>=400,1,0)
| stats count, sum(is_error) as errors by request_uri, upstream_service
| eval error_rate=round(errors/count*100,2)
| where error_rate > 5
| sort -error_rate
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Web.Web
  where Web.status>=400
  by Web.src Web.uri_path Web.status span=5m
| sort -count
```

## Visualization

Table (endpoints with error rates), Bar chart (error rate by endpoint), Line chart (error rate trend per endpoint).

## References

- [CIM: Web](https://docs.splunk.com/Documentation/CIM/latest/User/Web)
