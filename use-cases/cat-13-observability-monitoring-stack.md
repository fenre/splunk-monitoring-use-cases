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
index=* earliest=-15m
| eval latency=_indextime-_time
| stats avg(latency) as avg_latency, perc95(latency) as p95_latency by index, sourcetype
| where p95_latency > 300
| sort -p95_latency
```
- **Implementation:** Sample events periodically and calculate `_indextime` minus `_time`. Alert when p95 latency exceeds 5 minutes for critical sourcetypes. Investigate queue buildup, network latency, or time parsing issues.
- **Visualization:** Table (sourcetypes with high latency), Line chart (latency trend), Bar chart (latency by sourcetype).
- **CIM Models:** N/A

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
| stats count by host, _time span=1h
| where count > 3
```
- **Implementation:** Tune for crash loops; join with OOM killer logs on the OS if forwarded. Alert when hourly restart count exceeds threshold.
- **Visualization:** Table (restart count by host), Timeline (restart events).
- **CIM Models:** N/A

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
- **Premium Apps:** Splunk ITSI
- **Data Sources:** `itsi_summary` index
- **SPL:**
```spl
index=itsi_summary is_service_in_maintenance=0
| timechart span=1h avg(health_score) by service_name
```
- **Implementation:** Configure ITSI services with KPIs mapped to business services. Track health scores over time. Alert on score degradation. Use for SLA reporting and executive dashboards. Configure Glass Tables for NOC display.
- **Visualization:** Service Analyzer (ITSI native), Glass Table, Line chart (health trend), Status grid.
- **CIM Models:** N/A

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

---

### UC-13.2.4 · Entity Status Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Entity health provides granular visibility into individual infrastructure components feeding services. Unstable entities degrade service health.
- **App/TA:** Splunk ITSI
- **Data Sources:** ITSI entity overview, entity health scores
- **SPL:**
```spl
| inputlookup itsi_entities
| where entity_status!="active"
| table title, entity_type, entity_status, last_seen
```
- **Implementation:** Configure entity discovery (AD, CMDB, cloud APIs). Monitor entity states (active, inactive, unstable). Alert when critical entities become inactive. Track entity population for coverage analysis.
- **Visualization:** Status grid (entities by type × status), Table (inactive entities), Single value (active entity count).
- **CIM Models:** N/A

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


---

### UC-13.2.11 · KPI Threshold Violation Trending
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Trending KPI breaches over time shows chronic vs transient service issues and validates threshold tuning.
- **App/TA:** Splunk ITSI
- **Premium Apps:** Splunk ITSI
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

---

