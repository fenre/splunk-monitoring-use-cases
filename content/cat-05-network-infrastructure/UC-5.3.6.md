---
id: "5.3.6"
title: "Response Time Degradation (F5 BIG-IP)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.3.6 · Response Time Degradation (F5 BIG-IP)

## Description

Increasing response times indicate backend bottlenecks before they become outages.

## Value

Increasing response times indicate backend bottlenecks before they become outages.

## Implementation

Enable request logging with server-side timing. Track P95 latency per VIP. Alert when exceeding SLA threshold.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_f5-bigip`.
• Ensure the following data sources are available: F5 request logging (server_latency).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable request logging with server-side timing. Track P95 latency per VIP. Alert when exceeding SLA threshold.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network sourcetype="f5:bigip:ltm:http"
| timechart span=5m perc95(server_latency) as p95 by virtual_server | where p95>2000
```

Understanding this SPL

**Response Time Degradation (F5 BIG-IP)** — Increasing response times indicate backend bottlenecks before they become outages.

Documented **Data sources**: F5 request logging (server_latency). **App/TA** (typical add-on context): `Splunk_TA_f5-bigip`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: f5:bigip:ltm:http. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype="f5:bigip:ltm:http". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by virtual_server** — ideal for trending and alerting on this use case.
• Filters the current rows with `where p95>2000` — typically the threshold or rule expression for this monitoring goal.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` avg(Web.bytes) as avg_bytes count
  from datamodel=Web.Web
  by Web.uri_path Web.status span=5m
| sort -avg_bytes
```

Understanding this CIM / accelerated SPL

**Response Time Degradation (F5 BIG-IP)** — Increasing response times indicate backend bottlenecks before they become outages.

Documented **Data sources**: F5 request logging (server_latency). **App/TA** (typical add-on context): `Splunk_TA_f5-bigip`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Web.Web` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (P50/P95/P99), Table, Single value.

## SPL

```spl
index=network sourcetype="f5:bigip:ltm:http"
| timechart span=5m perc95(server_latency) as p95 by virtual_server | where p95>2000
```

## CIM SPL

```spl
| tstats `summariesonly` avg(Web.bytes) as avg_bytes count
  from datamodel=Web.Web
  by Web.uri_path Web.status span=5m
| sort -avg_bytes
```

## Visualization

Line chart (P50/P95/P99), Table, Single value.

## References

- [Splunk_TA_f5-bigip](https://splunkbase.splunk.com/app/2680)
- [CIM: Web](https://docs.splunk.com/Documentation/CIM/latest/User/Web)
