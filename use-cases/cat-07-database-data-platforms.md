## 7. Database & Data Platforms

### 7.1 Relational Databases

**Primary App/TA:** Splunk DB Connect (`splunk_app_db_connect`), Splunk Add-on for Microsoft SQL Server (`Splunk_TA_microsoft-sqlserver`), MySQL/PostgreSQL TAs, scripted inputs for DMVs/catalog queries.

---

### UC-7.1.1 · Slow Query Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
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

### 7.3 Cloud-Managed Databases

**Primary App/TA:** Cloud provider TAs — `Splunk_TA_aws` (CloudWatch, RDS logs), `Splunk_TA_microsoft-cloudservices` (Azure Monitor), GCP TA.

---

### UC-7.3.1 · RDS/Aurora Performance Insights
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
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

### 7.4 Data Warehouses & Analytics Platforms

**Primary App/TA:** Custom REST API inputs (Snowflake Account Usage, BigQuery INFORMATION_SCHEMA), cloud provider TAs for billing/usage data.

---

### UC-7.4.1 · Query Performance Trending
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
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
- **Implementation:** Ingest pipeline orchestrator logs (Airflow, dbt, custom). Track job outcomes, durations, and data freshness. Alert on any pipeline failure. Create data freshness SLA dashboard showing when each table was last updated.
- **Visualization:** Status grid (pipeline × status), Table (failed pipelines), Line chart (pipeline duration trend), Single value (overall success rate).
- **CIM Models:** N/A

---

### UC-7.4.4 · Credit / Cost per Query
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
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


### UC-7.1.16 · Open Cursor Leak Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
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
