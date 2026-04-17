## 7. Database & Data Platforms

### 7.1 Relational Databases

**Primary App/TA:** Splunk DB Connect (`splunk_app_db_connect`), Splunk Add-on for Microsoft SQL Server (`Splunk_TA_microsoft-sqlserver`), MySQL/PostgreSQL TAs, scripted inputs for DMVs/catalog queries.

---

### UC-7.1.1 · Slow Query Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Slow queries at the P95/P99 level directly impact checkout, search, and reporting latency, hitting revenue and SLA commitments. They also hold locks and inflate CPU/IO, degrading performance for other tenants and queries. Prioritize fixes by business-critical endpoint and wait type, not just raw query duration.
- **App/TA:** DB Connect, Splunk_TA_microsoft-sqlserver, MySQL slow query log
- **Data Sources:** Slow query logs, SQL Server DMVs (`sys.dm_exec_query_stats`), PostgreSQL `pg_stat_statements`
- **SPL:**
```spl
index=database sourcetype="mysql:slowquery"
| rex field=_raw "Query_time:\s+(?<query_time>[\d.]+)"
| where query_time > 5
| stats count, avg(query_time) as avg_time by db, user
| sort -avg_time
```
- **Implementation:** Enable MySQL slow query log (long_query_time=5). For SQL Server, poll DMVs via DB Connect. For PostgreSQL, enable `pg_stat_statements`. Ingest and alert on queries exceeding thresholds. Report top offenders weekly.
- **Visualization:** Table (slow queries with details), Bar chart (top slow queries by avg duration), Line chart (slow query count trend).
- **CIM Models:** Databases
- **CIM SPL:**
```spl
| tstats summariesonly=t count from datamodel=Databases.Query by Query.host, Query.action | sort - count
```
- **References:** [CIM: Databases](https://docs.splunk.com/Documentation/CIM/latest/User/Databases)

---

### UC-7.1.2 · Deadlock Monitoring
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Fault
- **Value:** Deadlocks cause transaction failures and application errors. Rapid detection and root cause analysis minimizes impact.
- **App/TA:** Splunk_TA_microsoft-sqlserver, database error logs
- **Data Sources:** SQL Server error log (deadlock graph), PostgreSQL `log_lock_waits`, Oracle alert log
- **SPL:**
```spl
index=database sourcetype="mssql:errorlog"
| search "deadlock" OR "Deadlock"
| stats count by _time, database_name
| timechart span=1h sum(count) as deadlocks
```
- **Implementation:** Enable trace flag 1222 for SQL Server deadlock graphs. For PostgreSQL, set `log_lock_waits=on` and `deadlock_timeout=1s`. Ingest error logs. Alert on any deadlock occurrence. Parse deadlock graphs for involved queries/objects.
- **Visualization:** Line chart (deadlocks over time), Table (deadlock details), Single value (deadlocks today).
- **CIM Models:** Databases
- **CIM SPL:**
```spl
| tstats summariesonly=t count from datamodel=Databases.Query by Query.host, Query.action span=1h | sort - count
```
- **References:** [CIM: Databases](https://docs.splunk.com/Documentation/CIM/latest/User/Databases)

---

### UC-7.1.3 · Connection Pool Exhaustion
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Capacity
- **Value:** Exhausted connection pools cause application failures. Monitoring prevents outages and guides pool sizing decisions.
- **App/TA:** DB Connect, performance counters
- **Data Sources:** SQL Server DMVs (`sys.dm_exec_connections`), PostgreSQL `pg_stat_activity`, app server connection pool metrics
- **SPL:**
```spl
index=database sourcetype="dbconnect:mssql_connections"
| timechart span=5m max(active_connections) as active, max(max_connections) as max_limit
| eval pct_used=round(active/max_limit*100,1)
| where pct_used > 80
```
- **Implementation:** Poll connection counts via DB Connect every 5 minutes. Compare against configured maximum. Alert at 80% and 95% thresholds. Track by application/user to identify connection leaks.
- **Visualization:** Gauge (% connections used), Line chart (connections over time), Table (connections by application).
- **CIM Models:** Databases
- **CIM SPL:**
```spl
| tstats summariesonly=t count from datamodel=Databases.Query by Query.host, Query.action span=5m | sort - count
```
- **References:** [CIM: Databases](https://docs.splunk.com/Documentation/CIM/latest/User/Databases)

---

### UC-7.1.4 · Replication Lag Monitoring
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Replication lag affects data consistency and failover readiness. Monitoring ensures HA/DR objectives are met.
- **App/TA:** DB Connect, vendor-specific monitoring
- **Data Sources:** SQL Server AG DMVs (`sys.dm_hadr_database_replica_states`), MySQL `SHOW SLAVE STATUS`, PostgreSQL replication slots
- **SPL:**
```spl
index=database sourcetype="dbconnect:replication_status"
| eval lag_seconds=coalesce(seconds_behind_master, replication_lag_sec)
| timechart span=5m max(lag_seconds) as max_lag by replica_name
| where max_lag > 60
```
- **Implementation:** Poll replication status via DB Connect at 5-minute intervals. Alert when lag exceeds RPO (e.g., >60 seconds). Track lag trend over time. Correlate spikes with batch jobs or network events.
- **Visualization:** Line chart (lag over time by replica), Single value (current max lag), Table (replicas with lag status).
- **CIM Models:** Databases
- **CIM SPL:**
```spl
| tstats summariesonly=t count from datamodel=Databases.Instance_Stats by Instance_Stats.host, Instance_Stats.action span=5m | sort - count
```
- **References:** [CIM: Databases](https://docs.splunk.com/Documentation/CIM/latest/User/Databases)

---

### UC-7.1.5 · Tablespace / Data File Growth
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Uncontrolled database growth leads to disk space exhaustion and outages. Trending enables proactive storage provisioning.
- **App/TA:** DB Connect
- **Data Sources:** `sys.database_files` (SQL Server), `dba_tablespaces` (Oracle), `pg_database_size()` (PostgreSQL)
- **SPL:**
```spl
index=database sourcetype="dbconnect:db_size"
| timechart span=1d latest(size_gb) as db_size by database_name
| predict db_size as predicted future_timespan=30
```
- **Implementation:** Poll database size metrics via DB Connect daily. Track growth rate per database. Use `predict` command for 30-day forecast. Alert when projected size exceeds available disk. Report top growing databases.
- **Visualization:** Line chart (size trend with prediction), Table (databases with growth rate), Bar chart (top databases by size).
- **CIM Models:** Databases
- **CIM SPL:**
```spl
| tstats summariesonly=t count from datamodel=Databases.Instance_Stats by Instance_Stats.host, Instance_Stats.action span=1d | sort - count
```
- **References:** [CIM: Databases](https://docs.splunk.com/Documentation/CIM/latest/User/Databases)

---

### UC-7.1.6 · Backup Success Verification
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Value:** Database backups are the last line of defense. Verifying success prevents discovering backup failures during a crisis.
- **App/TA:** DB Connect, Splunk_TA_microsoft-sqlserver
- **Data Sources:** `msdb.dbo.backupset` (SQL Server), `v$rman_backup_job_details` (Oracle), PostgreSQL `pg_basebackup` logs
- **SPL:**
```spl
index=database sourcetype="dbconnect:backup_history"
| stats latest(backup_finish_date) as last_backup, latest(type) as backup_type by database_name, server_name
| eval hours_since=round((now()-strptime(last_backup,"%Y-%m-%d %H:%M:%S"))/3600,1)
| where hours_since > 24
| table server_name, database_name, last_backup, backup_type, hours_since
```
- **Implementation:** Query backup history tables via DB Connect daily. Alert on any database without a successful backup in the expected window. Cross-reference with CMDB for backup classification (full/diff/log) requirements.
- **Visualization:** Table (databases with backup status), Single value (databases missing backup), Status grid (database × backup type).
- **CIM Models:** Databases
- **CIM SPL:**
```spl
| tstats summariesonly=t count from datamodel=Databases.Instance_Stats by Instance_Stats.host, Instance_Stats.action | sort - count
```
- **References:** [CIM: Databases](https://docs.splunk.com/Documentation/CIM/latest/User/Databases)

---

### UC-7.1.7 · Login Failure Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Repeated login failures may indicate brute-force attacks or misconfigured applications. Detection supports security posture.
- **App/TA:** Splunk_TA_microsoft-sqlserver, database error logs
- **Data Sources:** SQL Server error log (login failed events), PostgreSQL `log_connections`, Oracle audit trail
- **SPL:**
```spl
index=database sourcetype="mssql:errorlog"
| search "Login failed"
| rex "Login failed for user '(?<user>[^']+)'"
| stats count by user, src
| where count > 10
| sort -count
```
- **Implementation:** Ensure failed login auditing is enabled (SQL Server: "Both failed and successful logins"). Forward error logs to Splunk. Alert on >10 failures per user per hour. Correlate with AD lockout events.
- **Visualization:** Table (users with failed logins), Bar chart (failures by user), Line chart (failure rate over time).
- **CIM Models:** Databases
- **CIM SPL:**
```spl
| tstats summariesonly=t count from datamodel=Databases.Query by Query.host, Query.action | sort - count
```
- **References:** [CIM: Databases](https://docs.splunk.com/Documentation/CIM/latest/User/Databases)

---

### UC-7.1.8 · Long-Running Transaction Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Long transactions hold locks, causing blocking chains that degrade application performance for many users.
- **App/TA:** DB Connect
- **Data Sources:** `sys.dm_exec_requests` (SQL Server), `pg_stat_activity` (PostgreSQL), Oracle `v$transaction`
- **SPL:**
```spl
index=database sourcetype="dbconnect:active_transactions"
| where transaction_duration_sec > 300
| table _time, server, database_name, user, transaction_duration_sec, sql_text
| sort -transaction_duration_sec
```
- **Implementation:** Poll active transactions via DB Connect every 5 minutes. Alert when any transaction exceeds 5 minutes. Include SQL text and blocking information. Escalate transactions blocking other sessions.
- **Visualization:** Table (active long transactions), Single value (longest active transaction), Timeline (long transaction events).
- **CIM Models:** Databases
- **CIM SPL:**
```spl
| tstats summariesonly=t count from datamodel=Databases.Query by Query.host, Query.action | sort - count
```
- **References:** [CIM: Databases](https://docs.splunk.com/Documentation/CIM/latest/User/Databases)

---

### UC-7.1.9 · Index Fragmentation
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Highly fragmented indexes cause excessive I/O and slow query performance. Monitoring guides maintenance scheduling.
- **App/TA:** DB Connect
- **Data Sources:** `sys.dm_db_index_physical_stats` (SQL Server), `pg_stat_user_indexes` (PostgreSQL)
- **SPL:**
```spl
index=database sourcetype="dbconnect:index_stats"
| where avg_fragmentation_pct > 30
| table server, database_name, table_name, index_name, avg_fragmentation_pct, page_count
| sort -avg_fragmentation_pct
```
- **Implementation:** Poll index fragmentation stats via DB Connect weekly (resource-intensive query — schedule during off-hours). Alert when critical indexes exceed 30% fragmentation. Track fragmentation trend to optimize rebuild schedules.
- **Visualization:** Table (fragmented indexes), Bar chart (fragmentation by database), Heatmap (table × index fragmentation).
- **CIM Models:** Databases
- **CIM SPL:**
```spl
| tstats summariesonly=t count from datamodel=Databases.Instance_Stats by Instance_Stats.host, Instance_Stats.action | sort - count
```
- **References:** [CIM: Databases](https://docs.splunk.com/Documentation/CIM/latest/User/Databases)

---

### UC-7.1.10 · TempDB Contention (SQL Server)
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** TempDB contention is a common SQL Server bottleneck. Detection enables configuration tuning (multiple data files, trace flags).
- **App/TA:** DB Connect, Splunk_TA_microsoft-sqlserver
- **Data Sources:** `sys.dm_os_wait_stats` (PAGELATCH waits), `sys.dm_exec_query_stats`
- **SPL:**
```spl
index=database sourcetype="dbconnect:wait_stats"
| where wait_type LIKE "PAGELATCH%" AND resource_description LIKE "2:%"
| stats sum(wait_time_ms) as total_wait by wait_type
```
- **Implementation:** Poll wait statistics via DB Connect. Filter for PAGELATCH waits on TempDB (database_id 2). Alert when TempDB waits exceed baseline. Recommend adding TempDB data files equal to number of CPU cores (up to 8).
- **Visualization:** Bar chart (wait types), Line chart (TempDB wait trend), Single value (current TempDB wait ms).
- **CIM Models:** Databases
- **CIM SPL:**
```spl
| tstats summariesonly=t count from datamodel=Databases.Instance_Stats by Instance_Stats.host, Instance_Stats.action | sort - count
```
- **References:** [CIM: Databases](https://docs.splunk.com/Documentation/CIM/latest/User/Databases)

---

### UC-7.1.11 · Buffer Cache Hit Ratio
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Low buffer cache hit ratio means excessive disk I/O. Monitoring guides memory allocation decisions.
- **App/TA:** DB Connect, performance counters
- **Data Sources:** SQL Server performance counters, PostgreSQL `pg_stat_bgwriter`
- **SPL:**
```spl
index=database sourcetype="dbconnect:perf_counters"
| where counter_name="Buffer cache hit ratio"
| timechart span=15m avg(cntr_value) as hit_ratio by instance_name
| where hit_ratio < 95
```
- **Implementation:** Poll buffer cache performance counters via DB Connect every 15 minutes. Alert when hit ratio drops below 95% for sustained periods. Correlate with memory pressure and query workload changes.
- **Visualization:** Gauge (buffer cache hit ratio), Line chart (hit ratio over time), Single value (current hit ratio %).
- **CIM Models:** Databases
- **CIM SPL:**
```spl
| tstats summariesonly=t count from datamodel=Databases.Database_Instance by Database_Instance.host, Database_Instance.action span=15m | sort - count
```

- **References:** [CIM: Databases](https://docs.splunk.com/Documentation/CIM/latest/User/Databases)

---

### UC-7.1.12 · Database Availability Group Health
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** AG/RAC cluster health is essential for HA. Detecting unhealthy replicas prevents unplanned failover failures.
- **App/TA:** DB Connect, Splunk_TA_microsoft-sqlserver
- **Data Sources:** `sys.dm_hadr_availability_replica_states` (SQL Server), Oracle CRS logs
- **SPL:**
```spl
index=database sourcetype="dbconnect:ag_status"
| where synchronization_health_desc!="HEALTHY" OR connected_state_desc!="CONNECTED"
| table _time, ag_name, replica_server_name, role_desc, synchronization_health_desc
```
- **Implementation:** Poll AG replica state DMVs every 5 minutes. Alert on any non-HEALTHY or non-CONNECTED state. Track failover events from SQL Server error log. Create dashboard showing full AG topology and health.
- **Visualization:** Status grid (replica × health state), Table (unhealthy replicas), Timeline (failover events).
- **CIM Models:** Databases
- **CIM SPL:**
```spl
| tstats summariesonly=t count from datamodel=Databases.Instance_Stats by Instance_Stats.host, Instance_Stats.action | sort - count
```
- **References:** [CIM: Databases](https://docs.splunk.com/Documentation/CIM/latest/User/Databases)

---

### UC-7.1.13 · Schema Change Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Configuration
- **Value:** Unauthorized DDL changes to production databases can break applications. Detection ensures change control compliance.
- **App/TA:** DB Connect, SQL Server audit
- **Data Sources:** SQL Server DDL triggers, audit logs, PostgreSQL `log_statement='ddl'`
- **SPL:**
```spl
index=database sourcetype="mssql:audit" action_id IN ("CR","AL","DR")
| table _time, server_principal_name, database_name, object_name, statement
| sort -_time
```
- **Implementation:** Enable SQL Server audit for DDL events (CREATE, ALTER, DROP). For PostgreSQL, set `log_statement='ddl'`. Forward audit logs to Splunk. Alert on any DDL outside maintenance windows. Correlate with change tickets.
- **Visualization:** Table (DDL events with details), Timeline (schema changes), Bar chart (changes by user).
- **CIM Models:** Databases
- **CIM SPL:**
```spl
| tstats summariesonly=t count from datamodel=Databases.Query by Query.host, Query.action | sort - count
```
- **References:** [CIM: Databases](https://docs.splunk.com/Documentation/CIM/latest/User/Databases)

---

### UC-7.1.14 · Query Plan Regression
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Fault
- **Value:** Query plan changes can cause sudden performance degradation. Detection enables rapid intervention (plan forcing, hint application).
- **App/TA:** DB Connect
- **Data Sources:** SQL Server Query Store, `sys.dm_exec_query_plan`, PostgreSQL `pg_stat_statements`
- **SPL:**
```spl
index=database sourcetype="dbconnect:query_store"
| stats avg(avg_duration) as current_avg by query_id, plan_id
| join max=1 query_id [| inputlookup query_baselines.csv]
| eval regression_pct=round((current_avg-baseline_avg)/baseline_avg*100,1)
| where regression_pct > 50
```
- **Implementation:** Enable Query Store on SQL Server databases. Poll query performance metrics via DB Connect. Maintain baseline lookup of normal query durations. Alert when queries regress >50% from baseline. Enable automatic plan correction if available.
- **Visualization:** Table (regressed queries), Bar chart (regression % by query), Line chart (query duration trend).
- **CIM Models:** Databases
- **CIM SPL:**
```spl
| tstats summariesonly=t count from datamodel=Databases.Query by Query.host, Query.action | sort - count
```
- **References:** [CIM: Databases](https://docs.splunk.com/Documentation/CIM/latest/User/Databases)

---

### UC-7.1.15 · Privilege Escalation Audit
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security, Compliance
- **Value:** Unauthorized privilege changes can enable data theft or sabotage. Audit trail is required for compliance.
- **App/TA:** DB Connect, SQL Server audit
- **Data Sources:** Database audit logs (GRANT/REVOKE events), security event logs
- **SPL:**
```spl
index=database sourcetype="mssql:audit"
| search action_id IN ("G","R","GWG") statement="*GRANT*" OR statement="*REVOKE*"
| table _time, server_principal_name, database_name, statement, target_server_principal_name
```
- **Implementation:** Enable database audit for security events (GRANT, REVOKE, ALTER ROLE). Forward to Splunk. Alert on any privilege change in production. Correlate with change management tickets and access review cycles.
- **Visualization:** Table (privilege change events), Timeline (changes), Bar chart (changes by granting user).
- **CIM Models:** Databases
- **CIM SPL:**
```spl
| tstats summariesonly=t count from datamodel=Databases.Query by Query.host, Query.action | sort - count
```
- **References:** [CIM: Databases](https://docs.splunk.com/Documentation/CIM/latest/User/Databases)

---

### 7.2 NoSQL Databases

**Primary App/TA:** Custom scripted inputs, vendor management APIs (MongoDB Atlas API, Elasticsearch REST API), JMX for Java-based systems (Cassandra), Redis CLI scripted input.

---

### UC-7.2.1 · Cluster Membership Changes
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Node additions/removals affect data distribution and availability. Unexpected membership changes may indicate failures.
- **App/TA:** Custom scripted input, database event logs
- **Data Sources:** MongoDB replica set events, Cassandra `system.log`, Elasticsearch cluster state
- **SPL:**
```spl
index=database sourcetype="mongodb:log"
| search "replSet" ("added" OR "removed" OR "changed state" OR "election")
| table _time, host, message
| sort -_time
```
- **Implementation:** Forward database logs to Splunk. Parse membership change events. Alert on unexpected node departures. For Elasticsearch, poll `_cluster/health` API and alert on node count changes.
- **Visualization:** Timeline (membership events), Single value (current node count), Table (recent cluster changes).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-7.2.2 · Replication Lag / Consistency
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Replication lag causes stale reads and eventual consistency violations. Monitoring ensures data freshness SLAs are met.
- **App/TA:** Custom scripted input (rs.status(), nodetool)
- **Data Sources:** MongoDB `rs.status()`, Cassandra `nodetool status`, Redis `INFO replication`
- **SPL:**
```spl
index=database sourcetype="mongodb:rs_status"
| eval lag_sec=optime_primary-optime_secondary
| where lag_sec > 10
| table _time, replica_set, member, state, lag_sec
```
- **Implementation:** Run scripted input polling replica set status every minute. Parse member states and optime differences. Alert when lag exceeds threshold (e.g., >10 seconds). Track trend for capacity planning.
- **Visualization:** Line chart (replication lag over time), Table (replicas with lag), Single value (max current lag).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-7.2.3 · Read/Write Latency Trending
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Fault
- **Value:** Latency trending detects performance degradation before it impacts users. Enables proactive tuning and scaling decisions.
- **App/TA:** Custom metrics input, database stats API
- **Data Sources:** MongoDB `serverStatus()`, Cassandra JMX, Elasticsearch `_nodes/stats`
- **SPL:**
```spl
index=database sourcetype="mongodb:server_status"
| timechart span=5m avg(opcounters.query) as reads, avg(opcounters.insert) as writes, avg(opLatencies.reads.latency) as read_lat
```
- **Implementation:** Poll database metrics every 5 minutes via scripted input or API. Track read/write latency percentiles (p50, p95, p99). Baseline normal patterns and alert on sustained deviation. Correlate with workload changes.
- **Visualization:** Line chart (latency percentiles over time), Dual-axis chart (latency + throughput), Table (current latency by operation).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-7.2.4 · Shard Imbalance Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Uneven shard distribution causes hot spots and performance inconsistency. Rebalancing prevents overloaded nodes.
- **App/TA:** Custom scripted input
- **Data Sources:** MongoDB `sh.status()`, Elasticsearch `_cat/shards`
- **SPL:**
```spl
index=database sourcetype="mongodb:shard_status"
| stats sum(count) as doc_count, sum(size) as data_size by shard
| eventstats avg(doc_count) as avg_count
| eval imbalance_pct=round(abs(doc_count-avg_count)/avg_count*100,1)
| where imbalance_pct > 20
```
- **Implementation:** Poll shard statistics periodically. Calculate per-shard deviation from average. Alert when any shard deviates >20% from mean size. For Elasticsearch, track unassigned shards as a separate critical alert.
- **Visualization:** Bar chart (data size per shard), Table (shards with imbalance), Single value (max imbalance %).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-7.2.5 · Compaction Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Pending compactions consume I/O and can cause write amplification. Monitoring ensures compaction keeps pace with writes.
- **App/TA:** JMX input (Cassandra), database logs
- **Data Sources:** Cassandra `nodetool compactionstats`, MongoDB WiredTiger stats, Elasticsearch merge stats
- **SPL:**
```spl
index=database sourcetype="cassandra:compaction"
| timechart span=15m avg(pending_tasks) as pending, sum(bytes_compacted) as compacted
| where pending > 50
```
- **Implementation:** Poll compaction stats via JMX (Cassandra) or scripted input. Track pending compaction tasks and throughput. Alert when pending tasks grow consistently, indicating compaction cannot keep up with write volume.
- **Visualization:** Line chart (pending compactions over time), Dual-axis (pending + throughput), Single value (current pending).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-7.2.6 · GC Pause Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** Long GC pauses in Java-based databases (Cassandra, Elasticsearch) cause request timeouts and can trigger node eviction from the cluster.
- **App/TA:** GC log parsing, JMX
- **Data Sources:** JVM GC logs (`gc.log`), JMX GC metrics
- **SPL:**
```spl
index=database sourcetype="jvm:gc"
| where gc_pause_ms > 500
| stats count, avg(gc_pause_ms) as avg_pause, max(gc_pause_ms) as max_pause by host, gc_type
| where max_pause > 1000
```
- **Implementation:** Configure JVM GC logging on all Java-based database nodes. Forward GC logs to Splunk with proper field extraction. Alert on pauses >500ms. Track GC frequency and total pause time per hour. Recommend heap tuning when pauses are chronic.
- **Visualization:** Line chart (GC pause duration over time), Histogram (pause distribution), Table (hosts with excessive GC).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-7.2.7 · Connection Count Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Capacity
- **Value:** Approaching connection limits causes client rejections. Monitoring enables proactive limit adjustment or connection pooling.
- **App/TA:** Custom scripted input
- **Data Sources:** MongoDB `serverStatus().connections`, Redis `INFO clients`, Elasticsearch `_nodes/stats/transport`
- **SPL:**
```spl
index=database sourcetype="mongodb:server_status"
| eval pct_used=round(connections.current/connections.available*100,1)
| timechart span=5m max(pct_used) as connection_pct by host
| where connection_pct > 80
```
- **Implementation:** Poll connection metrics every 5 minutes. Calculate percentage of max connections used. Alert at 80% and 95%. Track by client application to identify connection leaks.
- **Visualization:** Gauge (% connections used per node), Line chart (connection count over time), Table (nodes approaching limit).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-7.2.8 · Index Build Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Index builds consume significant resources and can impact production performance. Tracking ensures builds complete within maintenance windows.
- **App/TA:** Database log parsing
- **Data Sources:** MongoDB log (`INDEX` messages), Elasticsearch `_tasks` API
- **SPL:**
```spl
index=database sourcetype="mongodb:log"
| search "index build"
| rex "building index on (?<collection>\S+)"
| table _time, host, collection, message
```
- **Implementation:** Parse database logs for index build events (start, progress, completion). Alert on index builds in production during business hours. Track build duration for capacity planning.
- **Visualization:** Table (active/recent index builds), Timeline (build events), Single value (builds in progress).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-7.2.9 · Memory Utilization
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Fault
- **Value:** NoSQL databases are memory-intensive. Evictions indicate undersized cache, causing disk reads and performance degradation.
- **App/TA:** Custom scripted input, JMX
- **Data Sources:** Redis `INFO memory`, MongoDB WiredTiger cache stats, Cassandra JMX heap metrics
- **SPL:**
```spl
index=database sourcetype="redis:info"
| eval mem_pct=round(used_memory/maxmemory*100,1)
| timechart span=5m max(mem_pct) as memory_pct, sum(evicted_keys) as evictions by host
| where memory_pct > 85
```
- **Implementation:** Poll memory metrics every 5 minutes. Track used vs max memory, eviction rate, and cache hit ratio. Alert when memory exceeds 85% or eviction rate spikes. Recommend sizing adjustments based on trends.
- **Visualization:** Gauge (memory % per node), Line chart (memory + evictions), Table (nodes with high utilization).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-7.2.10 · Elasticsearch Cluster Health
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Elasticsearch cluster status directly indicates data availability. Yellow/red status requires immediate attention to prevent data loss.
- **App/TA:** Custom REST API input
- **Data Sources:** Elasticsearch `_cluster/health` API
- **SPL:**
```spl
index=database sourcetype="elasticsearch:cluster_health"
| eval status_num=case(status="green",0, status="yellow",1, status="red",2)
| timechart span=5m latest(status_num) as health, latest(unassigned_shards) as unassigned by cluster_name
| where health > 0
```
- **Implementation:** Poll `_cluster/health` endpoint every minute. Alert on yellow status (warning) and red status (critical). Track unassigned shard count and node count. Correlate with JVM metrics and disk space to identify root cause.
- **Visualization:** Status indicator (green/yellow/red), Single value (unassigned shards), Line chart (cluster health timeline), Table (cluster details).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-7.2.11 · MongoDB Oplog Window
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Fault, Availability
- **Value:** Oplog window shrinking indicates replication at risk of falling behind. Exhausted oplog causes replica set members to resync from scratch (full resync), causing extended downtime.
- **App/TA:** Custom scripted input (mongosh)
- **Data Sources:** `rs.printReplicationInfo()`, `db.getReplicationInfo()`
- **SPL:**
```spl
index=database sourcetype="mongodb:replication_info"
| eval window_hours=round(timeDiff/3600, 1)
| where window_hours < 24
| timechart span=1h latest(window_hours) as oplog_window_hours by host
| where oplog_window_hours < 12
```
- **Implementation:** Run scripted input polling `rs.printReplicationInfo()` or `db.getReplicationInfo()` every 15–30 minutes via mongosh. Parse `timeDiff` (oplog window in seconds). Alert when window drops below 24 hours (warning) or 12 hours (critical). Correlate with write throughput and replication lag. Recommend oplog size increase when window consistently shrinks.
- **Visualization:** Line chart (oplog window hours over time), Single value (current window hours), Table (hosts with shrinking oplog).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-7.2.12 · MongoDB WiredTiger Cache Pressure
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance
- **Value:** Cache dirty/used ratio approaching eviction thresholds causes increased disk I/O and degraded query performance. Early detection enables cache sizing or workload tuning.
- **App/TA:** Custom scripted input (mongosh serverStatus)
- **Data Sources:** `db.serverStatus().wiredTiger.cache`
- **SPL:**
```spl
index=database sourcetype="mongodb:server_status"
| eval dirty_pct=round(bytes_dirty/bytes_currently_in_the_cache*100, 1)
| eval used_pct=round(bytes_currently_in_the_cache/cache_maximum_bytes_configured*100, 1)
| where dirty_pct > 20 OR used_pct > 90
| timechart span=5m avg(dirty_pct) as dirty_pct, avg(used_pct) as used_pct by host
```
- **Implementation:** Poll `db.serverStatus()` via mongosh every 5 minutes. Extract `wiredTiger.cache`; map MongoDB fields ("bytes dirty in the cache", "bytes currently in the cache", "maximum bytes configured") to bytes_dirty, bytes_currently_in_the_cache, cache_maximum_bytes_configured in the scripted input output. Compute dirty and used percentages. Alert when dirty_pct >20% (eviction pressure) or used_pct >90%. Track eviction count and evicted pages. Correlate with workload spikes.
- **Visualization:** Line chart (dirty % and used % over time), Gauge (cache pressure), Table (hosts with high cache pressure).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-7.2.13 · MongoDB Atlas Cluster Alerts
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability, Fault
- **Value:** Atlas project alerts (CPU, connections, replication) forwarded to Splunk provide a single pane with on-prem MongoDB. Rapid correlation during incidents.
- **App/TA:** MongoDB Atlas API / Atlas App Services webhook, HEC
- **Data Sources:** Atlas alert payloads (clusterId, alertType, status, metric values)
- **SPL:**
```spl
index=database sourcetype="mongodb:atlas:alert"
| where status="OPEN" OR severity IN ("CRITICAL","WARNING")
| stats latest(_time) as last_alert, values(alertType) as types by cluster_name, project_id
| sort -last_alert
```
- **Implementation:** Configure Atlas to send alerts to HTTPS endpoint (Splunk HEC) or poll Alerts API every minute. Normalize fields. Page on CRITICAL OPEN alerts.
- **Visualization:** Timeline (Atlas alerts), Table (cluster, alert type, status), Single value (open critical count).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-7.2.14 · Cassandra Compaction Backlog and Throughput
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Pending compactions and compaction throughput indicate whether the cluster keeps up with writes. Complements generic compaction UC with nodetool-derived rates.
- **App/TA:** JMX, `nodetool compactionstats` scripted input
- **Data Sources:** `pending_tasks`, `bytes_compacted`, `compaction throughput`
- **SPL:**
```spl
index=database sourcetype="cassandra:compactionstats"
| where pending_tasks > 100 OR compaction_throughput_mbps < 5
| timechart span=15m max(pending_tasks) as pending, avg(compaction_throughput_mbps) as tp_mbps by cluster_name
```
- **Implementation:** Poll nodetool every 5m per node. Alert when pending_tasks grows monotonically for 1h or throughput collapses.
- **Visualization:** Dual-axis (pending vs throughput), Table (nodes with backlog), Line chart (pending tasks).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-7.2.15 · Redis Memory Fragmentation (Cache Tier)
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** High `mem_fragmentation_ratio` on self-managed Redis (not only ElastiCache) wastes RAM and increases latency. Tracks non-cloud Redis clusters in the NoSQL section.
- **App/TA:** redis-cli scripted input
- **Data Sources:** `INFO memory` — `mem_fragmentation_ratio`, `used_memory_rss`
- **SPL:**
```spl
index=database sourcetype="redis:info" role=master
| where mem_fragmentation_ratio > 1.5
| timechart span=15m avg(mem_fragmentation_ratio) as frag by host
```
- **Implementation:** Poll every 15m. Alert when ratio >1.5 for 24h. Recommend active defrag or restart per policy.
- **Visualization:** Line chart (fragmentation ratio), Table (hosts over threshold), Gauge (current ratio).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-7.2.16 · DynamoDB Throttling Events
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance, Availability
- **Value:** Read/write throttle events mean application retries and latency spikes. Identifies hot partitions and undersized capacity modes.
- **App/TA:** `Splunk_TA_aws` (CloudWatch)
- **Data Sources:** `UserErrors`, `ThrottledRequests`, `ConsumedReadCapacityUnits`
- **SPL:**
```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/DynamoDB" metric_name="ThrottledRequests"
| timechart span=5m sum(Sum) as throttled by TableName, Operation
| where throttled > 0
```
- **Implementation:** Enable DynamoDB metrics with table dimension. Alert on any sustained throttling. Correlate with hot key patterns from access logs if available.
- **Visualization:** Line chart (throttled requests), Table (table, operation), Single value (throttle bursts per day).
- **CIM Models:** N/A

- **References:** [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)

---

### UC-7.2.17 · CouchDB Replication Conflicts
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** Growing `_conflicts` document count indicates divergent replicas and data quality issues. Early detection prevents silent wrong reads.
- **App/TA:** CouchDB `_stats`, `_active_tasks` API
- **Data Sources:** Replication task errors, document conflict counts (custom view or `_changes` sampling)
- **SPL:**
```spl
index=database sourcetype="couchdb:replication"
| where conflict_count > 0 OR error IS NOT NULL
| stats sum(conflict_count) as conflicts, latest(error) as err by database_name, source, target
| sort -conflicts
```
- **Implementation:** Ingest replication task status from `_active_tasks` and periodic conflict counts from a map view. Alert on replication errors or conflict_count increase week-over-week.
- **Visualization:** Table (DB, conflicts, error), Line chart (conflict trend), Single value (total conflicts).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-7.2.18 · MongoDB Oplog Window Sufficiency
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Availability
- **Value:** Validates minimum oplog window hours against replica catch-up time under peak load. Extends oplog monitoring with capacity-style thresholds per deployment class.
- **App/TA:** mongosh scripted input
- **Data Sources:** `getReplicationInfo()`, `rs.printReplicationInfo()`
- **SPL:**
```spl
index=database sourcetype="mongodb:replication_info"
| eval window_hrs=round(timeDiff/3600,2)
| lookup mongo_replica_tier class OUTPUT min_oplog_window_hrs
| where window_hrs < min_oplog_window_hrs
| table host window_hrs min_oplog_window_hrs
```
- **Implementation:** Define minimum window per environment in lookup. Alert below tier minimum. Recommend oplog size change when consistently borderline.
- **Visualization:** Line chart (oplog window hours), Table (hosts below tier min), Gauge (worst window).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-7.2.19 · Cassandra Tombstone Accumulation
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance
- **Value:** High tombstone counts per read and GC pressure slow queries and repairs. Monitoring `TombstoneHistogram` and read repair backlog prevents timeouts.
- **App/TA:** JMX, `nodetool tablestats`
- **Data Sources:** `Estimated droppable tombstones`, read path tombstone thresholds
- **SPL:**
```spl
index=database sourcetype="cassandra:tablestats"
| where droppable_tombstones > 100000 OR live_sstable_count > 50
| stats latest(droppable_tombstones) as tombstones by keyspace, table, host
| sort -tombstones
```
- **Implementation:** Poll tablestats weekly or daily per large tables. Alert on droppable tombstones above baseline. Correlate with TTL/schema design reviews.
- **Visualization:** Table (KS, table, tombstones), Bar chart (top tables), Line chart (tombstone trend).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-7.2.20 · Redis Eviction Rate
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Capacity
- **Value:** Rising `evicted_keys` per second indicates memory pressure and cache miss storms. Distinct from fragmentation and hit ratio for ops response.
- **App/TA:** redis-cli `INFO stats`
- **Data Sources:** `evicted_keys`, `maxmemory`, `used_memory`
- **SPL:**
```spl
index=database sourcetype="redis:info"
| timechart span=1m per_second(evicted_keys) as evict_per_sec by host
| where evict_per_sec > 10
```
- **Implementation:** Derive per-second evictions from counter deltas. Alert when sustained above baseline. Correlate with `maxmemory` policy and traffic.
- **Visualization:** Line chart (evictions/sec), Table (hosts spiking), Dual-axis (evictions + memory).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-7.2.21 · HBase RegionServer Failover Events
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** RegionServer death and region reassignment cause latency spikes and possible unavailability. Log and metric correlation speeds recovery.
- **App/TA:** HBase Master/RS logs, JMX
- **Data Sources:** `ServerShutdownHandler`, `Regions moved`, Dead RegionServer count
- **SPL:**
```spl
index=database sourcetype="hbase:master"
| search "ServerShutdownHandler" OR "Dead RegionServer" OR "FailedServerShutdown"
| stats count by cluster_name, host
| where count > 0
```
- **Implementation:** Forward HBase master and RS logs. Alert on any dead RS or failed shutdown. Track region-in-transition duration from JMX if ingested.
- **Visualization:** Timeline (RS failures), Table (cluster, host, events), Single value (RS down count).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-7.2.22 · CouchDB View Build Times
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Long-running view index builds block compaction and increase disk I/O. Tracks `_active_tasks` indexer progress and failures.
- **App/TA:** CouchDB `_active_tasks`, log ingestion
- **Data Sources:** Indexer task type, `progress`, `total_changes`
- **SPL:**
```spl
index=database sourcetype="couchdb:active_tasks" type=indexer
| eval pct=round(progress/total_changes*100,1)
| where pct < 100 AND updated_in_sec > 3600
| table database_name design_doc pct updated_in_sec
```
- **Implementation:** Poll `_active_tasks` every minute. Alert when indexer runs >1h with low progress or task errors. Correlate with data volume growth.
- **Visualization:** Table (design doc, % complete), Line chart (indexer duration), Single value (stuck indexers).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-7.2.23 · MongoDB Index Inefficiency (Usage vs Size)
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance
- **Value:** Indexes with near-zero `accesses.ops` and large `size` waste RAM and slow writes. Identifies candidates for drop or partial indexes.
- **App/TA:** mongosh `$indexStats`, log export
- **Data Sources:** `collStats`, `$indexStats` output
- **SPL:**
```spl
index=database sourcetype="mongodb:index_stats"
| eval usage=ops_since_start
| where index_size_bytes > 104857600 AND usage < 10
| table ns, name, index_size_bytes, usage
| sort -index_size_bytes
```
- **Implementation:** Weekly job exports `$indexStats`. Flag large indexes with minimal usage. Exclude `_id` and required unique indexes via lookup.
- **Visualization:** Table (namespace, index, size, ops), Bar chart (wasted index size), Single value (low-usage large indexes count).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### 7.3 Cloud-Managed Databases

**Primary App/TA:** Cloud provider TAs — `Splunk_TA_aws` (CloudWatch, RDS logs), `Splunk_TA_microsoft-cloudservices` (Azure Monitor), GCP TA.

---

### UC-7.3.1 · RDS/Aurora Performance Insights
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Performance Insights identifies top SQL and wait events without agent installation. Enables rapid diagnosis of managed database bottlenecks.
- **App/TA:** `Splunk_TA_aws` (CloudWatch)
- **Data Sources:** RDS Performance Insights API, CloudWatch Enhanced Monitoring
- **SPL:**
```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/RDS"
| where metric_name IN ("CPUUtilization","DatabaseConnections","ReadLatency","WriteLatency")
| timechart span=5m avg(Average) by metric_name, DBInstanceIdentifier
```
- **Implementation:** Enable Enhanced Monitoring and Performance Insights on RDS instances. Ingest CloudWatch metrics via Splunk Add-on for AWS. Enable RDS log exports (slow query, error, general) to CloudWatch Logs for deeper analysis.
- **Visualization:** Multi-line chart (CPU, connections, latency), Table (top wait events), Single value (current active sessions).
- **CIM Models:** N/A

- **References:** [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)

---

### UC-7.3.2 · Automated Failover Events
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Managed database failovers cause brief outages. Detection enables impact analysis and root cause investigation.
- **App/TA:** `Splunk_TA_aws` (CloudTrail/EventBridge), Azure Activity Log
- **Data Sources:** RDS events, Azure SQL activity log, Cloud SQL admin activity
- **SPL:**
```spl
index=aws sourcetype="aws:cloudwatch:events"
| search detail.EventCategories="failover"
| table _time, detail.SourceIdentifier, detail.Message
```
- **Implementation:** Ingest RDS event subscriptions via SNS → SQS → Splunk. Filter for failover events. Alert immediately with PagerDuty/ServiceNow integration. Correlate with application error spikes to measure impact duration.
- **Visualization:** Timeline (failover events), Table (failover details), Single value (days since last failover).
- **CIM Models:** N/A

- **References:** [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)

---

### UC-7.3.3 · Read Replica Lag
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Fault
- **Value:** Replica lag affects read consistency for applications using read replicas. Monitoring prevents stale data serving.
- **App/TA:** Cloud provider TAs (CloudWatch, Azure Monitor)
- **Data Sources:** CloudWatch `ReplicaLag` metric, Azure SQL `replication_lag`
- **SPL:**
```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/RDS" metric_name="ReplicaLag"
| timechart span=5m max(Maximum) as replica_lag_sec by DBInstanceIdentifier
| where replica_lag_sec > 30
```
- **Implementation:** Ingest CloudWatch RDS metrics. Alert when ReplicaLag exceeds application tolerance (e.g., >30 seconds). Track trend and correlate with write workload spikes. Alert on replica lag growing consistently.
- **Visualization:** Line chart (replica lag over time), Single value (current max lag), Table (replicas with lag).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-7.3.4 · Storage Auto-Scaling Events
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Tracks storage auto-scaling events for cost awareness and identifies databases with rapid growth needing attention.
- **App/TA:** Cloud provider TAs
- **Data Sources:** CloudTrail (ModifyDBInstance), Azure Activity Log
- **SPL:**
```spl
index=aws sourcetype="aws:cloudtrail" eventName="ModifyDBInstance"
| spath output=allocated requestParameters.allocatedStorage
| where isnotnull(allocated)
| table _time, requestParameters.dBInstanceIdentifier, allocated, userIdentity.principalId
```
- **Implementation:** Ingest CloudTrail events. Filter for storage modification events. Track growth frequency per database. Alert when auto-scaling occurs more than twice per week, indicating rapid growth needing review.
- **Visualization:** Timeline (scaling events), Table (databases with scaling history), Bar chart (scaling frequency by database).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-7.3.5 · Maintenance Window Tracking
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Awareness of upcoming and completed maintenance ensures teams are prepared for potential service impact.
- **App/TA:** Cloud provider TAs
- **Data Sources:** RDS event subscriptions, Azure Service Health, GCP maintenance notifications
- **SPL:**
```spl
index=aws sourcetype="aws:cloudwatch:events"
| search detail.EventCategories="maintenance"
| table _time, detail.SourceIdentifier, detail.Message, detail.Date
| sort detail.Date
```
- **Implementation:** Subscribe to RDS maintenance events via SNS. Ingest into Splunk. Create calendar view of upcoming maintenance. Alert 72 hours before scheduled maintenance. Log actual impact duration after completion.
- **Visualization:** Table (upcoming/recent maintenance), Calendar view, Timeline (maintenance history).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-7.3.6 · Redis Memory Fragmentation Ratio
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Fragmentation ratio > 1.5 indicating memory inefficiency. High fragmentation wastes RAM and can trigger OOM or evictions under memory pressure.
- **App/TA:** Custom scripted input (redis-cli INFO memory)
- **Data Sources:** redis-cli INFO memory (mem_fragmentation_ratio)
- **SPL:**
```spl
index=database sourcetype="redis:info"
| where mem_fragmentation_ratio > 1.5
| timechart span=15m avg(mem_fragmentation_ratio) as frag_ratio by host
| where frag_ratio > 1.5
```
- **Implementation:** Create scripted input running `redis-cli INFO memory` every 15 minutes. Parse `mem_fragmentation_ratio` (used_memory_rss/used_memory). Alert when ratio exceeds 1.5. Track `used_memory_rss` and `used_memory` for trend analysis. Consider `MEMORY PURGE` (Redis 4+) or restart for severe fragmentation. Correlate with eviction rate.
- **Visualization:** Line chart (fragmentation ratio over time), Gauge (current ratio), Table (hosts with high fragmentation).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-7.3.7 · Redis Keyspace Hit / Miss Ratio
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Cache effectiveness trending. Low hit ratio indicates cache is not serving requests effectively, increasing load on backing stores.
- **App/TA:** Custom scripted input (redis-cli INFO stats)
- **Data Sources:** redis-cli INFO stats (keyspace_hits, keyspace_misses)
- **SPL:**
```spl
index=database sourcetype="redis:info"
| eval total_ops=keyspace_hits+keyspace_misses
| eval hit_ratio_pct=round(100*keyspace_hits/nullif(total_ops,0), 2)
| where hit_ratio_pct < 90
| timechart span=15m avg(hit_ratio_pct) as hit_ratio_pct by host
```
- **Implementation:** Poll `redis-cli INFO stats` every 15 minutes. Extract `keyspace_hits` and `keyspace_misses`. Compute hit_ratio = hits/(hits+misses)*100. Alert when hit ratio drops below 90% for sustained periods. Track trend to identify cache warming after restarts or workload shifts. Correlate with eviction rate and memory usage.
- **Visualization:** Gauge (keyspace hit ratio %), Line chart (hit ratio over time), Table (hosts with low hit ratio).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-7.3.8 · Aurora Serverless Scaling Events
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance, Capacity
- **Value:** ACU (capacity unit) scale-up/down events explain latency and cost. Tracks whether scaling policy matches workload bursts.
- **App/TA:** `Splunk_TA_aws` (RDS events, CloudWatch)
- **Data Sources:** RDS event categories `notification`, `serverless`, CloudWatch `ServerlessDatabaseCapacity`
- **SPL:**
```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/RDS" metric_name="ServerlessDatabaseCapacity"
| timechart span=5m avg(Average) as acu by DBClusterIdentifier
```
- **Implementation:** Ingest ACU metric and RDS events for scale actions. Alert on repeated scale-to-max or throttling. Correlate with `DatabaseConnections` and CPU.
- **Visualization:** Line chart (ACU over time), Timeline (scaling events), Table (clusters at max ACU).
- **CIM Models:** N/A

- **References:** [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)

---

### UC-7.3.9 · Azure Cosmos DB RU Consumption
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance, Capacity
- **Value:** Normalized RU/s consumption vs provisioned throughput identifies hot partitions and autoscale effectiveness.
- **App/TA:** `Splunk_TA_microsoft-cloudservices`, Azure Monitor metrics
- **Data Sources:** `NormalizedRUConsumption`, `Total Request Units`
- **SPL:**
```spl
index=azure sourcetype="mssql:azuremonitor" OR sourcetype="azure:metrics"
| search metric_name="NormalizedRUConsumption" OR "*Cosmos*"
| timechart span=5m avg(average) as norm_ru by DatabaseName, CollectionName
| where norm_ru > 0.9
```
- **Implementation:** Map exact metric names from your Azure diagnostic settings. Alert when normalized consumption >90% sustained. Split by partition key if available in custom dimensions.
- **Visualization:** Line chart (RU consumption %), Table (collections over threshold), Single value (hottest collection).
- **CIM Models:** N/A

- **References:** [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)

---

### UC-7.3.10 · Cloud Spanner Instance Health
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** CPU utilization, hot spots, and replication delay for Spanner nodes indicate risk of write/read stalls on globally distributed data.
- **App/TA:** GCP Monitoring TA, scripted export
- **Data Sources:** `spanner.googleapis.com/instance/cpu/utilization`, `transaction_count`, `streaming_pull_response_count`
- **SPL:**
```spl
index=gcp sourcetype="gcp:monitoring" metric_type="spanner.googleapis.com/instance/cpu/utilization"
| timechart span=5m avg(value) as cpu_util by instance_id
| where cpu_util > 0.65
```
- **Implementation:** Ingest Spanner instance metrics per project. Alert on high CPU or increasing 99p latency metrics. Use query insights export for hot keys if enabled.
- **Visualization:** Line chart (CPU and latency), Table (instances over SLO), Heatmap (instance × region).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-7.3.11 · Managed Database Failover Events (Multi-Cloud)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Single search across RDS failover, Azure SQL failover, and Cloud SQL failover for hybrid teams. Supplements UC-7.3.2 with normalized fields.
- **App/TA:** CloudTrail, Azure Activity Log, GCP Audit Logs
- **Data Sources:** `Failover`, `failover`, `switchover` events
- **SPL:**
```spl
(index=aws sourcetype="aws:cloudwatch:events") OR (index=azure sourcetype="azure:activity") OR (index=gcp sourcetype="gcp:audit")
| search failover OR Failover OR switchover
| eval cloud=case(index=="aws","AWS", index=="azure","Azure", index=="gcp","GCP",1=1,"unknown")
| table _time, cloud, resource_name, message
| sort -_time
```
- **Implementation:** Normalize resource identifiers in CIM-style fields at ingest. Route to incident workflow with application dependency tags.
- **Visualization:** Timeline (failovers by cloud), Table (resource, cloud, time), Single value (failovers 30d).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-7.3.12 · Azure SQL Database DTU Exhaustion
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** DTU/vCore saturation causes throttling and query timeouts. Distinct from generic RDS CPU for Azure-only deployments.
- **App/TA:** `Splunk_TA_microsoft-cloudservices`
- **Data Sources:** `dtu_consumption_percent`, `cpu_percent`, `data_io_percent`
- **SPL:**
```spl
index=azure sourcetype="azure:sql:metrics"
| where dtu_consumption_percent > 85 OR cpu_percent > 90
| timechart span=5m max(dtu_consumption_percent) as dtu_pct by database_name, elastic_pool_name
```
- **Implementation:** Enable Azure Monitor metrics for SQL DB/elastic pool. Alert on sustained high DTU%. Recommend tier upgrade or elastic pool rebalance.
- **Visualization:** Line chart (DTU %), Gauge (current DTU), Table (databases over 85%).
- **CIM Models:** N/A

- **References:** [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)

---

### UC-7.3.13 · Cloud SQL Storage Auto-Grow Events
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Capacity
- **Value:** Automatic storage increases for GCP Cloud SQL (and similar) signal rapid data growth and cost impact.
- **App/TA:** GCP audit logs, Cloud SQL Admin API events
- **Data Sources:** `storageResize`, disk size change operations
- **SPL:**
```spl
index=gcp sourcetype="gcp:audit" protoPayload.methodName="*.sql.instances.patch"
| spath output=new_disk_gb protoPayload.request.settings.dataDiskSizeGb
| where isnotnull(new_disk_gb)
| table _time, resourceName, new_disk_gb, protoPayload.authenticationInfo.principalEmail
```
- **Implementation:** Parse patch operations that change disk size. Alert when more than one resize per week per instance. Forecast disk from `disk_utilization` metrics.
- **Visualization:** Timeline (resize events), Table (instance, new size GB), Line chart (disk size over time).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-7.3.14 · Managed Backup Retention Compliance
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Value:** Verifies automated backup snapshots exist within required retention for RDS, Azure SQL LTR, and Cloud SQL backups.
- **App/TA:** Cloud APIs (describe-db-snapshots, backup list)
- **Data Sources:** Snapshot timestamps, backup policy metadata
- **SPL:**
```spl
index=cloud sourcetype="rds:snapshot_inventory"
| stats latest(snapshot_time) as last_snap by db_instance_identifier
| eval days_since=round((now()-strptime(last_snap,"%Y-%m-%d %H:%M:%S"))/86400)
| where days_since > 1
| table db_instance_identifier last_snap days_since
```
- **Implementation:** Ingest daily snapshot inventory from AWS/Azure/GCP APIs. Compare to RPO policy (e.g., last snapshot <25h). Alert on missing snapshot for production tier.
- **Visualization:** Table (instances missing recent backup), Single value (non-compliant count), Calendar (snapshot coverage).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-7.3.15 · Read Replica Lag Trending (Percentiles)
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** p95/p99 replica lag exposes tail behavior missed by max-only dashboards. Applies to RDS, Aurora, and Azure read replicas.
- **App/TA:** CloudWatch, Azure Monitor
- **Data Sources:** `ReplicaLag` (seconds), `physical_replication_delay`
- **SPL:**
```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/RDS" metric_name="ReplicaLag"
| timechart span=5m perc95(Maximum) as p95_lag, max(Maximum) as max_lag by DBInstanceIdentifier
| where p95_lag > 30
```
- **Implementation:** Set SLA based on app freshness needs. Alert on p95 > threshold for 15m. Compare primary write IOPS to replica apply lag.
- **Visualization:** Line chart (p95/p99 replica lag), Table (replicas breaching SLA), Single value (worst p95).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-7.3.16 · Azure SQL Managed Instance Resource Utilization
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance, Capacity
- **Value:** SQL Managed Instance provides near-100% SQL Server compatibility in Azure. CPU, storage I/O, and memory pressure against provisioned limits directly impact query performance and can cause throttling.
- **App/TA:** `Splunk_TA_microsoft-cloudservices` (Azure Monitor metrics)
- **Data Sources:** `sourcetype=azure:monitor:metric` (Microsoft.Sql/managedInstances)
- **SPL:**
```spl
index=cloud sourcetype="azure:monitor:metric" resource_type="microsoft.sql/managedinstances"
| where metric_name IN ("avg_cpu_percent","io_bytes_read","io_bytes_written","storage_space_used_mb")
| timechart span=5m avg(average) as value by metric_name, resource_name
```
- **Implementation:** Collect Azure Monitor metrics for SQL Managed Instance. Key metrics: `avg_cpu_percent` (alert >85% sustained), `io_bytes_read`/`io_bytes_written` against provisioned IOPS for the service tier, and `storage_space_used_mb` versus reserved storage. Monitor `virtual_core_count` utilization to guide tier scaling decisions. Alert on sustained high CPU and storage approaching the limit.
- **Visualization:** Line chart (CPU % over time), Gauge (storage used vs. limit), Table (instances near capacity).
- **CIM Models:** Performance
- **CIM SPL:**
```spl
| tstats summariesonly=t avg(Performance.cpu_load_percent) as agg_value from datamodel=Performance.Storage by Performance.host span=5m | sort - agg_value
```

- **References:** [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110), [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)

---

### UC-7.3.17 · Azure SQL Managed Instance Failover Group Status
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Failover groups provide geo-redundancy for SQL Managed Instance. Monitoring replication lag and failover events ensures disaster recovery readiness and detects unplanned failovers.
- **App/TA:** `Splunk_TA_microsoft-cloudservices` (Azure Monitor metrics/Activity Log)
- **Data Sources:** `sourcetype=azure:monitor:activity`, `sourcetype=azure:monitor:metric`
- **SPL:**
```spl
index=cloud sourcetype="azure:monitor:activity" resourceType="microsoft.sql/managedinstances/failovergroups"
| where operationName="Microsoft.Sql/managedInstances/failoverGroups/failover/action"
| table _time, caller, status, resource_name
| sort -_time
```
- **Implementation:** Collect Activity Log events for failover group operations and Azure Monitor metrics for replication state. Alert on unplanned failover events (not initiated by known maintenance windows). Monitor `ReplicationState` metric — alert when state is not `SEEDING` or `CATCH_UP` for extended periods. Track replication lag to validate RPO compliance.
- **Visualization:** Timeline (failover events), Single value (current replication state), Table (failover history).
- **CIM Models:** N/A

- **References:** [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)

---

### 7.4 Data Warehouses & Analytics Platforms

**Primary App/TA:** Custom REST API inputs (Snowflake Account Usage, BigQuery INFORMATION_SCHEMA), cloud provider TAs for billing/usage data.

---

### UC-7.4.1 · Query Performance Trending
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity
- **Value:** Identifies expensive and slow queries impacting warehouse performance and cost. Enables query optimization and cost reduction.
- **App/TA:** Custom API input (Snowflake ACCOUNT_USAGE), DB Connect
- **Data Sources:** Snowflake `QUERY_HISTORY`, BigQuery `INFORMATION_SCHEMA.JOBS`, Redshift `STL_QUERY`
- **SPL:**
```spl
index=datawarehouse sourcetype="snowflake:query_history"
| where EXECUTION_STATUS="SUCCESS" AND TOTAL_ELAPSED_TIME > 60000
| stats avg(TOTAL_ELAPSED_TIME) as avg_ms, sum(CREDITS_USED_CLOUD_SERVICES) as credits by USER_NAME, WAREHOUSE_NAME
| sort -credits
```
- **Implementation:** Poll query history views via REST API or DB Connect daily. Track query duration, queue time, and cost. Identify top resource consumers. Create weekly optimization report for data engineering teams.
- **Visualization:** Table (expensive queries), Bar chart (cost/duration by warehouse), Line chart (query performance trend).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-7.4.2 · Cluster Scaling Events
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Tracks auto-scaling decisions for cost optimization. Identifies whether current scaling policies match workload patterns.
- **App/TA:** Custom API input, cloud provider TAs
- **Data Sources:** Snowflake `WAREHOUSE_EVENTS_HISTORY`, Redshift resize events, BigQuery slot utilization
- **SPL:**
```spl
index=datawarehouse sourcetype="snowflake:warehouse_events"
| search event_name IN ("RESIZE_CLUSTER","SUSPEND_CLUSTER","RESUME_CLUSTER")
| timechart span=1h count by event_name, warehouse_name
```
- **Implementation:** Poll warehouse event history. Track resume/suspend/scaling frequency. Correlate with query concurrency to validate scaling policies. Alert on unexpected scaling events outside business hours.
- **Visualization:** Timeline (scaling events), Stacked bar (events by type per day), Table (warehouse scaling summary).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-7.4.3 · Data Pipeline Health
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** Failed or delayed ETL/ELT pipelines cause stale data for reporting and analytics. Early detection prevents downstream impact.
- **App/TA:** Custom API input, orchestrator integration (Airflow, dbt)
- **Data Sources:** Airflow task logs, dbt run results, Snowflake TASK_HISTORY, pipeline orchestrator APIs
- **SPL:**
```spl
index=datawarehouse sourcetype="airflow:task_instance"
| stats count(eval(state="failed")) as failed, count(eval(state="success")) as success, count as total by dag_id, task_id
| eval fail_rate=round(failed/total*100,1)
| where fail_rate > 0
| sort -fail_rate
```
- **Implementation:** Ingest pipeline orchestrator logs (Airflow, dbt, custom). Track job outcomes, durations, and data freshness. Alert on any pipeline failure. Create data freshness SLA dashboard showing when each table was last updated. For dbt and Snowflake pipelines, create similar searches targeting their respective sourcetypes (e.g., snowflake:task_history, dbt:run_results).
- **Visualization:** Status grid (pipeline × status), Table (failed pipelines), Line chart (pipeline duration trend), Single value (overall success rate).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-7.4.4 · Credit / Cost per Query
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Directly ties compute cost to individual queries, enabling chargeback and cost optimization. Identifies runaway queries consuming excessive resources.
- **App/TA:** Custom API input (Snowflake ACCOUNT_USAGE)
- **Data Sources:** Snowflake `QUERY_HISTORY` (CREDITS_USED), BigQuery `INFORMATION_SCHEMA.JOBS` (total_bytes_billed)
- **SPL:**
```spl
index=datawarehouse sourcetype="snowflake:query_history"
| eval cost=CREDITS_USED_CLOUD_SERVICES * 3
| stats sum(cost) as total_cost, count as query_count by USER_NAME, WAREHOUSE_NAME
| eval cost_per_query=round(total_cost/query_count,2)
| sort -total_cost
```
- **Implementation:** Poll query history with cost metrics daily. Calculate cost per query, per user, and per team (using role mapping). Create weekly cost report. Alert on individual queries exceeding cost threshold. Set up warehouse-level budgets.
- **Visualization:** Bar chart (cost by user/warehouse), Table (most expensive queries), Line chart (daily cost trend), Pie chart (cost by team).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-7.4.5 · Warehouse Utilization
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Right-sizing warehouses reduces cost while maintaining performance. Utilization data drives scaling policy decisions.
- **App/TA:** Custom API input
- **Data Sources:** Snowflake `WAREHOUSE_LOAD_HISTORY`, Redshift `WLM_QUEUE_STATE`, BigQuery reservation utilization
- **SPL:**
```spl
index=datawarehouse sourcetype="snowflake:warehouse_load"
| timechart span=15m avg(AVG_RUNNING) as avg_queries, avg(AVG_QUEUED_LOAD) as avg_queued by WAREHOUSE_NAME
| where avg_queued > 1
```
- **Implementation:** Poll warehouse utilization metrics every 15 minutes. Track running vs queued queries. Alert when queuing occurs consistently (indicates undersized warehouse). Identify idle warehouses for auto-suspend policy adjustment.
- **Visualization:** Line chart (running vs queued queries), Heatmap (warehouse × hour utilization), Table (underutilized warehouses), Bar chart (utilization by warehouse).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-7.4.6 · Elasticsearch Cluster Health and Shard Status
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability, Fault
- **Value:** Red/yellow cluster, unassigned shards, and JVM pressure indicate data availability risk. Early detection prevents data loss and service degradation.
- **App/TA:** Custom scripted input (ES REST API)
- **Data Sources:** `_cluster/health`, `_cluster/stats`, `_cat/shards`
- **SPL:**
```spl
index=database sourcetype="elasticsearch:cluster_health"
| eval status_num=case(status="green",0, status="yellow",1, status="red",2)
| where status_num > 0 OR unassigned_shards > 0
| timechart span=5m latest(status_num) as health, latest(unassigned_shards) as unassigned, latest(active_primary_shards) as primary by cluster_name
```
- **Implementation:** Poll `GET _cluster/health?level=shards` and `GET _cat/shards?v&h=index,shard,prirep,state,node` every 1–2 minutes via REST API scripted input. Parse status (green/yellow/red), unassigned_shards, active_primary_shards. Poll `_cluster/stats` for JVM heap usage. Alert on red status (critical) or yellow (warning). Alert when unassigned_shards >0. Correlate with disk space, JVM pressure, and node availability.
- **Visualization:** Status indicator (green/yellow/red), Single value (unassigned shards), Table (unassigned shard details), Line chart (cluster health and JVM heap over time).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-7.4.7 · Elasticsearch Index Size and Document Count Trending
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity
- **Value:** Growth forecasting for indices enables proactive storage provisioning and index lifecycle management (ILM) tuning.
- **App/TA:** Custom scripted input (ES REST API)
- **Data Sources:** `_cat/indices`, `_stats`
- **SPL:**
```spl
index=database sourcetype="elasticsearch:indices"
| eval size_gb=round(store.size_in_bytes/1073741824, 2)
| timechart span=1d sum(size_gb) as total_gb, sum(docs.count) as doc_count by index
| predict total_gb as predicted_gb future_timespan=30
```
- **Implementation:** Poll `GET _cat/indices?v&h=index,docs.count,store.size&bytes=b` or `GET _stats` every 6–24 hours. Parse index name, document count, store size. Track per-index and cluster-wide growth. Use `predict` for 30-day forecast. Alert when projected size exceeds available storage. Support ILM policy tuning based on growth rate.
- **Visualization:** Line chart (index size and doc count with prediction), Table (indices by size and growth rate), Bar chart (top growing indices).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-7.4.8 · ClickHouse Query Performance
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance
- **Value:** Merge operations, insert rate, and query duration indicate system health. Monitoring enables tuning and capacity planning for analytical workloads.
- **App/TA:** Custom scripted input (ClickHouse system tables)
- **Data Sources:** `system.query_log`, `system.metrics`, `system.merges`
- **SPL:**
```spl
index=database sourcetype="clickhouse:query_log"
| where query_duration_ms > 30000
| stats count, avg(query_duration_ms) as avg_duration_ms, sum(read_rows) as total_rows by query_kind, user
| sort -avg_duration_ms
```
- **Implementation:** Poll `system.query_log` (or enable query_log and ingest via DB Connect/scripted input) for completed queries. Extract query_duration_ms, query_kind, read_rows, memory_usage. Poll `system.metrics` for Merge, Insert, Query metrics. Poll `system.merges` for active merge count and progress. Alert on queries >30s, merge backlog >10, or insert rate drop. Track p95/p99 query duration by type.
- **Visualization:** Table (slow queries with duration and rows), Line chart (query duration p95 over time), Bar chart (merge count and insert rate), Single value (active merges).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-7.4.9 · Snowflake Warehouse Credit Usage
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance, Capacity
- **Value:** Credits consumed per warehouse and role drive chargeback and right-sizing. Spikes indicate runaway queries or undersized warehouses thrashing.
- **App/TA:** Snowflake SQL via DB Connect, `ACCOUNT_USAGE` export
- **Data Sources:** `WAREHOUSE_METERING_HISTORY`, `QUERY_HISTORY` (credits)
- **SPL:**
```spl
index=datawarehouse sourcetype="snowflake:warehouse_metering"
| stats sum(credits_used) as credits by warehouse_name, _time span=1d
| eventstats avg(credits) as avg_c, stdev(credits) as s by warehouse_name
| where credits > avg_c + 3*s
| table warehouse_name credits avg_c
```
- **Implementation:** Daily load from `ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY`. Alert on statistical spikes. Dashboard top warehouses by credits.
- **Visualization:** Line chart (credits per day by warehouse), Bar chart (top consumers), Single value (total credits MTD).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-7.4.10 · Databricks Cluster Utilization
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Cluster DBU hours, worker counts, and idle time reveal over-provisioned pools and jobs that keep clusters alive unnecessarily.
- **App/TA:** Databricks audit logs, cluster events API, `system.billing.usage`
- **Data Sources:** `clusters` API events, billing export
- **SPL:**
```spl
index=databricks sourcetype="databricks:cluster_event"
| where event_type IN ("RUNNING","TERMINATED")
| stats sum(uptime_seconds) as uptime, dc(cluster_id) as clusters by _time span=1d
| eval dbu_estimate=uptime/3600*0.1
```
- **Implementation:** Ingest cluster lifecycle and DBU billing lines. Alert on clusters RUNNING >8h with low task activity (correlate with job logs). Normalize fields from your workspace audit pipeline.
- **Visualization:** Line chart (DBU per day), Table (long-running clusters), Heatmap (cluster × hour utilization).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-7.4.11 · Redshift Query Queue Depth
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** WLM queue length and max execution time show concurrency saturation. Growing queue depth precedes disk-based spills and timeouts.
- **App/TA:** CloudWatch, `STL_WLM_QUERY` export
- **Data Sources:** `WLMQueueDepth`, `WLMQueriesCompletedPerSecond`
- **SPL:**
```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/Redshift" metric_name="WLMQueueDepth"
| timechart span=5m max(Maximum) as queue_depth by ClusterIdentifier, QueueName
| where queue_depth > 10
```
- **Implementation:** Map queue names to workload classes. Alert when queue_depth sustained above SLA. Tune WLM slots or concurrency scaling.
- **Visualization:** Line chart (queue depth), Table (cluster, queue, depth), Single value (max depth).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-7.4.12 · BigQuery Cost Anomalies
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance
- **Value:** Sudden jumps in bytes billed or slot usage often trace to one bad query or new scheduled job. Statistical alerting limits surprise invoices.
- **App/TA:** BigQuery `INFORMATION_SCHEMA.JOBS`, billing export to Splunk
- **Data Sources:** `total_bytes_billed`, `total_slot_ms`, `creation_time`
- **SPL:**
```spl
index=datawarehouse sourcetype="bigquery:jobs"
| bin _time span=1d
| stats sum(total_bytes_billed) as bytes by project_id, user_email, _time
| eventstats avg(bytes) as avg_b, stdev(bytes) as s by project_id
| where bytes > avg_b + 3*s
| eval gb=round(bytes/1073741824,2)
```
- **Implementation:** Ingest completed jobs daily. Alert on project-day cost outliers. Drill into `job_id` for top offenders. Integrate with GCP billing export for ground truth.
- **Visualization:** Line chart (daily bytes billed), Table (anomalous days/projects), Bar chart (top users by cost).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-7.4.13 · Snowflake Query Spillage (Bytes Spilled to Local/Remote Storage)
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Spillage indicates insufficient warehouse size or poorly written queries (exploding joins). Drives warehouse tier and query tuning decisions.
- **App/TA:** Snowflake `QUERY_HISTORY`, `QUERY_ACCELERATION_HISTORY`
- **Data Sources:** `BYTES_SPILLED_TO_LOCAL_STORAGE`, `BYTES_SPILLED_TO_REMOTE_STORAGE`
- **SPL:**
```spl
index=datawarehouse sourcetype="snowflake:query_history"
| eval spill_bytes=BYTES_SPILLED_TO_LOCAL_STORAGE+BYTES_SPILLED_TO_REMOTE_STORAGE
| where spill_bytes > 1073741824
| stats sum(spill_bytes) as total_spill, count as qcount by USER_NAME, QUERY_ID
| sort -total_spill
```
- **Implementation:** Poll `QUERY_HISTORY` for completed queries. Alert on spill_bytes >1GB. Join with warehouse size for context.
- **Visualization:** Table (queries with spill), Bar chart (spill by user), Line chart (daily spill volume).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-7.4.14 · Databricks Job Failure Rate
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Fault
- **Value:** Failed notebook/jar jobs block downstream analytics. Failure rate by job name prioritizes fixes for critical pipelines.
- **App/TA:** Databricks job run API, `jobs` audit
- **Data Sources:** Job run result (`result_state`, `run_id`)
- **SPL:**
```spl
index=databricks sourcetype="databricks:job_run"
| stats count(eval(result_state="FAILED")) as failed, count as total by job_name, _time span=1d
| eval fail_rate=round(failed/total*100,1)
| where fail_rate > 5 OR failed > 0 AND total < 5
| table job_name failed total fail_rate
```
- **Implementation:** Ingest each run completion. Alert on any failure for tier-1 jobs; use fail_rate for high-volume jobs. Include `run_page_url` in raw events for triage.
- **Visualization:** Line chart (failure rate by job), Table (failed runs), Single value (failed jobs 24h).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-7.4.15 · Azure Synapse Analytics SQL Pool Performance
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance, Capacity
- **Value:** Synapse dedicated SQL pools have DWU-based resource limits. Queries competing for resources cause queueing, and tempdb contention degrades batch processing. Monitoring ensures analytics workloads meet SLAs.
- **App/TA:** `Splunk_TA_microsoft-cloudservices` (Azure Monitor metrics/diagnostics)
- **Data Sources:** `sourcetype=azure:monitor:metric` (Microsoft.Synapse/workspaces/sqlPools), `sourcetype=azure:diagnostics` (SqlRequests)
- **SPL:**
```spl
index=cloud sourcetype="azure:monitor:metric" resource_type="microsoft.synapse/workspaces/sqlpools"
| where metric_name IN ("DWUUsedPercent","ActiveQueries","QueuedQueries","AdaptiveCacheHitPercent")
| timechart span=5m avg(average) as value by metric_name, resource_name
```
- **Implementation:** Collect Azure Monitor metrics for Synapse SQL pools. Alert when `DWUUsedPercent` exceeds 90% sustained (scale up DWU), when `QueuedQueries` exceeds 10 (resource contention), or when `AdaptiveCacheHitPercent` drops below 50% (cold cache after pause/resume). Enable diagnostics for `SqlRequests` to track query execution times and identify long-running queries consuming resources.
- **Visualization:** Line chart (DWU % and queued queries), Table (long-running queries), Gauge (cache hit ratio).
- **CIM Models:** Performance
- **CIM SPL:**
```spl
| tstats summariesonly=t avg(Performance.cpu_load_percent) as agg_value from datamodel=Performance.CPU by Performance.host span=5m | sort - agg_value
```

- **References:** [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110), [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)

---

### UC-7.4.16 · Azure Synapse Pipeline Execution Health
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Fault
- **Value:** Synapse pipelines orchestrate data movement and transformation. Failed pipeline runs cause stale analytics data, broken reports, and missed business deadlines.
- **App/TA:** `Splunk_TA_microsoft-cloudservices` (Azure Monitor diagnostics)
- **Data Sources:** `sourcetype=azure:diagnostics` (SynapsePipelineRuns, SynapseActivityRuns)
- **SPL:**
```spl
index=cloud sourcetype="azure:diagnostics" Category="SynapsePipelineRuns"
| where Status="Failed"
| stats count as failures, latest(Start) as last_failure, latest(Error) as last_error by PipelineName, resource_name
| sort -failures
```
- **Implementation:** Enable diagnostics on Synapse workspaces to route `SynapsePipelineRuns` and `SynapseActivityRuns` to Splunk via Event Hub. Alert on failed pipeline runs. Track activity-level errors for root cause analysis (data movement failures, notebook errors, SQL script timeouts). Monitor pipeline duration trending to detect degradation.
- **Visualization:** Table (failed pipelines with error detail), Bar chart (failures by pipeline), Line chart (duration trend).
- **CIM Models:** N/A

- **References:** [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)

---


### UC-7.1.16 · Open Cursor Leak Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity
- **Value:** Open cursors that are never closed accumulate in the database session context and eventually exhaust the cursor limit (Oracle ORA-01000, SQL Server max open cursors), causing application errors and forcing emergency restarts. Nagios detects this via threshold checks on V$OPEN_CURSOR; Splunk enables trending, per-session attribution, and correlation with application deployments.
- **App/TA:** `splunk-db-connect` or `Splunk_TA_oracle`
- **Data Sources:** Oracle `V$OPEN_CURSOR`, `V$SESSION`; SQL Server `sys.dm_exec_cursors`; PostgreSQL `pg_cursors`
- **SPL:**
```spl
| dbxquery connection="oracle_prod" query="SELECT s.username, s.program, COUNT(*) AS open_cursors FROM v\$open_cursor oc JOIN v\$session s ON oc.sid=s.sid GROUP BY s.username, s.program ORDER BY open_cursors DESC"
| where open_cursors > 200
| eval alert=if(open_cursors > 800, "CRITICAL", if(open_cursors > 400, "WARNING", "OK"))
| table username, program, open_cursors, alert
```
- **Implementation:** Use Splunk DB Connect to poll `V$OPEN_CURSOR` every 5 minutes. Join with `V$SESSION` to identify which application user or service is leaking cursors. Alert when any single session exceeds 400 open cursors (WARNING) or 800 (CRITICAL). Correlate spikes with deployment events from CI/CD logs to pinpoint root cause. For SQL Server, poll `sys.dm_exec_cursors` grouped by `login_name`. Set `OPEN_CURSORS` init parameter baseline in a lookup for dynamic threshold comparison.
- **Visualization:** Line chart (total open cursors over time by application), Table (top sessions by cursor count), Single value (current max), Bar chart (cursors by application/service).
- **CIM Models:** N/A

- **References:** [Splunk DB Connect](https://splunkbase.splunk.com/app/2686)

---

### UC-7.1.17 · Database Connection Pool Exhaustion
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** When the application connection pool or database max_connections is exhausted, new requests fail with connection errors. Detecting high connection count and pool saturation prevents outages.
- **App/TA:** `splunk_app_db_connect`, database performance views
- **Data Sources:** Oracle `V$SESSION`/`V$PROCESS`, PostgreSQL `pg_stat_activity`, MySQL `SHOW PROCESSLIST`, SQL Server `sys.dm_exec_connections`
- **SPL:**
```spl
| dbxquery connection="oracle_prod" query="SELECT COUNT(*) AS conn_count FROM v\$session WHERE type='USER'"
| eval usage_pct=round(conn_count/400*100, 1)
| where usage_pct > 85
| table conn_count usage_pct
```
- **Implementation:** Use DB Connect to poll session/connection count every 1–5 minutes. Compare to max_connections (or pool size). Alert when utilization exceeds 85%. Correlate with application logs for connection leak or traffic spike.
- **Visualization:** Gauge (connection count vs max), Line chart (connections over time), Table (by program/user).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-7.1.18 · Long-Running Query and Blocking Session Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Queries that run for hours or sessions that block others cause timeouts and user impact. Identifying blocking chains and long-running queries supports tuning and kill decisions.
- **App/TA:** `splunk_app_db_connect`, database wait/block views
- **Data Sources:** Oracle `V$SESSION`/`V$SQL`, PostgreSQL `pg_stat_activity`, SQL Server `sys.dm_exec_requests`/`sys.dm_os_waiting_tasks`
- **SPL:**
```spl
| dbxquery connection="oracle_prod" query="SELECT s.sid, s.serial#, s.username, s.seconds_in_wait, s.blocking_session, sq.sql_text FROM v\$session s JOIN v\$sql sq ON s.sql_id=sq.sql_id WHERE s.seconds_in_wait > 300 OR s.blocking_session IS NOT NULL"
| table sid username seconds_in_wait blocking_session sql_text
```
- **Implementation:** Poll active sessions and wait/block info. Ingest sessions with elapsed time >5 minutes or with blocking_session set. Alert on blocking chains. Dashboard top long-running and blocked sessions with SQL text.
- **Visualization:** Table (session, user, wait time, blocker), Blocking chain diagram, Line chart (long-running count).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-7.1.19 · Table and Index Bloat and Maintenance Window
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance, Capacity
- **Value:** Table and index bloat (PostgreSQL) or fragmentation (SQL Server) degrades query performance and wastes space. Tracking bloat and last vacuum/rebuild supports maintenance scheduling.
- **App/TA:** `splunk_app_db_connect`, maintenance job logs
- **Data Sources:** PostgreSQL `pg_stat_user_tables`/bloat estimates, SQL Server `sys.dm_db_index_physical_stats`, Oracle segment size
- **SPL:**
```spl
| dbxquery connection="pg_prod" query="SELECT schemaname, relname, n_dead_tup, n_live_tup, last_vacuum, last_autovacuum FROM pg_stat_user_tables WHERE n_dead_tup > 10000"
| eval dead_ratio=round(n_dead_tup/n_live_tup*100, 2)
| where dead_ratio > 5
| table schemaname relname n_dead_tup last_autovacuum dead_ratio
```
- **Implementation:** Poll table/index stats and last maintenance timestamps. Compute dead tuple ratio or fragmentation %. Alert when bloat exceeds threshold or last vacuum/rebuild is older than 7 days for critical tables.
- **Visualization:** Table (table, bloat %, last vacuum), Bar chart (bloat by table), Single value (tables overdue for vacuum).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-7.1.20 · Database Backup and Archive Log Retention Verification
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Failed or missing backups and unarchived redo logs risk data loss and prevent point-in-time recovery. Verifying backup success and archive log retention ensures RPO is met.
- **App/TA:** `splunk_app_db_connect`, backup job logs
- **Data Sources:** Oracle RMAN output, SQL Server msdb backup history, PostgreSQL pg_backup (or vendor logs)
- **SPL:**
```spl
| dbxquery connection="oracle_prod" query="SELECT status, start_time, end_time, output_bytes FROM v\$rman_backup_job_details WHERE start_time > SYSDATE-1 ORDER BY start_time DESC"
| search status!="COMPLETED"
| table status start_time end_time output_bytes
```
- **Implementation:** Ingest backup job status (RMAN, SQL Server backup history, or backup vendor logs). Alert on any failed or incomplete backup. Track archive log destination space and retention; alert when space is low or retention is below policy.
- **Visualization:** Table (last backup, status, duration), Gauge (backup success %), Timeline of backup jobs.
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-7.1.21 · Database User and Privilege Change Audit
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security, Compliance
- **Value:** New users, role grants, or privilege changes can indicate compromise or policy violation. Auditing supports compliance (SOX, PCI) and security investigations.
- **App/TA:** Database audit logs, `splunk_app_db_connect`
- **Data Sources:** Oracle audit trail, PostgreSQL `pg_audit` or log_statement, SQL Server audit, MySQL general log
- **SPL:**
```spl
index=db_audit sourcetype=oracle_audit (action="CREATE USER" OR action="GRANT" OR action="ALTER USER")
| bin _time span=1h
| stats count by db_user, action, object_name, _time
| where count > 0
| table _time db_user action object_name
```
- **Implementation:** Enable database audit for user and privilege changes. Forward audit logs to Splunk. Alert on any CREATE USER, GRANT, or ALTER USER. Correlate with change management.
- **Visualization:** Events timeline, Table (user, action, object), Bar chart (changes by user).
- **CIM Models:** Change
- **CIM SPL:**
```spl
| tstats summariesonly=t count from datamodel=Change.All_Changes by All_Changes.action, All_Changes.object span=1h | sort - count
```

- **References:** [CIM: Change](https://docs.splunk.com/Documentation/CIM/latest/User/Change)

---

### UC-7.1.22 · PostgreSQL WAL Growth
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Fault, Capacity
- **Value:** WAL accumulation indicating replication issues or archival failures. Uncontrolled WAL growth exhausts disk space and can halt the database.
- **App/TA:** Splunk DB Connect or custom scripted input
- **Data Sources:** PostgreSQL `pg_stat_replication`, `pg_wal_lsn_diff()`, `pg_ls_waldir()` or filesystem WAL directory size
- **SPL:**
```spl
index=database sourcetype="dbconnect:postgresql_wal"
| eval wal_size_gb=round(wal_size_bytes/1073741824, 2)
| timechart span=1h latest(wal_size_gb) as wal_size_gb by host
| where wal_size_gb > 10
```
- **Implementation:** Use DB Connect or a scripted input to poll WAL metrics every 15–30 minutes. Query `pg_current_wal_lsn()` and compare with `pg_walfile_name()` to derive WAL size; alternatively, measure WAL directory on disk. Track replication slot lag via `pg_stat_replication` (replication_lag). Alert when WAL size exceeds threshold (e.g., >10 GB) or when replication lag indicates archival/streaming is falling behind. Correlate with `archive_command` failures and disk space.
- **Visualization:** Line chart (WAL size over time), Single value (current WAL size GB), Table (host, WAL size, replication lag).
- **CIM Models:** Databases
- **CIM SPL:**
```spl
| tstats summariesonly=t count from datamodel=Databases.Query by Query.dest span=1h | sort - count
```
- **References:** [Splunk DB Connect](https://splunkbase.splunk.com/app/2686), [CIM: Databases](https://docs.splunk.com/Documentation/CIM/latest/User/Databases)

---

### UC-7.1.23 · PostgreSQL Vacuum Activity
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance
- **Value:** Autovacuum running, dead tuples, and table bloat affect query performance. Monitoring ensures vacuum keeps pace with write workload and prevents bloat.
- **App/TA:** Splunk DB Connect or custom scripted input
- **Data Sources:** `pg_stat_user_tables` (n_dead_tup, n_live_tup, last_autovacuum, last_vacuum)
- **SPL:**
```spl
index=database sourcetype="dbconnect:pg_stat_user_tables"
| eval dead_ratio=round(n_dead_tup/nullif(n_live_tup,0)*100, 2)
| where dead_ratio > 5 OR n_dead_tup > 10000
| eval hours_since_vacuum=round((now()-strptime(last_autovacuum,"%Y-%m-%d %H:%M:%S"))/3600, 1)
| table schemaname, relname, n_dead_tup, n_live_tup, dead_ratio, last_autovacuum, hours_since_vacuum
| sort -n_dead_tup
```
- **Implementation:** Poll `pg_stat_user_tables` via DB Connect every hour. Extract `n_dead_tup`, `n_live_tup`, `last_autovacuum`. Compute dead tuple ratio and time since last vacuum. Alert when dead_ratio >5% or n_dead_tup >10000 for critical tables. Alert when last_autovacuum is >24 hours for high-churn tables. Track autovacuum runs from `pg_stat_progress_vacuum` if available.
- **Visualization:** Table (tables with bloat risk), Bar chart (dead tuples by table), Line chart (dead tuple ratio trend), Single value (tables overdue for vacuum).
- **CIM Models:** Databases
- **CIM SPL:**
```spl
| tstats summariesonly=t count from datamodel=Databases.Instance_Stats by Instance_Stats.host, Instance_Stats.action | sort - count
```
- **References:** [Splunk DB Connect](https://splunkbase.splunk.com/app/2686), [CIM: Databases](https://docs.splunk.com/Documentation/CIM/latest/User/Databases)

---

### UC-7.1.24 · PostgreSQL Connection Pool Monitoring (PgBouncer)
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance, Availability
- **Value:** Pool utilization and wait queue length indicate connection pressure. High utilization or growing wait queue causes application timeouts.
- **App/TA:** Custom scripted input (PgBouncer SHOW POOLS/STATS)
- **Data Sources:** PgBouncer admin console output (`SHOW POOLS`, `SHOW STATS`)
- **SPL:**
```spl
index=database sourcetype="pgbouncer:pools"
| eval pool_util_pct=round(cl_active+cl_wait)/nullif(max_client_conn,0)*100, 1
| eval wait_queue=cl_wait
| where pool_util_pct > 80 OR wait_queue > 5
| timechart span=5m max(pool_util_pct) as util_pct, max(wait_queue) as wait_queue by database, pool_mode
```
- **Implementation:** Create a scripted input that connects to PgBouncer admin console (default port 6432) and runs `SHOW POOLS` and `SHOW STATS` every 5 minutes. Parse output into structured events. Extract `cl_active`, `cl_wait`, `max_client_conn` per database/pool. Alert when pool utilization >80% or `cl_wait` >5. Track `sv_idle`, `sv_used` for server connection usage.
- **Visualization:** Gauge (pool utilization %), Line chart (active vs wait connections), Table (pools with high utilization or wait queue).
- **CIM Models:** Databases
- **CIM SPL:**
```spl
| tstats summariesonly=t count from datamodel=Databases.Instance_Stats by Instance_Stats.host, Instance_Stats.action span=5m | sort - count
```
- **References:** [CIM: Databases](https://docs.splunk.com/Documentation/CIM/latest/User/Databases)

---

### UC-7.1.25 · MySQL / MariaDB InnoDB Buffer Pool Hit Ratio
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Buffer pool effectiveness; low hit ratio means excessive disk I/O and degraded query performance.
- **App/TA:** Splunk DB Connect or custom scripted input
- **Data Sources:** `SHOW GLOBAL STATUS` (Innodb_buffer_pool_read_requests, Innodb_buffer_pool_reads)
- **SPL:**
```spl
index=database sourcetype="dbconnect:mysql_status"
| eval hit_ratio=round(100*(1-Innodb_buffer_pool_reads/nullif(Innodb_buffer_pool_read_requests,0)), 2)
| where hit_ratio < 99
| timechart span=15m avg(hit_ratio) as buffer_pool_hit_ratio by host
```
- **Implementation:** Poll `SHOW GLOBAL STATUS` via DB Connect every 15 minutes. Extract `Innodb_buffer_pool_read_requests` and `Innodb_buffer_pool_reads`. Compute hit ratio = (1 - reads/requests) * 100. Alert when hit ratio drops below 99% for sustained periods. Correlate with memory allocation and workload changes.
- **Visualization:** Gauge (buffer pool hit ratio %), Line chart (hit ratio over time), Single value (current hit ratio).
- **CIM Models:** Databases
- **CIM SPL:**
```spl
| tstats summariesonly=t count from datamodel=Databases.Query by Query.dest span=15m | sort - count
```
- **References:** [Splunk DB Connect](https://splunkbase.splunk.com/app/2686), [CIM: Databases](https://docs.splunk.com/Documentation/CIM/latest/User/Databases)

---

### UC-7.1.26 · MySQL Binary Log Space Usage
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity
- **Value:** Binlog accumulation on disk can exhaust disk space and impact replication. Monitoring enables proactive purging or archival.
- **App/TA:** Splunk DB Connect or custom scripted input
- **Data Sources:** `SHOW BINARY LOGS`, filesystem binlog directory size
- **SPL:**
```spl
index=database sourcetype="dbconnect:mysql_binlogs"
| eval size_gb=round(File_size/1073741824, 2)
| stats sum(File_size) as total_bytes by host
| eval total_gb=round(total_bytes/1073741824, 2)
| where total_gb > 50
| table host, total_gb, binlog_count
```
- **Implementation:** Poll `SHOW BINARY LOGS` via DB Connect daily or every 6 hours. Sum `File_size` across all binlogs. Optionally measure binlog directory on disk. Alert when total binlog size exceeds threshold (e.g., >50 GB). Track binlog purge lag (oldest binlog age). Correlate with replication lag and `expire_logs_days`/`binlog_expire_logs_seconds` settings.
- **Visualization:** Line chart (binlog total size over time), Single value (current binlog size GB), Table (host, size, count).
- **CIM Models:** Databases
- **CIM SPL:**
```spl
| tstats summariesonly=t count from datamodel=Databases.Query by Query.dest | sort - count
```
- **References:** [Splunk DB Connect](https://splunkbase.splunk.com/app/2686), [CIM: Databases](https://docs.splunk.com/Documentation/CIM/latest/User/Databases)

---

### UC-7.1.27 · Oracle Tablespace Utilization
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity
- **Value:** Approaching max size per tablespace causes ORA-1653 (out of space) errors and application failures. Proactive monitoring prevents outages.
- **App/TA:** Splunk DB Connect
- **Data Sources:** `DBA_TABLESPACE_USAGE_METRICS`, `DBA_DATA_FILES`
- **SPL:**
```spl
index=database sourcetype="dbconnect:oracle_tablespace"
| eval used_pct=round(USED_PERCENT, 1)
| where used_pct > 80
| timechart span=1d latest(used_pct) as used_pct by TABLESPACE_NAME
| where used_pct > 85
```
- **Implementation:** Poll `DBA_TABLESPACE_USAGE_METRICS` (or `DBA_FREE_SPACE` + `DBA_DATA_FILES`) via DB Connect every 4–6 hours. Extract used percent per tablespace. Alert at 80% (warning) and 90% (critical). Track growth rate for capacity planning. Include temp and undo tablespaces.
- **Visualization:** Gauge (tablespace used %), Table (tablespaces over threshold), Line chart (utilization trend by tablespace).
- **CIM Models:** Databases
- **CIM SPL:**
```spl
| tstats summariesonly=t count from datamodel=Databases.Tablespace by Tablespace.host, Tablespace.action span=1d | sort - count
```
- **References:** [Splunk DB Connect](https://splunkbase.splunk.com/app/2686), [CIM: Databases](https://docs.splunk.com/Documentation/CIM/latest/User/Databases)

---

### UC-7.1.28 · PostgreSQL Replication Lag (Streaming)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** `pg_stat_replication` write/flush/replay lag bytes and seconds catch standby drift before read-your-writes violations. Complements generic replication UC with PostgreSQL-native metrics.
- **App/TA:** DB Connect, `pg_stat_replication` scripted export
- **Data Sources:** `write_lag`, `flush_lag`, `replay_lag`, `sent_lsn`
- **SPL:**
```spl
index=database sourcetype="dbconnect:pg_replication"
| eval replay_lag_sec=extract(replay_lag, "(\d+)").0
| where replay_lag_sec > 60 OR pg_wal_lsn_diff(sent_lsn, replay_lsn) > 104857600
| table application_name client_addr replay_lag_sec state
```
- **Implementation:** Poll replication view every 1m. Map `application_name` to replica. Alert on replay lag > RPO seconds or LSN gap >100MB. Correlate with `archive_command` and network.
- **Visualization:** Line chart (replay lag per standby), Table (standby, lag sec), Single value (max lag).
- **CIM Models:** Databases
- **CIM SPL:**
```spl
| tstats summariesonly=t count from datamodel=Databases.Instance_Stats by Instance_Stats.host, Instance_Stats.action | sort - count
```
- **References:** [CIM: Databases](https://docs.splunk.com/Documentation/CIM/latest/User/Databases)

---

### UC-7.1.29 · MySQL InnoDB Buffer Pool Hit Ratio Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Fleet-wide buffer pool hit ratio SLO for MySQL/MariaDB with per-instance drilldown. Aligns capacity reviews with read IO pressure.
- **App/TA:** DB Connect, `SHOW GLOBAL STATUS`
- **Data Sources:** `Innodb_buffer_pool_read_requests`, `Innodb_buffer_pool_reads`
- **SPL:**
```spl
index=database sourcetype="dbconnect:mysql_status"
| eval hit_ratio=round(100*(1-Innodb_buffer_pool_reads/nullif(Innodb_buffer_pool_read_requests,0)),2)
| stats avg(hit_ratio) as fleet_avg, min(hit_ratio) as worst by _time span=1h
| where fleet_avg < 99 OR worst < 95
```
- **Implementation:** Aggregate hourly for executive view; retain per-host series for alerts. Correlate drops with large table scans or buffer pool size changes.
- **Visualization:** Line chart (fleet avg vs worst instance), Gauge (current hit ratio), Table (instances below 99%).
- **CIM Models:** Databases
- **CIM SPL:**
```spl
| tstats summariesonly=t count from datamodel=Databases.Query by Query.host, Query.action | sort - count
```
- **References:** [CIM: Databases](https://docs.splunk.com/Documentation/CIM/latest/User/Databases)

---

### UC-7.1.30 · Oracle Tablespace Growth Trending
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity
- **Value:** Week-over-week growth rate per tablespace drives forecast and ASM/space procurement. Extends point-in-time utilization with trend.
- **App/TA:** DB Connect
- **Data Sources:** `DBA_TABLESPACE_USAGE_METRICS` (used_space, tablespace_size)
- **SPL:**
```spl
index=database sourcetype="dbconnect:oracle_tablespace"
| timechart span=1d latest(USED_SPACE) as used_bytes by TABLESPACE_NAME
| streamstats window=7 range(used_bytes) as growth_7d by TABLESPACE_NAME
| eval growth_gb=round(growth_7d/1073741824,2)
| where growth_gb > 10
```
- **Implementation:** Daily snapshot. Alert on >10GB/week growth on critical tablespaces. Use `predict` on used_bytes for runway to maxsize.
- **Visualization:** Line chart (used GB trend), Table (tablespace, growth GB/week), Single value (fastest growing).
- **CIM Models:** Databases
- **CIM SPL:**
```spl
| tstats summariesonly=t count from datamodel=Databases.Tablespace by Tablespace.host, Tablespace.action span=1d | sort - count
```
- **References:** [CIM: Databases](https://docs.splunk.com/Documentation/CIM/latest/User/Databases)

---

### UC-7.1.31 · SQL Server Always On AG Health and Replica Sync
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Combined view of `synchronization_health`, redo queue, and log send queue sizes for AG replicas. Operationalizes UC-7.1.12 with queue depth.
- **App/TA:** DB Connect, `Splunk_TA_microsoft-sqlserver`
- **Data Sources:** `sys.dm_hadr_database_replica_states`, `log_send_queue_size`, `redo_queue_size`
- **SPL:**
```spl
index=database sourcetype="dbconnect:ag_replica_state"
| where synchronization_health_desc!="HEALTHY" OR log_send_queue_size > 104857600 OR redo_queue_size > 104857600
| table ag_name replica_server_name synchronization_health_desc log_send_queue_size redo_queue_size
```
- **Implementation:** Poll DMVs every 5m. Alert on unhealthy sync or queue >100MB (tune threshold). Track automatic failover readiness.
- **Visualization:** Status grid (replica × health), Line chart (queue sizes), Table (unhealthy AG databases).
- **CIM Models:** Databases
- **CIM SPL:**
```spl
| tstats summariesonly=t count from datamodel=Databases.Instance_Stats by Instance_Stats.host, Instance_Stats.action | sort - count
```
- **References:** [CIM: Databases](https://docs.splunk.com/Documentation/CIM/latest/User/Databases)

---

### UC-7.1.32 · Database Backup Chain Validation
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Compliance
- **Value:** Verifies full→diff→log chain continuity (SQL Server LSN chain, Oracle archivelog sequence) to detect missing backups before restore drills fail.
- **App/TA:** DB Connect, backup vendor logs
- **Data Sources:** `msdb.dbo.backupset` (first_lsn, last_lsn, type), RMAN backup pieces
- **SPL:**
```spl
index=database sourcetype="dbconnect:backup_chain"
| sort database_name, backup_finish_date
| streamstats window=2 previous(last_lsn) as prev_last by database_name
| where isnotnull(prev_last) AND first_lsn!=prev_last AND type!=1
| table database_name backup_finish_date type first_lsn prev_last
```
- **Implementation:** Custom SQL to flag LSN gaps. For Oracle, check archivelog sequence continuity. Alert on any break in chain for production databases.
- **Visualization:** Table (broken chains), Timeline (backup types), Single value (databases with gaps).
- **CIM Models:** Databases
- **CIM SPL:**
```spl
| tstats summariesonly=t count from datamodel=Databases.Instance_Stats by Instance_Stats.host, Instance_Stats.action | sort - count
```
- **References:** [CIM: Databases](https://docs.splunk.com/Documentation/CIM/latest/User/Databases)

---

### UC-7.1.33 · Long-Running Query Detection (Active Sessions)
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Surfaces currently running queries exceeding elapsed threshold with SQL hash and wait type—faster triage than transaction-only UC-7.1.8.
- **App/TA:** DB Connect
- **Data Sources:** `sys.dm_exec_requests`, `pg_stat_activity`, `V$SESSION` + `V$SQL`
- **SPL:**
```spl
index=database sourcetype="dbconnect:active_requests"
| where elapsed_sec > 300 AND status="running"
| stats max(elapsed_sec) as max_sec by session_id, database_name, sql_hash
| table session_id database_name sql_hash max_sec wait_type
```
- **Implementation:** Poll every 2m. Exclude known batch accounts via lookup. Alert when max_sec >900 for OLTP. Include optional `sql_text` sampling for compliance.
- **Visualization:** Table (long-running sessions), Line chart (count of long queries), Single value (longest elapsed sec).
- **CIM Models:** Databases
- **CIM SPL:**
```spl
| tstats summariesonly=t count from datamodel=Databases.Query by Query.host, Query.action | sort - count
```
- **References:** [CIM: Databases](https://docs.splunk.com/Documentation/CIM/latest/User/Databases)

---

### UC-7.1.34 · Deadlock Frequency by Database
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Fault
- **Value:** Counts deadlocks per hour/database to detect code regressions after releases. Complements UC-7.1.2 event search with KPIs.
- **App/TA:** Error log ingestion, extended events
- **Data Sources:** SQL Server errorlog deadlock graph frequency, PostgreSQL `log_lock_waits`, Oracle ORA-00060
- **SPL:**
```spl
index=database sourcetype="mssql:errorlog"
| search deadlock OR "Deadlock"
| bucket _time span=1h
| stats count as deadlocks by database_name, _time
| where deadlocks > 5
```
- **Implementation:** Parse database name from deadlock XML if available. Alert when hourly deadlocks exceed baseline. Tie to release markers.
- **Visualization:** Line chart (deadlocks over time), Bar chart (by database), Single value (deadlocks today).
- **CIM Models:** Databases
- **CIM SPL:**
```spl
| tstats summariesonly=t count from datamodel=Databases.Query by Query.host, Query.action | sort - count
```
- **References:** [CIM: Databases](https://docs.splunk.com/Documentation/CIM/latest/User/Databases)

---

### UC-7.1.35 · Connection Pool Exhaustion (Application vs Database Limit)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Joins app pool `activeThreads`/`waiting` with DB `session_count` to distinguish app-side pool starvation from DB `max_connections` hits.
- **App/TA:** OpenTelemetry, DB Connect
- **Data Sources:** HikariCP metrics, `pg_stat_activity` count, `sys.dm_exec_connections`
- **SPL:**
```spl
index=application sourcetype="hikaricp:metrics"
| eval pct=round(active_connections/max_connections*100,1)
| where pct > 90 OR threads_awaiting_connection > 5
| table host pool_name pct threads_awaiting_connection active_connections max_connections
```
- **Implementation:** Ingest both sides; use `transaction` or `join` on host+service. Alert when either side >90%. Dashboard side-by-side.
- **Visualization:** Gauge (app pool vs DB sessions), Line chart (pct over time), Table (hosts in danger).
- **CIM Models:** Databases
- **CIM SPL:**
```spl
| tstats summariesonly=t count from datamodel=Databases.Session_Info by Session_Info.host, Session_Info.action | sort - count
```
- **References:** [CIM: Databases](https://docs.splunk.com/Documentation/CIM/latest/User/Databases)

---

### UC-7.1.36 · Index Fragmentation Maintenance Priority
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Ranks indexes by fragmentation × page_count to schedule rebuilds during maintenance windows. Extends UC-7.1.9 with prioritization score.
- **App/TA:** DB Connect
- **Data Sources:** `sys.dm_db_index_physical_stats` (avg_fragmentation_in_percent, page_count)
- **SPL:**
```spl
index=database sourcetype="dbconnect:index_stats"
| eval priority_score=avg_fragmentation_pct * page_count / 1000000
| where avg_fragmentation_pct > 30 AND page_count > 1000
| sort -priority_score
| head 50
```
- **Implementation:** Weekly job. Export top 50 for DBA runbook. Exclude tiny indexes via page_count floor.
- **Visualization:** Table (index, frag %, pages, score), Bar chart (top priority_score).
- **CIM Models:** Databases
- **CIM SPL:**
```spl
| tstats summariesonly=t count from datamodel=Databases.Instance_Stats by Instance_Stats.host, Instance_Stats.action | sort - count
```
- **References:** [CIM: Databases](https://docs.splunk.com/Documentation/CIM/latest/User/Databases)

---

### UC-7.1.37 · Temp Tablespace Usage (Oracle TEMP)
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance, Capacity
- **Value:** High `TEMP` usage for sorts and hashes causes ORA-1652. Tracks session temp consumption vs temp tablespace limits.
- **App/TA:** DB Connect
- **Data Sources:** `V$TEMPSEG_USAGE`, `DBA_TEMP_FREE_SPACE`
- **SPL:**
```spl
index=database sourcetype="dbconnect:oracle_temp"
| stats sum(blocks_used) as used_blocks by tablespace_name, session_addr
| eventstats sum(used_blocks) as total_used by tablespace_name
| lookup oracle_temp_space tablespace_name OUTPUT max_blocks
| where total_used > max_blocks*0.85
| table tablespace_name total_used max_blocks
```
- **Implementation:** Poll `V$TEMPSEG_USAGE` every 5m. Alert at 85% of temp max. Identify top SQL by `sql_id` from same view.
- **Visualization:** Line chart (temp usage %), Table (sessions using temp), Single value (peak temp GB).
- **CIM Models:** Databases
- **CIM SPL:**
```spl
| tstats summariesonly=t count from datamodel=Databases.Lock_Stats by Lock_Stats.host, Lock_Stats.action | sort - count
```
- **References:** [CIM: Databases](https://docs.splunk.com/Documentation/CIM/latest/User/Databases)

---

### UC-7.1.38 · Query Plan Regression (Runtime vs Baseline)
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance
- **Value:** Compares current average CPU/duration from Query Store or AWR to baselines by `query_id`/`plan_hash`. Tightens UC-7.1.14 with explicit baseline lookup.
- **App/TA:** DB Connect, Query Store export
- **Data Sources:** `sys.query_store_runtime_stats`, `dba_hist_sqlstat`
- **SPL:**
```spl
index=database sourcetype="dbconnect:query_store_runtime"
| stats avg(avg_cpu_time) as cur_cpu by query_id, plan_id
| lookup query_baselines query_id OUTPUT baseline_cpu_ms
| eval regression_pct=round((cur_cpu-baseline_cpu_ms)/baseline_cpu_ms*100,1)
| where regression_pct > 40
```
- **Implementation:** Refresh baseline lookup weekly from stable period. Alert on regression >40% with new `plan_id`. Consider force plan workflow.
- **Visualization:** Table (regressed queries), Line chart (baseline vs current), Bar chart (regression %).
- **CIM Models:** Databases
- **CIM SPL:**
```spl
| tstats summariesonly=t count from datamodel=Databases.Query by Query.host, Query.action | sort - count
```
- **References:** [CIM: Databases](https://docs.splunk.com/Documentation/CIM/latest/User/Databases)

---

### UC-7.1.39 · Database Patch Compliance
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Value:** Compares instance `@@VERSION` / `banner` / Oracle `DBA_REGISTRY_HISTORY` to approved patch levels per environment. Supports security patching SLAs.
- **App/TA:** DB Connect, inventory scripted input
- **Data Sources:** SQL Server `@@VERSION`, Oracle `opatch`, PostgreSQL `pg_version`
- **SPL:**
```spl
index=database sourcetype="dbconnect:instance_version"
| lookup approved_db_patch matrix_key OUTPUT approved_build
| where build != approved_build
| table host, engine, build, approved_build, last_patch_date
```
- **Implementation:** Maintain `approved_db_patch` lookup (engine, major, approved CU/RU). Daily compare. Alert on non-compliant production instances.
- **Visualization:** Table (non-compliant hosts), Pie chart (compliant %), Single value (drift count).
- **CIM Models:** Databases
- **CIM SPL:**
```spl
| tstats summariesonly=t count from datamodel=Databases.Database_Instance by Database_Instance.host, Database_Instance.action | sort - count
```

- **References:** [CIM: Databases](https://docs.splunk.com/Documentation/CIM/latest/User/Databases)

---

### UC-7.1.40 · Database Audit Log Tampering Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Security
- **Value:** Detects unexpected audit trail disable, audit file deletion, or Unified Audit policy changes that may indicate cover-up activity.
- **App/TA:** OS audit, database audit, syslog
- **Data Sources:** Oracle `V$OPTION` where parameter='Unified Auditing', `ALTER SYSTEM AUDIT`, `DROP AUDIT POLICY`, SQL Server audit shutdown events
- **SPL:**
```spl
index=db_audit sourcetype=oracle_audit OR sourcetype=mssql:audit
| search action IN ("AUDIT DISABLED","AUDIT_POLICY_DROP","AUDIT_TRAIL_OFF") OR statement="*AUDIT*FALSE*"
| table _time, db_user, action, object_name, statement
| sort -_time
```
- **Implementation:** Forward database and OS audit to tamper-evident storage. Alert on any audit disable or policy drop outside CAB. Correlate with DBA group membership.
- **Visualization:** Timeline (audit config changes), Table (privileged actions), Single value (critical audit events 24h).
- **CIM Models:** Databases
- **CIM SPL:**
```spl
| tstats summariesonly=t count from datamodel=Databases.Query by Query.host, Query.action | sort - count
```
- **References:** [CIM: Databases](https://docs.splunk.com/Documentation/CIM/latest/User/Databases)

---

### 7.5 Search & Analytics Platforms

**Primary App/TA:** Custom scripted input or HTTP Event Collector against Elasticsearch/OpenSearch REST APIs (`_cluster/health`, `_cat`, `_nodes/stats`), Splunk Add-on for Elasticsearch where applicable; Apache Solr `metrics` API and Solr logs; Filebeat/Metricbeat modules for Elastic Stack.

---

### UC-7.5.1 · Elasticsearch Cluster Health (Red / Yellow)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Yellow or red cluster status means primary/replica shards are not fully allocated; search and indexing can fail or degrade. Catching status changes early limits user impact.
- **App/TA:** Custom REST scripted input (Elasticsearch `_cluster/health`)
- **Data Sources:** `sourcetype=elasticsearch:cluster_health`
- **SPL:**
```spl
index=database sourcetype="elasticsearch:cluster_health"
| where status IN ("yellow","red")
| eval severity=if(status="red",3,2)
| timechart span=5m max(severity) as severity by cluster_name
```
- **Implementation:** Poll `GET _cluster/health` every 1–2 minutes and index `status`, `active_primary_shards`, `unassigned_shards`, `number_of_nodes`. Alert immediately on `red` and on sustained `yellow`. Correlate with node loss and disk events.
- **Visualization:** Single value or status indicator (cluster status), Line chart (status over time), Table (clusters not green).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-7.5.2 · Elasticsearch Shard Allocation Failures
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** Unassigned or stuck relocating shards leave data unavailable or at risk; allocation explain output points to disk, routing, or settings issues before outages spread.
- **App/TA:** Custom REST scripted input (`_cluster/allocation/explain`, `_cat/shards`)
- **Data Sources:** `sourcetype=elasticsearch:shard_allocation`
- **SPL:**
```spl
index=database sourcetype="elasticsearch:shard_allocation"
| where state="UNASSIGNED" OR allocation_decision="NO"
| stats latest(deciders) as deciders, count by index, shard, prirep
| sort -count
```
- **Implementation:** Ingest `_cat/shards` with `state` filter and, for unassigned primaries, poll `POST _cluster/allocation/explain` on a schedule. Parse `allocate_explanation` and decider names. Alert when any primary shard is unassigned >5 minutes or replica unassigned count exceeds policy.
- **Visualization:** Table (index, shard, state, reason), Single value (unassigned shard count), Timeline of allocation events.
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-7.5.3 · OpenSearch Index Performance
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Slow merges, refresh intervals, and segment counts drive query latency and heap use; tracking per-index stats keeps search SLAs achievable.
- **App/TA:** Custom scripted input (OpenSearch `_stats`, `_cat/indices`)
- **Data Sources:** `sourcetype=opensearch:index_stats`
- **SPL:**
```spl
index=database sourcetype="opensearch:index_stats"
| eval merge_ms=primaries.merges.total_time_in_millis
| eval search_qps=primaries.search.query_total / nullif(uptime_sec,0)
| where merge_ms > 600000 OR primaries.refresh.total_time_in_millis > 300000
| table index, merge_ms, primaries.refresh.total_time_in_millis, store.size_in_bytes
```
- **Implementation:** Poll `GET /<index>/_stats` or per-index `_stats` every 15 minutes. Extract merges, refresh, indexing, and store size. Compare against baselines; alert when merge or refresh time spikes without matching traffic increase. Review ILM/ISM policies for hot indices.
- **Visualization:** Line chart (merge and refresh time by index), Table (top indices by merge cost), Bar chart (segment count if extracted).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-7.5.4 · OpenSearch Search Latency
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** P95/P99 query latency directly affects application UX; separating queue time from query time narrows tuning to thread pools vs. mappings and shards.
- **App/TA:** Custom scripted input (`_nodes/stats` search, slow log), OpenSearch slow search log
- **Data Sources:** `sourcetype=opensearch:search_latency`, `sourcetype=opensearch:slowlog`
- **SPL:**
```spl
index=database sourcetype="opensearch:search_latency" OR sourcetype="opensearch:slowlog"
| eval took_ms=coalesce(took_ms, took)
| where took_ms > 500
| timechart span=5m perc95(took_ms) as p95_ms, perc99(took_ms) as p99_ms by cluster_name
```
- **Implementation:** Ingest node-level search metrics (`primaries.search.query_time_in_millis` / `query_total`) for derived latency, and/or enable slow search logging and forward with a dedicated sourcetype. Baseline p95 per cluster; alert when p95 exceeds threshold for 15+ minutes. Correlate with heap GC and segment merges.
- **Visualization:** Line chart (p95/p99 search latency), Table (slow queries from slowlog), Histogram of `took_ms`.
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-7.5.5 · Elasticsearch Indexing Rate Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** A sudden drop in docs/s indexed can signal pipeline failures, bulk rejections, or cluster overload; sustained spikes may require scaling or throttling.
- **App/TA:** Custom scripted input (`_nodes/stats` indexing)
- **Data Sources:** `sourcetype=elasticsearch:indexing_stats`
- **SPL:**
```spl
index=database sourcetype="elasticsearch:indexing_stats"
| timechart span=1m per_second(indexing.index_total) as index_rate by node_name
```
- **Implementation:** Poll `GET _nodes/stats` every minute; extract `indices.indexing.index_total`, `index_time_in_millis`, and `index_current`. Store prior sample to compute rate of change. Set dynamic or static baselines; alert on drops below expected ingest or on `indexing` rejections from bulk thread pool.
- **Visualization:** Line chart (documents indexed per second by node), Single value (cluster aggregate rate), Area chart (indexing time vs. count).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-7.5.6 · Solr Query Cache Hit Ratio
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Low filter/query cache hit rates increase CPU and latency; tuning caches and queries improves headroom without adding nodes.
- **App/TA:** Custom scripted input (Solr `metrics` API), Solr log ingestion
- **Data Sources:** `sourcetype=solr:metrics`
- **SPL:**
```spl
index=database sourcetype="solr:metrics"
| where like(metric_path,"%queryResultCache%") OR like(metric_path,"%filterCache%")
| eval hit_ratio=lookup_hits / nullif(lookup_hits+lookup_misses,0)
| where hit_ratio < 0.7
| timechart span=15m avg(hit_ratio) as cache_hit_ratio by core, metric_path
```
- **Implementation:** Poll `GET /solr/admin/metrics` (or per-core metrics) every 5 minutes. Map `QUERY.queryResultCache` and `FILTER.filterCache` hits/misses. Compute hit ratio; alert below team-defined threshold (e.g., 0.7). Correlate with query pattern changes and deployments.
- **Visualization:** Gauge (cache hit ratio per core), Line chart (hit ratio trend), Table (cores below threshold).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-7.5.7 · Solr Replication Lag
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Followers lagging behind leaders serve stale results and extend recovery time; catching replication gaps protects read consistency and failover readiness.
- **App/TA:** Custom scripted input (Solr Cloud `CLUSTERSTATUS`, replica stats)
- **Data Sources:** `sourcetype=solr:replication`
- **SPL:**
```spl
index=database sourcetype="solr:replication"
| eval lag_bytes=leader_version - replica_version
| where lag_bytes > 1048576 OR index_version_lag > 100
| stats max(lag_bytes) as max_lag, max(replication_time_ms) as max_rep_ms by collection, shard, replica
| sort -max_lag
```
- **Implementation:** Ingest Solr Cloud replica state (version, generation, replication timing) from admin API or `REPLICATION` metrics. For standalone Solr, use master/slave `fetch` lag fields. Alert when replica index version lags leader beyond SLA (bytes or generations). Investigate network, disk, and TLog backlog.
- **Visualization:** Line chart (replication lag over time), Table (replicas over SLA), Single value (max lag per collection).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-7.5.8 · Elasticsearch Disk Watermark Alerts
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Capacity
- **Value:** Elasticsearch blocks shard allocation when flood-stage watermarks are hit; proactive disk alerts prevent read-only indices and cluster yellow/red states.
- **App/TA:** Custom scripted input (`_cat/allocation`, node stats fs)
- **Data Sources:** `sourcetype=elasticsearch:disk_watermark`
- **SPL:**
```spl
index=database sourcetype="elasticsearch:disk_watermark"
| eval used_pct=round(disk_used_bytes/disk_total_bytes*100,1)
| where used_pct >= watermark_low_pct OR blocks.has_read_only_allow_delete=="true"
| timechart span=5m max(used_pct) as used_pct by node_name
```
- **Implementation:** Poll `GET _cat/allocation?bytes=b&h=node,disk.avail,disk.total` or `_nodes/stats/fs` for each data node. Compare `disk.used_percent` to `cluster.routing.allocation.disk.watermark` settings. Alert at low/high/flood thresholds before Elasticsearch enforces blocks. Trigger capacity or ILM actions when trending toward limits.
- **Visualization:** Gauge (disk % per node), Table (nodes near watermark), Line chart (free space trend).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-7.5.9 · Elasticsearch JVM Heap Pressure
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** High heap usage and frequent GC pause search and indexing and can trigger circuit breakers; JVM trends predict node instability before restarts.
- **App/TA:** Custom scripted input (`_nodes/stats/jvm`)
- **Data Sources:** `sourcetype=elasticsearch:jvm`
- **SPL:**
```spl
index=database sourcetype="elasticsearch:jvm"
| eval heap_used_pct=round(mem.heap_used_in_bytes/mem.heap_max_in_bytes*100,1)
| where heap_used_pct > 85 OR gc.collectors.old.collection_time_in_millis > 30000
| timechart span=5m avg(heap_used_pct) as heap_pct, max(gc.collectors.old.collection_time_in_millis) as old_gc_ms by node_name
```
- **Implementation:** Poll JVM stats every 1–2 minutes. Track `heap_used_percent`, young/old GC collection time and count. Alert when heap consistently >85% or old GC time spikes. Correlate with fielddata, merges, and heap dumps policy.
- **Visualization:** Line chart (heap % and GC time), Area chart (heap used vs. max), Table (nodes over threshold).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-7.5.10 · OpenSearch Snapshot / Backup Status
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Failed or missing snapshots break restore and compliance RPO; monitoring repository and snapshot completion protects against silent backup gaps.
- **App/TA:** Custom scripted input (`_snapshot/_status`, `_cat/snapshots`)
- **Data Sources:** `sourcetype=opensearch:snapshot`
- **SPL:**
```spl
index=database sourcetype="opensearch:snapshot"
| eval end_epoch=if(isnotnull(end_time), end_time, _time)
| eval stale=if(state="SUCCESS" AND end_epoch < relative_time(now(),"-25h"),1,0)
| where state IN ("FAILED","PARTIAL") OR stale=1
| table repository, snapshot, state, end_epoch, stale
```
- **Implementation:** Ingest snapshot completion events from `_snapshot/<repo>/_all` or SLM/ISM policy history. Alert on `FAILED` or `PARTIAL` snapshots. Verify last successful snapshot per policy is within SLA (e.g., 24h). Monitor repository connectivity and `read_only` state.
- **Visualization:** Table (repository, last snapshot, state), Timeline (snapshot jobs), Single value (hours since last success).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-7.5.11 · Elasticsearch Circuit Breaker Trips
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Fault
- **Value:** Circuit breaker exceptions stop requests to protect the cluster; repeated trips indicate oversized aggregations, mapping issues, or undersized heap.
- **App/TA:** Elasticsearch slow logs / server logs forwarded to Splunk, JMX or `_nodes/stats` breaker fields
- **Data Sources:** `sourcetype=elasticsearch:server`, `sourcetype=elasticsearch:circuit_breaker`
- **SPL:**
```spl
index=database (sourcetype="elasticsearch:server" OR sourcetype="elasticsearch:circuit_breaker")
| search "CircuitBreakingException" OR breaker_tripped=1
| stats count by breaker_name, node_name, index
| where count > 0
| sort -count
```
- **Implementation:** Forward Elasticsearch logs with circuit breaker messages, or poll `_nodes/stats/breaker` and alert when `tripped` is true or estimated size exceeds limit. Group by `breaker_name` (parent, fielddata, request). Tie alerts to offending queries from slow logs.
- **Visualization:** Bar chart (trips by breaker type), Table (node, breaker, count), Line chart (breaker estimated size vs. limit).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-7.5.12 · Elasticsearch Thread Pool Rejections
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance, Fault
- **Value:** Thread pool rejections (HTTP 429) mean the cluster cannot keep up with search or indexing load. Sustained rejections cause data loss on ingest and timeouts on search.
- **App/TA:** Custom REST scripted input (`_nodes/stats/thread_pool`)
- **Data Sources:** `sourcetype=elasticsearch:thread_pool`
- **SPL:**
```spl
index=database sourcetype="elasticsearch:thread_pool"
| eval search_rejected_delta=search.rejected-prev_search_rejected, write_rejected_delta=write.rejected-prev_write_rejected
| where search_rejected_delta > 0 OR write_rejected_delta > 0
| timechart span=5m sum(search_rejected_delta) as search_rejections, sum(write_rejected_delta) as write_rejections by node_name
```
- **Implementation:** Poll `GET _nodes/stats/thread_pool/search,write,get` every minute. Store cumulative `rejected` counters and compute deltas between samples. Alert when any node shows rejections in a 5-minute window. Correlate with JVM heap and CPU to determine root cause (undersized cluster vs. expensive queries vs. bulk indexing spikes). Do not increase queue sizes as a fix — address the underlying load.
- **Visualization:** Line chart (rejections per pool over time), Bar chart (rejections by node), Single value (total rejections last hour).
- **CIM Models:** Performance
- **CIM SPL:**
```spl
| tstats summariesonly=t sum(Performance.cpu_load_percent) as agg_value from datamodel=Performance.CPU by Performance.host span=5m | sort - agg_value
```

- **References:** [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)

---

### UC-7.5.13 · Elasticsearch Search Latency and Slow Queries
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Search latency trending detects degradation before users notice. Slow log analysis identifies expensive queries for optimization.
- **App/TA:** Custom REST scripted input (`_nodes/stats`), Elasticsearch slow logs forwarded to Splunk
- **Data Sources:** `sourcetype=elasticsearch:search_stats`, `sourcetype=elasticsearch:slow_log`
- **SPL:**
```spl
index=database sourcetype="elasticsearch:search_stats"
| eval query_latency_ms=search.query_time_in_millis/search.query_total
| timechart span=5m avg(query_latency_ms) as avg_latency_ms, max(query_latency_ms) as p100_latency_ms by node_name
| where avg_latency_ms > 500
```
- **Implementation:** Poll `GET _nodes/stats/indices/search` to compute per-node average query latency from cumulative counters. Enable slow logs (`index.search.slowlog.threshold.query.warn: 5s`) and forward to Splunk. Correlate slow queries with specific indices and query patterns. Alert on sustained average latency above baseline or frequent slow log entries.
- **Visualization:** Line chart (query latency p50/p95/p100), Table (slow queries by index), Single value (current avg latency).
- **CIM Models:** Performance
- **CIM SPL:**
```spl
| tstats summariesonly=t count from datamodel=Performance.CPU by Performance.host span=5m | sort - count
```

- **References:** [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)

---

### UC-7.5.14 · Elasticsearch ILM Policy Failures
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** Failed ILM transitions leave indices in the wrong lifecycle phase — hot data stays on expensive storage, old data never deletes, rollover stops creating new indices. Silent failures accumulate until disk fills.
- **App/TA:** Custom REST scripted input (`_ilm/explain`)
- **Data Sources:** `sourcetype=elasticsearch:ilm_status`
- **SPL:**
```spl
index=database sourcetype="elasticsearch:ilm_status"
| where step="ERROR" OR action_time_millis > 3600000
| stats count as error_count, latest(failed_step) as failed_step, latest(step_info) as reason by index, policy
| sort -error_count
```
- **Implementation:** Poll `GET */_ilm/explain` periodically and extract indices where `step` equals `ERROR`. Capture the `failed_step`, `step_info`, and `phase_time` for root cause analysis. Alert on any index stuck in ERROR. Also monitor indices that have been in the same phase longer than expected (e.g., hot phase > 30 days when policy says 7 days).
- **Visualization:** Table (indices in error with reason), Single value (error count), Bar chart (errors by policy).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-7.5.15 · Elasticsearch Snapshot Failures
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Fault
- **Value:** Failed snapshots mean no viable backup for disaster recovery. Partial snapshots may leave indices unrecoverable. Monitoring ensures RPO commitments are met.
- **App/TA:** Custom REST scripted input (`_snapshot`)
- **Data Sources:** `sourcetype=elasticsearch:snapshot_status`
- **SPL:**
```spl
index=database sourcetype="elasticsearch:snapshot_status"
| where state IN ("FAILED","PARTIAL","INCOMPATIBLE")
| stats count by snapshot, repository, state, reason
| sort -count
```
- **Implementation:** Poll `GET _snapshot/_all/_all` or `GET _snapshot/<repo>/_current` to track snapshot state. Alert on any snapshot with state FAILED or PARTIAL. Also monitor time since last successful snapshot — alert when it exceeds RPO threshold (e.g., 24 hours). Check `_snapshot/<repo>/_status` for in-progress snapshot progress.
- **Visualization:** Table (recent snapshots with state), Single value (hours since last successful), Line chart (snapshot duration trend).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-7.5.16 · Elasticsearch Cross-Cluster Replication Lag
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance, Availability
- **Value:** CCR follower lag directly impacts disaster recovery readiness. Excessive lag means a failover would lose recent data. Monitoring ensures replication SLAs are met.
- **App/TA:** Custom REST scripted input (`_ccr/stats`)
- **Data Sources:** `sourcetype=elasticsearch:ccr_stats`
- **SPL:**
```spl
index=database sourcetype="elasticsearch:ccr_stats"
| eval lag_seconds=operations_behind/max(1, operations_per_second)
| where lag_seconds > 60 OR fatal_exception IS NOT NULL
| timechart span=5m max(lag_seconds) as max_lag_s, max(operations_behind) as ops_behind by follower_index
```
- **Implementation:** Poll `GET /_ccr/stats` to extract per-follower-index `operations_written`, `operations_read`, and `time_since_last_read`. Calculate replication lag as operations behind the leader. Alert when lag exceeds threshold (e.g., 60 seconds) or when `fatal_exception` is present. Monitor `read_exceptions` for transient network issues between clusters.
- **Visualization:** Line chart (lag per follower index), Table (follower status), Single value (max lag across all followers).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-7.5.17 · Elasticsearch Pending Cluster Tasks
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** A growing backlog of pending cluster tasks indicates the master node cannot process cluster state updates fast enough. This delays shard allocation, mapping updates, and index creation.
- **App/TA:** Custom REST scripted input (`_cluster/pending_tasks`)
- **Data Sources:** `sourcetype=elasticsearch:pending_tasks`
- **SPL:**
```spl
index=database sourcetype="elasticsearch:pending_tasks"
| stats max(insert_order) as queue_depth, max(time_in_queue_millis) as max_wait_ms
| where queue_depth > 5 OR max_wait_ms > 30000
```
- **Implementation:** Poll `GET _cluster/pending_tasks` every minute. Track the number of tasks and the `time_in_queue_millis` for the oldest task. Alert when queue depth stays above 5 for multiple consecutive samples or any task waits longer than 30 seconds. Common causes include frequent mapping changes, too many small indices, or an overloaded master node.
- **Visualization:** Line chart (pending task count), Single value (current queue depth), Table (pending tasks with wait time).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-7.5.18 · Elasticsearch Fielddata and Cache Evictions
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Fielddata evictions force expensive re-computation of in-memory data structures, causing search latency spikes. Query cache evictions reduce the benefit of repeated queries. Tracking eviction rates guides memory tuning.
- **App/TA:** Custom REST scripted input (`_nodes/stats/indices/fielddata,query_cache,request_cache`)
- **Data Sources:** `sourcetype=elasticsearch:cache_stats`
- **SPL:**
```spl
index=database sourcetype="elasticsearch:cache_stats"
| eval fd_evict_delta=fielddata.evictions-prev_fd_evictions, qc_evict_delta=query_cache.evictions-prev_qc_evictions
| where fd_evict_delta > 0 OR qc_evict_delta > 100
| timechart span=5m sum(fd_evict_delta) as fielddata_evictions, sum(qc_evict_delta) as query_cache_evictions by node_name
```
- **Implementation:** Poll `GET _nodes/stats/indices/fielddata,query_cache,request_cache` and compute deltas for `evictions` counters. Any fielddata eviction is significant — alert immediately and investigate which fields use fielddata (should be using doc_values instead). For query cache, alert when eviction rate exceeds a percentage of total cache entries. Correlate with heap usage.
- **Visualization:** Line chart (eviction rate by cache type), Bar chart (evictions by node), Single value (fielddata memory size).
- **CIM Models:** Performance
- **CIM SPL:**
```spl
| tstats summariesonly=t sum(Performance.cpu_load_percent) as agg_value from datamodel=Performance.CPU by Performance.host span=5m | sort - agg_value
```

- **References:** [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)

---

### UC-7.5.19 · Elasticsearch Segment Merge Pressure
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance
- **Value:** Heavy segment merge activity competes with search for disk I/O, causing latency spikes. Merge throttling slows indexing. Monitoring merge pressure helps balance indexing throughput against search performance.
- **App/TA:** Custom REST scripted input (`_nodes/stats/indices/merges`)
- **Data Sources:** `sourcetype=elasticsearch:merge_stats`
- **SPL:**
```spl
index=database sourcetype="elasticsearch:merge_stats"
| eval merge_rate_mb=merges.total_size_in_bytes/1048576
| timechart span=5m avg(merges.current) as active_merges, sum(merge_rate_mb) as merge_mb by node_name
| where active_merges > 3
```
- **Implementation:** Poll `GET _nodes/stats/indices/merges` for `current`, `total_size_in_bytes`, `total_time_in_millis`, and `total_throttled_time_in_millis`. Compute merge rate and throttle ratio. Alert when active merges remain high (>3) for sustained periods, or when throttle time exceeds 50% of total merge time. Correlate with indexing rate and search latency to detect I/O contention.
- **Visualization:** Line chart (active merges over time), Stacked area (merge vs. throttle time), Single value (current merge count).
- **CIM Models:** Performance
- **CIM SPL:**
```spl
| tstats summariesonly=t sum(Performance.cpu_load_percent) as agg_value from datamodel=Performance.Network by Performance.host span=5m | sort - agg_value
```

- **References:** [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)

---

### UC-7.5.20 · Solr Core Admin Health
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Core-level errors (recovery failures, corrupt index flags, leader election issues) degrade search for specific collections; admin health checks catch per-core problems early.
- **App/TA:** Custom scripted input (`/admin/cores?action=STATUS`), Solr logs
- **Data Sources:** `sourcetype=solr:core_status`
- **SPL:**
```spl
index=database sourcetype="solr:core_status"
| where state!="active" OR isnotnull(error_msg)
| stats latest(state) as state, latest(index_version) as index_version by core, collection, node_name
| sort state
```
- **Implementation:** Poll `STATUS` for all cores on a schedule; capture `instanceDir`, `dataDir`, `uptime`, replication/Cloud role fields. Ingest ERROR lines from `solr.log`. Alert when core state is not active, recovery fails, or leader/replica roles mismatch expectations.
- **Visualization:** Status grid (core × healthy), Table (cores with errors), Single value (unhealthy core count).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-7.5.21 · Elasticsearch Ingest Pipeline Error Rate
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** Ingest pipeline failures silently drop or corrupt documents before indexing. Monitoring error rates per pipeline ensures data quality and completeness.
- **App/TA:** Custom REST scripted input (`_nodes/stats/ingest`)
- **Data Sources:** `sourcetype=elasticsearch:ingest_stats`
- **SPL:**
```spl
index=database sourcetype="elasticsearch:ingest_stats"
| eval fail_rate=round(ingest.pipelines.failed/max(1,ingest.pipelines.count)*100,2)
| where fail_rate > 1 OR ingest.pipelines.failed > 0
| timechart span=5m sum(ingest.pipelines.failed) as failures by pipeline_name
```
- **Implementation:** Poll `GET _nodes/stats/ingest` and extract per-pipeline `count` and `failed` counters. Compute deltas between samples. Alert when any pipeline shows a non-zero failure rate. Investigate pipeline processor errors in Elasticsearch logs. Common causes include grok pattern mismatches, script errors, and date parsing failures.
- **Visualization:** Line chart (failures per pipeline), Table (pipeline error details), Single value (total ingest failures).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### 7.6 Database Trending

Trending metrics across relational database platforms: connection pool headroom, slow query volume, replication lag, backup growth, and index fragmentation. Uses consolidated `index=db` and native DB sourcetypes for DBA and capacity reviews.

---

### UC-7.6.1 · Database Connection Pool Utilization Trending
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance, Capacity
- **Value:** Peak connection pool utilization over 30 days shows how close applications are to exhausting database sessions. Rising peaks justify pool tuning, connection string fixes, or server scale-up before login storms cause outages.
- **App/TA:** Splunk DB Connect, vendor DB TAs (MySQL Enterprise, PostgreSQL, Oracle, SQL Server), application pool metrics if forwarded
- **Data Sources:** `index=db` `sourcetype=mysql:status`, `sourcetype=postgresql:metrics`, `sourcetype=mssql:perf`, `sourcetype=oracle:session`
- **SPL:**
```spl
index=db (sourcetype="mysql:status" OR sourcetype="postgresql:metrics" OR sourcetype="mssql:perf" OR sourcetype="oracle:session")
| eval active=coalesce(threads_connected, numbackends, active_sessions, session_count)
| eval max_conn=coalesce(max_connections, max_connections_setting, session_limit)
| eval pool_pct=if(max_conn>0, round(100*active/max_conn,2), null())
| timechart span=1d max(pool_pct) as peak_pool_util_pct by instance
```
- **Implementation:** Map instance identifiers consistently (`host` + `port` + `db_name`). For PgBouncer or RDS proxy, track pool versus backend limits separately. Alert on sustained peaks above policy (for example 80%). Combine with application-side pool settings to find mismatches. Use `perc95` if peaks are noisy from batch jobs only.
- **Visualization:** Line chart (peak pool % by instance), column chart (30-day max), table (instances over threshold).
- **CIM Models:** N/A

- **References:** [Splunk DB Connect](https://splunkbase.splunk.com/app/2686)

---

### UC-7.6.2 · Slow Query Volume Trending
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Counting queries exceeding a duration threshold per day quantifies database pain for developers and DBAs. Upward trends after releases often indicate missing indexes or plan regressions before p95 latency alerts fire.
- **App/TA:** Native slow logs, Percona, `pg_stat_statements` export, SQL Server extended events
- **Data Sources:** `index=db` `sourcetype=mysql:slow`, `sourcetype=postgresql:log`, `sourcetype=mssql:query`, `sourcetype=oracle:audit`
- **SPL:**
```spl
index=db sourcetype IN ("mysql:slow","postgresql:log","mssql:query","oracle:sql")
| eval dur_ms=coalesce(query_time_ms, duration_ms, query_duration*1000)
| where dur_ms > 1000
| bin _time span=1d
| stats count as slow_queries by _time, db_name
| timechart span=1d sum(slow_queries) as daily_slow_queries by db_name limit=12
```
- **Implementation:** Tune the millisecond threshold per environment (OLTP vs reporting). Hash or truncate SQL text for cardinality control. Exclude known batch accounts via `user` lookup. Join top patterns to `EXPLAIN` workflow or query store IDs when available. Retention on verbose logs may require summary indexing to `sourcetype=stash`.
- **Visualization:** Stacked column chart (slow queries per day by database), line chart (total slow count), table (top normalized query signatures).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-7.6.3 · Replication Lag Trending
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Maximum and average replication lag by replica over 30 days validates disaster-recovery readiness and read-consistency expectations. Gradual lag growth can signal network, disk, or write-volume problems before replica promotion fails.
- **App/TA:** MySQL replica status, PostgreSQL replication, Oracle Data Guard, SQL Server AG metrics
- **Data Sources:** `index=db` `sourcetype=mysql:slave`, `sourcetype=postgresql:replication`, `sourcetype=oracle:dg`, `sourcetype=mssql:ag`
- **SPL:**
```spl
index=db sourcetype IN ("mysql:slave","postgresql:replication","oracle:dg","mssql:ag")
| eval lag_sec=coalesce(seconds_behind_source, replay_lag_seconds, commit_lag_sec, ag_synchronization_health_seconds)
| timechart span=1d max(lag_sec) as max_replica_lag_sec avg(lag_sec) as avg_replica_lag_sec by replica_host limit=15
```
- **Implementation:** For SQL Server AG, prefer `database_replica` lag fields consistent with your sync mode. Filter out replicas in paused maintenance. Correlate spikes with large index builds or log chain breaks. Use the same clock source (NTP) across primary and replicas to avoid false lag. Cloud replicas may expose lag in milliseconds—normalize to seconds in `eval`.
- **Visualization:** Line chart (max lag per replica), area chart (avg lag), single value (worst replica lag now).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-7.6.4 · Database Backup Size Trending
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Capacity
- **Value:** Monthly backup size growth forecasts storage for backup appliances and cloud object storage costs. Anomalous jumps can indicate bulk data loads, failed truncations, or ransomware preparation worth investigating.
- **App/TA:** RMAN, SQL Server backup history, mysqldump / Percona log parsers, cloud backup APIs
- **Data Sources:** `index=db` `sourcetype=mssql:backup`, `sourcetype=mysql:backup`, `sourcetype=oracle:rman`
- **SPL:**
```spl
index=db sourcetype IN ("mssql:backup","mysql:backup","oracle:rman","postgresql:backup")
| eval size_gb=coalesce(backup_size_gb, round(backup_size_bytes/1073741824,3))
| where backup_status IN ("success","Success","completed") OR isnull(backup_status)
| bin _time span=1mon
| stats max(size_gb) as backup_size_gb by _time, database_name
| timechart span=1mon sum(backup_size_gb) as total_backup_gb by database_name limit=10
```
- **Implementation:** Deduplicate overlapping full/diff/incremental jobs with `backup_type`. Include compression ratio if logged for better capacity forecasting. Tag cloud vs on-prem targets separately. Alert on failed backups via a companion search; this UC focuses on growth trend only.
- **Visualization:** Line chart (backup size GB over months), column chart (month-over-month growth %), table (largest databases).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-7.6.5 · Index Fragmentation Trending
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Average fragmentation percentage over 30 days guides `REBUILD`/`REORG` scheduling and fill-factor reviews. Slow upward trends on hot tables correlate with extra I/O and slower queries even when CPU looks healthy.
- **App/TA:** SQL Server DMVs via scripted input, MySQL `information_schema` / InnoDB metrics, Oracle segment advisor exports
- **Data Sources:** `index=db` `sourcetype=mssql:fragmentation`, `sourcetype=mysql:innodb`, `sourcetype=oracle:segment`
- **SPL:**
```spl
index=db sourcetype IN ("mssql:fragmentation","mysql:innodb","oracle:segment","postgresql:index")
| eval frag_pct=coalesce(avg_fragmentation_in_percent, fragmentation_pct, bloat_ratio*100)
| where isnotnull(frag_pct)
| timechart span=1d avg(frag_pct) as avg_fragmentation_pct max(frag_pct) as max_fragmentation_pct by table_name limit=12
```
- **Implementation:** Sample large catalogs during off-peak windows to control license cost. Exclude tiny tables where fragmentation is meaningless. Join `table_name` to owner/schema for remediation tickets. PostgreSQL bloat metrics may use different units—normalize in `eval`. Pair with maintenance windows from change records.
- **Visualization:** Line chart (fragmentation % over time), heatmap (table × week), table (tables exceeding DBA threshold).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---
