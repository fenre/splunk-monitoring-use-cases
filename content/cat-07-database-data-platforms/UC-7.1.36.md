---
id: "7.1.36"
title: "Index Fragmentation Maintenance Priority"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-7.1.36 · Index Fragmentation Maintenance Priority

## Description

Ranks indexes by fragmentation × page_count to schedule rebuilds during maintenance windows. Extends UC-7.1.9 with prioritization score.

## Value

Ranks indexes by fragmentation × page_count to schedule rebuilds during maintenance windows. Extends UC-7.1.9 with prioritization score.

## Implementation

Weekly job. Export top 50 for DBA runbook. Exclude tiny indexes via page_count floor.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: DB Connect.
• Ensure the following data sources are available: `sys.dm_db_index_physical_stats` (avg_fragmentation_in_percent, page_count).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Weekly job. Export top 50 for DBA runbook. Exclude tiny indexes via page_count floor.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=database sourcetype="dbconnect:index_stats"
| eval priority_score=avg_fragmentation_pct * page_count / 1000000
| where avg_fragmentation_pct > 30 AND page_count > 1000
| sort -priority_score
| head 50
```

Understanding this SPL

**Index Fragmentation Maintenance Priority** — Ranks indexes by fragmentation × page_count to schedule rebuilds during maintenance windows. Extends UC-7.1.9 with prioritization score.

Documented **Data sources**: `sys.dm_db_index_physical_stats` (avg_fragmentation_in_percent, page_count). **App/TA** (typical add-on context): DB Connect. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: database; **sourcetype**: dbconnect:index_stats. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=database, sourcetype="dbconnect:index_stats". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **priority_score** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where avg_fragmentation_pct > 30 AND page_count > 1000` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
• Limits the number of rows with `head`.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t count from datamodel=Databases.Instance_Stats by Instance_Stats.host, Instance_Stats.action | sort - count
```

Understanding this CIM / accelerated SPL

**Index Fragmentation Maintenance Priority** — Ranks indexes by fragmentation × page_count to schedule rebuilds during maintenance windows. Extends UC-7.1.9 with prioritization score.

Documented **Data sources**: `sys.dm_db_index_physical_stats` (avg_fragmentation_in_percent, page_count). **App/TA** (typical add-on context): DB Connect. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Databases.Instance_Stats` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (index, frag %, pages, score), Bar chart (top priority_score).

## SPL

```spl
index=database sourcetype="dbconnect:index_stats"
| eval priority_score=avg_fragmentation_pct * page_count / 1000000
| where avg_fragmentation_pct > 30 AND page_count > 1000
| sort -priority_score
| head 50
```

## CIM SPL

```spl
| tstats summariesonly=t count from datamodel=Databases.Instance_Stats by Instance_Stats.host, Instance_Stats.action | sort - count
```

## Visualization

Table (index, frag %, pages, score), Bar chart (top priority_score).

## References

- [CIM: Databases](https://docs.splunk.com/Documentation/CIM/latest/User/Databases)
