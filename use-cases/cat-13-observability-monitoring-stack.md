## 13. Observability & Monitoring Stack

### 13.1 Splunk Platform Health

**Primary App/TA:** Splunk Monitoring Console (built-in), `_internal` and `_audit` indexes.

---

### UC-13.1.1 · Indexer Queue Fill Ratio
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Capacity
- **Value:** Backed-up indexing queues cause data loss or delay. Detection enables immediate investigation of ingestion bottlenecks.
- **App/TA:** Monitoring Console (built-in)
- **Data Sources:** `_internal` (metrics.log, queue metrics)
- **SPL:**
```spl
index=_internal sourcetype=splunkd group=queue
| eval fill_pct=round(current_size/max_size*100,1)
| where fill_pct > 70
| timechart span=5m max(fill_pct) as queue_pct by name
```
- **Implementation:** Monitor parsing, merging, and typing queues via `_internal`. Alert when any queue exceeds 70% fill ratio. Investigate source of data surge (new data source, burst events). Consider parallel pipelines or additional indexers.
- **Visualization:** Gauge (queue fill % per pipeline), Line chart (queue fill over time), Table (queues above threshold).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-13.1.2 · Search Concurrency Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Exceeding search concurrency limits causes search skipping and degraded user experience. Monitoring guides capacity decisions.
- **App/TA:** Monitoring Console
- **Data Sources:** `_internal` (scheduler logs, search dispatch)
- **SPL:**
```spl
index=_internal sourcetype=splunkd group=search_concurrency
| timechart span=5m max(active_hist_searches) as historical, max(active_rt_searches) as realtime
```
- **Implementation:** Track concurrent searches vs configured limits. Alert when approaching concurrency limits. Identify resource-intensive searches consuming disproportionate capacity. Report on search workload distribution.
- **Visualization:** Line chart (concurrent searches over time), Gauge (% of limit), Table (top resource consumers).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-13.1.3 · Forwarder Connectivity
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Silent forwarder failures mean data gaps that may not be noticed until an investigation fails. Detection ensures data completeness.
- **App/TA:** Monitoring Console, Deployment Monitor app
- **Data Sources:** `_internal` (metrics.log — tcpin_connections)
- **SPL:**
```spl
index=_internal sourcetype=splunkd group=tcpin_connections
| stats latest(_time) as last_seen by hostname, sourceIp
| eval hours_since=round((now()-last_seen)/3600,1)
| where hours_since > 1
| table hostname, sourceIp, hours_since
| sort -hours_since
```
- **Implementation:** Track last-seen timestamp per forwarder from `_internal`. Alert when any forwarder hasn't reported in >1 hour. Maintain forwarder inventory for coverage analysis. Cross-reference with host downtime events.
- **Visualization:** Table (silent forwarders), Single value (forwarders reporting), Status grid (forwarder × health), Bar chart (silent by location).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-13.1.4 · License Usage Trending
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity
- **Value:** License overages cause enforcement (search blocking). Trending enables proactive management and capacity planning.
- **App/TA:** Monitoring Console
- **Data Sources:** `_internal` (license_usage.log)
- **SPL:**
```spl
index=_internal sourcetype=splunkd group=license_usage
| timechart span=1d sum(b) as bytes_indexed
| eval gb=round(bytes_indexed/1024/1024/1024,2)
| predict gb as predicted future_timespan=30
```
- **Implementation:** Track daily license usage against entitled volume. Alert at 80% and 90% of daily limit. Use `predict` for 30-day forecast. Identify top sourcetypes contributing to growth. Report on usage trends.
- **Visualization:** Line chart (daily usage with license limit line), Single value (today's usage %), Bar chart (usage by sourcetype), Gauge (% of limit).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-13.1.5 · Skipped Search Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Skipped searches mean scheduled reports, alerts, and data enrichments aren't running. This creates blind spots in monitoring and compliance.
- **App/TA:** Monitoring Console
- **Data Sources:** `_internal` (scheduler.log)
- **SPL:**
```spl
index=_internal sourcetype=scheduler status="skipped"
| stats count by savedsearch_name, reason
| sort -count
```
- **Implementation:** Monitor scheduler logs for skipped searches. Alert when critical searches are skipped. Track skip reasons (concurrency, disabled, cron). Optimize skipped searches or increase search concurrency limits.
- **Visualization:** Table (skipped searches with reasons), Bar chart (top skipped searches), Line chart (skip rate trend).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-13.1.6 · Index Size Trending
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity
- **Value:** Index size growth affects storage costs and search performance. Trending enables proactive storage planning.
- **App/TA:** Monitoring Console
- **Data Sources:** `_internal` (indexes.conf, REST API)
- **SPL:**
```spl
| rest /services/data/indexes
| table title, currentDBSizeMB, maxTotalDataSizeMB, frozenTimePeriodInSecs
| eval pct_used=round(currentDBSizeMB/maxTotalDataSizeMB*100,1)
| sort -pct_used
```
- **Implementation:** Poll index sizes via REST API daily. Track growth rates per index. Alert when indexes approach maxTotalDataSizeMB (data will roll to frozen). Use `predict` to forecast when limits will be reached.
- **Visualization:** Table (index sizes with % used), Bar chart (top indexes by size), Line chart (growth trend), Gauge (% of max per index).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-13.1.7 · KV Store Health
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Fault
- **Value:** KV Store failures break lookups, app functionality, and ES correlation. Health monitoring prevents cascading application issues.
- **App/TA:** Monitoring Console
- **Data Sources:** `_internal` (kvstore logs)
- **SPL:**
```spl
index=_internal sourcetype=splunkd component=KVStoreServlet OR component=KvStore
| search log_level=ERROR OR log_level=WARN
| stats count by host, log_level, message
| sort -count
```
- **Implementation:** Monitor KV Store logs for errors and replication issues. Track replication lag between SHC members. Alert on KV Store service unavailability. Monitor collection sizes for capacity planning.
- **Visualization:** Status grid (SHC member × KV Store health), Table (KV Store errors), Line chart (replication lag).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-13.1.8 · Deployment Server Status
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Configuration
- **Value:** Deployment server issues prevent app/config distribution to forwarders, leaving them with stale or incorrect configurations.
- **App/TA:** Monitoring Console
- **Data Sources:** `_internal` (deployment server logs)
- **SPL:**
```spl
index=_internal sourcetype=splunkd component=DeploymentServer
| search log_level=ERROR
| stats count by message, host
| sort -count
```
- **Implementation:** Monitor deployment server logs for errors. Track successful vs failed deployments to clients. Alert on deployment failures. Verify client phone-home intervals are within expected ranges.
- **Visualization:** Table (deployment errors), Single value (clients checking in), Bar chart (failures by server class).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-13.1.9 · Data Ingestion Latency
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** High indexing latency (difference between event time and index time) means stale data for searches. Detection enables root cause analysis.
- **App/TA:** Monitoring Console
- **Data Sources:** Any index (sampling `_time` vs `_indextime`)
- **SPL:**
```spl
(index=main OR index=security OR index=os OR index=windows) earliest=-15m
| eval latency=_indextime-_time
| stats avg(latency) as avg_latency, perc95(latency) as p95_latency by index, sourcetype
| where p95_latency > 300
| sort -p95_latency
```
- **Implementation:** Sample events periodically and calculate `_indextime` minus `_time`. Alert when p95 latency exceeds 5 minutes for critical sourcetypes. Investigate queue buildup, network latency, or time parsing issues.
- **Visualization:** Table (sourcetypes with high latency), Line chart (latency trend), Bar chart (latency by sourcetype).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-13.1.10 · Search Head Cluster Status
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** SHC member failures affect user access and search capacity. Captain election issues can cause complete SHC outage.
- **App/TA:** Monitoring Console
- **Data Sources:** `_internal` (SHC logs, REST endpoints)
- **SPL:**
```spl
| rest /services/shcluster/member/members
| table label, status, last_heartbeat, replication_count
| eval heartbeat_age=now()-last_heartbeat
| where status!="Up" OR heartbeat_age > 300
```
- **Implementation:** Monitor SHC member health via REST API. Track captain status and election events. Alert on member disconnection or replication failures. Monitor artifact replication lag between members.
- **Visualization:** Status grid (SHC member × status), Table (member health), Timeline (captain election events).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-13.1.11 · Indexer Cluster Bucket Replication
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** Under-replicated buckets mean data is at risk of loss. Monitoring ensures the replication factor is maintained.
- **App/TA:** Monitoring Console
- **Data Sources:** `_internal` (CM logs, REST endpoints)
- **SPL:**
```spl
| rest /services/cluster/master/buckets
| where search_factor_met=0 OR replication_factor_met=0
| stats count as non_compliant_buckets
```
- **Implementation:** Monitor cluster master/manager REST endpoints. Track replication and search factor compliance. Alert on any buckets not meeting the configured factor. Investigate cause (indexer down, disk full, network issues).
- **Visualization:** Single value (non-compliant buckets — target: 0), Table (non-compliant bucket details), Line chart (compliance trend).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-13.1.12 · HEC Endpoint Health
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** HEC is a primary data ingestion path. Failures silently drop data from applications, containers, and cloud services.
- **App/TA:** Monitoring Console
- **Data Sources:** `_internal` (http_event_collector logs)
- **SPL:**
```spl
index=_internal sourcetype=splunkd component=HttpEventCollector
| stats count(eval(log_level="ERROR")) as errors, count as total by host
| eval error_rate=round(errors/total*100,2)
| where error_rate > 1
```
- **Implementation:** Monitor HEC endpoint health and error rates. Track HTTP status codes returned to clients. Alert on elevated error rates (4xx, 5xx). Monitor HEC token usage for capacity planning and security.
- **Visualization:** Single value (HEC error rate), Line chart (HEC throughput), Table (errors by token), Bar chart (status codes).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-13.1.13 · Sourcetype Breakdown Trending
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity
- **Value:** Understanding data volume per sourcetype enables cost optimization, retention tuning, and unexpected growth detection.
- **App/TA:** Monitoring Console
- **Data Sources:** `_internal` (license_usage.log)
- **SPL:**
```spl
index=_internal sourcetype=splunkd group=license_usage
| stats sum(b) as bytes by st
| eval gb=round(bytes/1024/1024/1024,2)
| sort -gb
| head 20
```
- **Implementation:** Track daily volume per sourcetype. Identify top consumers. Alert on sourcetypes with unexpected growth (>20% week-over-week). Use for license optimization and retention policy tuning.
- **Visualization:** Bar chart (top sourcetypes by volume), Pie chart (volume distribution), Line chart (growth trend for top sourcetypes).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-13.1.14 · Long-Running Search Detection
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Long-running searches consume shared resources and may indicate poorly written SPL or excessive time ranges.
- **App/TA:** Monitoring Console
- **Data Sources:** `_internal` (scheduler, search audit log)
- **SPL:**
```spl
index=_audit action=search info=completed
| where total_run_time > 600
| table _time, user, savedsearch_name, total_run_time, scan_count, event_count
| sort -total_run_time
```
- **Implementation:** Monitor search audit log for long-running searches (>10 minutes). Alert on searches consuming excessive resources. Identify optimization opportunities. Report on top resource-consuming searches weekly.
- **Visualization:** Table (long-running searches), Bar chart (top consumers by run time), Line chart (long search count trend).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-13.1.15 · Splunk Certificate Expiration
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Expired Splunk internal certificates break inter-component communication (forwarder→indexer, SHC replication, etc.).
- **App/TA:** Monitoring Console, scripted input
- **Data Sources:** `_internal` (splunkd certificate warnings), certificate check script
- **SPL:**
```spl
index=_internal sourcetype=splunkd "certificate" ("expire" OR "expiration" OR "not yet valid")
| stats count by host, message
```
- **Implementation:** Monitor `_internal` for certificate-related warnings. Deploy scripted input to check Splunk certificate files directly. Alert at 30, 14, and 7 days before expiry. Document certificate renewal procedure.
- **Visualization:** Table (certificates with expiry), Single value (days until nearest expiry), Status grid (component × cert status).
- **CIM Models:** N/A


- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-13.1.16 · Parsing Queue Health (_internal)
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Capacity
- **Value:** A saturated parsing queue delays ingestion and increases `_indextime` lag. Tracking fill ratio and blocked state isolates pipeline bottlenecks before data loss.
- **App/TA:** Monitoring Console
- **Data Sources:** `index=_internal` `sourcetype=splunkd` `group=queue` (parsingqueue)
- **SPL:**
```spl
index=_internal sourcetype=splunkd group=queue name=*parsing*
| eval fill_pct=if(max_size>0, round(current_size/max_size*100,1), null())
| where fill_pct > 70 OR is_blocked=1
| timechart span=5m max(fill_pct) as max_fill by host, name
```
- **Implementation:** Filter `metrics.log` queue metrics for parsing queue names. Alert on sustained fill >70% or `is_blocked`. Correlate with new sourcetypes, regex-heavy props, or indexer CPU.
- **Visualization:** Gauge (parsing fill %), Line chart (fill by host), Table (queues above threshold).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-13.1.17 · Merging Queue Health (_internal)
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Capacity
- **Value:** Merging queue backlog delays structured indexing and can block hot buckets. Monitoring prevents silent pipeline stall on heavy merge workloads.
- **App/TA:** Monitoring Console
- **Data Sources:** `index=_internal` `sourcetype=splunkd` `group=queue` (merging / agg queues)
- **SPL:**
```spl
index=_internal sourcetype=splunkd group=queue name=*merge*
| eval fill_pct=if(max_size>0, round(current_size/max_size*100,1), null())
| where fill_pct > 70
| stats latest(fill_pct) as fill_pct, latest(current_size) as depth by host, name
| sort -fill_pct
```
- **Implementation:** Track merging-related queue names per indexer. Alert on high fill or rapid growth. Correlate with index volume, replication, and disk I/O.
- **Visualization:** Line chart (merge queue depth over time), Table (top merging queues).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-13.1.18 · Typing Queue Health (_internal)
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Capacity
- **Value:** The typing queue applies rules to parsed events; backlog here delays field extraction and routing to indexes.
- **App/TA:** Monitoring Console
- **Data Sources:** `index=_internal` `sourcetype=splunkd` `group=queue` (typingqueue)
- **SPL:**
```spl
index=_internal sourcetype=splunkd group=queue name=*typing*
| eval fill_pct=if(max_size>0, round(current_size/max_size*100,1), null())
| timechart span=5m max(fill_pct) as max_fill by host
| where max_fill > 65
```
- **Implementation:** Monitor typing queue fill and blocked state. Tune props/transforms if chronic backlog. Correlate with high-cardinality lookups or expensive `EVAL` in transforms.
- **Visualization:** Area chart (typing queue fill), Single value (worst host).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-13.1.19 · TCP Output Connection Failures (_internal)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** Forwarders and intermediate tiers rely on TCP out to indexers. Connection failures mean data is queued or dropped at the source.
- **App/TA:** Monitoring Console
- **Data Sources:** `index=_internal` `sourcetype=splunkd` (TcpOutputProc, `group=tcpout_connections`)
- **SPL:**
```spl
index=_internal sourcetype=splunkd (TcpOutputProc OR group=tcpout_connections)
| search "connection" AND ("failed" OR "refused" OR "timed out" OR "broken pipe")
| stats count by host, destIp, destPort
| sort -count
```
- **Implementation:** Forward `splunkd` logs with TCP output connection events. Alert on rising failure counts per destination. Verify indexer reachability, certificates, and firewall paths.
- **Visualization:** Table (failures by destination), Line chart (failure rate), Status grid (forwarder × output group).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-13.1.20 · Modular Input Errors (_internal)
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** Scripted and modular inputs drive critical ingestion; errors stop or corrupt data collection without obvious UI failure.
- **App/TA:** Monitoring Console
- **Data Sources:** `index=_internal` `sourcetype=splunkd` (ModularInputs, ExecProcessor)
- **SPL:**
```spl
index=_internal sourcetype=splunkd (component=ModularInputs OR component=ExecProcessor)
| search log_level=ERROR OR log_level=FATAL
| stats count by host, stanza, message
| sort -count
```
- **Implementation:** Alert on ERROR/FATAL from modular inputs. Map `stanza` to `inputs.conf`. Verify script paths, credentials, and API rate limits.
- **Visualization:** Table (modular input errors), Timeline (error bursts).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-13.1.21 · Data Model Acceleration Status (_internal)
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Failed or lagging accelerations break pivot searches, ES views, and app dashboards that depend on `tstats`.
- **App/TA:** Monitoring Console, Data Model Editor
- **Data Sources:** `index=_internal` `sourcetype=splunkd` (AccelerationManager, DataModel)
- **SPL:**
```spl
index=_internal sourcetype=splunkd (AccelerationManager OR "Data Model")
| search ("failed" OR "rebuild" OR "lag" OR log_level=ERROR)
| stats count by host, object, message
| sort -count
```
- **Implementation:** Monitor acceleration build/rebuild failures and backlogs. Alert when acceleration is disabled unexpectedly or rebuild exceeds SLA. Review high-cardinality datasets.
- **Visualization:** Table (data models with issues), Single value (models not accelerated).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-13.1.22 · Summary Indexing Failures (_internal)
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** Summary index population jobs feed exec and compliance reports; silent failures skew metrics and dashboards.
- **App/TA:** Monitoring Console
- **Data Sources:** `index=_internal` `sourcetype=scheduler` (summary-index saved searches)
- **SPL:**
```spl
index=_internal sourcetype=scheduler status IN ("failed","skipped")
| search savedsearch_name="*summary*" OR savedsearch_name="*si_*"
| stats count by savedsearch_name, reason, status
| sort -count
```
- **Implementation:** Tag SI-populating searches and alert on failed/skipped runs. Verify disk space on summary indexers and search concurrency.
- **Visualization:** Table (failed summary searches), Line chart (SI job success rate).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-13.1.23 · Indexer Disk Space Utilization (_internal)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Capacity
- **Value:** Full indexer volumes stop writes and break replication; proactive disk monitoring avoids cascading cluster failure.
- **App/TA:** Monitoring Console
- **Data Sources:** `index=_internal` `sourcetype=splunk_disk_objects` / `splunkd` disk metrics
- **SPL:**
```spl
index=_internal sourcetype=splunk_disk_objects OR (sourcetype=splunkd "disk usage")
| eval pct_used=if(total_kb>0, round(used_kb/total_kb*100,1), null())
| where pct_used > 85
| stats latest(pct_used) as pct_used, latest(used_kb) as used_kb by host, mount_point
| sort -pct_used
```
- **Implementation:** Normalize mount paths for hot/warm/cold. Alert at 85% and 90%. Include frozen path and SmartStore cache volumes where applicable.
- **Visualization:** Gauge (disk % per indexer), Table (mounts at risk), Heatmap (host × volume).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-13.1.24 · SmartStore Cache Hit/Miss Ratio (_internal)
- **Criticality:** 🟠 High
- **Difficulty:** 🔴 Expert
- **Monitoring type:** Performance
- **Value:** Low cache hit rates increase S3/API latency and search cost. Trending hit/miss guides cache sizing and bucket locality.
- **App/TA:** Monitoring Console
- **Data Sources:** `index=_internal` `sourcetype=splunkd` (SmartStore, remote storage metrics)
- **SPL:**
```spl
index=_internal sourcetype=splunkd (SmartStore OR "remote_storage" OR S2Bucket)
| search ("cache" OR "download" OR "hit" OR "miss")
| rex "(?<metric>hit|miss|download)_count=(?<cnt>\d+)"
| stats sum(eval(if(match(metric,"hit"),cnt,0))) as hits, sum(eval(if(match(metric,"miss"),cnt,0))) as misses by host
| eval hit_ratio=if((hits+misses)>0, round(100*hits/(hits+misses),2), null())
| where hit_ratio < 70 OR isnull(hit_ratio)
```
- **Implementation:** Parse vendor-specific SmartStore metrics or use `metrics.log` patterns for remote fetch vs cache serve. Baseline hit ratio per indexer. Alert on sustained drops after upgrades or index changes.
- **Visualization:** Line chart (hit ratio over time), Single value (cluster avg hit %).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-13.1.25 · Cluster Bundle Push Failures (_internal)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Configuration
- **Value:** Failed bundle distribution leaves indexers with stale `indexes.conf`, apps, or peer configs, causing search/replication skew.
- **App/TA:** Monitoring Console, Cluster Manager
- **Data Sources:** `index=_internal` `sourcetype=splunkd` (CM, bundle replication)
- **SPL:**
```spl
index=_internal sourcetype=splunkd (bundle OR BundleReplication)
| search (log_level=ERROR OR "bundle.*fail" OR "Failed to apply")
| stats count by host, peer, message
| sort -count
```
- **Implementation:** Monitor CM and peer logs for bundle apply failures. Alert immediately. Verify disk space on peers and CM connectivity.
- **Visualization:** Table (peers with bundle errors), Timeline (bundle events).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-13.1.26 · splunkd Unexpected Restart Detection (_internal)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Unplanned `splunkd` restarts interrupt searches, replication, and ingestion. Correlating restarts speeds root cause (OOM, crash, admin).
- **App/TA:** Monitoring Console
- **Data Sources:** `index=_internal` `sourcetype=splunkd` (startup, shutdown, watchdog)
- **SPL:**
```spl
index=_internal sourcetype=splunkd
| search ("Splunkd starting" OR "Shutting down" OR "splunkd restarted" OR "detected unexpected")
| bin _time span=1h
| stats count by host, _time
| where count > 3
```
- **Implementation:** Tune for crash loops; join with OOM killer logs on the OS if forwarded. Alert when hourly restart count exceeds threshold.
- **Visualization:** Table (restart count by host), Timeline (restart events).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-13.1.27 · Splunk Web UI Errors (_internal)
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Fault
- **Value:** Web UI 5xx/timeout errors block analysts during incidents. Tracking errors isolates SHC vs load balancer vs app issues.
- **App/TA:** Monitoring Console
- **Data Sources:** `index=_internal` `sourcetype=splunk_web_access` / `splunkd_ui` / `splunkd` Web UI
- **SPL:**
```spl
index=_internal sourcetype IN ("splunk_web_access","splunkd_ui","splunkd") uri_path="*"
| search status>=500 OR match(_raw,"(?i)(error|exception|timeout)")
| stats count by status, uri_path, clientip
| sort -count
```
- **Implementation:** Ensure access logs include HTTP status. Alert on 5xx rate above baseline. Correlate with KV Store and SHC captain during UI-wide failures.
- **Visualization:** Line chart (5xx rate), Table (top failing URIs).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-13.1.28 · SHC Configuration Replication Lag (_internal)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Configuration
- **Value:** Lagging conf replication causes inconsistent searches and failed lookups across members.
- **App/TA:** Monitoring Console
- **Data Sources:** `index=_internal` `sourcetype=splunkd` (SHC, replication, `apply_bundle`)
- **SPL:**
```spl
index=_internal sourcetype=splunkd component=*SHC* OR component=*shcluster*
| search ("replication" OR "bundle" OR "lag") AND (log_level=WARN OR log_level=ERROR)
| stats count by host, message
| sort -count
```
- **Implementation:** Prefer REST `| rest /services/shcluster/member/members` for `last_conf_replication` where available. Alert on WARN/ERROR about replication lag or failed bundles.
- **Visualization:** Table (members with replication issues), Single value (max lag seconds).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-13.1.29 · Ingest Actions Pipeline Status (_internal)
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** Ingest actions (routing, filtering, streaming) failures drop or misroute security and operational data.
- **App/TA:** Monitoring Console
- **Data Sources:** `index=_internal` `sourcetype=splunkd` (IngestActions, `ingest_actions`)
- **SPL:**
```spl
index=_internal sourcetype=splunkd (IngestActions OR "ingest.action")
| search log_level=ERROR OR "failed" OR "dropped"
| stats count by host, pipeline, rule_id, message
| sort -count
```
- **Implementation:** Map errors to `props`/`transforms` ingest action stanzas. Alert on any sustained error rate. Verify HEC and indexer tier compatibility.
- **Visualization:** Table (failing ingest actions), Line chart (error trend).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-13.1.30 · Timestamp Parsing Accuracy (_internal)
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** Mis-parsed timestamps break RT searches, compliance, and `_indextime` lag metrics.
- **App/TA:** Monitoring Console
- **Data Sources:** `index=_internal` `sourcetype=splunkd` (DateParser, `could not use strptime`)
- **SPL:**
```spl
index=_internal sourcetype=splunkd (DateParser OR "strptime" OR "could not")
| search (log_level=WARN OR log_level=ERROR)
| stats count by host, sourcetype_extracted, message
| sort -count
```
- **Implementation:** Track DATE_CONFIG failures and warnings. Join with sample events from the same sourcetype in data tier. Fix `TIME_FORMAT`/`MAX_TIMESTAMP_LOOKAHEAD`.
- **Visualization:** Table (sourcetypes with parse warnings), Line chart (warning rate).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-13.1.31 · Workload Management Pool Saturation (_internal)
- **Criticality:** 🟠 High
- **Difficulty:** 🔴 Expert
- **Monitoring type:** Performance
- **Value:** WLM pools prevent search starvation; saturation delays critical searches and alerts.
- **App/TA:** Monitoring Console
- **Data Sources:** `index=_internal` `sourcetype=splunkd` (WorkloadManager, `workload_pool`)
- **SPL:**
```spl
index=_internal sourcetype=splunkd (WorkloadManager OR "workload_pool")
| search ("saturated" OR "rejected" OR "queue" OR log_level=ERROR)
| stats count by host, pool_name, message
| sort -count
```
- **Implementation:** Define pool limits per SLA. Alert on rejections or sustained queue depth. Correlate with ad-hoc search storms.
- **Visualization:** Table (pools with rejections), Gauge (pool utilization %).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-13.1.32 · Search Scheduler Fill Ratio (_internal)
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity
- **Value:** Scheduler at capacity skips searches—blind spots for alerts and summaries.
- **App/TA:** Monitoring Console
- **Data Sources:** `index=_internal` `sourcetype=scheduler` / `splunkd` `group=scheduler`
- **SPL:**
```spl
index=_internal sourcetype=scheduler
| stats count(eval(status="skipped")) as skipped, count as total
| eval fill_skip_pct=round(100*skipped/total,2)
| where fill_skip_pct > 5
```
- **Implementation:** Track skipped vs completed over sliding windows. Break down by app and user. Add concurrency or split heavy searches when fill ratio grows.
- **Visualization:** Line chart (scheduler skip %), Table (top skipped searches).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-13.1.33 · Knowledge Bundle Size Monitoring (_internal)
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Oversized knowledge bundles slow search distribution and SHC replication.
- **App/TA:** Monitoring Console
- **Data Sources:** `index=_internal` `sourcetype=splunkd` (bundles, `KnowledgeBundle`)
- **SPL:**
```spl
index=_internal sourcetype=splunkd "bundle" ("MB" OR "KB" OR "size")
| rex "(?<bundle_mb>\d+(\.\d+)?)\s*MB"
| where bundle_mb > 200
| stats count by host, user, app
| sort -bundle_mb
```
- **Implementation:** Prefer REST or scripted checks of bundle sizes on search heads. Alert when bundle size exceeds policy. Audit large lookups and unused apps.
- **Visualization:** Table (largest bundles), Bar chart (size by app).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-13.1.34 · Real-Time Search Resource Consumption (_internal)
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Real-time searches reserve cores and memory; runaway RT jobs degrade interactive and scheduled workload.
- **App/TA:** Monitoring Console
- **Data Sources:** `index=_internal` `sourcetype=splunkd` `group=search_concurrency` / `search_process`
- **SPL:**
```spl
index=_internal sourcetype=splunkd group=search_concurrency
| stats max(active_rt_searches) as rt_active, max(active_hist_searches) as hist by host
| eval rt_ratio=if((rt_active+hist)>0, round(100*rt_active/(rt_active+hist),1), null())
| where rt_active > 20 OR rt_ratio > 40
```
- **Implementation:** Baseline RT search counts per SH. Alert on unusual RT concurrency. Identify dashboards or users with many concurrent RT panels.
- **Visualization:** Line chart (RT vs historical searches), Table (hosts with high RT).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-13.1.35 · User Search Activity Audit (_audit)
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Compliance
- **Value:** Auditing who ran which searches supports insider-threat investigations and segregation of duties.
- **App/TA:** Audit trail (built-in)
- **Data Sources:** `index=_audit` `action=search`
- **SPL:**
```spl
index=_audit action=search info=started
| stats count, dc(search) as distinct_searches by user, app
| sort -count
```
- **Implementation:** Retain per policy. Report on after-hours or high-volume search users. Exclude known service accounts via lookup.
- **Visualization:** Table (users by search volume), Heatmap (hour × user).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-13.1.36 · Configuration File Change Tracking (_audit)
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Unauthorized `.conf` edits change data access and ingestion behavior; rapid detection limits blast radius.
- **App/TA:** Audit trail
- **Data Sources:** `index=_audit` (`action` for config changes)
- **SPL:**
```spl
index=_audit action IN ("edit_*","update")
| search file_path="*.conf" OR object_path="*local*"
| table _time, user, action, file_path, object_path
| sort -_time
```
- **Implementation:** Map `action` types to your Splunk version. Alert on changes outside change windows. Route to SecOps for prod SH/CM.
- **Visualization:** Timeline (config changes), Table (recent edits by user).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-13.1.37 · Knowledge Object Modification Audit (_audit)
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Value:** Dashboard and alert tampering can hide attacks or exfiltration; object-level audit supports SOC and GRC.
- **App/TA:** Audit trail
- **Data Sources:** `index=_audit` (knowledge object CRUD)
- **SPL:**
```spl
index=_audit object_type IN ("savedsearch","dashboard","lookup","macro")
| stats count by user, object_type, action
| sort -count
```
- **Implementation:** Tune `object_type` values for your version. Alert on delete or ACL change for critical objects. Use lookups for approved admins.
- **Visualization:** Table (changes by object type), Bar chart (actions by user).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-13.1.38 · REST API Access Pattern Analysis (_audit)
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Automated token abuse and reconnaissance often appear as unusual REST paths or volumes.
- **App/TA:** Audit trail / `splunkd_access`
- **Data Sources:** `index=_audit` `action=rest` OR `index=_internal` `sourcetype=splunkd_access`
- **SPL:**
```spl
(index=_audit action=rest) OR (index=_internal sourcetype=splunkd_access)
| stats count by user, uri_path, status
| where count > 500 OR status>=400
| sort -count
```
- **Implementation:** Baseline normal automation. Alert on new `uri_path` clusters or HTTP 401/403 bursts. Correlate with token ID if logged.
- **Visualization:** Table (top REST paths), Line chart (4xx/5xx rate).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-13.1.39 · Role and Capability Change Detection (_audit)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
- **Value:** Privilege escalation via new roles/capabilities must be detected in minutes, not days.
- **App/TA:** Audit trail
- **Data Sources:** `index=_audit` (authentication/authorization changes)
- **SPL:**
```spl
index=_audit object_type IN ("user","role","capabilities")
| search action IN ("create","update","delete","edit_user","edit_role")
| table _time, user, action, object, target_user, roles_added
| sort -_time
```
- **Implementation:** Field names vary by version—verify with `| metadata type=sourcetypes index=_audit`. Alert on any `admin` role grant or `edit_user` outside IT hours.
- **Visualization:** Timeline (privilege changes), Table (recent role mappings).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-13.1.40 · Per-Process CPU and Memory Trending (_introspection)
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** `splunkd` child processes (search, indexer, pipeline) resource trends predict OOM and slowdown before user impact.
- **App/TA:** Monitoring Console
- **Data Sources:** `index=_introspection` `sourcetype=splunk_resource_usage` / `splunk_disk_objects`
- **SPL:**
```spl
index=_introspection sourcetype=splunk_resource_usage
| timechart span=5m avg(data.cpu_pct) as cpu, avg(data.mem_used) as mem_kb by data.process_type, host
```
- **Implementation:** Enable introspection generators on all tiers. Alert when `cpu_pct` or memory for `search`/`indexing` exceeds baseline. Use `predict` for week-over-week growth.
- **Visualization:** Line chart (CPU/memory by process class), Heatmap (host × process).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-13.1.41 · Dispatch Directory Size (_introspection)
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity
- **Value:** Large dispatch directories fill disk and slow search teardown—common after runaway searches or stuck jobs.
- **App/TA:** Monitoring Console, scripted disk check
- **Data Sources:** Scripted input / HEC: `sourcetype=splunk:dispatch_stats` on `index=main` (dispatch dir size MB per SH)
- **SPL:**
```spl
index=main sourcetype="splunk:dispatch_stats"
| eval size_gb=round(dispatch_dir_size_mb/1024,2)
| where size_gb > 50
| stats max(size_gb) as max_gb by host
```
- **Implementation:** Nightly scripted input: `du -sm` on `$SPLUNK_HOME/var/run/splunk/dispatch`, emit JSON. Alert on rapid growth. Automate cleanup of orphaned jobs per support guidance.
- **Visualization:** Gauge (dispatch GB per SH), Line chart (growth trend).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-13.1.42 · I/O Wait Bottleneck Detection (_introspection)
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** High I/O wait on indexers correlates with slow searches, bucket replication, and ingestion lag.
- **App/TA:** Monitoring Console, OTel/node_exporter
- **Data Sources:** `index=_introspection` `sourcetype=splunk_resource_usage` (disk I/O fields) / host metrics
- **SPL:**
```spl
index=_introspection sourcetype=splunk_resource_usage
| where data.io_wait_pct > 25 OR data.disk_busy_pct > 80
| timechart span=5m avg(data.io_wait_pct) by host
```
- **Implementation:** Field names depend on platform; normalize in `props`. Correlate with storage latency metrics from SAN/NVMe. Alert when sustained `io_wait` exceeds threshold.
- **Visualization:** Line chart (iowait %), Table (hosts with disk saturation).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-13.1.43 · Splunk Version Compliance (operational inventory)
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Value:** Drift across Splunk Enterprise versions breaks feature parity and support eligibility.
- **App/TA:** Monitoring Console, REST inventory
- **Data Sources:** `| rest /services/server/info` (scripted aggregate), `sourcetype=splunk:version_inventory`
- **SPL:**
```spl
index=inventory sourcetype="splunk:version_inventory"
| stats dc(version) as version_count, values(version) as versions by group
| where version_count > 1
| table group, versions
```
- **Implementation:** Nightly scheduled search hits `server/info` on all peers via SH with credentials or forwarder-side scripted input. Compare to approved matrix. Report non-compliant hosts.
- **Visualization:** Table (hosts × version), Pie chart (version distribution).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-13.1.44 · App Version Consistency Across SHC (operational inventory)
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Configuration
- **Value:** Mixed app versions on SHC members cause bundle skew and intermittent UI or search errors.
- **App/TA:** SHC, REST
- **Data Sources:** `| rest /services/apps/local` per member, `sourcetype=splunk:shc_app_inventory`
- **SPL:**
```spl
index=inventory sourcetype="splunk:shc_app_inventory"
| stats values(app_version) as ver by app_name, member
| eventstats dc(ver) as ver_count by app_name
| where ver_count > 1
| table app_name, member, ver
```
- **Implementation:** Push inventory script via `runshellscript` or external job. Alert on mismatch for production apps. Exclude dev-only apps via lookup.
- **Visualization:** Matrix (app × member version), Table (mismatched apps).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-13.1.45 · Forwarder Version Compliance (operational inventory)
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Compliance
- **Value:** Old universal forwarders miss TLS fixes and acknowledgment behaviors required by security policy.
- **App/TA:** Deployment Server, `splunkd` phone-home
- **Data Sources:** `index=_internal` `group=deploymentclient` / `sourcetype=splunk:forwarder_inventory`
- **SPL:**
```spl
index=_internal sourcetype=splunkd group=deploymentclient
| stats latest(version) as uf_version by hostname
| lookup approved_uf_versions.csv version OUTPUT approved
| where isnull(approved)
| table hostname, uf_version
```
- **Implementation:** Maintain CSV of approved forwarder builds. Supplement with DS client list. Drive upgrades via DS server classes.
- **Visualization:** Bar chart (forwarders by version), Single value (% compliant).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-13.1.46 · Log Volume and Error Rate Anomaly per Sourcetype (MLTK)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Fault, Performance
- **Value:** Silent data pipeline breaks — a forwarder stops sending, a sourcetype drops to zero, or error rates spike — are invisible to threshold alerts that only fire on presence. By modeling expected log volume and error rate per sourcetype with MLTK, this detection catches ingestion failures within minutes instead of hours, preventing blind spots in security and operational monitoring.
- **App/TA:** Splunk Machine Learning Toolkit (MLTK)
- **Data Sources:** `index=_internal sourcetype=splunkd` (metrics.log), `index=_internal sourcetype=splunkd` (component=Metrics)
- **SPL:**
```spl
| tstats count WHERE index=* by _time span=15m, sourcetype
| xyseries _time sourcetype count
| fillnull value=0
| untable _time sourcetype count
| fit DensityFunction count by sourcetype into sourcetype_volume_model
| rename "IsOutlier(count)" as isOutlier
| where isOutlier > 0 OR count=0
| eval anomaly_type=if(count=0, "silent_drop", "volume_anomaly")
| table _time, sourcetype, count, anomaly_type
| sort anomaly_type, -_time
```
- **Implementation:** Schedule every 15 minutes against a 30-day trained DensityFunction model per sourcetype. Zero-count windows flag silent pipeline drops immediately. Volume spikes or dips that deviate from the learned distribution trigger volume anomaly alerts. Enrich with forwarder host metadata to pinpoint the broken pipeline segment. Integrate with PagerDuty or Splunk On-Call for infrastructure on-call routing. Retrain the model weekly via a separate scheduled search. Exclude maintenance windows using a KV store lookup.
- **Visualization:** Line chart (volume per sourcetype with anomaly markers), Table (anomalous sourcetypes), Single value (active silent drops).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-13.1.47 · License Usage Forecast with Seasonality (MLTK)
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Capacity
- **Value:** Splunk license overages trigger warnings and eventually block indexing. Forecasting daily license consumption with seasonal decomposition (weekly and monthly patterns) gives administrators 7–30 day advance warning to act — whether by reducing noisy sourcetypes, requesting license expansion, or shifting workloads.
- **App/TA:** Splunk Machine Learning Toolkit (MLTK)
- **Data Sources:** `index=_internal sourcetype=splunk_resource_usage` OR License Usage Report view
- **SPL:**
```spl
index=_internal source=*license_usage.log type=Usage
| bin _time span=1d
| stats sum(b) as bytes_used by _time
| eval gb_used=round(bytes_used/1073741824, 2)
| fit StateSpaceForecast gb_used holdback=0 forecast_k=30 conf_interval=95 into license_forecast_model
| eval over_license=if('predicted(gb_used)' > license_limit_gb, 1, 0)
| table _time, gb_used, "predicted(gb_used)", "lower95(predicted(gb_used))", "upper95(predicted(gb_used))", over_license
```
- **Implementation:** Pull daily license usage from `license_usage.log` and train a StateSpaceForecast model that captures weekly cycles (lower weekend volumes) and monthly trends (end-of-month batch jobs). Forecast 30 days ahead with 95% confidence intervals. Alert when the upper confidence bound crosses the licensed capacity threshold. Display the forecast in a capacity planning dashboard alongside current daily consumption. Retrain monthly. Supplement with `predict` command for simpler deployments that lack MLTK.
- **Visualization:** Area chart (actual vs forecast with confidence band), Single value (days until projected overage), Table (daily forecast).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-13.1.48 · Splunk Internal Queue Depth Multivariate Anomaly (MLTK)
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance
- **Value:** Individual queue metrics (parsing, merging, typing, indexing) may fluctuate normally, but simultaneous pressure across multiple queues indicates a systemic bottleneck. Multivariate anomaly detection catches correlated queue saturation that per-queue thresholds miss, enabling proactive capacity intervention before data loss occurs.
- **App/TA:** Splunk Machine Learning Toolkit (MLTK)
- **Data Sources:** `index=_internal sourcetype=splunkd` (component=Metrics, group=queue)
- **SPL:**
```spl
index=_internal sourcetype=splunkd component=Metrics group=queue
| bin _time span=5m
| stats avg(current_size_kb) as avg_size by _time, name
| xyseries _time name avg_size
| fillnull value=0
| fit DensityFunction parsingQueue indexQueue typingQueue mergingQueue tcpin_queue into queue_multivariate_model
| where isOutlier > 0
| eval severity=case(
    parsingQueue > 500 AND indexQueue > 500, "critical",
    parsingQueue > 500 OR indexQueue > 500, "high",
    true(), "medium")
| table _time, parsingQueue, indexQueue, typingQueue, mergingQueue, severity
| sort -_time
```
- **Implementation:** Collect queue metrics from `metrics.log` across all indexers. Pivot into a wide table (one column per queue) for multivariate DensityFunction modeling. The model learns the joint distribution of queue depths, catching correlated saturation that single-queue thresholds miss. Alert on critical (multiple large queues) and high (single large queue) severity. Correlate with ingestion volume spikes and forwarder connection counts. Route alerts to the Splunk platform team. Retrain the model weekly.
- **Visualization:** Multi-line chart (all queue depths over time), Heatmap (queue × indexer), Single value (current anomaly status).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-13.1.49 · Service Latency Seasonality and Anomaly (MLTK)
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance
- **Value:** Application response times follow predictable patterns — higher during business hours, lower at night. By decomposing latency into seasonal (hour-of-week) and residual components, this detection flags abnormal slowdowns that coincide with deployments, infrastructure changes, or emerging incidents — even when raw latency stays within static thresholds.
- **App/TA:** Splunk Machine Learning Toolkit (MLTK), Splunk Observability Cloud (optional)
- **Data Sources:** `index=main sourcetype=access_combined` or APM traces, `index=o11y sourcetype=otel:metrics`
- **SPL:**
```spl
index=main sourcetype=access_combined
| eval response_ms=response_time*1000
| bin _time span=5m
| stats p95(response_ms) as p95_latency, p99(response_ms) as p99_latency, count by _time, uri_path
| eval hour_of_week=(tonumber(strftime(_time,"%w"))*24) + tonumber(strftime(_time,"%H"))
| fit DensityFunction p95_latency p99_latency by uri_path into latency_seasonal_model
| rename "IsOutlier(p95_latency)" as is_p95_outlier, "IsOutlier(p99_latency)" as is_p99_outlier
| where is_p95_outlier > 0 OR is_p99_outlier > 0
| table _time, uri_path, p95_latency, p99_latency, hour_of_week, count
| sort -p95_latency
```
- **Implementation:** Collect p95 and p99 latency per endpoint in 5-minute bins. Train DensityFunction models per `uri_path` that learn hour-of-week seasonality. Anomalies represent latency that is unusual for that specific time window, not just above a flat threshold. Correlate with deployment events from CI/CD pipelines (cat-12) and infrastructure changes. Create ITSI KPIs from the anomaly output for service health scoring. Alert application owners via Splunk On-Call with endpoint-specific context. Retrain models weekly.
- **Visualization:** Line chart (p95 latency with seasonal overlay), Heatmap (endpoint × hour-of-week), Table (anomalous endpoints).
- **CIM Models:** Web
- **CIM SPL:**
```spl
| tstats summariesonly=t count from datamodel=Web.Web by Web.status, Web.http_method, Web.dest span=5m | sort - count
```

- **References:** [CIM: Web](https://docs.splunk.com/Documentation/CIM/latest/User/Web)

---

### UC-13.1.50 · Kubernetes HPA Replica Count Anomaly (MLTK)
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance, Capacity
- **Value:** Horizontal Pod Autoscaler (HPA) replica counts reflect traffic load. Unexpected spikes in replicas without corresponding traffic increases may indicate resource leaks, crash loops, or misconfigured scaling policies. Anomaly detection on replica counts relative to traffic volume catches autoscaler misbehavior before it exhausts cluster capacity.
- **App/TA:** Splunk Machine Learning Toolkit (MLTK), Splunk Connect for Kubernetes (Helm chart, github.com/splunk/splunk-connect-for-kubernetes)
- **Data Sources:** `index=k8s sourcetype=kube:objects:hpa`, `index=k8s sourcetype=kube:metrics`
- **SPL:**
```spl
index=k8s sourcetype="kube:objects:hpa"
| bin _time span=5m
| stats latest(status.currentReplicas) as replicas, latest(status.currentMetrics{}.resource.current.averageValue) as avg_cpu by _time, metadata.name, metadata.namespace
| eval replicas=tonumber(replicas), avg_cpu=tonumber(avg_cpu)
| fit DensityFunction replicas avg_cpu by "metadata.name" into hpa_anomaly_model
| rename "IsOutlier(replicas)" as replica_outlier
| where replica_outlier > 0
| table _time, metadata.namespace, metadata.name, replicas, avg_cpu
| sort -replicas
```
- **Implementation:** Collect HPA status objects from the Kubernetes API via Splunk Connect for Kubernetes. Model the joint distribution of replica count and CPU utilization per HPA target. Outliers where replica count spikes without proportional CPU increase indicate scaling misbehavior. Correlate with pod restart events and OOMKill signals from `kube:events`. Alert the platform engineering team and include the HPA configuration (min/max replicas, target utilization) for rapid triage. Retrain the model weekly.
- **Visualization:** Dual-axis line chart (replicas vs CPU), Table (anomalous HPAs), Bar chart (replica count distribution by namespace).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-13.1.51 · SLO Burn-Rate Multivariate Anomaly (MLTK)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔴 Expert
- **Monitoring type:** Performance, Compliance
- **Value:** Single-dimensional SLO burn-rate alerts trigger too late or too often. By combining error budget burn rates across availability, latency, and throughput SLOs into a multivariate model, this detection identifies services heading for SLO breach across multiple dimensions simultaneously — a stronger signal than any individual budget alarm.
- **App/TA:** Splunk Machine Learning Toolkit (MLTK), Splunk ITSI (optional)
- **Data Sources:** `index=o11y sourcetype=otel:metrics`, SLO definitions in KV store or ITSI
- **SPL:**
```spl
index=o11y sourcetype="otel:metrics" metric_name IN ("slo.error_budget.remaining_pct","slo.latency_budget.remaining_pct","slo.throughput_budget.remaining_pct")
| bin _time span=1h
| stats latest(metric_value) as budget_pct by _time, service.name, metric_name
| xyseries _time+"|"+service.name metric_name budget_pct
| fillnull value=100
| eval burn_avail=100-'slo.error_budget.remaining_pct', burn_latency=100-'slo.latency_budget.remaining_pct', burn_throughput=100-'slo.throughput_budget.remaining_pct'
| fit DensityFunction burn_avail burn_latency burn_throughput into slo_burnrate_model
| where isOutlier > 0
| eval composite_burn=burn_avail + burn_latency + burn_throughput
| sort -composite_burn
| table _time, service.name, burn_avail, burn_latency, burn_throughput, composite_burn
```
- **Implementation:** Define SLOs for each service across three dimensions: availability (error rate), latency (p99 target), and throughput (requests/sec floor). Calculate hourly burn rates as the percentage of monthly error budget consumed. Train a DensityFunction model on the joint burn-rate distribution across all three dimensions per service. Services where multiple budgets burn simultaneously are flagged as multivariate outliers. Integrate with ITSI service models to propagate SLO risk into service health scores. Alert service owners at 50% budget consumed (warning) and 80% consumed (critical). Use the model to provide SRE teams with a predicted breach timeline.
- **Visualization:** Radar chart (three SLO dimensions per service), Line chart (burn rates over time), Table (services at risk), Single value (services projected to breach this month).
- **CIM Models:** N/A

- **References:** [Splunk ITSI](https://splunkbase.splunk.com/app/1841)

---

### 13.2 Splunk ITSI (Premium)

**Primary App/TA:** Splunk IT Service Intelligence (Premium), Content Pack for Monitoring and Alerting.

---

### UC-13.2.1 · Service Health Score Trending
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Service health scores provide a single-pane view of business service status. Trending enables SLA reporting and proactive management.
- **App/TA:** Splunk ITSI
- **Premium Apps:** Splunk IT Service Intelligence (ITSI)
- **Data Sources:** `itsi_summary` index
- **SPL:**
```spl
index=itsi_summary is_service_in_maintenance=0
| timechart span=1h avg(health_score) by service_name
```
- **Implementation:** Configure ITSI services with KPIs mapped to business services. Track health scores over time. Alert on score degradation. Use for SLA reporting and executive dashboards. Configure Glass Tables for NOC display.
- **Visualization:** Service Analyzer (ITSI native), Glass Table, Line chart (health trend), Status grid.
- **CIM Models:** N/A

- **References:** [Splunk ITSI](https://splunkbase.splunk.com/app/1841)

---

### UC-13.2.2 · KPI Degradation Alerting
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** KPI threshold breaches provide early warning of service degradation. Adaptive thresholds reduce false positives vs static thresholds.
- **App/TA:** Splunk ITSI
- **Data Sources:** ITSI correlation searches, KPI data
- **SPL:**
```spl
index=itsi_summary severity_value>3
| stats count by service_name, kpi_name, severity_label
| sort -count
```
- **Implementation:** Configure KPIs with adaptive thresholds (ITSI machine learning). Set up correlation searches for threshold breach alerting. Route alerts to Episode Review for analyst triage. Tune thresholds based on feedback.
- **Visualization:** ITSI Deep Dive, Service Analyzer, Line chart with threshold bands.
- **CIM Models:** N/A

- **References:** [Splunk ITSI](https://splunkbase.splunk.com/app/1841)

---

### UC-13.2.3 · Episode Volume and MTTR
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Episode volume and resolution time measure IT operations effectiveness. Trending drives process improvement.
- **App/TA:** Splunk ITSI
- **Data Sources:** `itsi_grouped_alerts` index
- **SPL:**
```spl
index=itsi_grouped_alerts
| stats count as episodes, avg(duration) as avg_duration_sec by severity
| eval avg_mttr_min=round(avg_duration_sec/60,1)
```
- **Implementation:** Track episode creation, severity distribution, and time-to-resolution. Monitor episode assignment and owner workload. Alert on episode volume spikes. Report on MTTR by severity for management.
- **Visualization:** Bar chart (episodes by severity), Line chart (episode volume trend), Single value (avg MTTR), Table (open episodes).
- **CIM Models:** N/A

- **References:** [Splunk ITSI](https://splunkbase.splunk.com/app/1841)

---

### UC-13.2.4 · Entity Status Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Entity health provides granular visibility into individual infrastructure components feeding services. Unstable entities degrade service health.
- **App/TA:** Splunk ITSI
- **Data Sources:** ITSI entity overview, entity health scores
- **SPL:** *(Run in the ITSI app context or use your deployment’s fully qualified `itsi_entities` lookup path so the lookup resolves.)*
```spl
| inputlookup itsi_entities
| where entity_status!="active"
| table title, entity_type, entity_status, last_seen
```
- **Implementation:** Configure entity discovery (AD, CMDB, cloud APIs). Monitor entity states (active, inactive, unstable). Alert when critical entities become inactive. Track entity population for coverage analysis.
- **Visualization:** Status grid (entities by type × status), Table (inactive entities), Single value (active entity count).
- **CIM Models:** N/A

- **References:** [Splunk ITSI](https://splunkbase.splunk.com/app/1841)

---

### UC-13.2.5 · Base Search Performance
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Fault
- **Value:** ITSI base searches feed all KPIs. Slow or skipped base searches cause stale or missing KPI data across multiple services.
- **App/TA:** Splunk ITSI
- **Data Sources:** `_internal` (scheduler logs for ITSI searches)
- **SPL:**
```spl
index=_internal sourcetype=scheduler savedsearch_name="ITSI*Base*"
| stats avg(run_time) as avg_runtime, count(eval(status="skipped")) as skipped by savedsearch_name
| where avg_runtime > 120 OR skipped > 0
```
- **Implementation:** Monitor ITSI base search run times and skip rates. Alert when any base search is skipped or exceeds its schedule interval. Optimize slow base searches (reduce scope, improve SPL). Consider splitting overloaded base searches.
- **Visualization:** Table (base search performance), Bar chart (runtime by search), Single value (skipped searches).
- **CIM Models:** N/A

- **References:** [Splunk ITSI](https://splunkbase.splunk.com/app/1841)

---

### UC-13.2.6 · Rules Engine Health
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Fault
- **Value:** The ITSI Rules Engine processes events into episodes. Failure means alerts are not grouped or routed, breaking Event Analytics.
- **App/TA:** Splunk ITSI
- **Data Sources:** `_internal` (itsi_internal_log)
- **SPL:**
```spl
index=_internal sourcetype=itsi_internal_log component=RulesEngine
| search log_level=ERROR OR log_level=WARN
| stats count by log_level, message
```
- **Implementation:** Monitor Rules Engine logs for errors and warnings. Alert on Rules Engine restarts or processing failures. Track event-to-episode latency. Verify aggregation policies are functioning correctly.
- **Visualization:** Single value (Rules Engine status), Table (recent errors), Line chart (processing latency).
- **CIM Models:** N/A

- **References:** [Splunk ITSI](https://splunkbase.splunk.com/app/1841)

---

### UC-13.2.7 · Predictive Service Degradation
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Availability
- **Value:** Predicting service health degradation before it happens enables proactive remediation, reducing incident impact.
- **App/TA:** Splunk ITSI + MLTK
- **Data Sources:** `itsi_summary` + ML models
- **SPL:**
```spl
index=itsi_summary service_name="Production Web"
| timechart span=15m avg(health_score) as health
| predict health as predicted_health future_timespan=24 algorithm=LLP5
| where predicted_health < 50
```
- **Implementation:** Train ML models on service health history using MLTK. Predict health scores 4-24 hours ahead. Alert when predicted health falls below threshold. Investigate contributing KPIs proactively. This is an advanced ITSI capability.
- **Visualization:** Line chart (actual vs predicted health), Single value (predicted health in 4h), Alert timeline.
- **CIM Models:** N/A

- **References:** [Splunk ITSI](https://splunkbase.splunk.com/app/1841)

---

### UC-13.2.8 · Glass Table NOC Display
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Real-time service visualization for operations centers provides at-a-glance awareness of infrastructure and service health.
- **App/TA:** Splunk ITSI Glass Tables
- **Data Sources:** ITSI service/KPI data
- **SPL:**
```spl
| rest /servicesNS/-/-/data/ui/views
| search label="Glass*" OR label="NOC*"
| table title label author updated
| sort -updated
```
- **Implementation:** Design Glass Tables representing logical infrastructure views (network topology, service dependency map, data center layout). Map ITSI services and KPIs to visual elements. Deploy on NOC screens with auto-refresh.
- **Visualization:** ITSI Glass Table (custom visual layout with service health indicators, KPI widgets, and status icons).
- **CIM Models:** N/A

- **References:** [Splunk ITSI](https://splunkbase.splunk.com/app/1841)

---

### UC-13.2.9 · Elasticsearch Ingest Pipeline Errors
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** Log pipeline processing failures causing data loss or corruption.
- **App/TA:** Custom (ES REST API)
- **Data Sources:** Elasticsearch _nodes/stats/ingest, pipeline error counts
- **SPL:**
```spl
index=elasticsearch sourcetype="elasticsearch:ingest"
| where pipeline_failures > 0 OR pipeline_current > 100
| stats sum(pipeline_failures) as total_failures, sum(pipeline_current) as current_in_flight by node_name, pipeline_id
| sort -total_failures
```
- **Implementation:** Poll Elasticsearch `GET _nodes/stats/ingest` via scripted input or scheduled REST call. Parse `ingest.total.pipeline_failures`, `ingest.total.pipeline_current`, and per-pipeline stats. Ingest as events with node, pipeline ID, and counters. Alert when pipeline_failures increases or when pipeline_current exceeds threshold (backlog). Correlate with index rate and cluster health. Investigate pipeline processor errors (script failures, date parse errors, field mapping conflicts).
- **Visualization:** Table (pipelines with failures), Line chart (pipeline failures over time), Bar chart (failures by pipeline), Single value (total pipeline failures).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-13.2.10 · Fluentd / Fluent Bit Buffer Overflow
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault, Availability
- **Value:** Log forwarding buffer full, data at risk of being dropped.
- **App/TA:** Custom (Fluentd monitoring agent, Fluent Bit metrics)
- **Data Sources:** Fluentd /api/plugins.json, Fluent Bit /api/v1/metrics
- **SPL:**
```spl
index=fluent sourcetype IN ("fluentd:plugins", "fluentbit:metrics")
| eval buffer_usage_pct=if(isnum(buffer_queue_length) AND buffer_total_limit>0, round(buffer_queue_length/buffer_total_limit*100,1), null())
| where buffer_queue_length > 0 AND (buffer_usage_pct > 80 OR buffer_total_limit - buffer_queue_length < 1000)
| stats latest(buffer_queue_length) as queue_depth, latest(buffer_total_limit) as limit, latest(buffer_usage_pct) as pct by host, plugin_id, output_plugin
| sort -pct
```
- **Implementation:** For Fluentd, enable monitoring agent and poll `/api/plugins.json` (or use `in_monitor_agent`). For Fluent Bit, enable HTTP server and poll `/api/v1/metrics`. Ingest buffer_queue_length, buffer_total_limit, retry_count, and emit_count. Alert when buffer usage exceeds 80% or when retries spike. Correlate with downstream (Elasticsearch, Splunk) ingestion latency. Tune buffer size, flush interval, or add more workers.
- **Visualization:** Table (plugins with high buffer usage), Gauge (buffer fill % per output), Line chart (buffer depth over time), Bar chart (retries by plugin).
- **CIM Models:** N/A


- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-13.2.11 · KPI Threshold Violation Trending
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Trending KPI breaches over time shows chronic vs transient service issues and validates threshold tuning.
- **App/TA:** Splunk ITSI
- **Premium Apps:** Splunk IT Service Intelligence (ITSI)
- **Data Sources:** `index=itsi_summary`, `itsi_notable:audit`
- **SPL:**
```spl
index=itsi_summary severity_value>=3
| timechart span=1h count by service_name, kpi_name
| streamstats window=24 avg(count) as baseline by kpi_name
| where count > baseline * 2
```
- **Implementation:** Baseline breach counts per KPI with `streamstats` or `predict`. Alert on sustained elevation vs one-off spikes. Feed results into Episode Review for service owners.
- **Visualization:** Line chart (breaches per KPI), Heatmap (service × hour), Table (KPIs above baseline).
- **CIM Models:** N/A

- **References:** [Splunk ITSI](https://splunkbase.splunk.com/app/1841)

---

### UC-13.2.12 · Episode Correlation Accuracy
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔴 Expert
- **Monitoring type:** Performance
- **Value:** Measuring false merges and missed splits improves aggregation policies and reduces analyst rework.
- **App/TA:** Splunk ITSI Event Analytics
- **Data Sources:** `index=itsi_grouped_alerts`, analyst disposition (ServiceNow/Splunk On-Call)
- **SPL:**
```spl
index=itsi_grouped_alerts
| lookup episode_feedback episode_id OUTPUT disposition
| stats count by disposition, severity
| eval pct=round(100*count/sum(count),2)
```
- **Implementation:** Ingest manual episode disposition (false positive, wrong merge, should split) from ticketing or a KV store. Monthly review of `pct` by policy. Tune aggregation and similarity thresholds.
- **Visualization:** Pie chart (disposition mix), Bar chart (accuracy by policy), Table (episodes with poor feedback).
- **CIM Models:** N/A

- **References:** [Splunk ITSI](https://splunkbase.splunk.com/app/1841)

---

### UC-13.2.13 · Maintenance Window Compliance
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Compliance
- **Value:** Incorrect maintenance flags hide real outages during change windows, while noisy KPI alerts during true maintenance erode analyst trust. This use case validates that ITSI `is_service_in_maintenance` flags align with ITSM change windows, catching both missing and stale flags.
- **App/TA:** Splunk ITSI
- **Data Sources:** `index=itsi_summary`, maintenance windows via REST
- **SPL:**
```spl
index=itsi_summary is_service_in_maintenance=0
| join type=left max=1 service_name [
  | rest /servicesNS/nobody/SA-ITOA/maintenance_services
  | table title, service_name
]
| where severity_value>=4
| stats count by service_name
```
- **Implementation:** Compare active alerts against scheduled maintenance windows. Alert when KPIs fire outside declared windows for critical services (possible misconfiguration). Report on % of alerts during maintenance windows.
- **Visualization:** Table (services alerting outside window), Single value (non-compliant alert %).
- **CIM Models:** N/A

- **References:** [Splunk ITSI](https://splunkbase.splunk.com/app/1841)

---

### UC-13.2.14 · Glass Table SLA Breaches
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Glass Tables for NOC must reflect SLA-backed KPIs; breaches on the wallboard drive incident prioritization.
- **App/TA:** Splunk ITSI Glass Tables
- **Data Sources:** ITSI KPIs, `itsi_summary`, SLA lookup
- **SPL:**
```spl
index=itsi_summary
| lookup sla_targets service_name OUTPUT kpi_name, sla_target
| where health_score < sla_target OR severity_value>=4
| stats count by service_name, kpi_name
| sort -count
```
- **Implementation:** Maintain `sla_targets` lookup with minimum health score or max severity per service. Drive Glass Table color thresholds from the same search. Alert when executive-facing services breach SLA for >15 minutes.
- **Visualization:** Glass Table (SLA status), KPI ticker (breached services), Table (breach duration).
- **CIM Models:** N/A

- **References:** [Splunk ITSI](https://splunkbase.splunk.com/app/1841)

---

### UC-13.2.15 · Service Dependency Health Propagation
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Upstream dependency failure should roll up to dependent services; missing links cause wrong prioritization.
- **App/TA:** Splunk ITSI Service Analyzer
- **Data Sources:** ITSI service topology, `itsi_summary`
- **SPL:**
```spl
| inputlookup itsi_services
| search is_enabled=1
| join type=left max=1 service_name [
  search index=itsi_summary is_service_in_maintenance=0
  | stats latest(health_score) as health by service_name
]
| where health < 50
| table service_name, health, dependent_services
```
- **Implementation:** Validate service dependencies in ITSI. When a dependency drops below threshold, confirm dependent service health reflects impact (or use entity rules). Run weekly health of dependency graph completeness.
- **Visualization:** Service Analyzer tree, Sankey (dependency impact), Table (dependency × health).
- **CIM Models:** N/A

- **References:** [Splunk ITSI](https://splunkbase.splunk.com/app/1841)

---

### UC-13.2.16 · ITSI Backup Set Integrity
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** Corrupt or incomplete KV Store / ITSI backup objects prevent disaster recovery after SH loss.
- **App/TA:** Splunk ITSI, backup automation
- **Data Sources:** Backup job logs, `sourcetype=itsi:backup`
- **SPL:**
```spl
index=_internal OR index=main sourcetype="itsi:backup"
| search status IN ("failed","partial","corrupt") OR match(_raw,"(?i)(checksum|verify failed)")
| stats count by backup_job, host, message
| sort -count
```
- **Implementation:** Log ITSI backup jobs (scheduled exports, `kvstore` backup). Verify checksum after write. Alert on any non-success. Test restore quarterly to a lab SH.
- **Visualization:** Table (failed backups), Timeline (backup jobs), Single value (last successful backup age).
- **CIM Models:** N/A

- **References:** [Splunk ITSI](https://splunkbase.splunk.com/app/1841)

---

### UC-13.2.17 · Notable Event Suppression Audit
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Value:** Over-suppression hides incidents; audit ensures suppress rules and analyst actions are justified.
- **App/TA:** Splunk ITSI, ES correlation (if linked)
- **Data Sources:** `index=itsi_notable:audit` / notable audit logs
- **SPL:**
```spl
index=itsi_notable:audit OR index=notable sourcetype="itsi:notable_audit"
| search action IN ("suppress","close","suppress_episode")
| stats count by user, rule_id, reason
| sort -count
```
- **Implementation:** Ingest notable audit events with user, rule, and reason. Alert on high-volume suppression by single user or new rule. Review monthly for policy compliance.
- **Visualization:** Table (top suppressors), Bar chart (suppressions by rule), Timeline (suppression events).
- **CIM Models:** N/A

- **References:** [Splunk ITSI](https://splunkbase.splunk.com/app/1841)

---

### UC-13.2.18 · Adaptive Thresholding Effectiveness
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Availability
- **Value:** Adaptive thresholds reduce false positives; tracking effectiveness shows when to retrain or fall back to static limits.
- **App/TA:** Splunk ITSI (adaptive thresholds)
- **Data Sources:** `index=itsi_summary`, KPI threshold history
- **SPL:**
```spl
index=itsi_summary is_service_in_maintenance=0
| timechart span=1d count(eval(severity_value>=3)) as breaches by kpi_name
| join max=1 kpi_name [
  search index=itsi_summary kpi_threshold_type="adaptive"
  | stats dc(kpi_name) as adaptive_kpis by kpi_name
]
| where breaches > 10
```
- **Implementation:** Tag KPIs using adaptive vs static thresholds. Compare breach rate and analyst disposition before/after ML enablement. Retrain when seasonal drift causes misses.
- **Visualization:** Line chart (breaches per adaptive KPI), Table (KPIs needing threshold review).
- **CIM Models:** N/A

- **References:** [Splunk ITSI](https://splunkbase.splunk.com/app/1841)

---

### UC-13.2.19 · Multi-Tier Application Service Tree Modeling
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Availability
- **Value:** Service trees link infrastructure KPIs to business outcomes, enabling impact analysis that shows which component failure affects which customer-facing service.
- **App/TA:** Splunk ITSI
- **Premium Apps:** Splunk IT Service Intelligence (ITSI)
- **Data Sources:** `itsi_summary` index, entity discovery from infrastructure TAs
- **SPL:**
```spl
| rest /servicesNS/nobody/SA-ITOA/itoa_interface/service
| rename title as service_name
| eval kpi_count=mvcount(kpis), dep_count=mvcount(services_depends_on)
| table service_name kpi_count dep_count
| sort -dep_count
```
- **Implementation:** Model services top-down: business service → application tier → middleware → infrastructure. Use entity rules with host/IP aliases to dynamically bind entities. Define dependency relationships so parent health reflects child degradation. Use service templates for repeatable patterns across environments.
- **Visualization:** Service Analyzer (dependency tree), Glass Table (business service map).
- **CIM Models:** N/A

- **References:** [Splunk ITSI](https://splunkbase.splunk.com/app/1841)

---

### UC-13.2.20 · Entity Discovery Completeness Audit
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Configuration
- **Value:** Undiscovered entities create monitoring blind spots. Auditing entity coverage against infrastructure inventories ensures every critical asset is monitored by ITSI services.
- **App/TA:** Splunk ITSI, infrastructure TAs
- **Premium Apps:** Splunk IT Service Intelligence (ITSI)
- **Data Sources:** `itsi_entities` lookup, CMDB/asset inventory, `index=_internal`
- **SPL:** *(Run in the ITSI app context or use your deployment’s fully qualified `itsi_entities` lookup path so the lookup resolves.)*
```spl
| inputlookup itsi_entities
| stats dc(_key) as itsi_entities values(entity_type_ids) as types
| appendcols [
  | tstats dc(host) as infra_hosts where (index=main OR index=security OR index=os OR index=windows) by index
  | stats sum(infra_hosts) as total_infra_hosts
]
| eval coverage_pct=round(itsi_entities/total_infra_hosts*100,1)
| table itsi_entities total_infra_hosts coverage_pct types
```
- **Implementation:** Compare ITSI entity inventory against CMDB, cloud provider APIs, or Splunk host metadata. Identify unmonitored hosts. Use entity discovery searches or CSV imports to close gaps. Schedule weekly coverage audits. Track entity types to ensure classification is consistent.
- **Visualization:** Single value (coverage %), Table (unmatched hosts), Column chart (entity count by type).
- **CIM Models:** N/A

- **References:** [Splunk ITSI](https://splunkbase.splunk.com/app/1841)

---

### UC-13.2.21 · Content Pack Deployment Health (Monitoring and Alerting)
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** The Monitoring and Alerting content pack provides pre-built correlation searches and aggregation policies. Tracking deployment health ensures these critical components remain functional.
- **App/TA:** Splunk ITSI, DA-ITSI-CP-Monitoring-and-Alerting
- **Premium Apps:** Splunk IT Service Intelligence (ITSI)
- **Data Sources:** `index=_internal sourcetype=scheduler`, `itsi_tracked_alerts`, `itsi_grouped_alerts`
- **SPL:**
```spl
index=_internal sourcetype=scheduler app="DA-ITSI-CP-Monitoring-and-Alerting"
| stats count(eval(status="success")) as success count(eval(status="skipped")) as skipped count(eval(status!="success" AND status!="skipped")) as failed by savedsearch_name
| eval health=if(failed>0 OR skipped>success, "degraded", "healthy")
| sort -failed -skipped
```
- **Implementation:** Install the Monitoring and Alerting content pack via ITSI UI. Enable correlation searches incrementally. Monitor the lookup generator reports (schedule daily). Track notable event flow rates to confirm the pipeline is working. Alert on correlation search failures or skipped executions.
- **Visualization:** Table (search name, status, skip rate), Single value (healthy/degraded count).
- **CIM Models:** N/A

- **References:** [Splunk ITSI](https://splunkbase.splunk.com/app/1841)

---

### UC-13.2.23 · Notable Event Volume Trending by Source
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Tracking notable event volume by source correlation search identifies noisy rules, misconfigured thresholds, and alert fatigue risks before they overwhelm analysts.
- **App/TA:** Splunk ITSI
- **Premium Apps:** Splunk IT Service Intelligence (ITSI)
- **Data Sources:** `itsi_tracked_alerts`
- **SPL:**
```spl
index=itsi_tracked_alerts
| timechart span=1h count by source limit=20
| addtotals
| where Total > 50
```
- **Implementation:** Monitor notable event ingest rates per correlation search source. Identify sudden spikes (alert storms) and sustained high-volume sources (noisy rules). Set thresholds: >100 notables/hour from a single source warrants investigation. Tune or disable noisy correlation searches. Feed into Episode Review capacity planning.
- **Visualization:** Stacked area chart (events by source over time), Table (top 10 noisiest sources).
- **CIM Models:** N/A

- **References:** [Splunk ITSI](https://splunkbase.splunk.com/app/1841)

---

### UC-13.2.24 · KPI Drift Detection for Gradual Degradation
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance
- **Value:** Drift detection identifies gradual KPI value changes (e.g., slow memory leak, increasing latency) that stay within thresholds but indicate an emerging problem. Catches issues before threshold breach.
- **App/TA:** Splunk ITSI 4.20+
- **Premium Apps:** Splunk IT Service Intelligence (ITSI)
- **Data Sources:** `itsi_summary`, `itsi_summary_metrics`
- **SPL:**
```spl
index=itsi_summary is_service_in_maintenance=0 is_entity_in_maintenance=0
| timechart span=1d avg(alert_value) as daily_avg by kpi_name
| foreach * [
  | eval <<FIELD>>_trend=if(<<FIELD>> > 0, round((<<FIELD>> - exact(<<FIELD>>))/exact(<<FIELD>>)*100, 2), 0)
]
| untable _time kpi_name daily_avg
| eventstats avg(daily_avg) as baseline stdev(daily_avg) as sigma by kpi_name
| eval drift_score=round(abs(daily_avg - baseline) / sigma, 2)
| where drift_score > 2
```
- **Implementation:** Enable drift detection in ITSI 4.20+ Configuration Assistant. For earlier versions, use MLTK regression models on KPI time series. Compare rolling 7-day averages against 30-day baselines. Alert when drift exceeds 2 sigma. Common drift patterns: memory leaks, disk fill, queue depth growth, connection pool exhaustion.
- **Visualization:** Line chart (KPI value with baseline band), Table (drifting KPIs ranked by score).
- **CIM Models:** N/A

- **References:** [Splunk ITSI](https://splunkbase.splunk.com/app/1841)

---

### UC-13.2.25 · MLTK Custom Anomaly Detection on KPI Data
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔴 Expert
- **Monitoring type:** Performance
- **Value:** Combining MLTK with ITSI KPI data enables custom anomaly models that detect multi-dimensional patterns (e.g., CPU+memory+latency correlation) impossible with single-KPI thresholds.
- **App/TA:** Splunk ITSI, Splunk Machine Learning Toolkit (MLTK)
- **Premium Apps:** Splunk IT Service Intelligence (ITSI)
- **Data Sources:** `itsi_summary`, MLTK models
- **SPL:**
```spl
index=itsi_summary is_service_aggregate=0 kpi_name IN ("CPU Utilization", "Memory Usage", "Response Time")
| timechart span=5m avg(alert_value) by kpi_name
| fit DensityFunction "CPU Utilization" "Memory Usage" "Response Time" into itsi_multivariate_model
| where isOutlier > 0
```
- **Implementation:** Extract KPI data from `itsi_summary`. Build MLTK models (DensityFunction for outlier detection, RandomForestRegressor for prediction). Create residual KPIs: predicted vs actual values. Feed MLTK output back as ITSI KPIs for service health scoring. Retrain models monthly or on significant infrastructure changes.
- **Visualization:** Scatter plot (multi-dimensional KPI space with outliers highlighted), Line chart (residual KPI over time).
- **CIM Models:** N/A

- **References:** [Splunk ITSI](https://splunkbase.splunk.com/app/1841)

---

### UC-13.2.26 · Splunk On-Call (VictorOps) Alert Routing
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** Routing ITSI episode alerts to Splunk On-Call ensures the right on-call engineer is paged with full service context, reducing MTTA by eliminating manual triage.
- **App/TA:** Splunk ITSI, Splunk On-Call
- **Premium Apps:** Splunk IT Service Intelligence (ITSI)
- **Data Sources:** `itsi_grouped_alerts`, On-Call incident logs
- **SPL:**
```spl
index=itsi_grouped_alerts status=1 severity>=4
| eval routing_key=case(
    match(service_name, "(?i)payment|checkout"), "payment-team",
    match(service_name, "(?i)database|sql"), "dba-team",
    1=1, "general-ops"
)
| stats count by routing_key severity
| sort -severity
```
- **Implementation:** Configure Splunk On-Call integration in ITSI notable event actions. Map episode severity to On-Call urgency levels. Define routing keys per service or service tree branch. Enable auto-acknowledgment when analysts claim episodes in Episode Review. Track MTTA and MTTR per routing key.
- **Visualization:** Table (routing key, severity, count), Single value (unacknowledged critical episodes).
- **CIM Models:** N/A

- **References:** [Splunk ITSI](https://splunkbase.splunk.com/app/1841)

---

### UC-13.2.27 · Observability Cloud Alert Ingestion
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Availability
- **Value:** Ingesting Splunk Observability Cloud alerts into ITSI unifies cloud-native and on-prem monitoring into a single episode management workflow, eliminating tool-switching.
- **App/TA:** Splunk ITSI, Splunk Observability Cloud
- **Premium Apps:** Splunk IT Service Intelligence (ITSI)
- **Data Sources:** Observability Cloud webhooks, `itsi_tracked_alerts`
- **SPL:**
```spl
index=itsi_tracked_alerts source="*observability*" OR source="*o11y*"
| stats count by service_name severity source
| sort -count
```
- **Implementation:** Configure Observability Cloud to forward alerts via webhook to Splunk HEC. Normalize alert payloads into the ITSI Universal Alerting schema. Create a Universal Correlation Search to convert incoming alerts into notable events. Configure NEAPs to group O11y alerts with infrastructure alerts into unified episodes. Track alert volume and false positive rate.
- **Visualization:** Table (O11y alert source, count, severity), Time chart (alert volume over time).
- **CIM Models:** Alerts
- **CIM SPL:**
```spl
| tstats summariesonly=t count from datamodel=Alerts.Alerts by Alerts.severity, Alerts.signature, Alerts.app | sort - count
```

- **References:** [Splunk ITSI](https://splunkbase.splunk.com/app/1841), [CIM: Alerts](https://docs.splunk.com/Documentation/CIM/latest/User/Alerts)

---

### UC-13.2.28 · Service Template Adoption and Consistency
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Configuration
- **Value:** Service templates ensure consistent KPI definitions, thresholds, and entity rules across environments (dev/staging/prod). Tracking adoption prevents configuration drift.
- **App/TA:** Splunk ITSI
- **Premium Apps:** Splunk IT Service Intelligence (ITSI)
- **Data Sources:** ITSI REST API, `itsi_services` lookup
- **SPL:**
```spl
| rest /servicesNS/nobody/SA-ITOA/itoa_interface/service
| rename title as service_name
| eval has_template=if(isnotnull(base_service_template_id), "yes", "no")
| stats count by has_template
| eval adoption_pct=round(count/sum(count)*100, 1)
```
- **Implementation:** Create service templates for standard service types (web app, database, message queue). Link services to templates for consistent KPI inheritance. Monitor template adherence — services that diverge from templates should be reviewed. Use ITSI REST API to programmatically create services from templates during CI/CD deployments.
- **Visualization:** Pie chart (templated vs non-templated), Table (services diverging from template).
- **CIM Models:** N/A

- **References:** [Splunk ITSI](https://splunkbase.splunk.com/app/1841)

---

### UC-13.2.29 · Entity-Level Adaptive Threshold Tuning
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔴 Expert
- **Monitoring type:** Performance
- **Value:** Entity-level adaptive thresholds (ITSI 4.20+) provide per-host baselines instead of aggregate, drastically reducing false positives in heterogeneous environments where host behavior varies.
- **App/TA:** Splunk ITSI 4.20+
- **Premium Apps:** Splunk IT Service Intelligence (ITSI)
- **Data Sources:** `itsi_summary`, per-entity KPI data
- **SPL:**
```spl
index=itsi_summary is_entity_in_maintenance=0 is_service_in_maintenance=0
| stats avg(alert_value) as avg_val stdev(alert_value) as stdev_val count by entity_title kpi_name
| where stdev_val/avg_val > 0.5 AND count > 100
| sort -stdev_val
| head 20
```
- **Implementation:** Enable entity-level adaptive thresholds for KPIs with high per-entity variance (e.g., CPU on mixed workload hosts). Review the coefficient of variation (stdev/mean) — values > 0.5 indicate entity-level thresholds will significantly outperform aggregate. Monitor false positive reduction after enablement. Fall back to static thresholds for entities with insufficient data.
- **Visualization:** Table (entity, KPI, variance, threshold type), Line chart (per-entity KPI with threshold bands).
- **CIM Models:** N/A

- **References:** [Splunk ITSI](https://splunkbase.splunk.com/app/1841)

---

### UC-13.2.30 · Configuration Assistant Recommendations Tracking
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Configuration
- **Value:** The Configuration Assistant (ITSI 4.20+) provides AI-powered optimization recommendations. Tracking which recommendations are implemented vs ignored ensures continuous ITSI health improvement.
- **App/TA:** Splunk ITSI 4.20+
- **Premium Apps:** Splunk IT Service Intelligence (ITSI)
- **Data Sources:** `index=_internal sourcetype=itsi_internal_log`, Configuration Assistant UI
- **SPL:**
```spl
index=_internal sourcetype=itsi_internal_log component=ConfigurationAssistant
| stats count by recommendation_type action_taken
| eval implementation_rate=round(count/sum(count)*100, 1)
```
- **Implementation:** Review Configuration Assistant recommendations weekly. Categorize by type: threshold tuning, KPI consolidation, entity rule optimization, base search performance. Track implementation rate and measure impact (reduced skipped searches, fewer false positives, improved health score stability). Prioritize recommendations that affect critical services.
- **Visualization:** Table (recommendation type, count, implementation status), Single value (implementation rate %).
- **CIM Models:** N/A

- **References:** [Splunk ITSI](https://splunkbase.splunk.com/app/1841)

---

### UC-13.2.31 · Deep Dive Utilization and Performance
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Deep Dives are ITSI's primary investigation tool. Tracking utilization reveals which KPIs analysts actually use for troubleshooting and identifies slow-rendering dives that need optimization.
- **App/TA:** Splunk ITSI
- **Premium Apps:** Splunk IT Service Intelligence (ITSI)
- **Data Sources:** `index=_internal`, ITSI access logs
- **SPL:**
```spl
index=_internal sourcetype=splunkd_ui_access uri_path="*deep_dive*"
| stats count avg(spent) as avg_load_time_ms by user uri_path
| sort -count
| eval avg_load_time_s=round(avg_load_time_ms/1000, 2)
```
- **Implementation:** Monitor Deep Dive access patterns to understand analyst workflows. Identify unused deep dives for cleanup. Track load times — dives exceeding 10s typically have too many KPIs or overly broad time ranges. Optimize by reducing KPI count per lane, enabling backfill, or narrowing default time ranges.
- **Visualization:** Table (deep dive name, user, access count, avg load time), Bar chart (top 10 most-used dives).
- **CIM Models:** N/A

- **References:** [Splunk ITSI](https://splunkbase.splunk.com/app/1841)

---

### UC-13.2.32 · ITSI Team Permission and RBAC Audit
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Splunk Pillar:** Security
- **Value:** ITSI team assignments control service visibility and episode access. Auditing permissions ensures least-privilege access and prevents unauthorized service modifications.
- **App/TA:** Splunk ITSI
- **Premium Apps:** Splunk IT Service Intelligence (ITSI)
- **Data Sources:** ITSI REST API, `authorize.conf`
- **SPL:**
```spl
| rest /servicesNS/nobody/SA-ITOA/itoa_interface/team
| rename title as team_name
| eval member_count=mvcount(members)
| eval service_count=mvcount(services)
| table team_name member_count service_count
| sort -service_count
```
- **Implementation:** Define ITSI teams aligned to organizational structure. Assign services to teams for scoped visibility. Audit team membership quarterly — remove departed users, verify role assignments (itoa_admin, itoa_team_admin, itoa_analyst, itoa_user). Ensure admin role inherits itoa_admin in authorize.conf. Monitor for users with excessive permissions.
- **Visualization:** Table (team, members, services, role distribution), Single value (users with admin access).
- **CIM Models:** N/A

- **References:** [Splunk ITSI](https://splunkbase.splunk.com/app/1841)

---

### UC-13.2.33 · Business Service SLA Composite Scoring
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance
- **Value:** Composite SLA scores aggregate ITSI health data across services to produce contractual SLA metrics (e.g., 99.9% availability), directly supporting customer and executive reporting.
- **App/TA:** Splunk ITSI
- **Premium Apps:** Splunk IT Service Intelligence (ITSI)
- **Data Sources:** `itsi_summary`, SLA definitions
- **SPL:**
```spl
index=itsi_summary is_service_aggregate=1
  service_name IN ("Payment Gateway", "Customer Portal", "API Platform")
| bin _time span=1d
| stats avg(health_score) as daily_health by _time service_name
| eval sla_met=if(daily_health >= 70, 1, 0)
| stats sum(sla_met) as days_met count as total_days by service_name
| eval sla_pct=round(days_met/total_days*100, 3)
| eval sla_target=99.9
| eval sla_status=if(sla_pct >= sla_target, "MET", "BREACHED")
```
- **Implementation:** Define SLA targets per business service (e.g., 99.9% availability). Map ITSI health score thresholds to SLA compliance (health >= 70 = available). Calculate daily/monthly/quarterly SLA metrics. Use Glass Tables for executive dashboards showing SLA status. Alert on projected SLA breach based on error budget burn rate. Integrate with ITSM for SLA violation reporting.
- **Visualization:** Glass Table (SLA dashboard), Single value (current SLA %), Gauge (error budget remaining), Table (service SLA history).
- **CIM Models:** N/A

- **References:** [Splunk ITSI](https://splunkbase.splunk.com/app/1841)

---

### UC-13.2.34 · Episode MTTR Analysis by Service Tier
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Breaking MTTR down by service tier (Tier 1 critical, Tier 2 important, Tier 3 internal) reveals whether high-priority services get faster resolution and identifies process bottlenecks.
- **App/TA:** Splunk ITSI
- **Premium Apps:** Splunk IT Service Intelligence (ITSI)
- **Data Sources:** `itsi_grouped_alerts`
- **SPL:**
```spl
index=itsi_grouped_alerts status=5
| eval create_time=strptime(create_time, "%Y-%m-%dT%H:%M:%S")
| eval close_time=strptime(mod_time, "%Y-%m-%dT%H:%M:%S")
| eval mttr_minutes=round((close_time - create_time) / 60, 1)
| eval tier=case(
    severity>=6, "Tier 1 - Critical",
    severity>=4, "Tier 2 - Important",
    1=1, "Tier 3 - Internal"
)
| stats avg(mttr_minutes) as avg_mttr median(mttr_minutes) as median_mttr count by tier
| sort tier
```
- **Implementation:** Define service tiers based on business impact (severity mapping). Track MTTR per tier over time. Set targets: Tier 1 < 15 min, Tier 2 < 60 min, Tier 3 < 4 hours. Analyze outliers to identify process gaps. Correlate MTTR with time-of-day and team assignment for resource optimization.
- **Visualization:** Bar chart (avg MTTR by tier), Line chart (MTTR trend over weeks), Table (slowest-resolved episodes).
- **CIM Models:** N/A

- **References:** [Splunk ITSI](https://splunkbase.splunk.com/app/1841)

---

### UC-13.2.35 · ITSI License and Capacity Utilization
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity
- **Value:** ITSI licensing is based on entity count and KPI volume. Tracking utilization prevents license overages and supports capacity planning for service expansion.
- **App/TA:** Splunk ITSI
- **Premium Apps:** Splunk IT Service Intelligence (ITSI)
- **Data Sources:** `itsi_entities` lookup, `itsi_summary`, `index=_internal`
- **SPL:** *(Run in the ITSI app context or use your deployment’s fully qualified `itsi_entities` lookup path so the lookup resolves.)*
```spl
| inputlookup itsi_entities
| stats dc(_key) as total_entities
| appendcols [
  | rest /servicesNS/nobody/SA-ITOA/itoa_interface/service
  | stats count as total_services
]
| appendcols [
  | rest /servicesNS/nobody/SA-ITOA/itoa_interface/kpi_base_search
  | stats count as total_base_searches
]
| table total_entities total_services total_base_searches
```
- **Implementation:** Monitor entity count against license tier. Track KPI count growth over time. Project when the next license tier will be needed. Identify unused or orphaned entities for cleanup. Monitor base search count and execution time as a proxy for ITSI compute load.
- **Visualization:** Single value (entity count vs license limit), Line chart (entity growth trend), Table (entity count by type).
- **CIM Models:** N/A

- **References:** [Splunk ITSI](https://splunkbase.splunk.com/app/1841)

---

### UC-13.2.36 · Azure Log Analytics Workspace Ingestion Health
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance, Capacity
- **Value:** Azure Log Analytics Workspace is the central logging destination for Azure Monitor, Defender for Cloud, and Sentinel. Ingestion lag or data cap throttling silently breaks alerting and investigation workflows across the entire Azure monitoring stack.
- **App/TA:** `Splunk_TA_microsoft-cloudservices` (Azure Monitor metrics)
- **Data Sources:** `sourcetype=azure:monitor:metric` (Microsoft.OperationalInsights/workspaces)
- **SPL:**
```spl
index=cloud sourcetype="azure:monitor:metric" resource_type="microsoft.operationalinsights/workspaces"
| where metric_name IN ("IngestionRate","IngestionLatencyInSeconds","DataBytes","BillableDataGB")
| timechart span=5m avg(average) as value by metric_name, resource_name
```
- **Implementation:** Collect Azure Monitor metrics for Log Analytics workspaces. Key metrics: `IngestionLatencyInSeconds` (alert >300s — indicates data delay for all downstream analytics), `IngestionRate` (sudden drops mean data sources stopped sending), and `BillableDataGB` versus daily cap (when cap is hit, ingestion stops until reset). Track per-table ingestion volume using workspace diagnostic settings to identify data spikes.
- **Visualization:** Line chart (ingestion latency and rate), Gauge (daily volume vs. cap), Table (top tables by volume).
- **CIM Models:** N/A

- **References:** [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)

---

### UC-13.2.37 · Entity-Level Multivariate Anomaly Detection (MLTK + ITSI)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔴 Expert
- **Monitoring type:** Performance, Fault
- **Value:** ITSI's adaptive thresholds evaluate KPIs individually per service. But many real incidents manifest as subtle, simultaneous deviations across multiple KPIs for a single entity — CPU slightly elevated, memory climbing, response time drifting up. Per-entity multivariate anomaly detection via MLTK catches these correlated degradation patterns before any single KPI breaches its threshold, providing minutes of early warning for cascading failures.
- **App/TA:** Splunk Machine Learning Toolkit (MLTK), Splunk IT Service Intelligence (ITSI)
- **Premium Apps:** Splunk IT Service Intelligence (ITSI)
- **Data Sources:** `itsi_summary` (per-entity KPI values)
- **SPL:**
```spl
index=itsi_summary is_service_aggregate=0 is_entity_in_maintenance=0
    kpi_name IN ("CPU Utilization","Memory Usage","Response Time","Error Rate","Disk IO Wait")
| bin _time span=5m
| stats avg(alert_value) as val by _time, entity_key, entity_title, kpi_name
| xyseries _time+"|"+entity_key kpi_name val
| fillnull value=0
| fit DensityFunction "CPU Utilization" "Memory Usage" "Response Time" "Error Rate" "Disk IO Wait" by entity_key into entity_multivariate_model
| where isOutlier > 0
| eval composite_score=round('CPU Utilization' + 'Memory Usage' + 'Response Time' + 'Error Rate', 2)
| sort -composite_score
| table _time, entity_key, "CPU Utilization", "Memory Usage", "Response Time", "Error Rate", "Disk IO Wait", composite_score
```
- **Implementation:** Extract entity-level KPI data from `itsi_summary` for all monitored KPIs within a service. Pivot into wide format (one column per KPI) per entity per time bin. Train DensityFunction models per entity that learn the joint distribution of their KPI values. Schedule the detection search every 5 minutes. Outliers represent entities where the combination of KPI values is unusual, even if each individual KPI is within its threshold. Feed the anomaly score back into ITSI as a synthetic "Entity Health Anomaly" KPI that contributes to the service health score. Alert service owners via ITSI notable event rules when the composite anomaly persists for 3+ consecutive windows. Retrain models weekly; use entity groups (by service or tier) if per-entity training data is sparse.
- **Visualization:** Radar chart (KPI values for anomalous entity), Line chart (composite anomaly score over time), Table (top anomalous entities with KPI breakdown).
- **CIM Models:** N/A

- **References:** [Splunk IT Service Intelligence](https://splunkbase.splunk.com/app/1841)

---

### UC-13.2.38 · Causal KPI Ranking — Root-Cause Acceleration (MLTK + ITSI)
- **Criticality:** 🟠 High
- **Difficulty:** 🔴 Expert
- **Monitoring type:** Performance
- **Value:** When a parent service health score drops, operators must manually investigate child KPIs to find the root cause. A trained model that ranks which child KPIs best explain parent health changes accelerates root-cause analysis from minutes to seconds — showing "memory pressure on the database tier explains 68% of the service degradation" instead of requiring manual drill-down through dozens of KPIs.
- **App/TA:** Splunk Machine Learning Toolkit (MLTK), Splunk IT Service Intelligence (ITSI)
- **Premium Apps:** Splunk IT Service Intelligence (ITSI)
- **Data Sources:** `itsi_summary` (service-level and KPI-level health scores)
- **SPL:**
```spl
index=itsi_summary is_service_aggregate=1
| eval parent_health=alert_level
| join type=left service_id _time
    [search index=itsi_summary is_service_aggregate=0
    | stats avg(alert_value) as kpi_val by _time, service_id, kpi_name]
| xyseries _time+"|"+service_id kpi_name kpi_val
| fillnull value=0
| fit RandomForestRegressor parent_health from * into causal_kpi_model
| summary causal_kpi_model
| sort -importance
| head 10
| table feature, importance
```
- **Implementation:** Collect time-aligned parent service health scores and all child KPI values from `itsi_summary`. Train a RandomForestRegressor or GradientBoostedTrees model where the target variable is the parent health score and features are individual KPI values. Extract feature importance rankings to identify which KPIs most strongly influence parent health. Publish the ranked KPI list as a lookup that Glass Tables and Deep Dives reference for "top contributing KPIs" context. Retrain monthly or after service tree changes. For real-time use, apply the pre-trained model to current KPI snapshots and display the top-3 contributing KPIs alongside each degraded service on the NOC Glass Table. Consider using Shapley values (via DSDL) for more accurate per-incident causal attribution.
- **Visualization:** Bar chart (KPI feature importance), Table (top causal KPIs per service), Sankey (parent health → child KPI contributions).
- **CIM Models:** N/A

- **References:** [Splunk IT Service Intelligence](https://splunkbase.splunk.com/app/1841)

---

### 13.3 Third-Party Monitoring Integration

**Primary App/TA:** Custom webhook/API inputs, Prometheus remote write receiver, SNMP trap receiver.

---

### UC-13.3.1 · Nagios/Zabbix Alert Ingestion
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Consolidating legacy monitoring alerts into Splunk enables cross-tool correlation and single-pane-of-glass operations.
- **App/TA:** Custom webhook input, syslog
- **Data Sources:** Nagios/Zabbix webhook exports, syslog notifications
- **SPL:**
```spl
index=monitoring sourcetype="nagios:notification" OR sourcetype="zabbix:webhook"
| stats count by host, service, state, severity
| sort -count
```
- **Implementation:** Configure Nagios/Zabbix to send alerts to Splunk via webhook or syslog. Normalize alert fields (host, service, severity, state) using CIM. Correlate with Splunk-native monitoring. Phase out legacy tools over time.
- **Visualization:** Table (third-party alerts), Bar chart (alerts by source tool), Status grid (host × service).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-13.3.2 · Prometheus Metric Ingestion
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Ingesting Prometheus metrics into Splunk enables long-term storage, cross-domain correlation, and unified dashboarding.
- **App/TA:** OpenTelemetry Collector, Prometheus remote write
- **Data Sources:** Prometheus remote write endpoint, OpenTelemetry metrics
- **SPL:**
```spl
| mstats avg(_value) WHERE index=prometheus metric_name="node_cpu_seconds_total" by host span=5m
```
- **Implementation:** Configure Prometheus remote_write to Splunk's metrics endpoint or use OpenTelemetry Collector as intermediary. Ingest as Splunk metrics. Use `mstats` for efficient querying. Create unified dashboards combining Prometheus and Splunk data.
- **Visualization:** Line chart (metric trends), Multi-metric dashboard, Table (metric summaries).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-13.3.3 · PagerDuty/Opsgenie Integration
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Tracking alert lifecycle and on-call response metrics ensures incident response SLAs are met and identifies process improvements.
- **App/TA:** PagerDuty API input
- **Data Sources:** PagerDuty incidents API, Opsgenie alerts API
- **SPL:**
```spl
index=pagerduty sourcetype="pagerduty:incident"
| eval ack_time_min=round((acknowledged_at_epoch-created_at_epoch)/60,1)
| stats avg(ack_time_min) as avg_ack, avg(resolved_at_epoch-created_at_epoch)/60 as avg_resolve by service
```
- **Implementation:** Poll PagerDuty/Opsgenie API for incident data. Track acknowledgment time, resolution time, and escalation rates. Report on on-call workload distribution. Alert when acknowledgment SLA is breached.
- **Visualization:** Bar chart (MTTA by service), Line chart (incident volume trend), Table (open incidents), Single value (avg MTTA).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-13.3.4 · Monitoring Coverage Gap Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🔴 Expert
- **Monitoring type:** Compliance
- **Value:** Hosts not covered by any monitoring tool are blind spots. Detection ensures comprehensive infrastructure visibility.
- **App/TA:** Cross-tool asset correlation
- **Data Sources:** CMDB + all monitoring tool inventories
- **SPL:**
```spl
| inputlookup cmdb_hosts.csv
| join type=left max=1 hostname [search index=_internal group=tcpin_connections | stats latest(_time) as splunk_last by hostname]
| join type=left max=1 hostname [search index=edr sourcetype="*sensor*" | stats latest(_time) as edr_last by hostname]
| where isnull(splunk_last) AND isnull(edr_last)
| table hostname, os, department
```
- **Implementation:** Cross-reference CMDB with all monitoring tool inventories (Splunk forwarders, EDR agents, SNMP targets). Identify assets not monitored by any tool. Alert on new unmonitored assets. Track coverage percentage as a KPI.
- **Visualization:** Table (unmonitored hosts), Single value (coverage %), Pie chart (monitored vs unmonitored), Bar chart (gaps by department).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-13.3.5 · Alert Storm Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Anomaly
- **Value:** Correlated alert storms across monitoring tools indicate major incidents. Detection enables rapid escalation and noise reduction.
- **App/TA:** Multi-source alert correlation
- **Data Sources:** All monitoring tool alerts ingested into Splunk
- **SPL:**
```spl
index=alerts sourcetype=*
| timechart span=5m count as alert_count
| where alert_count > 50
| eval storm="Alert storm detected"
```
- **Implementation:** Ingest alerts from all monitoring tools into a common index. Track alert rate across all sources. Alert when rate exceeds normal baseline by >5× (indicates correlated event). Use ITSI Event Analytics for intelligent grouping.
- **Visualization:** Line chart (alert rate across all sources), Single value (current alert rate), Timeline (alert storm events), Table (contributing alerts).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-13.3.6 · SLO Burn Rate and Error Budget Tracking
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Burn rate and error budget show how fast SLO is consumed. Tracking supports proactive action before SLA breach and prioritization of reliability work.
- **App/TA:** ITSI, custom SLO metrics, APM data
- **Data Sources:** SLO compliance metrics, error budget calculations
- **SPL:**
```spl
index=slos sourcetype="slo:compliance"
| eval burn_rate=1-(success_count/(success_count+failure_count))
| bin _time span=1h
| stats avg(burn_rate) as avg_burn, sum(error_budget_consumed) as consumed by service, slo_name, _time
| where avg_burn > 0.1
```
- **Implementation:** Compute SLO compliance and error budget from availability/latency data. Ingest into Splunk. Alert on burn rate above threshold or error budget exhaustion. Report on remaining budget by service.
- **Visualization:** Gauge (error budget remaining), Line chart (burn rate), Table (services by budget consumed).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-13.3.7 · Distributed Trace Sampling and Coverage
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Trace sampling rate and coverage affect observability. Monitoring sampling decisions and trace completeness supports tuning and gap detection.
- **App/TA:** APM/tracing TAs (Jaeger, Tempo, OTLP)
- **Data Sources:** Trace metadata, sampling flags, span counts per trace
- **SPL:**
```spl
index=traces sourcetype="trace:span"
| bin _time span=1h
| stats count as spans, dc(trace_id) as traces, avg(sample_rate) as avg_sample by service, _time
| eval spans_per_trace=spans/traces
| where spans_per_trace < 5 OR avg_sample < 0.01
```
- **Implementation:** Ingest trace metadata and sampling rates. Alert when sampling drops below target or trace completeness (spans per trace) is low for critical services. Report on coverage by service and env.
- **Visualization:** Line chart (sampling rate by service), Table (low-coverage services), Bar chart (spans per trace).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-13.3.8 · Log Ingestion Backlog and Lag
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Ingestion backlog or lag causes delayed alerting and search. Monitoring lag per source ensures data freshness and pipeline health.
- **App/TA:** Splunk _internal, forwarder metrics
- **Data Sources:** Indexer acknowledgment, forwarder queue depth, event timestamps
- **SPL:**
```spl
index=_internal source=*metrics* group=queue
| stats latest(current_size) as queue_depth by host, name
| where queue_depth > 1000
| table host, name, queue_depth
```
- **Implementation:** Monitor forwarder and indexer queue metrics. Alert when queue depth or event lag (now - event time) exceeds threshold. Report on lag by source and index.
- **Visualization:** Table (hosts with backlog), Single value (max lag minutes), Line chart (queue depth trend).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-13.3.9 · Dashboard and Saved Search Usage Analytics
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Usage of dashboards and saved searches guides optimization and retirement. Analytics support adoption and reduce stale or unused content.
- **App/TA:** Splunk audit logs, usage metadata
- **Data Sources:** Dashboard view and search run audit logs
- **SPL:**
```spl
index=_audit action=view OR action=run
| search (resource_type="dashboard" OR resource_type="saved_search")
| stats count by user, resource_name, resource_type
| sort -count
```
- **Implementation:** Ingest Splunk audit or usage logs for dashboard and search runs. Report on most/least used dashboards and searches. Identify unused content for archival. Track adoption by team.
- **Visualization:** Bar chart (views by dashboard), Table (search run count by name), Pie chart (usage by user).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-13.3.10 · Synthetic Check Failure and Geographic Variance
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Synthetic checks validate user-facing availability. Failure or variance by geography highlights regional issues and CDN/edge health.
- **App/TA:** Synthetic monitoring product logs, Splunk HTTP Event Collector
- **Data Sources:** Synthetic check results, response time, status by location
- **SPL:**
```spl
index=synthetic sourcetype="synthetic:check"
| where success="false" OR response_time_ms > 5000
| bin _time span=15m
| stats count, avg(response_time_ms) as avg_ms by check_name, location, _time
| sort -count
```
- **Implementation:** Ingest synthetic check results from Datadog, Pingdom, or custom scripts. Alert on failure or latency above threshold. Compare success rate and latency by region. Report on SLA by check and location.
- **Visualization:** Table (failed checks by location), Geo map (failure by region), Line chart (latency by location).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-13.3.11 · Prometheus Target Scrape Failures
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Targets down or unreachable; gaps in metrics collection.
- **App/TA:** Custom (Prometheus /api/v1/targets)
- **Data Sources:** Prometheus targets API, up metric
- **SPL:**
```spl
index=prometheus sourcetype="prometheus:targets" health="down"
| stats latest(_time) as last_check, values(job) as job, values(instance) as instance by scrapeUrl
| eval down_since=round((now()-last_check)/60,0)
| table scrapeUrl, job, instance, down_since
| sort -down_since
```
- **Implementation:** Poll Prometheus `/api/v1/targets` via scripted input or HTTP Event Collector. Parse JSON response and index target health (up/down), last scrape time, and last error. Alternatively, ingest `up` metric (value 0 = down) from Prometheus remote write. Alert when any target has been down >5 minutes. Track scrape duration and failure reasons (connection refused, timeout, DNS) for root cause analysis.
- **Visualization:** Table (down targets with duration), Status grid (job × instance health), Single value (targets down count), Line chart (scrape failure rate over time).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-13.3.12 · Prometheus TSDB Compaction Failures
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Fault
- **Value:** Storage engine issues impacting metric retention.
- **App/TA:** Custom (Prometheus /api/v1/status/tsdb, prometheus logs)
- **Data Sources:** Prometheus TSDB stats, server logs
- **SPL:**
```spl
index=prometheus (sourcetype="prometheus:tsdb" OR sourcetype="prometheus:log")
| search "compaction" AND ("failed" OR "error" OR "panic")
| stats count, latest(_time) as last_occurrence by host, message
| eval last_occurrence_human=strftime(last_occurrence,"%Y-%m-%d %H:%M:%S")
| table host, message, count, last_occurrence_human
| sort -count
```
- **Implementation:** Poll Prometheus `/api/v1/status/tsdb` for head stats, block count, and retention info. Ingest Prometheus server logs (stderr) for compaction-related errors. Parse TSDB head chunk count and series count for anomaly detection. Alert on compaction failure messages or when head series count grows abnormally (potential compaction backlog). Correlate with disk I/O and storage capacity metrics.
- **Visualization:** Table (compaction errors by host), Single value (TSDB health status), Line chart (head series count trend), Bar chart (block count by retention).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-13.3.13 · Grafana Datasource Health
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Datasource connectivity and query errors; broken dashboards.
- **App/TA:** Custom (Grafana API)
- **Data Sources:** Grafana /api/datasources/proxy/:id, health check endpoint
- **SPL:**
```spl
index=grafana sourcetype="grafana:datasource"
| where status!="success" OR response_time_ms > 3000
| stats count, avg(response_time_ms) as avg_ms, values(error_message) as errors by datasource_name, datasource_type, host
| sort -count
```
- **Implementation:** Use scripted input or scheduled search to call Grafana `/api/datasources` and `/api/datasources/proxy/:id/health` (or datasource-specific health endpoints). Ingest response status, latency, and error messages. Alternatively, parse Grafana server logs for datasource query errors. Alert when any datasource fails health check or when error rate exceeds threshold. Track which dashboards use each datasource for impact assessment.
- **Visualization:** Table (unhealthy datasources with errors), Status grid (datasource × status), Single value (healthy datasource count), Line chart (datasource latency trend).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-13.3.14 · OpenTelemetry Collector Dropped Spans and Metrics
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** Collector queue pressure causing data loss.
- **App/TA:** Custom (OTel Collector metrics)
- **Data Sources:** OTel Collector internal metrics (otelcol_exporter_send_failed_spans, otelcol_processor_dropped_metric_points)
- **SPL:**
```spl
| mstats avg(_value) WHERE index=otel_collector metric_name IN ("otelcol_exporter_send_failed_spans", "otelcol_processor_dropped_metric_points", "otelcol_exporter_send_failed_metric_points") BY metric_name, exporter, processor span=5m
| where _value > 0
| timechart span=5m sum(_value) as dropped by metric_name
```
- **Implementation:** Scrape OpenTelemetry Collector's internal metrics endpoint (default :8888/metrics) via Prometheus or OTLP. Ingest `otelcol_exporter_send_failed_spans`, `otelcol_processor_dropped_metric_points`, `otelcol_exporter_send_failed_metric_points`, and `otelcol_processor_dropped_spans`. Alert when any dropped/failed count >0 for critical pipelines. Correlate with `otelcol_receiver_accepted_spans` and queue depth metrics to identify backpressure. Tune batch size, retries, or add more collector replicas.
- **Visualization:** Line chart (dropped spans/metrics over time), Table (dropped by exporter/processor), Single value (total dropped in last hour), Bar chart (dropped by pipeline).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-13.3.15 · OpenTelemetry Collector Pipeline Throughput and Backpressure
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance, Fault
- **Value:** The OTel Collector is a single point of failure for observability data. When exporters can't keep up with receiver intake, the batch processor queue fills and backpressure propagates upstream — first dropping low-priority data, then refusing new data entirely. By the time you notice missing traces in your backend, thousands of spans are already lost. Monitoring pipeline throughput and queue saturation in real-time catches backpressure within minutes, before it becomes data loss.
- **App/TA:** Splunk Distribution of OpenTelemetry Collector, Prometheus remote write, custom HEC
- **Data Sources:** OTel Collector internal metrics (`otelcol_receiver_accepted_*`, `otelcol_exporter_queue_size`, `otelcol_exporter_queue_capacity`, `otelcol_processor_batch_*`)
- **SPL:**
```spl
| mstats latest(_value) as val WHERE index=otel_metrics metric_name IN (
    "otelcol_receiver_accepted_spans",
    "otelcol_receiver_accepted_metric_points",
    "otelcol_receiver_accepted_log_records",
    "otelcol_exporter_queue_size",
    "otelcol_exporter_queue_capacity",
    "otelcol_exporter_sent_spans",
    "otelcol_exporter_sent_metric_points"
  ) BY metric_name, service_instance_id, exporter, receiver span=1m
| eval signal_type=case(
    match(metric_name, "spans"), "traces",
    match(metric_name, "metric"), "metrics",
    match(metric_name, "log"), "logs")
| eval component=case(
    match(metric_name, "receiver"), "receiver",
    match(metric_name, "exporter_queue"), "queue",
    match(metric_name, "exporter_sent"), "exporter")
| xyseries _time, metric_name, val
| eval queue_pct=round('otelcol_exporter_queue_size'*100/'otelcol_exporter_queue_capacity', 1)
| where queue_pct > 70
| table _time, service_instance_id, exporter, queue_pct, otelcol_exporter_queue_size, otelcol_exporter_queue_capacity
| sort -queue_pct
```
- **Implementation:** Every OTel Collector instance exposes internal metrics on `:8888/metrics` by default. Scrape these metrics using a second collector or Prometheus federation, then forward to Splunk via OTLP or Prometheus remote write. Key metrics: `otelcol_receiver_accepted_*` (input throughput by signal type), `otelcol_exporter_queue_size` / `queue_capacity` (export queue saturation), `otelcol_exporter_sent_*` (output throughput), and `otelcol_processor_batch_batch_send_size` (batch efficiency). Alert at 70% queue saturation (warning) and 90% (critical). Track the ratio of accepted to sent — divergence indicates data accumulation or loss. Label each collector instance by `service_instance_id` to identify which replica is under pressure. Common remediation: increase queue size, add collector replicas, tune batch processor `send_batch_size` and `timeout`, or reduce exporter concurrency.
- **Visualization:** Line chart (queue saturation % per collector), Area chart (received vs sent throughput by signal), Gauge (peak queue saturation), Table (collectors above 70% queue).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-13.3.16 · OpenTelemetry Collector Memory and CPU Utilization
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance, Fault
- **Value:** OTel Collectors are Go processes that can OOM-kill under sustained load or memory leaks, especially with processors like `groupbytrace` or `tail_sampling` that hold data in memory. A killed collector creates a gap in observability data exactly when you need it most — during incidents. Tracking heap allocation growth patterns and CPU utilization catches runaway collectors before the OOM killer does.
- **App/TA:** Splunk Distribution of OpenTelemetry Collector
- **Data Sources:** OTel Collector process metrics (`process_runtime_*`, `runtime.uptime`)
- **SPL:**
```spl
| mstats latest(_value) as val WHERE index=otel_metrics metric_name IN (
    "process_runtime_total_alloc_bytes",
    "process_runtime_heap_alloc_bytes",
    "process_cpu_seconds",
    "runtime.uptime"
  ) BY metric_name, service_instance_id span=5m
| eval metric_short=replace(metric_name, "process_runtime_|process_", "")
| xyseries _time, metric_short, val
| eval heap_mb=round(heap_alloc_bytes/1048576, 1)
| streamstats window=6 avg(heap_mb) as avg_heap_mb by service_instance_id
| eval heap_growth_pct=round((heap_mb - avg_heap_mb)*100/avg_heap_mb, 1)
| where heap_mb > 512 OR heap_growth_pct > 30
| table _time, service_instance_id, heap_mb, avg_heap_mb, heap_growth_pct
| sort -heap_mb
```
- **Implementation:** OTel Collectors emit Go runtime metrics by default: `process_runtime_heap_alloc_bytes` (current heap usage), `process_runtime_total_alloc_bytes` (cumulative allocations), `process_cpu_seconds` (CPU time), and `runtime.uptime` (time since start). Ingest via the collector's internal metrics pipeline. Set memory limits using `memory_limiter` processor in collector config (recommended: 80% of container memory limit). Alert when heap exceeds 512 MB (adjust based on deployment sizing) or shows >30% growth over 30-minute rolling average. Short uptimes (<5 minutes) combined with high allocation rates indicate crash-restart loops. Correlate with Kubernetes pod restarts (UC-3.2.1) if collectors run as DaemonSets. Track CPU utilization against collector pod resource requests to identify under-provisioned instances.
- **Visualization:** Line chart (heap MB per collector over 24 hours), Area chart (CPU seconds rate), Table (collectors exceeding memory threshold), Single value (collector with highest heap).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-13.3.17 · OpenTelemetry Collector Configuration Drift Detection
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance, Fault
- **Value:** In a fleet of dozens or hundreds of OTel Collector instances (DaemonSets, gateway deployments, agent sidecars), configuration inconsistency causes silent observability failures. One collector running a stale config may be missing a processor, dropping a signal type, or exporting to a decommissioned endpoint — while appearing healthy. Configuration drift detection ensures every collector runs the intended config after rollouts, preventing partial observability gaps.
- **App/TA:** Splunk Distribution of OpenTelemetry Collector, Kubernetes ConfigMap tracking
- **Data Sources:** OTel Collector config hash (custom metric or log), `sourcetype=kube:events` (ConfigMap updates)
- **SPL:**
```spl
index=otel_metrics sourcetype="otel:collector:info"
| stats latest(config_hash) as config_hash, latest(collector_version) as version, latest(_time) as last_seen by service_instance_id, host, k8s_namespace
| eventstats dc(config_hash) as unique_configs, mode(config_hash) as expected_hash
| eval drifted=if(config_hash!=expected_hash, "Yes", "No")
| eval stale_hours=round((now()-last_seen)/3600, 1)
| where drifted="Yes" OR stale_hours > 1
| table service_instance_id, host, k8s_namespace, config_hash, expected_hash, drifted, version, stale_hours
| sort drifted, -stale_hours
```
- **Implementation:** Add a custom processor or extension to each collector that computes a SHA-256 hash of the active configuration and emits it as a metric attribute or log event on startup and at regular intervals (every 5 minutes). Alternatively, use the `zpages` extension to expose config and scrape it. Store the expected config hash in a KV store lookup, updated when deployments roll out. Compare each collector's reported hash against the expected value. Alert when any collector reports a different hash after a rollout window (30 minutes). Also detect stale collectors that haven't reported recently — these may have crashed without restarting. For Kubernetes deployments, correlate with ConfigMap update events to verify that DaemonSet pods restarted after config changes.
- **Visualization:** Single value (collectors with drift), Table (drifted instances with config hash comparison), Pie chart (config version distribution), Timeline (config rollout events).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-13.3.18 · OpenTelemetry Receiver Health by Signal Type
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability, Fault
- **Value:** Each OTel Collector receiver (OTLP, Jaeger, Prometheus, filelog, hostmetrics) independently accepts or refuses data by signal type (traces, metrics, logs). A receiver that starts refusing spans while accepting metrics indicates endpoint-specific authentication failures, protocol mismatches, or resource exhaustion on a single pipeline. Per-receiver, per-signal health monitoring pinpoints exactly which instrumentation endpoint is broken, reducing MTTR from "something is wrong with observability" to "the Jaeger receiver on collector-5 is refusing spans due to gRPC auth errors."
- **App/TA:** Splunk Distribution of OpenTelemetry Collector
- **Data Sources:** OTel Collector internal metrics (`otelcol_receiver_accepted_*`, `otelcol_receiver_refused_*`)
- **SPL:**
```spl
| mstats latest(_value) as val WHERE index=otel_metrics metric_name IN (
    "otelcol_receiver_accepted_spans",
    "otelcol_receiver_refused_spans",
    "otelcol_receiver_accepted_metric_points",
    "otelcol_receiver_refused_metric_points",
    "otelcol_receiver_accepted_log_records",
    "otelcol_receiver_refused_log_records"
  ) BY metric_name, receiver, transport, service_instance_id span=5m
| eval signal=case(match(metric_name,"spans"),"traces", match(metric_name,"metric"),"metrics", match(metric_name,"log"),"logs")
| eval status=if(match(metric_name,"refused"), "refused", "accepted")
| stats sum(val) as total by _time, receiver, signal, status, service_instance_id
| xyseries _time, status, total
| eval refuse_pct=round(refused*100/(accepted+refused), 2)
| where refused > 0
| table _time, receiver, signal, service_instance_id, accepted, refused, refuse_pct
| sort -refuse_pct
```
- **Implementation:** OTel Collector emits `otelcol_receiver_accepted_*` and `otelcol_receiver_refused_*` metrics per receiver and transport (grpc, http). Refused data indicates the collector rejected incoming telemetry — causes include: authentication failure, payload too large, receiver shutting down, or unsupported format. Alert when refuse rate exceeds 0% for any receiver/signal combination (any refusal is abnormal). Correlate with collector logs for the specific error reason. Track accepted counts to detect instrumentation gaps: if a receiver that normally accepts 10K spans/minute suddenly drops to zero, the upstream service likely lost connectivity. Build a receiver health matrix showing each receiver × signal type × collector instance status for fleet-wide visibility.
- **Visualization:** Heatmap (receiver × signal health status), Line chart (accepted vs refused per receiver), Table (receivers with refusals), Single value (total active receivers).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-13.3.19 · OpenTelemetry Exporter Retry and Timeout Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault, Performance
- **Value:** OTel Collector exporters retry failed sends with exponential backoff. Persistent retry failures indicate backend unavailability, authentication expiry, or network partitions. Timeouts indicate backend performance degradation that slows the entire pipeline. Monitoring retry counts and timeout rates per exporter and destination prevents the cascade where a slow backend fills queues, triggers backpressure, and ultimately causes data loss across all signals — not just the one with the failing backend.
- **App/TA:** Splunk Distribution of OpenTelemetry Collector
- **Data Sources:** OTel Collector internal metrics (`otelcol_exporter_send_failed_*`, `otelcol_exporter_sent_*`), collector logs
- **SPL:**
```spl
| mstats sum(_value) as val WHERE index=otel_metrics metric_name IN (
    "otelcol_exporter_send_failed_spans",
    "otelcol_exporter_send_failed_metric_points",
    "otelcol_exporter_send_failed_log_records",
    "otelcol_exporter_sent_spans",
    "otelcol_exporter_sent_metric_points",
    "otelcol_exporter_sent_log_records"
  ) BY metric_name, exporter, service_instance_id span=5m
| eval signal=case(match(metric_name,"spans"),"traces", match(metric_name,"metric"),"metrics", match(metric_name,"log"),"logs")
| eval status=if(match(metric_name,"failed"), "failed", "sent")
| stats sum(val) as total by _time, exporter, signal, status, service_instance_id
| xyseries _time, status, total
| eval failure_pct=round(failed*100/nullif(sent+failed, 0), 2)
| where failed > 0
| table _time, exporter, signal, service_instance_id, sent, failed, failure_pct
| sort -failure_pct
```
- **Implementation:** OTel Collector exporters emit `otelcol_exporter_send_failed_*` counters per signal type and exporter name. These increment on each failed send attempt (including retries). Track failure percentage per exporter: sustained failures above 1% indicate a backend problem requiring investigation. Check collector logs for specific error codes: 429 (rate limited), 503 (backend overloaded), context deadline exceeded (timeout), and TLS handshake failures. For Splunk HEC exporters, correlate with HEC endpoint health (UC-13.1.12). For OTLP exporters, verify the receiving collector or backend is healthy. Alert when any exporter shows failures for more than 10 consecutive minutes. Monitor the retry queue: exporters with `retry_on_failure` enabled accumulate data during transient failures, but persistent failures eventually hit `max_elapsed_time` and data is dropped permanently.
- **Visualization:** Line chart (failure rate per exporter over 24 hours), Table (exporters with active failures), Bar chart (failures by signal type and exporter), Single value (exporters currently healthy vs failing).
- **CIM Models:** N/A

- **References:** [Splunk Enterprise Security](https://splunkbase.splunk.com/app/263)

---

### 13.3.TE Cisco ThousandEyes — Platform Integration

---

### 13.4 AI & LLM Observability

**Primary App/TA:** Splunk OpenTelemetry Collector, Azure OpenAI / OpenAI log exports, custom HEC for LLM gateways, ESCU (Splunk Enterprise Security Content Update), Microsoft 365 / Copilot audit connectors.

---

### UC-13.4.1 · LLM API Latency and Error Rate (OpenAI, Azure OpenAI)
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance, Fault
- **Value:** High latency or error rates on managed LLM endpoints directly impact user experience and SLOs; tracking both by model and region isolates provider issues versus client misuse.
- **App/TA:** Azure Monitor Add-on, custom OpenAI proxy logs, HEC
- **Data Sources:** `sourcetype=openai:api`, `sourcetype=azure:openai`
- **SPL:**
```spl
index=ai_ops (sourcetype="openai:api" OR sourcetype="azure:openai")
| eval failed=if(status>=400 OR isnotnull(error_code),1,0)
| timechart span=5m avg(latency_ms) as avg_latency p99(latency_ms) as p99_latency sum(failed) as errors count as calls
| eval error_rate_pct=round(100*errors/calls,2)
```
- **Implementation:** Ingest REST proxy or provider diagnostic logs with HTTP status, `latency_ms`, model id, deployment, and region. Normalize field names across OpenAI and Azure OpenAI. Alert when p99 latency or error rate exceeds baselines. Track 429 separately if you manage quota.
- **Visualization:** Line chart (latency p99, error rate), Single value (SLO burn), Table (top failing models/regions).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-13.4.2 · Token Usage and Cost per Model and Application
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity, Compliance
- **Value:** Token spend ties directly to budget and chargeback; per-application and per-model views prevent surprise bills and highlight inefficient prompts or runaway automation.
- **App/TA:** Custom billing export, OpenAI Usage API → HEC
- **Data Sources:** `sourcetype=openai:api`, `sourcetype=azure:openai`
- **SPL:**
```spl
index=ai_ops (sourcetype="openai:api" OR sourcetype="azure:openai")
| eval prompt_tokens=coalesce(prompt_tokens,0), completion_tokens=coalesce(completion_tokens,0)
| eval total_tokens=prompt_tokens+completion_tokens
| eval est_cost_usd=round((total_tokens/1000)*coalesce(price_per_1k_tokens,0.002),4)
| stats sum(total_tokens) as tokens sum(est_cost_usd) as cost_usd by app_id, model
| sort -cost_usd
```
- **Implementation:** Ensure each request carries `app_id` or API key alias. Ingest usage records with token counts; join a lookup table for price per model per 1k tokens (refresh monthly). Schedule daily cost reports and threshold alerts for tenants or apps.
- **Visualization:** Bar chart (cost by app), Treemap (cost by model), Table (tokens and cost detail).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-13.4.3 · GPU and TPU Utilization for Inference Workloads
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance, Capacity
- **Value:** Underutilized accelerators waste capex; saturated GPUs increase queue time and latency for inference—utilization guides autoscaling and instance right-sizing.
- **App/TA:** Splunk OTel Collector, NVIDIA DCGM exporter, Kubernetes metrics
- **Data Sources:** `sourcetype=otel:metrics`
- **SPL:**
```spl
index=infra sourcetype="otel:metrics" (metric_name="gpu.utilization" OR metric_name="dcgm.gpu.utilization")
| bin _time span=1m
| stats avg(value) as gpu_util by _time, host, gpu_id
| where gpu_util > 90 OR gpu_util < 15
| timechart span=15m avg(gpu_util) by host
```
- **Implementation:** Scrape DCGM or cloud TPU metrics via OTel Prometheus receiver. Tag by cluster, pool, and model deployment. Alert on sustained high utilization (queue risk) or chronic low utilization (oversized nodes). Correlate with inference request rate from gateway logs if present.
- **Visualization:** Timechart (GPU %), Heatmap (GPU × host), Single value (cluster avg utilization).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-13.4.4 · Model Version Deployment Tracking
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Change, Compliance
- **Value:** Knowing which model revision serves production supports rollback, audit, and safety reviews when behavior or cost shifts after a rollout.
- **App/TA:** CI/CD webhooks, Kubernetes labels, LLM gateway config audit
- **Data Sources:** `sourcetype=openai:api`, `sourcetype=k8s:deployment`
- **SPL:**
```spl
(index=ai_ops sourcetype="openai:api") OR (index=platform sourcetype="k8s:deployment")
| eval model_id=coalesce(model, model_name, image_tag)
| stats latest(_time) as last_seen, latest(model_id) as current_model by deployment, namespace, environment
| sort environment, deployment
```
- **Implementation:** Log model id from inference gateway on each request; for self-hosted models, ingest deployment events with image tag or `MODEL_ID` env. Maintain a lookup of approved model versions per environment. Alert on requests referencing undeployed or deprecated model strings.
- **Visualization:** Table (environment × model version), Timeline (version changes), Single value (unapproved model calls).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-13.4.5 · AI Gateway Rate Limiting and Quota Management
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance, Security
- **Value:** Gateway limits protect backends and budgets; monitoring 429s and quota headers prevents one client from starving others and validates limit tuning.
- **App/TA:** Kong, Azure API Management, Envoy access logs → Splunk
- **Data Sources:** `sourcetype=openai:api`, `sourcetype=haproxy:access`
- **SPL:**
```spl
index=ai_ops sourcetype="openai:api"
| eval throttled=if(status=429 OR match(_raw,"(?i)rate.?limit"),1,0)
| stats sum(throttled) as throttled_reqs count as total by client_id, route
| eval throttle_pct=round(100*throttled_reqs/total,2)
| where throttle_pct > 5
| sort -throttle_pct
```
- **Implementation:** Centralize LLM traffic through an API gateway and log client identity, route, status, and optional `X-RateLimit-*` headers. Alert on rising 429 share per key or app. Feed quota resets into a small KV store for dashboards if headers are present.
- **Visualization:** Bar chart (429% by client), Line chart (throttled requests over time), Table (top limited routes).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-13.4.6 · Ollama Local LLM Abuse Detection (ESCU)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Security
- **Value:** Self-hosted Ollama endpoints can be probed or misused for bulk generation; correlating ESCU-style analytics with local logs catches abuse before resource exhaustion or data leakage.
- **App/TA:** ESCU (Analytic Story: Local LLM abuse patterns), Ollama HTTP logs
- **Data Sources:** `sourcetype=ollama:logs`
- **SPL:**
```spl
index=ai_ops sourcetype="ollama:logs"
| search path IN ("/api/generate","/api/chat")
| eventstats count as reqs_per_src by src
| where status>=400 OR duration_ms>60000 OR reqs_per_src>100
| eval suspicious=if(reqs_per_src>100,"high_volume",if(match(user_agent,"curl|python-requests"),"scripted","normal"))
| stats count, dc(path) as paths, values(user_agent) as ua by src, host, suspicious
| where count>50 OR match(ua,"(?i)(scanner|masscan)")
```
- **Implementation:** Forward Ollama access logs with client IP, path, model, duration, and status. Tune ESCU detections for unusual volume, off-hours spikes, and known scanner user agents. Block or rate-limit at the network edge based on Splunk alerts. Enrich with asset and identity lookups where available.
- **Visualization:** Map (source IPs), Table (suspicious sessions), Timeline (request bursts).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-13.4.7 · MCP Server Suspicious Activity Detection (ESCU)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Security
- **Value:** Model Context Protocol servers expose tools and data to agents; anomalous tool invocation or auth patterns may indicate compromise or prompt-driven misuse.
- **App/TA:** ESCU (custom correlation searches), MCP server audit logs
- **Data Sources:** `sourcetype=mcp:audit`
- **SPL:**
```spl
index=security sourcetype="mcp:audit"
| search tool_name IN ("filesystem.write","shell.exec","secrets.read") OR result="denied"
| eval risk=case(match(tool_name,"shell|filesystem|secrets"),"high",result="denied","medium",true(),"low")
| stats count by session_id, principal, tool_name, risk
| where risk="high" AND count>10
| sort -count
```
- **Implementation:** Emit structured MCP events: session, tool, args hash (not raw secrets), allow/deny, latency. Map to ESCU-compatible data models and run threshold and rare-process detections. Alert on denied high-risk tools, impossible travel for sessions, or burst tool calls from a single agent identity.
- **Visualization:** Table (high-risk tool calls), Sankey (tool flow), Timeline (session anomalies).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-13.4.8 · Microsoft 365 Copilot Data Exfiltration Risk (ESCU)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Security, Compliance
- **Value:** Copilot can surface sensitive content; monitoring risky prompts and large exports supports insider-threat and DLP alignment with Microsoft’s recommended logging.
- **App/TA:** Microsoft 365 Add-on, Microsoft Graph audit, ESCU (Microsoft Cloud content)
- **Data Sources:** `sourcetype=o365:audit`
- **SPL:**
```spl
index=o365 sourcetype="o365:audit" Workload="Copilot"
| search (Operation="CopilotInteraction" OR Operation="Search") AND (match(SensitivityLabel,"Highly Confidential") OR match(ObjectId,"(?i)export|download"))
| stats count by UserId, Operation, ObjectId
| where count>20
| sort -count
```
- **Implementation:** Ingest Copilot-related audit events and sensitivity labels from Purview where available. Tune for bulk retrieval, unusual Copilot sessions after privilege changes, and interactions with restricted sites. Align alerts with ESCU Microsoft 365 analytic stories and incident response playbooks.
- **Visualization:** Table (users and operations), Bar chart (events by label), Timeline (Copilot activity spikes).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-13.4.9 · LLM Prompt Injection Attempt Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Security
- **Value:** Injection attempts try to override system instructions or exfiltrate context; logging and alerting limits abuse before secrets or policies are bypassed.
- **App/TA:** LLM gateway with prompt logging (redacted), DLP on egress
- **Data Sources:** `sourcetype=openai:api`, `sourcetype=azure:openai`
- **SPL:**
```spl
index=ai_ops sourcetype IN ("openai:api","azure:openai")
| search match(lower(prompt_preview),"(ignore|disregard|system prompt|jailbreak|sudo mode|base64)")
| eval severity=if(match(prompt_preview,"(?i)(password|secret|api[_-]?key)"),"critical","high")
| stats count by user_id, app_id, severity
| where count>=3
| sort -count
```
- **Implementation:** Log truncated or hashed prompts server-side only (privacy review required). Use regex and optional ML classifiers for injection patterns. Route critical hits to SOC. Do not index full PII-heavy prompts without policy. Pair with response policy blocks.
- **Visualization:** Table (injection attempts), Single value (daily blocked prompts), Timeline (repeat offenders).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-13.4.10 · AI Model API Key Rotation Compliance
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance, Security
- **Value:** Stale API keys increase breach impact; proving rotation cadence supports security policy and vendor audits.
- **App/TA:** Secret manager audit (Vault, AWS Secrets Manager), key metadata sync
- **Data Sources:** `sourcetype=vault:audit`, `sourcetype=aws:cloudtrail`
- **SPL:**
```spl
index=security (sourcetype="vault:audit" OR sourcetype="aws:cloudtrail")
| search (operation="rotate" OR eventName="RotateSecret") AND match(_raw,"(?i)openai|azure.?openai|llm")
| stats latest(_time) as last_rotate by secret_path
| eval key_age_days=round((now()-last_rotate)/86400,0)
| where key_age_days > 90
| table secret_path, key_age_days
```
- **Implementation:** Track last rotation timestamp per logical key from your secret store. Join usage logs to key id if you issue per-app keys. Alert when age exceeds policy (e.g., 90 days since last rotation) or rotation job fails. Dashboard compliance percentage by business unit.
- **Visualization:** Table (keys past due), Single value (% compliant), Bar chart (age distribution).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-13.4.11 · LLM Output Content Policy Violation Logging
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance, Security
- **Value:** Provider and organizational safety filters block harmful content; logging violations supports red-teaming, policy tuning, and audit trails for regulated use cases.
- **App/TA:** Azure OpenAI content filter logs, OpenAI moderation API results
- **Data Sources:** `sourcetype=azure:openai`, `sourcetype=openai:api`
- **SPL:**
```spl
index=ai_ops (sourcetype="azure:openai" OR sourcetype="openai:api")
| search content_filter_result="blocked" OR finish_reason="content_filter" OR moderation_flagged="true"
| stats count by filter_category, model, app_id
| sort -count
```
- **Implementation:** Capture moderation and content-filter outcomes from API responses (categories, severity). Avoid storing blocked text; store hashes or length only if needed. Review spikes by app or model after prompt changes. Feed executive summary dashboards for AI governance.
- **Visualization:** Bar chart (violations by category), Line chart (trend), Table (top apps).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-13.4.12 · AI Inference Pipeline Error Rate
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** End-to-end inference includes preprocess, model call, and postprocess; pipeline-level error rates catch failures that raw HTTP 200s miss (e.g., empty generations, schema errors).
- **App/TA:** Application logs, OpenTelemetry traces
- **Data Sources:** `sourcetype=otel:metrics`
- **SPL:**
```spl
index=ai_ops sourcetype="otel:metrics" metric_name IN ("inference.pipeline.errors","inference.pipeline.requests")
| bin _time span=5m
| stats sum(eval(if(metric_name="inference.pipeline.errors",value,0))) as errors,
        sum(eval(if(metric_name="inference.pipeline.requests",value,0))) as reqs by _time, service.name
| eval err_rate=round(100*errors/nullif(reqs,0),3)
| where err_rate > 1
| timechart span=5m avg(err_rate) by service.name
```
- **Implementation:** Instrument each pipeline stage with OTel counters or structured logs (`stage`, `error_class`). Emit `inference.pipeline.errors` and `inference.pipeline.requests` counters per service. Alert on SLO burn for error rate. Correlate with deployments and model version changes.
- **Visualization:** Line chart (pipeline error rate), Table (errors by stage), Single value (SLO status).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-13.4.13 · Seq2Seq Log Anomaly Detection via Reconstruction Error (DSDL)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔴 Expert
- **Monitoring type:** Fault, Security
- **Value:** Traditional log monitoring relies on known patterns — regex, keywords, error codes. But novel failures, zero-day exploits, and subtle misconfigurations produce log lines that have never been seen before. An LSTM or Transformer autoencoder trained on normal log sequences learns the "grammar" of healthy log output and flags lines with high reconstruction error — catching anomalies that no predefined rule could anticipate.
- **App/TA:** Splunk Deep Learning Toolkit (DSDL), custom Python container
- **Data Sources:** Any structured log index (`index=main`, `index=os`, `index=web`, `index=security`)
- **SPL:**
```spl
index=main sourcetype=syslog earliest=-1h
| eval log_token=lower(replace(_raw, "\d+", "N"))
| eval log_token=replace(log_token, "[0-9a-f]{8,}", "HEX")
| streamstats count as seq_pos by host
| apply pretrained_log_autoencoder_dsdl
| rename reconstruction_error as recon_err
| where recon_err > 0.85
| eval anomaly_severity=case(recon_err>0.95, "critical", recon_err>0.90, "high", true(), "medium")
| table _time, host, sourcetype, _raw, recon_err, anomaly_severity
| sort -recon_err
```
- **Implementation:** Tokenize log lines by replacing numeric values with placeholders (N) and hex strings with HEX to reduce vocabulary size. Train an LSTM autoencoder (or Transformer encoder-decoder) in the DSDL container on 30 days of normal-state logs per sourcetype. The model learns to reconstruct typical log line sequences; lines it cannot reconstruct well (high reconstruction error) are anomalous. Deploy the model via `apply` in a scheduled search running every 15 minutes. Tune the threshold per sourcetype — security logs may have higher natural variance than infrastructure logs. Route critical anomalies (>0.95 error) to the SOC and high anomalies (>0.90) to operations. Track model performance weekly by reviewing false positive rates and adjusting the threshold. Retrain quarterly or after major infrastructure changes. Consider training separate models for high-volume sourcetypes (Windows Security, syslog, application logs) for better precision.
- **Visualization:** Table (anomalous log lines with reconstruction error), Line chart (reconstruction error distribution over time), Histogram (error score distribution), Single value (anomalies detected in last hour).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-13.4.14 · Host-Metric Heatmap Anomaly via CNN (DSDL)
- **Criticality:** 🟠 High
- **Difficulty:** 🔴 Expert
- **Monitoring type:** Performance, Fault
- **Value:** Infrastructure metrics (CPU, memory, disk I/O, network throughput) per host form a time × metric matrix that looks like an image. A Convolutional Neural Network trained on these "metric heatmaps" detects complex, multi-metric degradation patterns — such as the specific combination of rising CPU, flat memory, and oscillating disk I/O that precedes a particular failure mode — that univariate thresholds and even multivariate statistical models cannot capture.
- **App/TA:** Splunk Deep Learning Toolkit (DSDL), custom Python container with TensorFlow/PyTorch
- **Data Sources:** `index=infra sourcetype=collectd_http` or `sourcetype=otel:metrics` or `sourcetype=vmware:perf:*`
- **SPL:**
```spl
index=infra sourcetype IN ("collectd_http","otel:metrics","vmware:perf:cpu","vmware:perf:mem","vmware:perf:disk")
| bin _time span=5m
| stats avg(metric_value) as val by _time, host, metric_name
| xyseries _time host+"|"+metric_name val
| fillnull value=0
| apply pretrained_metric_cnn_dsdl
| rename anomaly_score as cnn_score
| where cnn_score > 0.80
| eval severity=case(cnn_score>0.95, "critical", cnn_score>0.90, "high", true(), "medium")
| table _time, host, cnn_score, severity
| sort -cnn_score
```
- **Implementation:** Construct metric heatmaps: for each host, create a 2D matrix where rows are metrics (CPU user, CPU system, memory used, disk read IOPS, disk write IOPS, network bytes in/out) and columns are time bins (e.g., 288 bins for 24 hours at 5-minute intervals). Normalize each metric row to [0,1]. Train a CNN autoencoder in the DSDL container on healthy-state heatmaps. At inference time, compute reconstruction error per host-day; high error indicates an anomalous metric pattern. The CNN captures spatial correlations across metrics that linear models miss — for example, the co-occurrence of CPU saturation with specific disk I/O patterns that precede storage controller failures. Schedule daily scoring with a 24-hour sliding window. Alert infrastructure teams on critical patterns and correlate with recent change events. Retrain monthly with new healthy baselines.
- **Visualization:** Heatmap (metric × time for anomalous hosts), Line chart (CNN anomaly score over time), Table (top anomalous hosts), Image (reconstructed vs actual heatmap for investigation).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-13.4.15 · MLTK Model Drift and Performance Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance, Compliance
- **Value:** All ML models deployed in production (security detections, capacity forecasts, anomaly detectors) degrade as data distributions shift. Without drift monitoring, a model that was 95% accurate at deployment may silently drop to 60% accuracy over months. This meta-use-case tracks model health metrics so teams know when to retrain before detection quality degrades.
- **App/TA:** Splunk Machine Learning Toolkit (MLTK), Splunk Deep Learning Toolkit (DSDL)
- **Data Sources:** MLTK model artifacts, custom model performance logs (`sourcetype=mltk:model:metrics`)
- **SPL:**
```spl
index=ml_ops sourcetype="mltk:model:metrics"
| bin _time span=1d
| stats avg(precision) as precision, avg(recall) as recall, avg(f1_score) as f1, latest(training_date) as last_trained by model_name, _time
| eval model_age_days=round((now() - strptime(last_trained, "%Y-%m-%d")) / 86400, 0)
| eval drift_alert=case(
    f1 < 0.70, "critical_drift",
    f1 < 0.80, "moderate_drift",
    model_age_days > 90, "stale_model",
    true(), "healthy")
| where drift_alert != "healthy"
| table _time, model_name, precision, recall, f1, model_age_days, drift_alert
| sort drift_alert, -model_age_days
```
- **Implementation:** Instrument all deployed MLTK and DSDL models to emit performance metrics (precision, recall, F1 score, reconstruction error mean/std, prediction distribution) to a dedicated `ml_ops` index. For supervised models, compare predictions against ground-truth labels (analyst dispositions, confirmed incidents). For unsupervised models, track anomaly rate stability and reconstruction error distribution. Alert data science teams when F1 drops below 0.80 or model age exceeds 90 days. Maintain a model registry KV store with model name, version, training date, data hash, and performance baseline. Automate retraining pipelines for models that drift past thresholds. Dashboard the health of all production ML models for ML platform governance.
- **Visualization:** Line chart (F1 score over time per model), Table (model registry with drift status), Bar chart (model age distribution), Single value (models requiring retraining).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### 13.5 OpenTelemetry, Observability Pipelines & SRE Patterns

**Primary App/TA:** Splunk Distribution of OpenTelemetry Collector, Splunk Observability Cloud (APM, RUM, Synthetics, Infrastructure Monitoring), Prometheus, Jaeger, Grafana.

---

### UC-13.5.1 · Trace Duration Anomaly and Slow Transaction Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance
- **Value:** A deployment that adds 200ms to a critical checkout flow costs revenue every second it runs. Static latency thresholds generate noise during normal traffic variation and miss gradual regressions. By baselining p50/p95/p99 trace duration per service and operation, this detection identifies statistically significant latency regressions within minutes of a deployment — before enough users complain to reach support.
- **App/TA:** Splunk Observability Cloud (APM), Splunk Distribution of OpenTelemetry Collector, Jaeger
- **Data Sources:** `sourcetype=otel:traces` or APM span data, `index=traces`
- **SPL:**
```spl
index=traces sourcetype="otel:traces"
| eval duration_ms=duration_nano/1000000
| bin _time span=15m
| stats p50(duration_ms) as p50, p95(duration_ms) as p95, p99(duration_ms) as p99, count as span_count by _time, service_name, span_name
| eventstats avg(p99) as baseline_p99, stdev(p99) as std_p99 by service_name, span_name
| eval z_score=round((p99 - baseline_p99) / nullif(std_p99, 0), 2)
| where z_score > 2 AND span_count > 50
| table _time, service_name, span_name, p50, p95, p99, baseline_p99, z_score, span_count
| sort -z_score
```
- **Implementation:** Ingest OTel trace data via OTLP exporter to Splunk (HEC or Observability Cloud). Calculate duration percentiles per service and operation in 15-minute windows. Baseline using 7-day rolling statistics. Flag operations where p99 exceeds 2 standard deviations above the baseline with sufficient sample size (>50 spans). Correlate with deployment events (cat-12) to identify which release caused the regression. For Splunk APM users, the APM service map provides built-in latency comparison; this UC replicates the pattern for platform-only deployments. Track regressions over time to measure release quality trends.
- **Visualization:** Line chart (p50/p95/p99 duration per operation over 24 hours), Table (operations with latency regressions), Heatmap (service × operation p99), Bar chart (top 10 slowest operations).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-13.5.2 · Trace Error Rate by Service and Operation
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** Error rate is the most immediate signal of service degradation. Tracking error spans (status_code=ERROR) by service, operation, and error type creates accountability: each team sees their service's error contribution. When the checkout service suddenly jumps from 0.1% to 5% errors on the `processPayment` operation, the payment team gets alerted immediately rather than waiting for downstream impact to cascade.
- **App/TA:** Splunk Observability Cloud (APM), Splunk Distribution of OpenTelemetry Collector
- **Data Sources:** `sourcetype=otel:traces`, `index=traces`
- **SPL:**
```spl
index=traces sourcetype="otel:traces"
| eval is_error=if(status_code=="ERROR" OR status_code==2, 1, 0)
| bin _time span=5m
| stats count as total_spans, sum(is_error) as error_spans by _time, service_name, span_name
| eval error_rate_pct=round(error_spans*100/total_spans, 2)
| where error_rate_pct > 1 AND total_spans > 20
| eventstats avg(error_rate_pct) as baseline_error by service_name, span_name
| eval error_spike=round(error_rate_pct / nullif(baseline_error, 0), 1)
| where error_spike > 3 OR error_rate_pct > 5
| table _time, service_name, span_name, total_spans, error_spans, error_rate_pct, baseline_error, error_spike
| sort -error_rate_pct
```
- **Implementation:** Ingest OTel trace data. Map status codes: OTel status `ERROR` (code=2) and HTTP status codes >=500 in span attributes indicate errors. Calculate error rate per service/operation in 5-minute windows. Alert when error rate exceeds 3x the baseline or crosses an absolute 5% threshold. Enrich with error messages from span events (exception.type, exception.message) to group errors by root cause. Build service ownership lookups to route alerts to the responsible team. Track error rate trends per service over 30 days to measure reliability improvements.
- **Visualization:** Line chart (error rate per service over 24 hours), Table (services with elevated errors), Bar chart (top error types by volume), Single value (fleet-wide error rate).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-13.5.3 · Trace Completeness and Orphan Span Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Fault, Compliance
- **Value:** Incomplete traces — missing parent spans, single-span traces from multi-service flows, or orphaned spans with no root — indicate broken context propagation, missing instrumentation, or sampling inconsistencies. These gaps make distributed debugging impossible exactly when it matters most. Measuring trace completeness quantifies instrumentation quality and identifies which services need propagation fixes.
- **App/TA:** Splunk Distribution of OpenTelemetry Collector, Splunk Observability Cloud (APM)
- **Data Sources:** `sourcetype=otel:traces`, `index=traces`
- **SPL:**
```spl
index=traces sourcetype="otel:traces"
| bin _time span=1h
| stats dc(span_id) as span_count, dc(service_name) as service_count,
    sum(eval(if(parent_span_id="" OR isnull(parent_span_id), 1, 0))) as root_spans
    by _time, trace_id
| eval completeness=case(
    service_count==1 AND span_count==1, "single_span",
    root_spans==0, "orphan_no_root",
    root_spans>1, "multiple_roots",
    1==1, "complete")
| stats count as trace_count,
    sum(eval(if(completeness=="single_span",1,0))) as single_spans,
    sum(eval(if(completeness=="orphan_no_root",1,0))) as orphans,
    sum(eval(if(completeness=="multiple_roots",1,0))) as multi_root
    by _time
| eval completeness_pct=round((trace_count - single_spans - orphans - multi_root)*100/trace_count, 1)
| table _time, trace_count, completeness_pct, single_spans, orphans, multi_root
```
- **Implementation:** Analyze trace structure by examining parent-child span relationships within each trace_id. Classify traces: "complete" (single root, proper parent chain), "single_span" (only one span — missing downstream instrumentation), "orphan_no_root" (no span has an empty parent_span_id — broken propagation), "multiple_roots" (more than one root span — context fragmentation). Track completeness percentage over time. Alert when completeness drops below 90%. Identify which services produce the most orphan spans by joining back to service_name. For tail-sampling deployments, validate that sampling decisions are consistent across services (UC-13.3.7 covers sampling rate; this UC covers the resulting trace quality).
- **Visualization:** Line chart (completeness % over 7 days), Pie chart (trace classification breakdown), Table (services producing most orphan spans), Single value (current completeness %).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-13.5.4 · Cross-Service Dependency Map from Traces
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Security, Performance
- **Value:** Service-to-service dependencies are often undocumented, especially in microservice architectures where teams add new API calls without updating architecture diagrams. Auto-discovering the dependency graph from trace data reveals the actual topology — including unexpected edges that represent security risks (why is the frontend calling the billing database directly?) or change risks (this "isolated" service actually has 12 downstream dependents). New edges appearing after deployments are an immediate change management signal.
- **App/TA:** Splunk Observability Cloud (APM), Splunk Distribution of OpenTelemetry Collector
- **Data Sources:** `sourcetype=otel:traces`, `index=traces`
- **SPL:**
```spl
index=traces sourcetype="otel:traces" parent_span_id=* parent_span_id!=""
| join type=left parent_span_id [search index=traces sourcetype="otel:traces"
    | rename span_id as parent_span_id, service_name as parent_service
    | fields parent_span_id, parent_service]
| where isnotnull(parent_service) AND parent_service!=service_name
| eval edge=parent_service." → ".service_name
| bin _time span=1d
| stats count as call_count, avg(duration_nano)/1000000 as avg_latency_ms, dc(trace_id) as trace_count by _time, parent_service, service_name, edge
| eventstats earliest(_time) as first_seen by edge
| eval is_new_edge=if(first_seen > relative_time(now(), "-7d"), "NEW", "known")
| where is_new_edge="NEW" OR call_count > 100
| sort is_new_edge, -call_count
| table _time, edge, parent_service, service_name, call_count, avg_latency_ms, is_new_edge, first_seen
```
- **Implementation:** Extract parent-child service relationships from traces by joining each span's `parent_span_id` to its parent span's `service_name`. Filter cross-service edges (parent_service != service_name). Aggregate daily to build the dependency graph. Track `first_seen` per edge to detect new dependencies appearing after deployments. Alert on new edges (services communicating for the first time) as a change/security signal. For Splunk APM users, the Service Map provides this visualization natively; this UC replicates the detection for platform-only deployments. Export the edge list to a network graph visualization or integrate with Splunk ITSI service dependency trees.
- **Visualization:** Force-directed graph (service dependency map), Table (new edges detected this week), Bar chart (top dependencies by call volume), Line chart (edge count trend — growing complexity indicator).
- **CIM Models:** N/A

- **References:** [Splunk ITSI](https://splunkbase.splunk.com/app/1841)

---

### UC-13.5.5 · Log-to-Trace Correlation Coverage
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Value:** Logs without trace context are isolated events that can't be correlated to specific user requests. When only 30% of log events carry `trace_id` and `span_id`, debugging a failed request requires manual timestamp-based guesswork across services. Measuring log-trace correlation coverage per service quantifies instrumentation maturity and identifies which teams need to add OTel context propagation to their logging frameworks.
- **App/TA:** Splunk Distribution of OpenTelemetry Collector, any log framework with OTel integration
- **Data Sources:** Application logs with optional `trace_id` and `span_id` fields
- **SPL:**
```spl
index=app_logs
| eval has_trace=if(isnotnull(trace_id) AND trace_id!="" AND trace_id!="0000000000000000", 1, 0)
| eval has_span=if(isnotnull(span_id) AND span_id!="" AND span_id!="0000000000000000", 1, 0)
| bin _time span=1d
| stats count as total_logs, sum(has_trace) as with_trace, sum(has_span) as with_span by _time, service_name, sourcetype
| eval trace_coverage_pct=round(with_trace*100/total_logs, 1)
| eval span_coverage_pct=round(with_span*100/total_logs, 1)
| table _time, service_name, sourcetype, total_logs, trace_coverage_pct, span_coverage_pct
| sort trace_coverage_pct
```
- **Implementation:** Modern logging frameworks (Log4j2, Logback, Python logging, Serilog) support automatic injection of OTel trace context (`trace_id`, `span_id`, `trace_flags`) into log events via MDC/context propagation. The OTel SDK logging bridge also carries this context. Measure what percentage of log events per service contain valid trace IDs (not null, not zero-padded). Target: 80%+ for instrumented services. Services below 50% likely haven't configured their logging framework's OTel integration. Provide a weekly instrumentation scorecard by team. Exclude infrastructure logs (syslog, container runtime) from the calculation as they're not expected to carry trace context. Track improvement over time to measure observability maturity program progress.
- **Visualization:** Bar chart (trace coverage % by service — sorted ascending), Line chart (fleet-wide coverage trend over 90 days), Table (services with lowest coverage), Single value (fleet average coverage %).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-13.5.6 · Trace Fanout and Depth Anomaly
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance, Fault
- **Value:** Traces with unusually high span counts or deep nesting reveal N+1 query patterns, recursive service calls, and runaway microservice chains that consume disproportionate resources. A single API call generating 10,000 spans indicates a loop or unbounded fan-out that impacts both application performance and observability infrastructure cost. Detecting these "mega-traces" prevents both performance degradation and observability platform overload.
- **App/TA:** Splunk Observability Cloud (APM), Splunk Distribution of OpenTelemetry Collector
- **Data Sources:** `sourcetype=otel:traces`, `index=traces`
- **SPL:**
```spl
index=traces sourcetype="otel:traces"
| stats count as span_count, dc(service_name) as service_count, sum(duration_nano)/1000000 as total_duration_ms by trace_id
| eventstats avg(span_count) as avg_spans, stdev(span_count) as std_spans
| eval span_z_score=round((span_count - avg_spans) / if(std_spans==0,null(),std_spans), 2)
| eval anomaly_type=case(
    span_count > 1000, "mega_trace",
    span_z_score > 3, "high_fanout",
    service_count > 15, "wide_fanout",
    1==1, null())
| where isnotnull(anomaly_type)
| sort -span_count
| head 100
| table trace_id, anomaly_type, span_count, service_count, total_duration_ms, span_z_score
```
- **Implementation:** Aggregate span counts per `trace_id` to identify traces with unusually high fan-out. Traces exceeding 1,000 spans are "mega-traces" that likely indicate N+1 queries or unbounded pagination loops. Traces touching more than 15 services signal wide fan-out across the architecture. Calculate z-scores against the population to detect statistically anomalous traces. For each anomalous trace, identify the service and operation that generates the most child spans — this is the fan-out origin to investigate. Common root causes: ORM lazy loading in loops, recursive microservice calls without depth limits, batch jobs that create per-item spans. Alert when mega-traces exceed 5 per hour. Feed findings to development teams with specific trace IDs for investigation.
- **Visualization:** Histogram (span count distribution with anomaly threshold), Table (anomalous traces with details), Bar chart (top services producing high-fanout traces), Single value (mega-traces in last hour).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-13.5.7 · Splunk APM Service Map Health (RED Metrics)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance, Fault
- **Value:** Splunk APM's service map provides real-time Request rate, Error rate, and Duration (RED) metrics per service and endpoint. Ingesting these metrics into Splunk Enterprise enables correlation with infrastructure data, security events, and business metrics that live outside Observability Cloud — creating a unified view that neither platform provides alone. Degrading RED metrics in APM can trigger Splunk Enterprise workflows, populate ITSI service trees, or enrich ES risk scores.
- **App/TA:** Splunk Observability Cloud (APM), Splunk Add-on for Splunk Observability Cloud
- **Data Sources:** Splunk APM service metrics via API or OTel Collector relay, `sourcetype=signalfx:apm:metrics`
- **SPL:**
```spl
index=observability sourcetype="signalfx:apm:metrics"
| bin _time span=5m
| stats avg(request_rate) as req_rate, avg(error_rate) as err_rate, avg(p99_duration_ms) as p99_ms by _time, service_name, environment
| eventstats avg(err_rate) as baseline_err, avg(p99_ms) as baseline_p99 by service_name
| eval err_spike=round(err_rate / nullif(baseline_err, 0), 1)
| eval latency_spike=round(p99_ms / nullif(baseline_p99, 0), 1)
| where err_spike > 3 OR latency_spike > 2 OR err_rate > 5
| table _time, service_name, environment, req_rate, err_rate, err_spike, p99_ms, latency_spike
| sort -err_spike
```
- **Implementation:** Export Splunk APM metrics to Splunk Enterprise via the OTel Collector (using the SignalFx exporter → Splunk HEC pipeline) or via the Observability Cloud API with a scripted input. Key metrics: `service.request.count` (rate), `service.request.duration.ns.p99` (latency), `service.error.count` (errors). Calculate RED metrics per service in 5-minute windows. Compare against rolling baselines to detect spikes. For ITSI integration, map APM services to ITSI service entities and feed RED metrics as KPIs. For ES integration, generate risk events when critical services show sustained error spikes. Track RED metrics trend over 30 days to measure service reliability improvement.
- **Visualization:** Table (service health matrix — green/yellow/red by RED metric), Line chart (RED metrics per service over 24 hours), Gauge (error rate per critical service), Heatmap (service × time error rate).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-13.5.8 · Splunk APM Database Query Performance
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Database spans in APM traces reveal which SQL queries contribute most to service latency. A single unoptimized query hiding behind 50ms average response time can drive p99 to 2 seconds. APM database query analysis identifies the specific queries and calling services responsible for database-driven latency, providing actionable evidence for query optimization and index tuning — bridging the gap between application and database teams.
- **App/TA:** Splunk Observability Cloud (APM), Splunk Distribution of OpenTelemetry Collector
- **Data Sources:** APM database span data, `sourcetype=otel:traces` (db.* attributes)
- **SPL:**
```spl
index=traces sourcetype="otel:traces" span_kind="CLIENT" db_system=*
| eval query_duration_ms=duration_nano/1000000
| eval db_statement_short=substr(db_statement, 1, 200)
| bin _time span=15m
| stats avg(query_duration_ms) as avg_ms, p95(query_duration_ms) as p95_ms, p99(query_duration_ms) as p99_ms, count as query_count, sum(eval(if(status_code=="ERROR",1,0))) as errors by _time, service_name, db_system, db_name, db_statement_short
| where p99_ms > 500 OR errors > 0
| eval impact_score=round(query_count * p99_ms / 1000, 1)
| sort -impact_score
| table _time, service_name, db_system, db_name, db_statement_short, query_count, avg_ms, p95_ms, p99_ms, errors, impact_score
```
- **Implementation:** OTel auto-instrumentation captures database spans with semantic conventions: `db.system` (mysql, postgresql, redis), `db.name`, `db.statement` (sanitized query), and `db.operation` (SELECT, INSERT, etc.). Ingest these spans and analyze query performance per service. The `impact_score` (query_count × p99_ms) prioritizes the queries that contribute most to total service latency — a query running 10,000 times at 100ms p99 has higher impact than one running 10 times at 5,000ms. Alert when any query's p99 exceeds 500ms or when errors appear. Correlate with database monitoring (cat-07) to validate that database-side metrics confirm the latency seen in traces. Truncate `db.statement` for display while preserving enough for identification.
- **Visualization:** Table (top queries by impact score), Line chart (query p99 trend per service), Bar chart (query count by database system), Scatter plot (query count vs p99 latency — bubble size = impact).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-13.5.9 · Splunk RUM Core Web Vitals Tracking
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Google's Core Web Vitals — Largest Contentful Paint (LCP), Interaction to Next Paint (INP), and Cumulative Layout Shift (CLS) — directly impact search ranking and user experience. Splunk RUM captures these metrics per page, browser, device type, and geographic location. Tracking CWV trends detects regressions after frontend deployments before they affect SEO ranking or user conversion rates. A 100ms LCP regression on the product page can reduce conversion by 1-2%.
- **App/TA:** Splunk Observability Cloud (RUM), Splunk RUM agent
- **Data Sources:** Splunk RUM telemetry, `sourcetype=signalfx:rum:metrics`
- **SPL:**
```spl
index=observability sourcetype="signalfx:rum:metrics"
| bin _time span=1h
| stats avg(lcp_ms) as avg_lcp, p75(lcp_ms) as p75_lcp, avg(inp_ms) as avg_inp, p75(inp_ms) as p75_inp, avg(cls) as avg_cls, p75(cls) as p75_cls, count as page_views by _time, page_url, browser_name, device_type
| eval lcp_rating=case(p75_lcp<=2500, "Good", p75_lcp<=4000, "Needs Improvement", 1==1, "Poor")
| eval inp_rating=case(p75_inp<=200, "Good", p75_inp<=500, "Needs Improvement", 1==1, "Poor")
| eval cls_rating=case(p75_cls<=0.1, "Good", p75_cls<=0.25, "Needs Improvement", 1==1, "Poor")
| where lcp_rating!="Good" OR inp_rating!="Good" OR cls_rating!="Good"
| sort -p75_lcp
| table _time, page_url, browser_name, device_type, p75_lcp, lcp_rating, p75_inp, inp_rating, p75_cls, cls_rating, page_views
```
- **Implementation:** Deploy Splunk RUM agent on frontend pages. RUM automatically captures CWV metrics using the web-vitals library. Ingest RUM data into Splunk via the Observability Cloud API or OTel Collector relay. Google measures CWV at the 75th percentile: LCP ≤2.5s (good), INP ≤200ms (good), CLS ≤0.1 (good). Track p75 values per page URL, browser, and device type (mobile vs desktop — mobile often has worse LCP). Alert frontend teams when any high-traffic page drops from "Good" to "Needs Improvement." Compare CWV before and after deployments using deployment markers. Provide weekly CWV reports to product owners with page-level detail and trend direction.
- **Visualization:** Scorecard (CWV status per top page — green/yellow/red), Line chart (LCP/INP/CLS p75 trend over 30 days), Table (pages with poor CWV), Bar chart (CWV by device type).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-13.5.10 · Splunk RUM JavaScript Error Rate by Page
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** Frontend JavaScript errors — unhandled exceptions, failed API calls, resource loading failures — directly degrade user experience but are invisible to backend monitoring. RUM captures these errors with full stack traces, page URL, browser, and user session context. Tracking JS error rate by page detects regressions after deployments, identifies browser-specific bugs, and quantifies the user impact of frontend failures that backend health checks miss entirely.
- **App/TA:** Splunk Observability Cloud (RUM), Splunk RUM agent
- **Data Sources:** Splunk RUM error events, `sourcetype=signalfx:rum:errors`
- **SPL:**
```spl
index=observability sourcetype="signalfx:rum:errors"
| eval error_type=coalesce(exception_type, "UnknownError")
| bin _time span=1h
| stats count as error_count, dc(session_id) as affected_sessions, values(error_type) as error_types by _time, page_url, browser_name
| join type=left _time page_url [search index=observability sourcetype="signalfx:rum:metrics"
    | bin _time span=1h
    | stats dc(session_id) as total_sessions by _time, page_url]
| eval error_session_pct=round(affected_sessions*100/nullif(total_sessions, 0), 1)
| where error_count > 10 OR error_session_pct > 5
| table _time, page_url, browser_name, error_count, affected_sessions, error_session_pct, error_types
| sort -error_session_pct
```
- **Implementation:** Splunk RUM captures JavaScript errors including: uncaught exceptions, unhandled promise rejections, resource loading failures (img, script, CSS 404s), and fetch/XHR errors. Each error event includes stack trace, page URL, browser, OS, and session ID. Calculate the percentage of user sessions experiencing errors per page — this measures user impact more accurately than raw error count (one broken page viewed by 100 users = 100 errors but 100% session impact). Alert when error session percentage exceeds 5% for any page with >100 views. Compare error rates by browser to identify browser-specific regressions. Link RUM errors to backend traces via trace_id to identify full-stack root causes.
- **Visualization:** Line chart (error session % per page over 7 days), Table (pages with highest error impact), Bar chart (errors by type), Pie chart (errors by browser).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-13.5.11 · Splunk Synthetic Monitoring Multi-Step Transaction SLA
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability, Performance
- **Value:** Beyond simple pass/fail synthetic checks (UC-13.3.10), multi-step browser transactions test complete user workflows — login, search, add-to-cart, checkout. Step-level timing trends reveal which step is degrading: if the login step takes 500ms longer in one geography, that points to a regional identity provider issue. Transaction SLA tracking quantifies end-user experience commitments and provides evidence for SLA breach discussions with internal service owners or external vendors.
- **App/TA:** Splunk Observability Cloud (Synthetics), Splunk Synthetic Monitoring
- **Data Sources:** Splunk Synthetic test results, `sourcetype=signalfx:synthetics:results`
- **SPL:**
```spl
index=observability sourcetype="signalfx:synthetics:results" test_type="browser"
| eval step_duration_ms=step_end_ms - step_start_ms
| bin _time span=1h
| stats avg(step_duration_ms) as avg_step_ms, p95(step_duration_ms) as p95_step_ms, sum(eval(if(step_status=="FAIL",1,0))) as step_failures, count as step_runs by _time, test_name, step_name, location
| eval step_success_pct=round((step_runs-step_failures)*100/step_runs, 1)
| eval sla_met=if(step_success_pct >= 99.5 AND p95_step_ms < 3000, "Yes", "No")
| stats avg(step_success_pct) as avg_success, avg(p95_step_ms) as avg_p95, min(step_success_pct) as worst_success by test_name, step_name, location
| where avg_success < 99.5 OR avg_p95 > 3000
| table test_name, step_name, location, avg_success, avg_p95, worst_success
| sort avg_success
```
- **Implementation:** Configure Splunk Synthetic browser tests for critical user journeys (login flow, checkout, search, account management) running from multiple geographic locations every 5-15 minutes. Ingest results with per-step timing and status. Define SLA targets per transaction (e.g., 99.5% success, p95 < 3 seconds). Track step-level performance to identify which step in the journey degrades. Compare performance across locations to detect regional infrastructure issues. Alert when any transaction drops below SLA for 2 consecutive hours. Provide weekly SLA reports to service owners showing uptime, performance, and geographic variance. Correlate synthetic failures with infrastructure events (cat-01, cat-05) to distinguish application from infrastructure issues.
- **Visualization:** Table (transaction SLA status by location — green/red), Line chart (step duration trend per test), Bar chart (success rate by geography), Heatmap (test × location performance).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-13.5.12 · Splunk Observability Cloud Detector Health
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability, Compliance
- **Value:** Observability Cloud detectors (alerts) degrade silently: a detector may be permanently muted, have no recent data feeding its signal, fire so frequently it's ignored (alert fatigue), or have a condition that can never trigger due to metric name changes. Monitoring detector health ensures the alerting layer that protects production services is itself healthy — preventing the dangerous situation where teams believe they're covered by alerts that haven't actually fired or evaluated in months.
- **App/TA:** Splunk Observability Cloud API, custom scripted input
- **Data Sources:** Observability Cloud Detector API (`sourcetype=signalfx:detectors`), alert event history
- **SPL:**
```spl
index=observability sourcetype="signalfx:detectors"
| stats latest(is_muted) as muted, latest(last_triggered) as last_trigger, latest(last_updated) as last_update, count(eval(severity=="Critical")) as critical_fires, count(eval(severity=="Warning")) as warning_fires by detector_name, detector_id, creator
| eval days_since_trigger=if(isnotnull(last_trigger), round((now()-last_trigger)/86400, 0), "Never")
| eval days_since_update=round((now()-last_update)/86400, 0)
| eval health=case(
    muted=="true", "MUTED",
    days_since_trigger=="Never" OR days_since_trigger > 90, "STALE - Never/Rarely Fires",
    critical_fires > 100, "NOISY - Excessive Alerts",
    days_since_update > 365, "ABANDONED - Not Updated",
    1==1, "Healthy")
| where health!="Healthy"
| table detector_name, creator, health, muted, days_since_trigger, days_since_update, critical_fires
| sort health
```
- **Implementation:** Deploy a scripted input that polls the Observability Cloud Detector API daily, extracting detector metadata (name, creator, mute status, last update), and alert event history (last triggered, firing frequency). Classify detector health: "MUTED" (permanently silenced — may be intentional or forgotten), "STALE" (never fired or hasn't fired in 90 days — may have no data or an impossible condition), "NOISY" (fires more than 100 times — creates alert fatigue), "ABANDONED" (not updated in 1 year — may reference deprecated metrics). Provide a quarterly detector hygiene report to platform teams. Alert when critical-severity detectors are muted for more than 7 days. Track detector count over time to measure observability sprawl.
- **Visualization:** Pie chart (detector health distribution), Table (unhealthy detectors with details), Bar chart (detectors by health category), Single value (% of healthy detectors).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-13.5.13 · RED Metrics Dashboard Template (Rate, Errors, Duration)
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance, Fault
- **Value:** The RED method (Rate, Errors, Duration) is the standard SRE pattern for monitoring request-driven services. This template UC provides a reusable SPL pattern applicable to any HTTP/gRPC service instrumented with OTel — producing the three essential metrics that answer "is this service healthy right now?" Having a standardized RED pattern ensures every team monitors their services consistently, enabling fleet-wide comparison and prioritization.
- **App/TA:** Splunk Distribution of OpenTelemetry Collector, any HTTP/gRPC access log
- **Data Sources:** `sourcetype=otel:traces` (spans), `sourcetype=access_combined` (HTTP logs), OTel metrics
- **SPL:**
```spl
index=traces sourcetype="otel:traces" span_kind="SERVER"
| eval duration_ms=duration_nano/1000000
| eval is_error=if(status_code=="ERROR" OR http_status_code>=500, 1, 0)
| bin _time span=5m
| stats count as requests, sum(is_error) as errors, avg(duration_ms) as avg_duration, p50(duration_ms) as p50, p95(duration_ms) as p95, p99(duration_ms) as p99 by _time, service_name
| eval error_rate_pct=round(errors*100/requests, 2)
| eval req_per_sec=round(requests/300, 1)
| table _time, service_name, req_per_sec, error_rate_pct, p50, p95, p99
```
- **Implementation:** Filter for SERVER spans (inbound requests to the service) from OTel trace data. Calculate three metrics per 5-minute window: Rate (requests per second), Errors (percentage of requests with error status), Duration (latency percentiles). This template works with any OTel-instrumented service. Alternatively, compute RED from HTTP access logs using `status>=500` for errors and response time fields for duration. Deploy as a saved search macro `red_metrics(service_name)` for reusability across dashboards. Each team clones the template for their services. Combine with deployment markers to immediately visualize RED impact of releases. Set standard thresholds: error rate >1% (warning), >5% (critical); p99 >2x baseline (warning).
- **Visualization:** Three-panel row per service: Single value (request rate with sparkline), Gauge (error rate with green/yellow/red), Line chart (p50/p95/p99 duration). Repeatable per service.
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-13.5.14 · USE Method for Infrastructure (Utilization, Saturation, Errors)
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance, Capacity
- **Value:** The USE method (Utilization, Saturation, Errors) is the standard SRE pattern for monitoring resource-driven systems (CPU, memory, disk, network). While individual infrastructure UCs exist across cat-01 and cat-05, this template consolidates all three signals per resource into a unified view that answers "is this resource the bottleneck?" Having the USE framework as a structured pattern ensures systematic coverage — teams often monitor utilization but miss saturation (the queue) and errors (the failures).
- **App/TA:** Splunk Distribution of OpenTelemetry Collector (hostmetrics receiver), Splunk Infrastructure Monitoring
- **Data Sources:** OTel host metrics (`system.cpu.*`, `system.memory.*`, `system.disk.*`, `system.network.*`)
- **SPL:**
```spl
| mstats avg(_value) as val WHERE index=infra_metrics metric_name IN (
    "system.cpu.utilization",
    "system.cpu.load_average.5m",
    "system.memory.utilization",
    "system.memory.usage",
    "system.disk.utilization",
    "system.disk.io_time",
    "system.network.dropped",
    "system.network.errors"
  ) BY metric_name, host span=5m
| eval resource=case(
    match(metric_name, "cpu"), "CPU",
    match(metric_name, "memory"), "Memory",
    match(metric_name, "disk"), "Disk",
    match(metric_name, "network"), "Network")
| eval signal=case(
    match(metric_name, "utilization"), "Utilization",
    match(metric_name, "load_average|io_time|dropped"), "Saturation",
    match(metric_name, "errors"), "Errors")
| stats avg(val) as avg_val, max(val) as max_val by host, resource, signal
| eval status=case(
    signal=="Utilization" AND max_val > 0.9, "Critical",
    signal=="Utilization" AND max_val > 0.7, "Warning",
    signal=="Saturation" AND max_val > 0, "Warning",
    signal=="Errors" AND max_val > 0, "Critical",
    1==1, "OK")
| where status!="OK"
| table host, resource, signal, avg_val, max_val, status
| sort status, resource
```
- **Implementation:** Deploy OTel Collector with the `hostmetrics` receiver on all infrastructure hosts. Map OTel host metrics to the USE framework: Utilization (% of resource capacity in use), Saturation (work queued or waiting — load average, disk I/O wait, network drops), Errors (hardware/software errors — disk errors, network errors). For each resource type, define USE metric mappings: CPU (utilization=cpu.utilization, saturation=load_average, errors=N/A), Memory (utilization=memory.utilization, saturation=swap usage, errors=ECC errors), Disk (utilization=disk.utilization, saturation=io_time, errors=disk errors), Network (utilization=bandwidth%, saturation=dropped packets, errors=errors). Alert when any resource shows high utilization (>90%) combined with saturation. This pattern complements per-host monitoring by providing a methodological framework for bottleneck identification.
- **Visualization:** Matrix table (host × resource with USE status coloring), Gauge (utilization per resource), Bar chart (hosts with saturation), Single value (resources in critical state).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-13.5.15 · Golden Signals Composite Health per Service
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance, Availability
- **Value:** Google SRE's four Golden Signals — Latency, Traffic, Errors, Saturation — provide a complete view of service health when combined into a composite score. Individual signal monitoring exists across various UCs, but a composite score enables service-level comparison and prioritization: when 20 services degrade simultaneously during an incident, the composite score instantly ranks which services are worst-affected. This is particularly valuable for non-ITSI deployments that lack ITSI's built-in service health scoring.
- **App/TA:** Splunk Distribution of OpenTelemetry Collector, Splunk Observability Cloud
- **Data Sources:** `sourcetype=otel:traces` (spans), OTel metrics, application logs
- **SPL:**
```spl
index=traces sourcetype="otel:traces" span_kind="SERVER"
| eval duration_ms=duration_nano/1000000
| eval is_error=if(status_code=="ERROR", 1, 0)
| bin _time span=5m
| stats count as traffic, sum(is_error) as errors, p99(duration_ms) as latency_p99 by _time, service_name
| eval error_rate=round(errors*100/traffic, 2)
| join type=left _time service_name [
    | mstats avg(_value) as saturation WHERE index=infra_metrics metric_name="system.cpu.utilization" BY service_name span=5m]
| eval latency_score=case(latency_p99<200, 100, latency_p99<500, 80, latency_p99<1000, 60, latency_p99<2000, 40, 1==1, 20)
| eval error_score=case(error_rate<0.1, 100, error_rate<1, 80, error_rate<5, 60, error_rate<10, 40, 1==1, 20)
| eval traffic_score=if(traffic>0, 100, 0)
| eval sat_score=case(saturation<0.5, 100, saturation<0.7, 80, saturation<0.85, 60, saturation<0.95, 40, 1==1, 20)
| eval composite_health=round((latency_score*0.3 + error_score*0.3 + traffic_score*0.2 + sat_score*0.2), 0)
| table _time, service_name, composite_health, latency_p99, error_rate, traffic, saturation
| sort composite_health
```
- **Implementation:** Combine the four Golden Signals per service into a weighted composite score (0-100). Weights: Latency 30%, Errors 30%, Traffic 20% (presence/absence), Saturation 20%. Score each signal on a 0-100 scale based on configurable thresholds. The composite score enables instant service ranking during incidents. For services with ITSI coverage, this complements rather than replaces ITSI health scores — ITSI provides richer KPI modeling while this provides a lightweight alternative for services not yet onboarded to ITSI. Store service-level scores in a summary index for historical trending. Build a fleet-wide service health leaderboard sorted by composite score.
- **Visualization:** Table (service leaderboard sorted by composite health — color coded), Gauge (composite health per critical service), Line chart (composite health trend per service over 7 days), Treemap (services sized by traffic, colored by health).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-13.5.16 · SLO Definition and Multi-Window Burn Rate Alerting
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Availability, Performance
- **Value:** Simple error rate thresholds create two failure modes: too sensitive (alert on every transient error) or too lenient (miss sustained degradation). Google SRE's multi-window burn rate alerting solves this by measuring how fast you're consuming your error budget across multiple time windows. A fast burn (5min/1hr window) catches severe outages immediately; a slow burn (30min/6hr window) catches gradual degradation that compounds. This structured approach replaces ad-hoc threshold alerting with mathematically rigorous SLO-based alerting.
- **App/TA:** Splunk Distribution of OpenTelemetry Collector, Splunk Observability Cloud
- **Data Sources:** `sourcetype=otel:traces`, service metrics, `sourcetype=access_combined`
- **SPL:**
```spl
index=traces sourcetype="otel:traces" span_kind="SERVER" service_name="$service$"
| eval good=if(status_code!="ERROR" AND (isnull(http_status_code) OR http_status_code<500), 1, 0)
| bin _time span=1m
| stats count as total, sum(good) as good_count by _time
| eval error_ratio=1-(good_count/total)
| eval slo_target=0.999
| eval budget_total=1-slo_target
| sort _time
| streamstats sum(total) as window_total, sum(eval(total-good_count)) as window_errors window=5
| eval burn_rate_5m=round((window_errors/window_total)/budget_total, 2)
| streamstats sum(total) as window_total_1h, sum(eval(total-good_count)) as window_errors_1h window=60
| eval burn_rate_1h=round((window_errors_1h/window_total_1h)/budget_total, 2)
| eval fast_burn_alert=if(burn_rate_5m > 14.4 AND burn_rate_1h > 14.4, 1, 0)
| eval slow_burn_alert=if(burn_rate_1h > 6 AND burn_rate_5m > 6, 1, 0)
| where fast_burn_alert=1 OR slow_burn_alert=1
| eval alert_type=case(fast_burn_alert=1, "FAST BURN", slow_burn_alert=1, "SLOW BURN")
| table _time, alert_type, burn_rate_5m, burn_rate_1h, error_ratio, window_total
```
- **Implementation:** Define SLOs per service as availability targets (e.g., 99.9% = 0.1% error budget over 30 days). Calculate burn rate as (observed error rate / error budget rate). Google SRE recommends multi-window alerting: Fast burn (14.4x burn rate over 5min AND 1hr windows) catches severe incidents — at this rate, the entire monthly budget is consumed in 2 hours. Slow burn (6x burn rate over 30min AND 6hr windows) catches gradual degradation — budget consumed in 5 days. Store SLO definitions in a KV store lookup (service, slo_target, budget_period_days). Calculate remaining error budget percentage per service and display on an SLO dashboard. Pair with UC-13.5.17 for error budget policy enforcement when budget is exhausted.
- **Visualization:** Gauge (error budget remaining % per service), Line chart (burn rate over 24 hours with threshold lines), Table (services with active burn rate alerts), Single value (services currently burning budget).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-13.5.17 · Error Budget Policy Enforcement
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance, Availability
- **Value:** An SLO without enforcement is just a dashboard. Error budget policies define what happens when a service exhausts its error budget: feature freeze, mandatory reliability work, postmortem requirement, or escalation to engineering leadership. Tracking error budget consumption per service per period and automatically flagging services that have exhausted their budget creates accountability — transforming SLOs from aspirational targets into governance mechanisms that balance feature velocity with reliability investment.
- **App/TA:** Splunk Distribution of OpenTelemetry Collector, Splunk Observability Cloud
- **Data Sources:** `sourcetype=otel:traces`, SLO definition lookup (KV store)
- **SPL:**
```spl
index=traces sourcetype="otel:traces" span_kind="SERVER"
| eval good=if(status_code!="ERROR" AND (isnull(http_status_code) OR http_status_code<500), 1, 0)
| bin _time span=1d
| stats count as total, sum(good) as good_count by _time, service_name
| lookup slo_definitions service_name OUTPUT slo_target, budget_period_days, service_tier, owning_team
| eval daily_error_rate=round((total-good_count)*100/total, 3)
| eval allowed_error_pct=round((1-slo_target)*100, 3)
| streamstats sum(total) as period_total, sum(good_count) as period_good window=30 by service_name
| eval period_availability=round(period_good*100/period_total, 3)
| eval budget_consumed_pct=round((100-period_availability)*100/(100-slo_target*100), 1)
| eval policy_action=case(
    budget_consumed_pct >= 100, "BUDGET EXHAUSTED - Feature Freeze",
    budget_consumed_pct >= 80, "WARNING - Prioritize Reliability",
    budget_consumed_pct >= 50, "CAUTION - Monitor Closely",
    1==1, "OK - Budget Available")
| where budget_consumed_pct >= 50
| table service_name, owning_team, service_tier, slo_target, period_availability, budget_consumed_pct, policy_action
| sort -budget_consumed_pct
```
- **Implementation:** Create a `slo_definitions` KV store lookup with columns: service_name, slo_target (e.g., 0.999), budget_period_days (typically 30), service_tier (critical/standard/best-effort), and owning_team. Calculate rolling 30-day availability per service from trace data. Compute error budget consumption as the ratio of actual errors to allowed errors. Define policy actions at thresholds: 50% consumed (caution — team should be aware), 80% consumed (warning — shift priorities to reliability), 100% consumed (feature freeze — only reliability and security work until budget replenishes). Generate weekly error budget reports for engineering leadership. Integrate with JIRA/ServiceNow to automatically create reliability work items when budget hits 80%. Track budget consumption trend to forecast when budget will be exhausted.
- **Visualization:** Table (service error budget status with policy action), Gauge (budget remaining % per critical service), Line chart (budget consumption trend over 30 days), Bar chart (services by budget consumption — sorted descending).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-13.5.18 · Observability Data Volume and Cost Attribution
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Cost, Capacity
- **Value:** Observability platforms charge by data volume (metrics data points, trace spans, log GB). Without attribution, a single team's misconfigured debug logging or high-cardinality metrics can spike the monthly bill by 40% while no one knows who caused it. Attributing observability data volume to services, teams, and environments enables FinOps governance — teams that generate the most telemetry bear the cost, creating incentive to instrument efficiently rather than indiscriminately.
- **App/TA:** Splunk Distribution of OpenTelemetry Collector, Splunk License Manager
- **Data Sources:** OTel Collector throughput metrics, Splunk license usage (`_internal`), `sourcetype=otel:traces`
- **SPL:**
```spl
| mstats sum(_value) as val WHERE index=otel_metrics metric_name IN (
    "otelcol_receiver_accepted_spans",
    "otelcol_receiver_accepted_metric_points",
    "otelcol_receiver_accepted_log_records"
  ) BY metric_name, service_name span=1d
| eval signal=case(match(metric_name,"spans"),"traces", match(metric_name,"metric"),"metrics", match(metric_name,"log"),"logs")
| lookup service_ownership service_name OUTPUT owning_team, cost_center, environment
| stats sum(val) as volume by owning_team, cost_center, signal
| eval estimated_cost=case(
    signal=="traces", round(volume * 0.000005, 2),
    signal=="metrics", round(volume * 0.000001, 2),
    signal=="logs", round(volume * 0.0000008, 2))
| stats sum(volume) as total_volume, sum(estimated_cost) as total_cost by owning_team, cost_center
| sort -total_cost
| table owning_team, cost_center, total_volume, total_cost
```
- **Implementation:** Track OTel Collector throughput metrics attributed to `service_name` (extracted from span/metric/log resource attributes). Build a `service_ownership` lookup mapping services to teams and cost centers. Aggregate daily data volume by signal type (traces, metrics, logs) and team. Apply cost-per-unit estimates based on your observability platform pricing (Splunk Cloud, Observability Cloud, or self-hosted). Generate monthly chargeback or showback reports. Identify the top 10 services by volume for optimization review. Common volume reduction strategies: reduce trace sampling for low-risk services, aggregate metrics at the collector (use `metricstransform` processor), filter debug-level logs before export.
- **Visualization:** Bar chart (cost by team), Pie chart (volume by signal type), Table (top services by volume), Line chart (total volume trend over 90 days).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-13.5.19 · Observability Cardinality Explosion Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance, Cost
- **Value:** Metric cardinality — the number of unique time series — is the hidden cost driver of observability platforms. Adding a high-cardinality label like `user_id` or `request_id` to a metric can create millions of unique time series, overwhelming TSDB backends and causing query timeouts, memory exhaustion, and unexpected cost spikes. Detecting cardinality explosions before they impact platform stability prevents outages in the observability infrastructure itself.
- **App/TA:** Splunk Distribution of OpenTelemetry Collector, Prometheus, Splunk Observability Cloud
- **Data Sources:** OTel Collector metrics, TSDB cardinality endpoints, `sourcetype=otel:metrics`
- **SPL:**
```spl
| mcatalog values(metric_name) WHERE index=otel_metrics by metric_name
| map maxsearches=500 search="| mcatalog values(_dims) as dimensions WHERE index=otel_metrics metric_name=\"$metric_name$\" | eval metric_name=\"$metric_name$\" | eval cardinality=mvcount(dimensions)"
| sort -cardinality
| head 50
| eventstats sum(cardinality) as total_cardinality
| eval pct_of_total=round(cardinality*100/total_cardinality, 1)
| where cardinality > 10000 OR pct_of_total > 5
| table metric_name, cardinality, pct_of_total
```
- **Implementation:** Periodically audit metric cardinality by counting unique label combinations (time series) per metric name. Metrics with cardinality >10,000 are candidates for label reduction. Common offenders: HTTP metrics with `path` labels containing IDs (`/users/12345`), metrics with `pod_name` labels in auto-scaling environments, and custom metrics with unbounded label values. Use the OTel Collector's `metricstransform` processor to aggregate or drop high-cardinality labels before export. For Splunk Observability Cloud, monitor the `sf.org.numCustomMetrics` org metric. Alert when any single metric exceeds 10,000 time series or when total cardinality grows more than 20% week-over-week. Build a cardinality budget per team aligned with cost allocation.
- **Visualization:** Bar chart (top 20 metrics by cardinality), Line chart (total cardinality trend over 30 days), Table (metrics exceeding threshold with label analysis), Single value (total active time series).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-13.5.20 · Instrumentation Coverage Audit
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Value:** You can't debug what you can't see. Services without OTel instrumentation are "dark" — when they fail, you diagnose from the outside using downstream error messages and infrastructure metrics, adding 30-60 minutes to MTTR. Measuring instrumentation coverage per team (what percentage of their services emit traces, metrics, and logs with trace context) drives observability maturity programs with data rather than mandates. A coverage target of 90% for critical services creates measurable accountability.
- **App/TA:** Splunk Distribution of OpenTelemetry Collector, service registry
- **Data Sources:** OTel Collector receiver metrics, service registry/CMDB, `sourcetype=otel:traces`
- **SPL:**
```spl
| inputlookup service_registry where status="active"
| fields service_name, owning_team, service_tier, expected_signals
| join type=left service_name [
    search index=traces sourcetype="otel:traces" earliest=-7d
    | stats dc(trace_id) as trace_count, dc(span_name) as operations by service_name
    | eval has_traces="Yes"]
| join type=left service_name [
    | mstats count(_value) as count WHERE index=otel_metrics metric_name=* BY service_name span=7d
    | where count > 0
    | eval has_metrics="Yes"
    | fields service_name, has_metrics]
| fillnull has_traces has_metrics value="No"
| eval coverage=case(
    has_traces=="Yes" AND has_metrics=="Yes", "Full",
    has_traces=="Yes" OR has_metrics=="Yes", "Partial",
    1==1, "Dark")
| stats count as total, sum(eval(if(coverage=="Full",1,0))) as full, sum(eval(if(coverage=="Partial",1,0))) as partial, sum(eval(if(coverage=="Dark",1,0))) as dark by owning_team
| eval coverage_pct=round(full*100/total, 1)
| table owning_team, total, full, partial, dark, coverage_pct
| sort coverage_pct
```
- **Implementation:** Maintain a `service_registry` lookup (from CMDB, Kubernetes service discovery, or manual inventory) listing all active services with their owning team, tier, and expected telemetry signals. Compare the registry against actual telemetry received in the last 7 days: services emitting traces are "instrumented for tracing," services emitting metrics are "instrumented for metrics." Classify each service as Full (both signals), Partial (one signal), or Dark (no telemetry). Calculate coverage percentage per team. Target: 90% full coverage for Tier-1 services, 70% for Tier-2. Generate weekly instrumentation scorecards for engineering leadership. Track coverage improvement over quarters to measure observability maturity program progress.
- **Visualization:** Bar chart (coverage % by team), Table (dark services by team), Pie chart (fleet-wide coverage distribution), Line chart (coverage trend over quarters), Single value (fleet coverage %).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-13.5.21 · Telemetry Signal Freshness and Staleness
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability, Fault
- **Value:** A service that stops emitting metrics or traces could mean two very different things: the service is down (infrastructure problem requiring immediate response) or the instrumentation broke (observability gap requiring engineering fix). Monitoring signal freshness — how recently each service last emitted each signal type — distinguishes these cases. If infrastructure monitoring shows the service is running but traces stopped, the instrumentation broke. If both stop, the service is likely down. Without freshness monitoring, instrumentation failures go unnoticed until the next incident when debugging tools fail.
- **App/TA:** Splunk Distribution of OpenTelemetry Collector
- **Data Sources:** `sourcetype=otel:traces`, OTel metrics, application logs
- **SPL:**
```spl
| tstats latest(_time) as last_trace WHERE index=traces sourcetype="otel:traces" BY service_name
| join type=left service_name [
    | mstats max(_time) as last_metric WHERE index=otel_metrics metric_name=* BY service_name]
| join type=left service_name [
    | tstats latest(_time) as last_log WHERE index=app_logs BY service_name]
| eval trace_age_min=round((now()-last_trace)/60, 0)
| eval metric_age_min=round((now()-last_metric)/60, 0)
| eval log_age_min=round((now()-last_log)/60, 0)
| eval trace_status=case(isnull(trace_age_min), "Never", trace_age_min>60, "STALE", trace_age_min>15, "Warning", 1==1, "Fresh")
| eval metric_status=case(isnull(metric_age_min), "Never", metric_age_min>30, "STALE", metric_age_min>10, "Warning", 1==1, "Fresh")
| eval log_status=case(isnull(log_age_min), "Never", log_age_min>30, "STALE", log_age_min>10, "Warning", 1==1, "Fresh")
| where trace_status!="Fresh" OR metric_status!="Fresh" OR log_status!="Fresh"
| table service_name, trace_status, trace_age_min, metric_status, metric_age_min, log_status, log_age_min
| sort trace_status, metric_status
```
- **Implementation:** Track the latest timestamp per service for each signal type (traces, metrics, logs). Calculate the age of each signal in minutes. Define freshness thresholds: traces stale after 60 minutes (services typically generate spans continuously), metrics stale after 30 minutes (collection interval is usually 10-60 seconds), logs stale after 30 minutes. Alert when any service's signal goes stale. Cross-reference with infrastructure health: if the host/pod is running (CPU/memory metrics flowing via node-level collection) but application signals stopped, the instrumentation broke, not the service. Distinguish between services that should be continuously active versus batch/scheduled services that naturally have quiet periods. Maintain an expected-schedule lookup for batch services.
- **Visualization:** Status matrix (service × signal type — green/yellow/red), Table (services with stale signals), Single value (services with all signals fresh), Line chart (stale service count trend over 7 days).
- **CIM Models:** N/A
- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)
