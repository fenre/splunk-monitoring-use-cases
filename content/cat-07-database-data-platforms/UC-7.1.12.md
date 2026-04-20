---
id: "7.1.12"
title: "Database Availability Group Health"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-7.1.12 · Database Availability Group Health

## Description

AG/RAC cluster health is essential for HA. Detecting unhealthy replicas prevents unplanned failover failures.

## Value

AG/RAC cluster health is essential for HA. Detecting unhealthy replicas prevents unplanned failover failures.

## Implementation

Poll AG replica state DMVs every 5 minutes. Alert on any non-HEALTHY or non-CONNECTED state. Track failover events from SQL Server error log. Create dashboard showing full AG topology and health.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: DB Connect, Splunk_TA_microsoft-sqlserver.
• Ensure the following data sources are available: `sys.dm_hadr_availability_replica_states` (SQL Server), Oracle CRS logs.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll AG replica state DMVs every 5 minutes. Alert on any non-HEALTHY or non-CONNECTED state. Track failover events from SQL Server error log. Create dashboard showing full AG topology and health.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=database sourcetype="dbconnect:ag_status"
| where synchronization_health_desc!="HEALTHY" OR connected_state_desc!="CONNECTED"
| table _time, ag_name, replica_server_name, role_desc, synchronization_health_desc
```

Understanding this SPL

**Database Availability Group Health** — AG/RAC cluster health is essential for HA. Detecting unhealthy replicas prevents unplanned failover failures.

Documented **Data sources**: `sys.dm_hadr_availability_replica_states` (SQL Server), Oracle CRS logs. **App/TA** (typical add-on context): DB Connect, Splunk_TA_microsoft-sqlserver. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: database; **sourcetype**: dbconnect:ag_status. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=database, sourcetype="dbconnect:ag_status". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where synchronization_health_desc!="HEALTHY" OR connected_state_desc!="CONNECTED"` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Database Availability Group Health**): table _time, ag_name, replica_server_name, role_desc, synchronization_health_desc

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t count from datamodel=Databases.Instance_Stats by Instance_Stats.host, Instance_Stats.action | sort - count
```

Understanding this CIM / accelerated SPL

**Database Availability Group Health** — AG/RAC cluster health is essential for HA. Detecting unhealthy replicas prevents unplanned failover failures.

Documented **Data sources**: `sys.dm_hadr_availability_replica_states` (SQL Server), Oracle CRS logs. **App/TA** (typical add-on context): DB Connect, Splunk_TA_microsoft-sqlserver. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Databases.Instance_Stats` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Status grid (replica × health state), Table (unhealthy replicas), Timeline (failover events).

## SPL

```spl
index=database sourcetype="dbconnect:ag_status"
| where synchronization_health_desc!="HEALTHY" OR connected_state_desc!="CONNECTED"
| table _time, ag_name, replica_server_name, role_desc, synchronization_health_desc
```

## CIM SPL

```spl
| tstats summariesonly=t count from datamodel=Databases.Instance_Stats by Instance_Stats.host, Instance_Stats.action | sort - count
```

## Visualization

Status grid (replica × health state), Table (unhealthy replicas), Timeline (failover events).

## References

- [CIM: Databases](https://docs.splunk.com/Documentation/CIM/latest/User/Databases)
