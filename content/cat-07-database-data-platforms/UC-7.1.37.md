---
id: "7.1.37"
title: "Temp Tablespace Usage (Oracle TEMP)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-7.1.37 · Temp Tablespace Usage (Oracle TEMP)

## Description

High `TEMP` usage for sorts and hashes causes ORA-1652. Tracks session temp consumption vs temp tablespace limits.

## Value

High `TEMP` usage for sorts and hashes causes ORA-1652. Tracks session temp consumption vs temp tablespace limits.

## Implementation

Poll `V$TEMPSEG_USAGE` every 5m. Alert at 85% of temp max. Identify top SQL by `sql_id` from same view.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: DB Connect.
• Ensure the following data sources are available: `V$TEMPSEG_USAGE`, `DBA_TEMP_FREE_SPACE`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll `V$TEMPSEG_USAGE` every 5m. Alert at 85% of temp max. Identify top SQL by `sql_id` from same view.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=database sourcetype="dbconnect:oracle_temp"
| stats sum(blocks_used) as used_blocks by tablespace_name, session_addr
| eventstats sum(used_blocks) as total_used by tablespace_name
| lookup oracle_temp_space tablespace_name OUTPUT max_blocks
| where total_used > max_blocks*0.85
| table tablespace_name total_used max_blocks
```

Understanding this SPL

**Temp Tablespace Usage (Oracle TEMP)** — High `TEMP` usage for sorts and hashes causes ORA-1652. Tracks session temp consumption vs temp tablespace limits.

Documented **Data sources**: `V$TEMPSEG_USAGE`, `DBA_TEMP_FREE_SPACE`. **App/TA** (typical add-on context): DB Connect. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: database; **sourcetype**: dbconnect:oracle_temp. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=database, sourcetype="dbconnect:oracle_temp". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by tablespace_name, session_addr** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eventstats` rolls up events into metrics; results are split **by tablespace_name** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Enriches events using `lookup` (lookup definition + optional OUTPUT fields).
• Filters the current rows with `where total_used > max_blocks*0.85` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Temp Tablespace Usage (Oracle TEMP)**): table tablespace_name total_used max_blocks

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t count from datamodel=Databases.Lock_Stats by Lock_Stats.host, Lock_Stats.action | sort - count
```

Understanding this CIM / accelerated SPL

**Temp Tablespace Usage (Oracle TEMP)** — High `TEMP` usage for sorts and hashes causes ORA-1652. Tracks session temp consumption vs temp tablespace limits.

Documented **Data sources**: `V$TEMPSEG_USAGE`, `DBA_TEMP_FREE_SPACE`. **App/TA** (typical add-on context): DB Connect. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Databases.Lock_Stats` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (temp usage %), Table (sessions using temp), Single value (peak temp GB).

## SPL

```spl
index=database sourcetype="dbconnect:oracle_temp"
| stats sum(blocks_used) as used_blocks by tablespace_name, session_addr
| eventstats sum(used_blocks) as total_used by tablespace_name
| lookup oracle_temp_space tablespace_name OUTPUT max_blocks
| where total_used > max_blocks*0.85
| table tablespace_name total_used max_blocks
```

## CIM SPL

```spl
| tstats summariesonly=t count from datamodel=Databases.Lock_Stats by Lock_Stats.host, Lock_Stats.action | sort - count
```

## Visualization

Line chart (temp usage %), Table (sessions using temp), Single value (peak temp GB).

## References

- [CIM: Databases](https://docs.splunk.com/Documentation/CIM/latest/User/Databases)
