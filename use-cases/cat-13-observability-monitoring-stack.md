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
```
N/A — Glass Tables are configured via ITSI UI, not SPL
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

