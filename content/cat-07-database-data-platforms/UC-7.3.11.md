<!-- AUTO-GENERATED from UC-7.3.11.json — DO NOT EDIT -->

---
id: "7.3.11"
title: "Managed Database Failover Events (Multi-Cloud)"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-7.3.11 · Managed Database Failover Events (Multi-Cloud)

## Description

Single search across RDS failover, Azure SQL failover, and Cloud SQL failover for hybrid teams. Supplements UC-7.3.2 with normalized fields.

## Value

Single search across RDS failover, Azure SQL failover, and Cloud SQL failover for hybrid teams. Supplements UC-7.3.2 with normalized fields.

## Implementation

Normalize resource identifiers in CIM-style fields at ingest. Route to incident workflow with application dependency tags.

## Detailed Implementation

Prerequisites
• In operations we align Splunk with the cloud provider’s database console and metrics to rule out a platform maintenance window.
• Install and configure the required add-on or app: CloudTrail, Azure Activity Log, GCP Audit Logs.
• Ensure the following data sources are available: `Failover`, `failover`, `switchover` events.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Normalize resource identifiers in CIM-style fields at ingest. Route to incident workflow with application dependency tags.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
(index=aws sourcetype="aws:cloudwatch:events") OR (index=azure sourcetype="azure:activity") OR (index=gcp sourcetype="gcp:audit")
| search failover OR Failover OR switchover
| eval cloud=case(index=="aws","AWS", index=="azure","Azure", index=="gcp","GCP",1=1,"unknown")
| table _time, cloud, resource_name, message
| sort -_time
```

Understanding this SPL

**Managed Database Failover Events (Multi-Cloud)** — Single search across RDS failover, Azure SQL failover, and Cloud SQL failover for hybrid teams. Supplements UC-7.3.2 with normalized fields.

Documented **Data sources**: `Failover`, `failover`, `switchover` events. **App/TA** (typical add-on context): CloudTrail, Azure Activity Log, GCP Audit Logs. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws, azure, gcp; **sourcetype**: aws:cloudwatch:events, azure:activity, gcp:audit. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=aws, index=azure, index=gcp, sourcetype="aws:cloudwatch:events". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Applies an explicit `search` filter to narrow the current result set.
• `eval` defines or adjusts **cloud** — often to normalize units, derive a ratio, or prepare for thresholds.
• Pipeline stage (see **Managed Database Failover Events (Multi-Cloud)**): table _time, cloud, resource_name, message
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
For the same time range, compare Splunk results with the engine’s own tools and system views (SQL Server: SQL Server Management Studio and `sys.dm_*`; Oracle: Oracle Enterprise Manager, SQLcl, or `V$` views; MySQL: Workbench or `performance_schema` / `SHOW` output; PostgreSQL: `pg_stat_*` in psql or pgAdmin; MongoDB: mongosh or Atlas metrics; Cassandra: nodetool; Elasticsearch/OpenSearch: Kibana or REST `_cat` / `_cluster/health`; ClickHouse: `system` tables in clickhouse-client; Snowflake: Snowsight or `ACCOUNT_USAGE`; others: the managed PaaS console). Confirm event counts, field names, timestamps, and Splunk role permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Timeline (failovers by cloud), Table (resource, cloud, time), Single value (failovers 30d).

## SPL

```spl
(index=aws sourcetype="aws:cloudwatch:events") OR (index=azure sourcetype="azure:activity") OR (index=gcp sourcetype="gcp:audit")
| search failover OR Failover OR switchover
| eval cloud=case(index=="aws","AWS", index=="azure","Azure", index=="gcp","GCP",1=1,"unknown")
| table _time, cloud, resource_name, message
| sort -_time
```

## Visualization

Timeline (failovers by cloud), Table (resource, cloud, time), Single value (failovers 30d).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
