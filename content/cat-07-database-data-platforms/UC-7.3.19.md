<!-- AUTO-GENERATED from UC-7.3.19.json — DO NOT EDIT -->

---
id: "7.3.19"
title: "PostgreSQL FATAL Authentication Failure Spike"
criticality: "high"
splunkPillar: "Security"
---

# UC-7.3.19 · PostgreSQL FATAL Authentication Failure Spike

## Description

Repeated FATAL authentication messages often indicate credential attacks, mis-rotated passwords, or broken service accounts. This is standard PostgreSQL security monitoring.

## Value

Detects credential attacks and misconfigurations before lockouts or application brownouts across many clients.

## Implementation

Ensure log_line_prefix includes user and client address for parsing. Extract user and src_ip fields at ingest. Baseline failures per environment. Feed high-volume alerts into risk scoring if Splunk Enterprise Security is available.

## SPL

```spl
index=database sourcetype="postgresql:log"
| search "FATAL" ("password authentication failed" OR "no pg_hba.conf entry")
| bin _time span=15m
| stats count as failures dc(user) as users dc(src_ip) as sources by host, _time
| where failures > 50
```

## Visualization

Timeline (failures), Table (host, user, sources), Single value (failures per hour).

## References

- [PostgreSQL client authentication](https://www.postgresql.org/docs/current/client-authentication.html)
