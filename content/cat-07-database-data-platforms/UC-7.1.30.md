---
id: "7.1.30"
title: "Oracle Tablespace Growth Trending"
criticality: "high"
splunkPillar: "Observability"
---

# UC-7.1.30 · Oracle Tablespace Growth Trending

## Description

Week-over-week growth rate per tablespace drives forecast and ASM/space procurement. Extends point-in-time utilization with trend.

## Value

Week-over-week growth rate per tablespace drives forecast and ASM/space procurement. Extends point-in-time utilization with trend.

## Implementation

Daily snapshot. Alert on >10GB/week growth on critical tablespaces. Use `predict` on used_bytes for runway to maxsize.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: DB Connect.
• Ensure the following data sources are available: `DBA_TABLESPACE_USAGE_METRICS` (used_space, tablespace_size).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Daily snapshot. Alert on >10GB/week growth on critical tablespaces. Use `predict` on used_bytes for runway to maxsize.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=database sourcetype="dbconnect:oracle_tablespace"
| timechart span=1d latest(USED_SPACE) as used_bytes by TABLESPACE_NAME
| streamstats window=7 range(used_bytes) as growth_7d by TABLESPACE_NAME
| eval growth_gb=round(growth_7d/1073741824,2)
| where growth_gb > 10
```

Understanding this SPL

**Oracle Tablespace Growth Trending** — Week-over-week growth rate per tablespace drives forecast and ASM/space procurement. Extends point-in-time utilization with trend.

Documented **Data sources**: `DBA_TABLESPACE_USAGE_METRICS` (used_space, tablespace_size). **App/TA** (typical add-on context): DB Connect. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: database; **sourcetype**: dbconnect:oracle_tablespace. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=database, sourcetype="dbconnect:oracle_tablespace". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=1d** buckets with a separate series **by TABLESPACE_NAME** — ideal for trending and alerting on this use case.
• `streamstats` rolls up events into metrics; results are split **by TABLESPACE_NAME** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **growth_gb** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where growth_gb > 10` — typically the threshold or rule expression for this monitoring goal.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t count from datamodel=Databases.Tablespace by Tablespace.host, Tablespace.action span=1d | sort - count
```

Understanding this CIM / accelerated SPL

**Oracle Tablespace Growth Trending** — Week-over-week growth rate per tablespace drives forecast and ASM/space procurement. Extends point-in-time utilization with trend.

Documented **Data sources**: `DBA_TABLESPACE_USAGE_METRICS` (used_space, tablespace_size). **App/TA** (typical add-on context): DB Connect. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Databases.Tablespace` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (used GB trend), Table (tablespace, growth GB/week), Single value (fastest growing).

## SPL

```spl
index=database sourcetype="dbconnect:oracle_tablespace"
| timechart span=1d latest(USED_SPACE) as used_bytes by TABLESPACE_NAME
| streamstats window=7 range(used_bytes) as growth_7d by TABLESPACE_NAME
| eval growth_gb=round(growth_7d/1073741824,2)
| where growth_gb > 10
```

## CIM SPL

```spl
| tstats summariesonly=t count from datamodel=Databases.Tablespace by Tablespace.host, Tablespace.action span=1d | sort - count
```

## Visualization

Line chart (used GB trend), Table (tablespace, growth GB/week), Single value (fastest growing).

## References

- [CIM: Databases](https://docs.splunk.com/Documentation/CIM/latest/User/Databases)
