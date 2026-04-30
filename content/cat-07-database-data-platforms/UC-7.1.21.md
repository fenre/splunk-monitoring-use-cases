<!-- AUTO-GENERATED from UC-7.1.21.json — DO NOT EDIT -->

---
id: "7.1.21"
title: "Database User and Privilege Change Audit"
status: "verified"
criticality: "high"
splunkPillar: "Security"
---

# UC-7.1.21 · Database User and Privilege Change Audit

> **Criticality:** High &middot; **Difficulty:** Beginner &middot; **Pillar:** Security &middot; **Type:** Security, Compliance &middot; **Status:** Verified

*We track who changed users and privileges in our databases so we can support compliance and spot unauthorized access paths early.*

---

## Description

New users, role grants, or privilege changes can indicate compromise or policy violation. Auditing supports compliance (SOX, PCI) and security investigations.

## Value

New users, role grants, or privilege changes can indicate compromise or policy violation. Auditing supports compliance (SOX, PCI) and security investigations.

## Implementation

Enable database audit for user and privilege changes. Forward audit logs to Splunk. Alert on any CREATE USER, GRANT, or ALTER USER. Correlate with change management.

## Detailed Implementation

### Prerequisites
- In operations we cross-check the same window in SQL Server Management Studio, Azure Data Studio, or the Azure SQL portal with `sys.dm_*` views; Oracle Enterprise Manager, SQLcl, or SQL Developer with `V$` views; psql, pgAdmin, or the managed-PostgreSQL console with `pg_stat_*` and replication views; MySQL Workbench, the managed-MySQL console, or `performance_schema` / replica status so live metrics match what Splunk shows.
- Install and configure the required add-on or app: Database audit logs, `splunk_app_db_connect`.
- Ensure the following data sources are available: Oracle audit trail, PostgreSQL `pg_audit` or log_statement, SQL Server audit, MySQL general log.
- For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

### Step 1 — Configure data collection
Enable database audit for user and privilege changes. Forward audit logs to Splunk. Alert on any CREATE USER, GRANT, or ALTER USER. Correlate with change management.

### Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=db_audit sourcetype=oracle_audit (action="CREATE USER" OR action="GRANT" OR action="ALTER USER")
| bin _time span=1h
| stats count by db_user, action, object_name, _time
| where count > 0
| table _time db_user action object_name
```

#### Understanding this SPL

**Database User and Privilege Change Audit** — New users, role grants, or privilege changes can indicate compromise or policy violation. Auditing supports compliance (SOX, PCI) and security investigations.

Documented **Data sources**: Oracle audit trail, PostgreSQL `pg_audit` or log_statement, SQL Server audit, MySQL general log. **App/TA** (typical add-on context): Database audit logs, `splunk_app_db_connect`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: db_audit; **sourcetype**: oracle_audit. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

- Scopes the data: index=db_audit, sourcetype=oracle_audit. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
- Discretizes time or numeric ranges with `bin`/`bucket`.
- `stats` rolls up events into metrics; results are split **by db_user, action, object_name, _time** so each row reflects one combination of those dimensions.
- Filters the current rows with `where count > 0` — typically the threshold or rule expression for this monitoring goal.
- Pipeline stage (see **Database User and Privilege Change Audit**): table _time db_user action object_name

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t count from datamodel=Change.All_Changes by All_Changes.user, All_Changes.action, All_Changes.object span=1h | sort - count
```

Understanding this CIM / accelerated SPL

**Database User and Privilege Change Audit** — New users, role grants, or privilege changes can indicate compromise or policy violation. Auditing supports compliance (SOX, PCI) and security investigations.

Documented **Data sources**: Oracle audit trail, PostgreSQL `pg_audit` or log_statement, SQL Server audit, MySQL general log. **App/TA** (typical add-on context): Database audit logs, `splunk_app_db_connect`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

- Uses `tstats` against accelerated summaries for data model `Change.All_Changes` — enable acceleration for that model.
- Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


### Step 3 — Validate
For the same time range, compare Splunk results with the engine’s own tools and system views (SQL Server: SQL Server Management Studio and `sys.dm_*`; Oracle: Oracle Enterprise Manager, SQLcl, or `V$` views; MySQL: Workbench or `performance_schema` / `SHOW` output; PostgreSQL: `pg_stat_*` in psql or pgAdmin; MongoDB: mongosh or Atlas metrics; Cassandra: nodetool; Elasticsearch/OpenSearch: Kibana or REST `_cat` / `_cluster/health`; ClickHouse: `system` tables in clickhouse-client; Snowflake: Snowsight or `ACCOUNT_USAGE`; others: the managed PaaS console). Confirm event counts, field names, timestamps, and Splunk role permissions.

### Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Events timeline, Table (user, action, object), Bar chart (changes by user).

## SPL

```spl
index=db_audit sourcetype=oracle_audit (action="CREATE USER" OR action="GRANT" OR action="ALTER USER")
| bin _time span=1h
| stats count by db_user, action, object_name, _time
| where count > 0
| table _time db_user action object_name
```

## CIM SPL

```spl
| tstats summariesonly=t count from datamodel=Change.All_Changes by All_Changes.user, All_Changes.action, All_Changes.object span=1h | sort - count
```

## Visualization

Events timeline, Table (user, action, object), Bar chart (changes by user).

## Known False Positives

Planned access reviews, recertification, break-glass accounts, and vendor maintenance can emit privilege- or access-change events that match the rule but are already approved; require a change ticket for context.

## References

- [CIM: Change](https://docs.splunk.com/Documentation/CIM/latest/User/Change)
