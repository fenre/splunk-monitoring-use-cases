---
id: "7.1.31"
title: "SQL Server Always On AG Health and Replica Sync"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-7.1.31 · SQL Server Always On AG Health and Replica Sync

## Description

Combined view of `synchronization_health`, redo queue, and log send queue sizes for AG replicas. Operationalizes UC-7.1.12 with queue depth.

## Value

Combined view of `synchronization_health`, redo queue, and log send queue sizes for AG replicas. Operationalizes UC-7.1.12 with queue depth.

## Implementation

Poll DMVs every 5m. Alert on unhealthy sync or queue >100MB (tune threshold). Track automatic failover readiness.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: DB Connect, `Splunk_TA_microsoft-sqlserver`.
• Ensure the following data sources are available: `sys.dm_hadr_database_replica_states`, `log_send_queue_size`, `redo_queue_size`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll DMVs every 5m. Alert on unhealthy sync or queue >100MB (tune threshold). Track automatic failover readiness.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=database sourcetype="dbconnect:ag_replica_state"
| where synchronization_health_desc!="HEALTHY" OR log_send_queue_size > 104857600 OR redo_queue_size > 104857600
| table ag_name replica_server_name synchronization_health_desc log_send_queue_size redo_queue_size
```

Understanding this SPL

**SQL Server Always On AG Health and Replica Sync** — Combined view of `synchronization_health`, redo queue, and log send queue sizes for AG replicas. Operationalizes UC-7.1.12 with queue depth.

Documented **Data sources**: `sys.dm_hadr_database_replica_states`, `log_send_queue_size`, `redo_queue_size`. **App/TA** (typical add-on context): DB Connect, `Splunk_TA_microsoft-sqlserver`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: database; **sourcetype**: dbconnect:ag_replica_state. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=database, sourcetype="dbconnect:ag_replica_state". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where synchronization_health_desc!="HEALTHY" OR log_send_queue_size > 104857600 OR redo_queue_size > 104857600` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **SQL Server Always On AG Health and Replica Sync**): table ag_name replica_server_name synchronization_health_desc log_send_queue_size redo_queue_size

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t count from datamodel=Databases.Instance_Stats by Instance_Stats.host, Instance_Stats.action | sort - count
```

Understanding this CIM / accelerated SPL

**SQL Server Always On AG Health and Replica Sync** — Combined view of `synchronization_health`, redo queue, and log send queue sizes for AG replicas. Operationalizes UC-7.1.12 with queue depth.

Documented **Data sources**: `sys.dm_hadr_database_replica_states`, `log_send_queue_size`, `redo_queue_size`. **App/TA** (typical add-on context): DB Connect, `Splunk_TA_microsoft-sqlserver`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Databases.Instance_Stats` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Status grid (replica × health), Line chart (queue sizes), Table (unhealthy AG databases).

## SPL

```spl
index=database sourcetype="dbconnect:ag_replica_state"
| where synchronization_health_desc!="HEALTHY" OR log_send_queue_size > 104857600 OR redo_queue_size > 104857600
| table ag_name replica_server_name synchronization_health_desc log_send_queue_size redo_queue_size
```

## CIM SPL

```spl
| tstats summariesonly=t count from datamodel=Databases.Instance_Stats by Instance_Stats.host, Instance_Stats.action | sort - count
```

## Visualization

Status grid (replica × health), Line chart (queue sizes), Table (unhealthy AG databases).

## References

- [CIM: Databases](https://docs.splunk.com/Documentation/CIM/latest/User/Databases)