### UC-13.2.13 · Maintenance Window Compliance
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Compliance
- **Value:** Alerts on services in maintenance flood Episode Review; verifying `is_service_in_maintenance` usage reduces noise and false escalations.
- **App/TA:** Splunk ITSI
- **Data Sources:** `index=itsi_summary`, maintenance windows via REST
- **SPL:**
```spl
index=itsi_summary is_service_in_maintenance=0
| join type=left service_name [
  | rest /servicesNS/nobody/SA-ITOA/maintenance_services
  | table title, service_name
]
| where severity_value>=4
| stats count by service_name
```
- **Implementation:** Compare active alerts against scheduled maintenance windows. Alert when KPIs fire outside declared windows for critical services (possible misconfiguration). Report on % of alerts during maintenance windows.
- **Visualization:** Table (services alerting outside window), Single value (non-compliant alert %).
- **CIM Models:** N/A

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
| join type=left service_name [
  search index=itsi_summary is_service_in_maintenance=0
  | stats latest(health_score) as health by service_name
]
| where health < 50
| table service_name, health, dependent_services
```
- **Implementation:** Validate service dependencies in ITSI. When a dependency drops below threshold, confirm dependent service health reflects impact (or use entity rules). Run weekly health of dependency graph completeness.
- **Visualization:** Service Analyzer tree, Sankey (dependency impact), Table (dependency × health).
- **CIM Models:** N/A

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
| join kpi_name [
  search index=itsi_summary kpi_threshold_type="adaptive"
  | stats dc(kpi_name) as adaptive_kpis by kpi_name
]
| where breaches > 10
```
- **Implementation:** Tag KPIs using adaptive vs static thresholds. Compare breach rate and analyst disposition before/after ML enablement. Retrain when seasonal drift causes misses.
- **Visualization:** Line chart (breaches per adaptive KPI), Table (KPIs needing threshold review).
- **CIM Models:** N/A


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
| join type=left hostname [search index=_internal group=tcpin_connections | stats latest(_time) as splunk_last by hostname]
| join type=left hostname [search index=edr sourcetype="*sensor*" | stats latest(_time) as edr_last by hostname]
| where isnull(splunk_last) AND isnull(edr_last)
| table hostname, os, department
```
- **Implementation:** Cross-reference CMDB with all monitoring tool inventories (Splunk forwarders, EDR agents, SNMP targets). Identify assets not monitored by any tool. Alert on new unmonitored assets. Track coverage percentage as a KPI.
- **Visualization:** Table (unmonitored hosts), Single value (coverage %), Pie chart (monitored vs unmonitored), Bar chart (gaps by department).
- **CIM Models:** N/A

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
| stats avg(burn_rate) as avg_burn, sum(error_budget_consumed) as consumed by service, slo_name, _time span=1h
| where avg_burn > 0.1
```
- **Implementation:** Compute SLO compliance and error budget from availability/latency data. Ingest into Splunk. Alert on burn rate above threshold or error budget exhaustion. Report on remaining budget by service.
- **Visualization:** Gauge (error budget remaining), Line chart (burn rate), Table (services by budget consumed).
- **CIM Models:** N/A

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
| stats count as spans, dc(trace_id) as traces, avg(sample_rate) as avg_sample by service, _time span=1h
| eval spans_per_trace=spans/traces
| where spans_per_trace < 5 OR avg_sample < 0.01
```
- **Implementation:** Ingest trace metadata and sampling rates. Alert when sampling drops below target or trace completeness (spans per trace) is low for critical services. Report on coverage by service and env.
- **Visualization:** Line chart (sampling rate by service), Table (low-coverage services), Bar chart (spans per trace).
- **CIM Models:** N/A

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
| stats count, avg(response_time_ms) as avg_ms by check_name, location, _time span=15m
| sort -count
```
- **Implementation:** Ingest synthetic check results from Datadog, Pingdom, or custom scripts. Alert on failure or latency above threshold. Compare success rate and latency by region. Report on SLA by check and location.
- **Visualization:** Table (failed checks by location), Geo map (failure by region), Line chart (latency by location).
- **CIM Models:** N/A

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

---

### 13.3.TE Cisco ThousandEyes — Platform Integration

---

### UC-13.3.15 · ThousandEyes Alert Severity Distribution
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Provides a centralized view of all ThousandEyes alerts in Splunk by severity, enabling SOC and NOC teams to prioritize response across network, application, and voice test alerts alongside other infrastructure alerts.
- **App/TA:** `Cisco ThousandEyes App for Splunk` (Splunkbase 7719)
- **Data Sources:** `index=thousandeyes`, ThousandEyes Alerts Stream (webhook via HEC)
- **SPL:**
```spl
`stream_index` sourcetype="thousandeyes:alerts"
| stats count by severity, alert.rule.name, alert.test.name, alert.type
| sort severity, -count
```
- **Implementation:** Configure the Alerts Stream input in the Cisco ThousandEyes App for Splunk. Select the ThousandEyes user, account group, and alert rules to receive. The app automatically creates a webhook connector in ThousandEyes and associates it with selected alert rules. Alerts flow in real-time to Splunk via HEC. The Splunk App Alerts dashboard provides pre-built panels for alert severity distribution, timeline, and drilldown.
- **Visualization:** Pie chart (alerts by severity), Bar chart (alerts by type), Table (rule, test, severity, count), Single value (active critical alerts).
- **CIM Models:** N/A

---

