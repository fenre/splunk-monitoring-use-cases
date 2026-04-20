---
id: "9.2.3"
title: "Schema Modification Audit"
criticality: "critical"
splunkPillar: "Security"
---

# UC-9.2.3 · Schema Modification Audit

## Description

Schema changes to directory services can break applications and are rarely expected. Detection ensures change control compliance.

## Value

Schema changes to directory services can break applications and are rarely expected. Detection ensures change control compliance.

## Implementation

Enable LDAP audit logging (overlay in OpenLDAP, audit log in 389 DS). Forward to Splunk. Alert on any schema modification. These should be extremely rare and always correlated with change tickets.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: LDAP audit log.
• Ensure the following data sources are available: LDAP server audit log (schema modification events).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable LDAP audit logging (overlay in OpenLDAP, audit log in 389 DS). Forward to Splunk. Alert on any schema modification. These should be extremely rare and always correlated with change tickets.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=ldap sourcetype="openldap:audit"
| search "cn=schema" ("add:" OR "delete:" OR "replace:")
| table _time, modifier_dn, changetype, modification
```

Understanding this SPL

**Schema Modification Audit** — Schema changes to directory services can break applications and are rarely expected. Detection ensures change control compliance.

Documented **Data sources**: LDAP server audit log (schema modification events). **App/TA** (typical add-on context): LDAP audit log. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: ldap; **sourcetype**: openldap:audit. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=ldap, sourcetype="openldap:audit". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Applies an explicit `search` filter to narrow the current result set.
• Pipeline stage (see **Schema Modification Audit**): table _time, modifier_dn, changetype, modification

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  where match(All_Changes.object, "(?i)cn=schema")
  by All_Changes.user All_Changes.object span=1d
| sort -count
```

Understanding this CIM / accelerated SPL

**Schema Modification Audit** — Schema changes to directory services can break applications and are rarely expected. Detection ensures change control compliance.

Documented **Data sources**: LDAP server audit log (schema modification events). **App/TA** (typical add-on context): LDAP audit log. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Change.All_Changes` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Timeline (schema changes), Table (change details), Single value (schema changes this month).

## SPL

```spl
index=ldap sourcetype="openldap:audit"
| search "cn=schema" ("add:" OR "delete:" OR "replace:")
| table _time, modifier_dn, changetype, modification
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  where match(All_Changes.object, "(?i)cn=schema")
  by All_Changes.user All_Changes.object span=1d
| sort -count
```

## Visualization

Timeline (schema changes), Table (change details), Single value (schema changes this month).

## Known False Positives

Administrative tasks, scheduled jobs or platform updates can match this pattern — correlate with change management, maintenance windows and user role before raising severity.

## References

- [CIM: Change](https://docs.splunk.com/Documentation/CIM/latest/User/Change)
