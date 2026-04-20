---
id: "8.1.16"
title: "Web Server Thread Pool Exhaustion"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.1.16 · Web Server Thread Pool Exhaustion

## Description

IIS `QueueFull`, NGINX worker saturation, or Apache `BusyWorkers` at limit causes queueing. Unified thresholding across stacks.

## Value

IIS `QueueFull`, NGINX worker saturation, or Apache `BusyWorkers` at limit causes queueing. Unified thresholding across stacks.

## Implementation

Normalize field names at ingest. Alert when util >85% for 10m or IIS request queue length sustained high. Correlate with CPU and backend latency.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `TA-nginx` stub_status, `Splunk_TA_windows` perfmon, Apache mod_status.
• Ensure the following data sources are available: `nginx:stub_status`, `Perfmon:W3SVC_W3WP`, `apache:server_status`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Normalize field names at ingest. Alert when util >85% for 10m or IIS request queue length sustained high. Correlate with CPU and backend latency.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=web (sourcetype="nginx:stub_status" OR sourcetype="apache:server_status" OR sourcetype="Perfmon:W3SVC_W3WP")
| eval util_pct=coalesce(worker_util_pct, pct_busy, thread_pool_queue_length/max_threads*100)
| where util_pct > 85 OR queue_current > 50
| timechart span=5m max(util_pct) as util by host, sourcetype
```

Understanding this SPL

**Web Server Thread Pool Exhaustion** — IIS `QueueFull`, NGINX worker saturation, or Apache `BusyWorkers` at limit causes queueing. Unified thresholding across stacks.

Documented **Data sources**: `nginx:stub_status`, `Perfmon:W3SVC_W3WP`, `apache:server_status`. **App/TA** (typical add-on context): `TA-nginx` stub_status, `Splunk_TA_windows` perfmon, Apache mod_status. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: web; **sourcetype**: nginx:stub_status, apache:server_status, Perfmon:W3SVC_W3WP. Those sourcetypes align with what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=web, sourcetype="nginx:stub_status". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **util_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where util_pct > 85 OR queue_current > 50` — typically the threshold or rule expression for this monitoring goal.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by host, sourcetype** — ideal for trending and alerting on this use case.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t count from datamodel=Web.Web by Web.dest span=5m | sort - count
```

Understanding this CIM / accelerated SPL

**Web Server Thread Pool Exhaustion** — IIS `QueueFull`, NGINX worker saturation, or Apache `BusyWorkers` at limit causes queueing. Unified thresholding across stacks.

Documented **Data sources**: `nginx:stub_status`, `Perfmon:W3SVC_W3WP`, `apache:server_status`. **App/TA** (typical add-on context): `TA-nginx` stub_status, `Splunk_TA_windows` perfmon, Apache mod_status. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Web.Web` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Gauge (util %), Line chart (util and queue), Table (hosts over threshold).

## SPL

```spl
index=web (sourcetype="nginx:stub_status" OR sourcetype="apache:server_status" OR sourcetype="Perfmon:W3SVC_W3WP")
| eval util_pct=coalesce(worker_util_pct, pct_busy, thread_pool_queue_length/max_threads*100)
| where util_pct > 85 OR queue_current > 50
| timechart span=5m max(util_pct) as util by host, sourcetype
```

## CIM SPL

```spl
| tstats summariesonly=t count from datamodel=Web.Web by Web.dest span=5m | sort - count
```

## Visualization

Gauge (util %), Line chart (util and queue), Table (hosts over threshold).

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
- [CIM: Web](https://docs.splunk.com/Documentation/CIM/latest/User/Web)
