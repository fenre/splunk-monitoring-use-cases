## 7. Database & Data Platforms

### 7.1 Relational Databases

**Primary App/TA:** Splunk DB Connect (`splunk_app_db_connect`), Splunk Add-on for Microsoft SQL Server (`Splunk_TA_microsoft-sqlserver`), MySQL/PostgreSQL TAs, scripted inputs for DMVs/catalog queries.

---

### UC-7.1.1 · Slow Query Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Slow queries degrade application performance and user experience. Identifying them enables targeted optimization.
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
| stats count by user, src_ip
| where count > 10
| sort -count
```
- **Implementation:** Ensure failed login auditing is enabled (SQL Server: "Both failed and successful logins"). Forward error logs to Splunk. Alert on >10 failures per user per hour. Correlate with AD lockout events.
- **Visualization:** Table (users with failed logins), Bar chart (failures by user), Line chart (failure rate over time).
- **CIM Models:** Databases

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
| join query_id [| inputlookup query_baselines.csv]
| eval regression_pct=round((current_avg-baseline_avg)/baseline_avg*100,1)
| where regression_pct > 50
```
- **Implementation:** Enable Query Store on SQL Server databases. Poll query performance metrics via DB Connect. Maintain baseline lookup of normal query durations. Alert when queries regress >50% from baseline. Enable automatic plan correction if available.
- **Visualization:** Table (regressed queries), Bar chart (regression % by query), Line chart (query duration trend).
- **CIM Models:** Databases

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

---
