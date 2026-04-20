---
id: "7.1.27"
title: "Oracle Tablespace Utilization"
criticality: "high"
splunkPillar: "Observability"
---

# UC-7.1.27 · Oracle Tablespace Utilization

## Description

Approaching max size per tablespace causes ORA-1653 (out of space) errors and application failures. Proactive monitoring prevents outages.

## Value

Approaching max size per tablespace causes ORA-1653 (out of space) errors and application failures. Proactive monitoring prevents outages.

## Implementation

Poll `DBA_TABLESPACE_USAGE_METRICS` (or `DBA_FREE_SPACE` + `DBA_DATA_FILES`) via DB Connect every 4–6 hours. Extract used percent per tablespace. Alert at 80% (warning) and 90% (critical). Track growth rate for capacity planning. Include temp and undo tablespaces.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk DB Connect.
• Ensure the following data sources are available: `DBA_TABLESPACE_USAGE_METRICS`, `DBA_DATA_FILES`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll `DBA_TABLESPACE_USAGE_METRICS` (or `DBA_FREE_SPACE` + `DBA_DATA_FILES`) via DB Connect every 4–6 hours. Extract used percent per tablespace. Alert at 80% (warning) and 90% (critical). Track growth rate for capacity planning. Include temp and undo tablespaces.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=database sourcetype="dbconnect:oracle_tablespace"
| eval used_pct=round(USED_PERCENT, 1)
| where used_pct > 80
| timechart span=1d latest(used_pct) as used_pct by TABLESPACE_NAME
| where used_pct > 85
```

Understanding this SPL

**Oracle Tablespace Utilization** — Approaching max size per tablespace causes ORA-1653 (out of space) errors and application failures. Proactive monitoring prevents outages.

Documented **Data sources**: `DBA_TABLESPACE_USAGE_METRICS`, `DBA_DATA_FILES`. **App/TA** (typical add-on context): Splunk DB Connect. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: database; **sourcetype**: dbconnect:oracle_tablespace. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=database, sourcetype="dbconnect:oracle_tablespace". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **used_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where used_pct > 80` — typically the threshold or rule expression for this monitoring goal.
• `timechart` plots the metric over time using **span=1d** buckets with a separate series **by TABLESPACE_NAME** — ideal for trending and alerting on this use case.
• Filters the current rows with `where used_pct > 85` — typically the threshold or rule expression for this monitoring goal.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t count from datamodel=Databases.Tablespace by Tablespace.host, Tablespace.action span=1d | sort - count
```

Understanding this CIM / accelerated SPL

**Oracle Tablespace Utilization** — Approaching max size per tablespace causes ORA-1653 (out of space) errors and application failures. Proactive monitoring prevents outages.

Documented **Data sources**: `DBA_TABLESPACE_USAGE_METRICS`, `DBA_DATA_FILES`. **App/TA** (typical add-on context): Splunk DB Connect. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Databases.Tablespace` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Gauge (tablespace used %), Table (tablespaces over threshold), Line chart (utilization trend by tablespace).

## SPL

```spl
index=database sourcetype="dbconnect:oracle_tablespace"
| eval used_pct=round(USED_PERCENT, 1)
| where used_pct > 80
| timechart span=1d latest(used_pct) as used_pct by TABLESPACE_NAME
| where used_pct > 85
```

## CIM SPL

```spl
| tstats summariesonly=t count from datamodel=Databases.Tablespace by Tablespace.host, Tablespace.action span=1d | sort - count
```

## Visualization

Gauge (tablespace used %), Table (tablespaces over threshold), Line chart (utilization trend by tablespace).

## References

- [Splunk DB Connect](https://splunkbase.splunk.com/app/2686)
- [CIM: Databases](https://docs.splunk.com/Documentation/CIM/latest/User/Databases)
