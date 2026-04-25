<!-- AUTO-GENERATED from UC-7.4.19.json — DO NOT EDIT -->

---
id: "7.4.19"
title: "PostgreSQL Database Size Growth Trend"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-7.4.19 · PostgreSQL Database Size Growth Trend

## Description

Database-level byte growth complements tablespace monitoring and catches bloat, logging, or staging schemas before backups and disk alerts fail.

## Value

Improves capacity forecasting for PostgreSQL clusters where per-database chargeback or tenant isolation matters.

## Implementation

Daily DB Connect query listing datname and pg_database_size. Exclude template databases. Alert on percentage growth versus trailing baseline. Correlate with autovacuum and WAL metrics.

## SPL

```spl
index=database sourcetype="postgresql:db_size"
| eval size_gb=round(size_bytes/1073741824,2)
| timechart span=1d max(size_gb) as db_gb by datname, host
| streamstats window=14 avg(db_gb) as baseline by datname, host
| where db_gb > baseline*1.2
```

## Visualization

Line chart (GB per database), Table (growth %), Stacked area (top databases).

## References

- [PostgreSQL Database Size Functions](https://www.postgresql.org/docs/current/functions-admin.html#FUNCTIONS-ADMIN-DBOBJECT)
- [Splunk DB Connect](https://splunkbase.splunk.com/app/2686)
