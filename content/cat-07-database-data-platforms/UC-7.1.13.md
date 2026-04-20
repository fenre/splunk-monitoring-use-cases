---
id: "7.1.13"
title: "Schema Change Detection"
criticality: "high"
splunkPillar: "Security"
---

# UC-7.1.13 · Schema Change Detection

## Description

Unauthorized DDL changes to production databases can break applications. Detection ensures change control compliance.

## Value

Unauthorized DDL changes to production databases can break applications. Detection ensures change control compliance.

## Implementation

Enable SQL Server audit for DDL events (CREATE, ALTER, DROP). For PostgreSQL, set `log_statement='ddl'`. Forward audit logs to Splunk. Alert on any DDL outside maintenance windows. Correlate with change tickets.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: DB Connect, SQL Server audit.
• Ensure the following data sources are available: SQL Server DDL triggers, audit logs, PostgreSQL `log_statement='ddl'`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable SQL Server audit for DDL events (CREATE, ALTER, DROP). For PostgreSQL, set `log_statement='ddl'`. Forward audit logs to Splunk. Alert on any DDL outside maintenance windows. Correlate with change tickets.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=database sourcetype="mssql:audit" action_id IN ("CR","AL","DR")
| table _time, server_principal_name, database_name, object_name, statement
| sort -_time
```

Understanding this SPL

**Schema Change Detection** — Unauthorized DDL changes to production databases can break applications. Detection ensures change control compliance.

Documented **Data sources**: SQL Server DDL triggers, audit logs, PostgreSQL `log_statement='ddl'`. **App/TA** (typical add-on context): DB Connect, SQL Server audit. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: database; **sourcetype**: mssql:audit. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=database, sourcetype="mssql:audit". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Pipeline stage (see **Schema Change Detection**): table _time, server_principal_name, database_name, object_name, statement
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t count from datamodel=Databases.Query by Query.host, Query.action | sort - count
```

Understanding this CIM / accelerated SPL

**Schema Change Detection** — Unauthorized DDL changes to production databases can break applications. Detection ensures change control compliance.

Documented **Data sources**: SQL Server DDL triggers, audit logs, PostgreSQL `log_statement='ddl'`. **App/TA** (typical add-on context): DB Connect, SQL Server audit. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Databases.Query` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (DDL events with details), Timeline (schema changes), Bar chart (changes by user).

## SPL

```spl
index=database sourcetype="mssql:audit" action_id IN ("CR","AL","DR")
| table _time, server_principal_name, database_name, object_name, statement
| sort -_time
```

## CIM SPL

```spl
| tstats summariesonly=t count from datamodel=Databases.Query by Query.host, Query.action | sort - count
```

## Visualization

Table (DDL events with details), Timeline (schema changes), Bar chart (changes by user).

## References

- [CIM: Databases](https://docs.splunk.com/Documentation/CIM/latest/User/Databases)
