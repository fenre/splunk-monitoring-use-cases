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

