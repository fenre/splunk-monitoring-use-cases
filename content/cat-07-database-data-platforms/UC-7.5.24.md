<!-- AUTO-GENERATED from UC-7.5.24.json — DO NOT EDIT -->

---
id: "7.5.24"
title: "PostgreSQL GRANT and REVOKE Privilege Change Audit"
criticality: "high"
splunkPillar: "Security"
---

# UC-7.5.24 · PostgreSQL GRANT and REVOKE Privilege Change Audit

## Description

Privilege changes are high-risk events for PostgreSQL security assessments. Logging GRANT/REVOKE and role changes is recommended for regulated environments.

## Value

Supports least-privilege reviews and proves who expanded database access before an incident.

## Implementation

Enable pgaudit or appropriate log_min_duration settings for DDL on privileged roles only if possible. Parse session user and object. Forward to a tamper-evident index. Correlate with change tickets.

## SPL

```spl
index=database sourcetype="postgresql:log"
| search "GRANT " OR "REVOKE " OR "ALTER ROLE" OR "CREATE ROLE" OR "DROP ROLE"
| stats count by db_user, object_name, host
| sort -count
```

## Visualization

Timeline (changes), Table (user, object), Top statements.

## References

- [PostgreSQL pgAudit](https://github.com/pgaudit/pgaudit/blob/master/README.md)
