---
id: "7.1.15"
title: "Privilege Escalation Audit"
criticality: "critical"
splunkPillar: "Security"
---

# UC-7.1.15 · Privilege Escalation Audit

## Description

Unauthorized privilege changes can enable data theft or sabotage. Audit trail is required for compliance.

## Value

Unauthorized privilege changes can enable data theft or sabotage. Audit trail is required for compliance.

## Implementation

Enable database audit for security events (GRANT, REVOKE, ALTER ROLE). Forward to Splunk. Alert on any privilege change in production. Correlate with change management tickets and access review cycles.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: DB Connect, SQL Server audit.
• Ensure the following data sources are available: Database audit logs (GRANT/REVOKE events), security event logs.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable database audit for security events (GRANT, REVOKE, ALTER ROLE). Forward to Splunk. Alert on any privilege change in production. Correlate with change management tickets and access review cycles.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=database sourcetype="mssql:audit"
| search action_id IN ("G","R","GWG") statement="*GRANT*" OR statement="*REVOKE*"
| table _time, server_principal_name, database_name, statement, target_server_principal_name
```

Understanding this SPL

**Privilege Escalation Audit** — Unauthorized privilege changes can enable data theft or sabotage. Audit trail is required for compliance.

Documented **Data sources**: Database audit logs (GRANT/REVOKE events), security event logs. **App/TA** (typical add-on context): DB Connect, SQL Server audit. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: database; **sourcetype**: mssql:audit. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=database, sourcetype="mssql:audit". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Applies an explicit `search` filter to narrow the current result set.
• Pipeline stage (see **Privilege Escalation Audit**): table _time, server_principal_name, database_name, statement, target_server_principal_name

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t count from datamodel=Databases.Query by Query.host, Query.action | sort - count
```

Understanding this CIM / accelerated SPL

**Privilege Escalation Audit** — Unauthorized privilege changes can enable data theft or sabotage. Audit trail is required for compliance.

Documented **Data sources**: Database audit logs (GRANT/REVOKE events), security event logs. **App/TA** (typical add-on context): DB Connect, SQL Server audit. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Databases.Query` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (privilege change events), Timeline (changes), Bar chart (changes by granting user).

## SPL

```spl
index=database sourcetype="mssql:audit"
| search action_id IN ("G","R","GWG") statement="*GRANT*" OR statement="*REVOKE*"
| table _time, server_principal_name, database_name, statement, target_server_principal_name
```

## CIM SPL

```spl
| tstats summariesonly=t count from datamodel=Databases.Query by Query.host, Query.action | sort - count
```

## Visualization

Table (privilege change events), Timeline (changes), Bar chart (changes by granting user).

## References

- [CIM: Databases](https://docs.splunk.com/Documentation/CIM/latest/User/Databases)
