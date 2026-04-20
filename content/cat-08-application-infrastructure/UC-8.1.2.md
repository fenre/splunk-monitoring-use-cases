---
id: "8.1.2"
title: "Response Time Trending"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.1.2 · Response Time Trending

## Description

Increasing response times degrade user experience before complete failures occur. Trending enables proactive optimization.

## Value

Increasing response times degrade user experience before complete failures occur. Trending enables proactive optimization.

## Implementation

Enable response time logging in web server config (Apache: `%D` in LogFormat, NGINX: `$request_time`). Track p50/p95/p99 percentiles. Alert on p95 exceeding SLA threshold. Correlate with backend service health.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_apache`, `TA-nginx`.
• Ensure the following data sources are available: Access logs with `%D` (Apache) or `$request_time` (NGINX).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable response time logging in web server config (Apache: `%D` in LogFormat, NGINX: `$request_time`). Track p50/p95/p99 percentiles. Alert on p95 exceeding SLA threshold. Correlate with backend service health.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=web sourcetype="access_combined"
| timechart span=5m perc95(response_time) as p95, avg(response_time) as avg_rt by host
| where p95 > 2000
```

Understanding this SPL

**Response Time Trending** — Increasing response times degrade user experience before complete failures occur. Trending enables proactive optimization.

Documented **Data sources**: Access logs with `%D` (Apache) or `$request_time` (NGINX). **App/TA** (typical add-on context): `Splunk_TA_apache`, `TA-nginx`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: web; **sourcetype**: access_combined. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=web, sourcetype="access_combined". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by host** — ideal for trending and alerting on this use case.
• Filters the current rows with `where p95 > 2000` — typically the threshold or rule expression for this monitoring goal.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` perc95(Web.duration) as p95_ms avg(Web.duration) as avg_ms
  from datamodel=Web.Web
  by Web.dest Web.uri_path span=5m
| where p95_ms > 2000
```

Understanding this CIM / accelerated SPL

**Response Time Trending** — Increasing response times degrade user experience before complete failures occur. Trending enables proactive optimization.

Documented **Data sources**: Access logs with `%D` (Apache) or `$request_time` (NGINX). **App/TA** (typical add-on context): `Splunk_TA_apache`, `TA-nginx`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Web.Web` — enable acceleration for that model.
• Filters the current rows with `where p95_ms > 2000` — typically the threshold or rule expression for this monitoring goal.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (p50/p95/p99 over time), Histogram (response time distribution), Table (slowest endpoints).

## SPL

```spl
index=web sourcetype="access_combined"
| timechart span=5m perc95(response_time) as p95, avg(response_time) as avg_rt by host
| where p95 > 2000
```

## CIM SPL

```spl
| tstats `summariesonly` perc95(Web.duration) as p95_ms avg(Web.duration) as avg_ms
  from datamodel=Web.Web
  by Web.dest Web.uri_path span=5m
| where p95_ms > 2000
```

## Visualization

Line chart (p50/p95/p99 over time), Histogram (response time distribution), Table (slowest endpoints).

## References

- [CIM: Web](https://docs.splunk.com/Documentation/CIM/latest/User/Web)
