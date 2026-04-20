---
id: "7.1.38"
title: "Query Plan Regression (Runtime vs Baseline)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-7.1.38 · Query Plan Regression (Runtime vs Baseline)

## Description

Compares current average CPU/duration from Query Store or AWR to baselines by `query_id`/`plan_hash`. Tightens UC-7.1.14 with explicit baseline lookup.

## Value

Compares current average CPU/duration from Query Store or AWR to baselines by `query_id`/`plan_hash`. Tightens UC-7.1.14 with explicit baseline lookup.

## Implementation

Refresh baseline lookup weekly from stable period. Alert on regression >40% with new `plan_id`. Consider force plan workflow.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: DB Connect, Query Store export.
• Ensure the following data sources are available: `sys.query_store_runtime_stats`, `dba_hist_sqlstat`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Refresh baseline lookup weekly from stable period. Alert on regression >40% with new `plan_id`. Consider force plan workflow.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=database sourcetype="dbconnect:query_store_runtime"
| stats avg(avg_cpu_time) as cur_cpu by query_id, plan_id
| lookup query_baselines query_id OUTPUT baseline_cpu_ms
| eval regression_pct=round((cur_cpu-baseline_cpu_ms)/baseline_cpu_ms*100,1)
| where regression_pct > 40
```

Understanding this SPL

**Query Plan Regression (Runtime vs Baseline)** — Compares current average CPU/duration from Query Store or AWR to baselines by `query_id`/`plan_hash`. Tightens UC-7.1.14 with explicit baseline lookup.

Documented **Data sources**: `sys.query_store_runtime_stats`, `dba_hist_sqlstat`. **App/TA** (typical add-on context): DB Connect, Query Store export. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: database; **sourcetype**: dbconnect:query_store_runtime. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=database, sourcetype="dbconnect:query_store_runtime". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by query_id, plan_id** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Enriches events using `lookup` (lookup definition + optional OUTPUT fields).
• `eval` defines or adjusts **regression_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where regression_pct > 40` — typically the threshold or rule expression for this monitoring goal.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t count from datamodel=Databases.Query by Query.host, Query.action | sort - count
```

Understanding this CIM / accelerated SPL

**Query Plan Regression (Runtime vs Baseline)** — Compares current average CPU/duration from Query Store or AWR to baselines by `query_id`/`plan_hash`. Tightens UC-7.1.14 with explicit baseline lookup.

Documented **Data sources**: `sys.query_store_runtime_stats`, `dba_hist_sqlstat`. **App/TA** (typical add-on context): DB Connect, Query Store export. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Databases.Query` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (regressed queries), Line chart (baseline vs current), Bar chart (regression %).

## SPL

```spl
index=database sourcetype="dbconnect:query_store_runtime"
| stats avg(avg_cpu_time) as cur_cpu by query_id, plan_id
| lookup query_baselines query_id OUTPUT baseline_cpu_ms
| eval regression_pct=round((cur_cpu-baseline_cpu_ms)/baseline_cpu_ms*100,1)
| where regression_pct > 40
```

## CIM SPL

```spl
| tstats summariesonly=t count from datamodel=Databases.Query by Query.host, Query.action | sort - count
```

## Visualization

Table (regressed queries), Line chart (baseline vs current), Bar chart (regression %).

## References

- [CIM: Databases](https://docs.splunk.com/Documentation/CIM/latest/User/Databases)
