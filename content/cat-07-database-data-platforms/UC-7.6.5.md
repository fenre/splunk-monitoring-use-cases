---
id: "7.6.5"
title: "Index Fragmentation Trending"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-7.6.5 · Index Fragmentation Trending

## Description

Average fragmentation percentage over 30 days guides `REBUILD`/`REORG` scheduling and fill-factor reviews. Slow upward trends on hot tables correlate with extra I/O and slower queries even when CPU looks healthy.

## Value

Average fragmentation percentage over 30 days guides `REBUILD`/`REORG` scheduling and fill-factor reviews. Slow upward trends on hot tables correlate with extra I/O and slower queries even when CPU looks healthy.

## Implementation

Sample large catalogs during off-peak windows to control license cost. Exclude tiny tables where fragmentation is meaningless. Join `table_name` to owner/schema for remediation tickets. PostgreSQL bloat metrics may use different units—normalize in `eval`. Pair with maintenance windows from change records.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: SQL Server DMVs via scripted input, MySQL `information_schema` / InnoDB metrics, Oracle segment advisor exports.
• Ensure the following data sources are available: `index=db` `sourcetype=mssql:fragmentation`, `sourcetype=mysql:innodb`, `sourcetype=oracle:segment`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Sample large catalogs during off-peak windows to control license cost. Exclude tiny tables where fragmentation is meaningless. Join `table_name` to owner/schema for remediation tickets. PostgreSQL bloat metrics may use different units—normalize in `eval`. Pair with maintenance windows from change records.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=db sourcetype IN ("mssql:fragmentation","mysql:innodb","oracle:segment","postgresql:index")
| eval frag_pct=coalesce(avg_fragmentation_in_percent, fragmentation_pct, bloat_ratio*100)
| where isnotnull(frag_pct)
| timechart span=1d avg(frag_pct) as avg_fragmentation_pct max(frag_pct) as max_fragmentation_pct by table_name limit=12
```

Understanding this SPL

**Index Fragmentation Trending** — Average fragmentation percentage over 30 days guides `REBUILD`/`REORG` scheduling and fill-factor reviews. Slow upward trends on hot tables correlate with extra I/O and slower queries even when CPU looks healthy.

Documented **Data sources**: `index=db` `sourcetype=mssql:fragmentation`, `sourcetype=mysql:innodb`, `sourcetype=oracle:segment`. **App/TA** (typical add-on context): SQL Server DMVs via scripted input, MySQL `information_schema` / InnoDB metrics, Oracle segment advisor exports. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: db.

**Pipeline walkthrough**

• Scopes the data: index=db. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **frag_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where isnotnull(frag_pct)` — typically the threshold or rule expression for this monitoring goal.
• `timechart` plots the metric over time using **span=1d** buckets with a separate series **by table_name limit=12** — ideal for trending and alerting on this use case.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (fragmentation % over time), heatmap (table × week), table (tables exceeding DBA threshold).

## SPL

```spl
index=db sourcetype IN ("mssql:fragmentation","mysql:innodb","oracle:segment","postgresql:index")
| eval frag_pct=coalesce(avg_fragmentation_in_percent, fragmentation_pct, bloat_ratio*100)
| where isnotnull(frag_pct)
| timechart span=1d avg(frag_pct) as avg_fragmentation_pct max(frag_pct) as max_fragmentation_pct by table_name limit=12
```

## Visualization

Line chart (fragmentation % over time), heatmap (table × week), table (tables exceeding DBA threshold).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
