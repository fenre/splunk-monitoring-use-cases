<!-- AUTO-GENERATED from UC-7.2.29.json — DO NOT EDIT -->

---
id: "7.2.29"
title: "PostgreSQL Replication Slot Lag and WAL Retention"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-7.2.29 · PostgreSQL Replication Slot Lag and WAL Retention

## Description

Inactive or lagging logical replication slots retain WAL and can fill the primary disk; this is a well-known PostgreSQL production failure mode for CDC and standby consumers.

## Value

Prevents primary outages from WAL bloat and protects logical decoding consumers before they exceed RPO.

## Implementation

Poll pg_replication_slots with pg_wal_lsn_diff or retained_bytes if available on your version. Alert on lag_bytes crossing capacity thresholds or when critical slots are inactive unexpectedly. Map slot_name to owning teams and Debezium/ETL pipelines.

## SPL

```spl
index=database sourcetype="postgresql:replication_slots"
| eval lag_bytes=tonumber(lag_bytes)
| where lag_bytes > 1073741824
| stats max(lag_bytes) as max_lag_bytes latest(active) as active by slot_name, database, host
| eval lag_gb=round(max_lag_bytes/1073741824,2)
| sort -lag_gb
```

## Visualization

Table (slot, lag GB, active), Line chart (lag trend), Single value (max lag).

## References

- [PostgreSQL — Replication Slots](https://www.postgresql.org/docs/current/warm-standby.html#STREAMING-REPLICATION-SLOTS)
- [Splunk DB Connect](https://splunkbase.splunk.com/app/2686)
