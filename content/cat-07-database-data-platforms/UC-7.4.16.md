<!-- AUTO-GENERATED from UC-7.4.16.json — DO NOT EDIT -->

---
id: "7.4.16"
title: "Azure Synapse Pipeline Execution Health"
criticality: "high"
splunkPillar: "Observability"
---

# UC-7.4.16 · Azure Synapse Pipeline Execution Health

## Description

Synapse pipelines orchestrate data movement and transformation. Failed pipeline runs cause stale analytics data, broken reports, and missed business deadlines.

## Value

Synapse pipelines orchestrate data movement and transformation. Failed pipeline runs cause stale analytics data, broken reports, and missed business deadlines.

## Implementation

Enable diagnostics on Synapse workspaces to route `SynapsePipelineRuns` and `SynapseActivityRuns` to Splunk via Event Hub. Alert on failed pipeline runs. Track activity-level errors for root cause analysis (data movement failures, notebook errors, SQL script timeouts). Monitor pipeline duration trending to detect degradation.

## Detailed Implementation

Prerequisites
• In operations we confirm in pgAdmin, psql, and `pg_stat*` views, or the managed PostgreSQL console.
• Install and configure the required add-on or app: `Splunk_TA_microsoft-cloudservices` (Azure Monitor diagnostics).
• Ensure the following data sources are available: `sourcetype=azure:diagnostics` (SynapsePipelineRuns, SynapseActivityRuns).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable diagnostics on Synapse workspaces to route `SynapsePipelineRuns` and `SynapseActivityRuns` to Splunk via Event Hub. Alert on failed pipeline runs. Track activity-level errors for root cause analysis (data movement failures, notebook errors, SQL script timeouts). Monitor pipeline duration trending to detect degradation.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cloud sourcetype="azure:diagnostics" Category="SynapsePipelineRuns"
| where Status="Failed"
| stats count as failures, latest(Start) as last_failure, latest(Error) as last_error by PipelineName, resource_name
| sort -failures
```

Understanding this SPL

**Azure Synapse Pipeline Execution Health** — Synapse pipelines orchestrate data movement and transformation. Failed pipeline runs cause stale analytics data, broken reports, and missed business deadlines.

Documented **Data sources**: `sourcetype=azure:diagnostics` (SynapsePipelineRuns, SynapseActivityRuns). **App/TA** (typical add-on context): `Splunk_TA_microsoft-cloudservices` (Azure Monitor diagnostics). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cloud; **sourcetype**: azure:diagnostics. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=cloud, sourcetype="azure:diagnostics". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where Status="Failed"` — typically the threshold or rule expression for this monitoring goal.
• `stats` rolls up events into metrics; results are split **by PipelineName, resource_name** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
For the same time range, compare Splunk results with the engine’s own tools and system views (SQL Server: SQL Server Management Studio and `sys.dm_*`; Oracle: Oracle Enterprise Manager, SQLcl, or `V$` views; MySQL: Workbench or `performance_schema` / `SHOW` output; PostgreSQL: `pg_stat_*` in psql or pgAdmin; MongoDB: mongosh or Atlas metrics; Cassandra: nodetool; Elasticsearch/OpenSearch: Kibana or REST `_cat` / `_cluster/health`; ClickHouse: `system` tables in clickhouse-client; Snowflake: Snowsight or `ACCOUNT_USAGE`; others: the managed PaaS console). Confirm event counts, field names, timestamps, and Splunk role permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (failed pipelines with error detail), Bar chart (failures by pipeline), Line chart (duration trend).

## SPL

```spl
index=cloud sourcetype="azure:diagnostics" Category="SynapsePipelineRuns"
| where Status="Failed"
| stats count as failures, latest(Start) as last_failure, latest(Error) as last_error by PipelineName, resource_name
| sort -failures
```

## Visualization

Table (failed pipelines with error detail), Bar chart (failures by pipeline), Line chart (duration trend).

## References

- [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)