### UC-13.3.16 · ThousandEyes Alert Timeline Trending
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Anomaly
- **Value:** Trending alert volume over time reveals patterns — recurring issues at specific times, increasing alert frequency indicating degradation, or correlation with change windows. Helps teams move from reactive to proactive operations.
- **App/TA:** `Cisco ThousandEyes App for Splunk` (Splunkbase 7719)
- **Data Sources:** `index=thousandeyes`, ThousandEyes Alerts Stream (webhook via HEC)
- **SPL:**
```spl
`stream_index` sourcetype="thousandeyes:alerts"
| timechart span=1h count by severity
```
- **Implementation:** The Splunk App Alerts dashboard includes a "Alerts Timeline" line chart and a "Severity Distribution Trend" chart. Use these pre-built panels or customize with the `stream_index` macro. Set adaptive alerts on alert volume increases — a sudden spike in ThousandEyes alerts often precedes user-reported incidents. Correlate alert timing with change management windows.
- **Visualization:** Line chart (alerts over time by severity), Stacked bar chart (alerts per hour), Table (trending alert rules).
- **CIM Models:** N/A

---

### UC-13.3.17 · ThousandEyes Activity Log Audit Trail
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
- **Value:** Ingests ThousandEyes platform activity logs into Splunk for audit, compliance, and change tracking. Tracks who created, modified, or deleted tests, users, and alert rules — essential for troubleshooting test behavior changes and meeting compliance requirements.
- **App/TA:** `Cisco ThousandEyes App for Splunk` (Splunkbase 7719)
- **Data Sources:** `index=thousandeyes`, ThousandEyes Activity Log API
- **SPL:**
```spl
`activity_index`
| stats count by event, accountGroupName, aid
| sort -count
```
- **Implementation:** Configure the Activity Log input in the Cisco ThousandEyes App with a ThousandEyes user and account group. Activity logs are fetched at a configurable interval via the ThousandEyes API. Update the `activity_index` macro to point to the correct index. Events include test creation/modification/deletion, user management, alert rule changes, and account group configuration changes.
- **Visualization:** Table (event type, account group, count), Timeline (activity events), Pie chart (activity by event type).
- **CIM Models:** N/A

---

### UC-13.3.18 · ThousandEyes Data Collection Health Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Monitors the health of the ThousandEyes-to-Splunk data pipeline itself. Detects gaps in data collection, API errors, or HEC delivery failures that would cause blind spots in network and application monitoring.
- **App/TA:** `Cisco ThousandEyes App for Splunk` (Splunkbase 7719)
- **Data Sources:** `index=thousandeyes`, Splunk internal logs
- **SPL:**
```spl
`stream_index`
| timechart span=5m count as event_count
| where event_count < 1
```
- **Implementation:** Monitor the data flow from ThousandEyes to Splunk by tracking event volume per collection interval. A drop to zero events indicates a pipeline failure — possible causes include expired ThousandEyes API tokens, HEC token issues, or ThousandEyes streaming configuration changes. Combine with `index=_internal sourcetype=splunkd component=HttpInputDataHandler` to monitor HEC health. The Splunk App Health dashboard provides data freshness panels.
- **Visualization:** Line chart (event volume over time), Single value (events in last 5 min), Alert on zero events for >15 min.
- **CIM Models:** N/A

---

### UC-13.3.19 · ThousandEyes ITSI Service Health (Content Pack)
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability, Performance
- **Value:** The ITSI Content Pack for Cisco ThousandEyes provides pre-built service templates, KPI base searches, entity types, and Glass Tables for service-centric monitoring. It maps ThousandEyes test results to ITSI services for unified health scoring across all monitoring domains.
- **App/TA:** `Cisco ThousandEyes App for Splunk` (Splunkbase 7719), ITSI Content Pack for Cisco ThousandEyes
- **Data Sources:** `index=thousandeyes`, ThousandEyes OTel data via ITSI KPI base searches
- **SPL:**
```spl
| from datamodel:"ITSI_KPI_Summary"
| where service_name="*ThousandEyes*"
| stats latest(kpi_urgency) as urgency latest(alert_level) as alert_level by service_name, kpiid, itsi_kpi_id
| sort -urgency
```
- **Implementation:** Install the ITSI Content Pack for Cisco ThousandEyes from the ITSI Content Library. The content pack provides: entity types (ThousandEyes Test, ThousandEyes Agent), KPI base searches (latency, loss, jitter, availability, MOS for each test type), service templates, and Glass Table templates. After installation, import the service templates and configure entity discovery to match your ThousandEyes tests. KPIs are automatically populated from the ThousandEyes data model.
- **Visualization:** ITSI Service Tree, Glass Table, KPI cards (latency, loss, availability, MOS), Service health score.
- **CIM Models:** N/A

