---
id: "4.3.35"
title: "Cloud SQL Connection Limits"
criticality: "high"
splunkPillar: "Observability"
---

# UC-4.3.35 · Cloud SQL Connection Limits

## Description

Hitting max connections causes application errors; trending connections versus tier limits guides pool sizing and read replicas.

## Value

Hitting max connections causes application errors; trending connections versus tier limits guides pool sizing and read replicas.

## Implementation

Maintain lookup of instance tier to max connections. Alert at 85% sustained. Correlate with connection pool metrics from apps. Plan vertical scale or read replicas before hard failures.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_google-cloudplatform`.
• Ensure the following data sources are available: `sourcetype=google:gcp:monitoring` (`cloudsql.googleapis.com/database/network/connections`, `postgresql.googleapis.com/connection_count`).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Maintain lookup of instance tier to max connections. Alert at 85% sustained. Correlate with connection pool metrics from apps. Plan vertical scale or read replicas before hard failures.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=gcp sourcetype="google:gcp:monitoring" metric.type="cloudsql.googleapis.com/database/network/connections"
| stats latest(value) as conns by resource.labels.database_id, bin(_time, 5m)
| lookup cloudsql_tier_limits database_id OUTPUT max_connections
| where conns > max_connections * 0.85
```

Understanding this SPL

**Cloud SQL Connection Limits** — Hitting max connections causes application errors; trending connections versus tier limits guides pool sizing and read replicas.

Documented **Data sources**: `sourcetype=google:gcp:monitoring` (`cloudsql.googleapis.com/database/network/connections`, `postgresql.googleapis.com/connection_count`). **App/TA** (typical add-on context): `Splunk_TA_google-cloudplatform`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: gcp; **sourcetype**: google:gcp:monitoring. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=gcp, sourcetype="google:gcp:monitoring". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by resource.labels.database_id, bin(_time, 5m)** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Enriches events using `lookup` (lookup definition + optional OUTPUT fields).
• Filters the current rows with `where conns > max_connections * 0.85` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (connections vs limit), Gauge (utilization %), Table (instance, conns).

## SPL

```spl
index=gcp sourcetype="google:gcp:monitoring" metric.type="cloudsql.googleapis.com/database/network/connections"
| stats latest(value) as conns by resource.labels.database_id, bin(_time, 5m)
| lookup cloudsql_tier_limits database_id OUTPUT max_connections
| where conns > max_connections * 0.85
```

## Visualization

Line chart (connections vs limit), Gauge (utilization %), Table (instance, conns).

## References

- [Splunk_TA_google-cloudplatform](https://splunkbase.splunk.com/app/3088)
