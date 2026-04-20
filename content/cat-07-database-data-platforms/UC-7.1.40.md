---
id: "7.1.40"
title: "Database Audit Log Tampering Detection"
status: "verified"
criticality: "critical"
splunkPillar: "Security"
---

# UC-7.1.40 · Database Audit Log Tampering Detection

## Description

Detects unexpected audit trail disable, audit file deletion, or Unified Audit policy changes that may indicate cover-up activity.

## Value

Detects unexpected audit trail disable, audit file deletion, or Unified Audit policy changes that may indicate cover-up activity.

## Implementation

Forward database and OS audit to tamper-evident storage. Alert on any audit disable or policy drop outside CAB. Correlate with DBA group membership.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: OS audit, database audit, syslog.
• Ensure the following data sources are available: Oracle `V$OPTION` where parameter='Unified Auditing', `ALTER SYSTEM AUDIT`, `DROP AUDIT POLICY`, SQL Server audit shutdown events.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Forward database and OS audit to tamper-evident storage. Alert on any audit disable or policy drop outside CAB. Correlate with DBA group membership.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=db_audit sourcetype=oracle_audit OR sourcetype=mssql:audit
| search action IN ("AUDIT DISABLED","AUDIT_POLICY_DROP","AUDIT_TRAIL_OFF") OR statement="*AUDIT*FALSE*"
| table _time, db_user, action, object_name, statement
| sort -_time
```

Understanding this SPL

**Database Audit Log Tampering Detection** — Detects unexpected audit trail disable, audit file deletion, or Unified Audit policy changes that may indicate cover-up activity.

Documented **Data sources**: Oracle `V$OPTION` where parameter='Unified Auditing', `ALTER SYSTEM AUDIT`, `DROP AUDIT POLICY`, SQL Server audit shutdown events. **App/TA** (typical add-on context): OS audit, database audit, syslog. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: db_audit; **sourcetype**: oracle_audit, mssql:audit. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=db_audit, sourcetype=oracle_audit. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Applies an explicit `search` filter to narrow the current result set.
• Pipeline stage (see **Database Audit Log Tampering Detection**): table _time, db_user, action, object_name, statement
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t count from datamodel=Databases.Query by Query.host, Query.action | sort - count
```

Understanding this CIM / accelerated SPL

**Database Audit Log Tampering Detection** — Detects unexpected audit trail disable, audit file deletion, or Unified Audit policy changes that may indicate cover-up activity.

Documented **Data sources**: Oracle `V$OPTION` where parameter='Unified Auditing', `ALTER SYSTEM AUDIT`, `DROP AUDIT POLICY`, SQL Server audit shutdown events. **App/TA** (typical add-on context): OS audit, database audit, syslog. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Databases.Query` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Timeline (audit config changes), Table (privileged actions), Single value (critical audit events 24h).

## SPL

```spl
index=db_audit sourcetype=oracle_audit OR sourcetype=mssql:audit
| search action IN ("AUDIT DISABLED","AUDIT_POLICY_DROP","AUDIT_TRAIL_OFF") OR statement="*AUDIT*FALSE*"
| table _time, db_user, action, object_name, statement
| sort -_time
```

## CIM SPL

```spl
| tstats summariesonly=t count from datamodel=Databases.Query by Query.host, Query.action | sort - count
```

## Visualization

Timeline (audit config changes), Table (privileged actions), Single value (critical audit events 24h).

## References

- [CIM: Databases](https://docs.splunk.com/Documentation/CIM/latest/User/Databases)