---

### UC-13.3.20 · Splunk On-Call Incident Routing from ThousandEyes
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Routes ThousandEyes alerts directly to Splunk On-Call (formerly VictorOps) for incident management, on-call paging, and war room coordination. Ensures network and application issues detected by ThousandEyes reach the right team within seconds.
- **App/TA:** ThousandEyes webhook integration with Splunk On-Call
- **Data Sources:** ThousandEyes alert webhooks
- **SPL:**
```spl
index=oncall sourcetype="oncall:incidents" monitoring_tool="ThousandEyes"
| stats count by incident_state, routing_key, entity_id
| sort -count
```
- **Implementation:** Configure ThousandEyes to send alert notifications to Splunk On-Call via the REST API endpoint webhook integration. In ThousandEyes, create a webhook notification pointing to the Splunk On-Call REST endpoint URL with your routing key. Map ThousandEyes alert severity to Splunk On-Call incident severity (critical→critical, warning→warning, info→info). The integration supports recovery messages to automatically resolve incidents when ThousandEyes alerts clear.
- **Visualization:** Table (incidents by state and routing key), Timeline (incident creation/resolution), Single value (active incidents from ThousandEyes).
- **CIM Models:** N/A

---

### UC-13.3.21 · ThousandEyes Trace Span Analysis and Drill-Down
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance
- **Value:** ThousandEyes Transaction tests can emit OpenTelemetry traces with span-level timing for each step of the scripted workflow. Ingesting these traces into Splunk enables correlation with application traces from Splunk APM for end-to-end distributed tracing.
- **App/TA:** `Cisco ThousandEyes App for Splunk` (Splunkbase 7719)
- **Data Sources:** `index=thousandeyes`, ThousandEyes OTel Tests Stream — Traces
- **SPL:**
```spl
`stream_index` sourcetype="thousandeyes:traces"
| stats count avg(duration_ms) as avg_span_duration_ms by service.name, span.name, span.kind
| sort -avg_span_duration_ms
```
- **Implementation:** Enable the Tests Stream — Traces input in the Cisco ThousandEyes App. Traces are emitted for Transaction tests and provide span-level timing for each step of the scripted workflow. The trace data follows OpenTelemetry conventions with `trace_id`, `span_id`, `parent_span_id`, `service.name`, `span.name`, `duration`, and custom attributes. Traces can be correlated with Splunk APM traces using shared context propagation.
- **Visualization:** Table (spans by duration), Trace waterfall (via Splunk APM or custom visualization), Bar chart (avg span duration by step).
- **CIM Models:** N/A

---

