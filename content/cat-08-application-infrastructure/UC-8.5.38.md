<!-- AUTO-GENERATED from UC-8.5.38.json — DO NOT EDIT -->

---
id: "8.5.38"
title: "ActiveMQ JDBC Message Store Lock Contention and Slow Persistence"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.5.38 · ActiveMQ JDBC Message Store Lock Contention and Slow Persistence

## Description

JDBC-backed brokers depend on database row-level locking around `activemq_msgs` and related tables; lock wait timeouts and SQL errors manifest as send latency spikes and redelivery loops. Aggregating JDBC-related errors from broker logs gives a single pane when the database, not the JVM, is the bottleneck.

## Value

Shortens diagnosis of intermittent messaging latency during DB maintenance, connection pool exhaustion, or index drift on message tables.

## Implementation

Redact SQL parameters if logs include literals. Join to DB AWR or Splunk DB Connect slow-query index by timestamp + host. Separate Artemis vs Classic log formats if both exist.

## SPL

```spl
index=messaging (sourcetype="activemq:log" OR sourcetype="activemq:audit") earliest=-24h
| search ("JdbcPersistenceAdapter" OR "JDBC" OR "SQLException" OR "Lock wait timeout" OR "deadlock" OR "could not insert" OR "could not update" OR "Communications link failure")
| rex field=_raw "(?<sql_state>SQLSTATE\s+\w+)?"
| bucket _time span=5m
| stats count as jdbc_faults values(sql_state) as states latest(_raw) as sample by _time, host
| where jdbc_faults >= 5
| sort -jdbc_faults
```

## Visualization

Timeline of JDBC error counts, table (host, states), link-out to DBA dashboards.

## References

- [Apache ActiveMQ — JDBC Persistence](https://activemq.apache.org/jdbc)
- [Apache ActiveMQ — Features](https://activemq.apache.org/features)
