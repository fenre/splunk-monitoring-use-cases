<!-- AUTO-GENERATED from UC-8.1.9.json — DO NOT EDIT -->

---
id: "8.1.9"
title: "Slow POST Detection"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-8.1.9 · Slow POST Detection

## Description

Slow POST requests often indicate application-level performance issues (large form submissions, file uploads, database writes) distinct from slow GETs.

## Value

Slow POST requests often indicate application-level performance issues (large form submissions, file uploads, database writes) distinct from slow GETs.

## Implementation

Filter access logs for POST requests with high response times. Track by endpoint to identify specific bottlenecks. Correlate with backend database/API latency. Report top slow POST endpoints weekly.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_apache`, `TA-nginx`.
• Ensure the following data sources are available: Access logs with response time.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Filter access logs for POST requests with high response times. Track by endpoint to identify specific bottlenecks. Correlate with backend database/API latency. Report top slow POST endpoints weekly.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=web sourcetype="access_combined" method=POST
| where response_time > 5000
| stats count, avg(response_time) as avg_rt by uri_path
| sort -avg_rt
```

Understanding this SPL

**Slow POST Detection** — Slow POST requests often indicate application-level performance issues (large form submissions, file uploads, database writes) distinct from slow GETs.

Documented **Data sources**: Access logs with response time. **App/TA** (typical add-on context): `Splunk_TA_apache`, `TA-nginx`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: web; **sourcetype**: access_combined. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=web, sourcetype="access_combined". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where response_time > 5000` — typically the threshold or rule expression for this monitoring goal.
• `stats` rolls up events into metrics; results are split **by uri_path** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Compare with web server access logs on disk (Apache, NGINX, or W3C) for the same time range, or tail the same sourcetype in Search, to confirm status codes, URIs, and counts.


Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (slow POST endpoints), Bar chart (avg response time by URI), Line chart (slow POST count trend).

## SPL

```spl
index=web sourcetype="access_combined" method=POST
| where response_time > 5000
| stats count, avg(response_time) as avg_rt by uri_path
| sort -avg_rt
```

## CIM SPL

```spl
| tstats `summariesonly` perc95(Web.duration) as p95_ms count
  from datamodel=Web.Web
  where Web.http_method="POST"
  by Web.uri_path span=5m
| where p95_ms > 5000
```

## Visualization

Table (slow POST endpoints), Bar chart (avg response time by URI), Line chart (slow POST count trend).

## References

- [CIM: Web](https://docs.splunk.com/Documentation/CIM/latest/User/Web)
