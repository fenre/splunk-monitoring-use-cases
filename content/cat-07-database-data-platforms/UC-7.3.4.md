<!-- AUTO-GENERATED from UC-7.3.4.json — DO NOT EDIT -->

---
id: "7.3.4"
title: "Storage Auto-Scaling Events"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-7.3.4 · Storage Auto-Scaling Events

## Description

Tracks storage auto-scaling events for cost awareness and identifies databases with rapid growth needing attention.

## Value

Tracks storage auto-scaling events for cost awareness and identifies databases with rapid growth needing attention.

## Implementation

Ingest CloudTrail events. Filter for storage modification events. Track growth frequency per database. Alert when auto-scaling occurs more than twice per week, indicating rapid growth needing review.

## Detailed Implementation

Prerequisites
• In operations we confirm in MySQL Workbench, Percona tools, or the managed MySQL console.
• Install and configure the required add-on or app: Cloud provider TAs.
• Ensure the following data sources are available: CloudTrail (ModifyDBInstance), Azure Activity Log.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Ingest CloudTrail events. Filter for storage modification events. Track growth frequency per database. Alert when auto-scaling occurs more than twice per week, indicating rapid growth needing review.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:cloudtrail" eventName="ModifyDBInstance"
| spath output=allocated requestParameters.allocatedStorage
| where isnotnull(allocated)
| table _time, requestParameters.dBInstanceIdentifier, allocated, userIdentity.principalId
```

Understanding this SPL

**Storage Auto-Scaling Events** — Tracks storage auto-scaling events for cost awareness and identifies databases with rapid growth needing attention.

Documented **Data sources**: CloudTrail (ModifyDBInstance), Azure Activity Log. **App/TA** (typical add-on context): Cloud provider TAs. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:cloudtrail. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=aws, sourcetype="aws:cloudtrail". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Extracts structured paths (JSON/XML) with `spath`.
• Filters the current rows with `where isnotnull(allocated)` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Storage Auto-Scaling Events**): table _time, requestParameters.dBInstanceIdentifier, allocated, userIdentity.principalId


Step 3 — Validate
For the same time range, compare Splunk results with the engine’s own tools and system views (SQL Server: SQL Server Management Studio and `sys.dm_*`; Oracle: Oracle Enterprise Manager, SQLcl, or `V$` views; MySQL: Workbench or `performance_schema` / `SHOW` output; PostgreSQL: `pg_stat_*` in psql or pgAdmin; MongoDB: mongosh or Atlas metrics; Cassandra: nodetool; Elasticsearch/OpenSearch: Kibana or REST `_cat` / `_cluster/health`; ClickHouse: `system` tables in clickhouse-client; Snowflake: Snowsight or `ACCOUNT_USAGE`; others: the managed PaaS console). Confirm event counts, field names, timestamps, and Splunk role permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Timeline (scaling events), Table (databases with scaling history), Bar chart (scaling frequency by database).

## SPL

```spl
index=aws sourcetype="aws:cloudtrail" eventName="ModifyDBInstance"
| spath output=allocated requestParameters.allocatedStorage
| where isnotnull(allocated)
| table _time, requestParameters.dBInstanceIdentifier, allocated, userIdentity.principalId
```

## Visualization

Timeline (scaling events), Table (databases with scaling history), Bar chart (scaling frequency by database).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