### UC-13.3.22 · Cross-Platform Correlation (ThousandEyes Network + Splunk APM)
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Anomaly
- **Value:** Correlates ThousandEyes network path quality data with Splunk APM application traces to determine whether performance issues are caused by the network or the application. This is the core value proposition of the Splunk + ThousandEyes integration — unified observability across network and application layers.
- **App/TA:** `Cisco ThousandEyes App for Splunk` (Splunkbase 7719), Splunk APM
- **Data Sources:** `index=thousandeyes` (network metrics), Splunk APM traces
- **SPL:**
```spl
`stream_index` thousandeyes.test.type="agent-to-server"
| stats avg(network.latency) as avg_net_latency_s avg(network.loss) as avg_net_loss by server.address, _time span=5m
| join type=outer server.address [
  search index=apm_traces
  | stats avg(duration_ms) as avg_app_latency_ms p99(duration_ms) as p99_app_latency_ms by service.name, server.address, _time span=5m
]
| eval avg_net_latency_ms=round(avg_net_latency_s*1000,1)
| eval root_cause=case(avg_net_latency_ms>200 AND avg_app_latency_ms<500, "Network", avg_net_latency_ms<50 AND avg_app_latency_ms>2000, "Application", avg_net_latency_ms>200 AND avg_app_latency_ms>2000, "Both", 1=1, "Normal")
| where root_cause!="Normal"
| table _time, server.address, service.name, avg_net_latency_ms, avg_net_loss, avg_app_latency_ms, root_cause
```
- **Implementation:** This correlation requires both ThousandEyes network data and Splunk APM trace data indexed in Splunk. The key join field is the server address or service endpoint. When network latency is high but application processing is fast, the network is the bottleneck. When network latency is low but application response is slow, the issue is in the application. This "network vs. app" isolation significantly reduces MTTR by directing the right team to investigate.
- **Visualization:** Table (endpoint, network latency, app latency, root cause), Dual-axis chart (network vs app latency), Dashboard with network and app panels side-by-side.
- **CIM Models:** N/A

---

### UC-13.3.23 · MTTR Reduction via Network vs Application Isolation
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Anomaly
- **Value:** Quantifies the business value of ThousandEyes + Splunk integration by measuring how quickly teams can isolate whether a performance issue is network-caused or application-caused. Tracks Mean Time to Resolution and Mean Time to Isolate metrics for incidents where ThousandEyes data was available.
- **App/TA:** `Cisco ThousandEyes App for Splunk` (Splunkbase 7719)
- **Data Sources:** `index=thousandeyes` (alerts, events), incident management system data
- **SPL:**
```spl
`stream_index` sourcetype="thousandeyes:alerts"
| stats earliest(_time) as alert_start latest(_time) as alert_end by alert.rule.name, alert.test.name
| eval mtti_minutes=round((alert_end-alert_start)/60,1)
| join type=outer alert.test.name [
  search `event_index`
  | stats earliest(_time) as event_start latest(state) as final_state by thousandeyes.test.name
  | rename thousandeyes.test.name as alert.test.name
]
| eval isolation_method=if(isnotnull(event_start), "ThousandEyes Event + Alert", "ThousandEyes Alert Only")
| stats avg(mtti_minutes) as avg_mtti count by isolation_method
```
- **Implementation:** This meta-analysis use case measures how ThousandEyes data accelerates incident resolution. Track the time from ThousandEyes alert trigger to resolution (MTTR). Compare MTTR for incidents where ThousandEyes data was available vs. those without. Over time, this demonstrates the ROI of the ThousandEyes + Splunk integration. Combine with ITSM data (ServiceNow, Jira Service Management) for complete MTTR tracking.
- **Visualization:** Single value (avg MTTR with ThousandEyes), Comparison chart (MTTR with vs. without TE data), Table (incidents and isolation times), Trend line (MTTR improvement over time).
- **CIM Models:** N/A

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
| eventstats count as reqs_per_src by src_ip
| where status>=400 OR duration_ms>60000 OR reqs_per_src>100
| eval suspicious=if(reqs_per_src>100,"high_volume",if(match(user_agent,"curl|python-requests"),"scripted","normal"))
| stats count, dc(path) as paths, values(user_agent) as ua by src_ip, host, suspicious
| where count>50 OR match(ua,"(?i)(scanner|masscan)")
```
- **Implementation:** Forward Ollama access logs with client IP, path, model, duration, and status. Tune ESCU detections for unusual volume, off-hours spikes, and known scanner user agents. Block or rate-limit at the network edge based on Splunk alerts. Enrich with asset and identity lookups where available.
- **Visualization:** Map (source IPs), Table (suspicious sessions), Timeline (request bursts).
- **CIM Models:** N/A

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
