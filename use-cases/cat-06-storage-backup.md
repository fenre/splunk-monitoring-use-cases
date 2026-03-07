## 6. Storage & Backup

### 6.1 SAN / NAS Storage

**Primary App/TA:** Vendor-specific TAs — NetApp TA (`TA-netapp_ontap`), Dell EMC TA, Pure Storage TA; SNMP TA for generic arrays; scripted/API inputs for REST-based arrays.

---

### UC-6.1.1 · Volume Capacity Trending
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity
- **Value:** Prevents application outages caused by full volumes. Enables proactive capacity planning and procurement.
- **App/TA:** Vendor TA (e.g., `TA-netapp_ontap`) or scripted API input
- **Data Sources:** Storage array REST API metrics, SNMP hrStorageTable
- **SPL:**
```spl
index=storage sourcetype="netapp:ontap:volume"
| timechart span=1d avg(size_used_percent) as pct_used by volume_name
| where pct_used > 85
```
- **Implementation:** Deploy vendor TA on a heavy forwarder. Configure REST API polling (every 15 min) for volume metrics. Create alert for >85% and >95% thresholds. Build capacity forecast using `predict` command.
- **Visualization:** Line chart (capacity trend per volume), Single value (current % used), Table (volumes above threshold).
- **CIM Models:** N/A

---

### UC-6.1.2 · Storage Latency Monitoring
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Fault
- **Value:** High storage latency directly impacts application performance. Early detection prevents SLA breaches and user experience degradation.
- **App/TA:** Vendor TA or SNMP polling
- **Data Sources:** Array performance metrics (avg_latency, read_latency, write_latency)
- **SPL:**
```spl
index=storage sourcetype="netapp:ontap:volume_perf"
| timechart span=5m avg(avg_latency) as latency_ms by volume_name
| where latency_ms > 20
```
- **Implementation:** Poll latency metrics via REST or SNMP every 5 minutes. Set tiered alerts: warning >10ms, critical >20ms for production volumes. Correlate with IOPS spikes to distinguish overload from hardware issues.
- **Visualization:** Line chart (latency over time by volume), Heatmap (volume × time), Single value (current avg latency).
- **CIM Models:** N/A

---

### UC-6.1.3 · IOPS Trending per Volume
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity
- **Value:** Identifies workload hotspots and enables data placement optimization. Supports capacity planning for storage refreshes.
- **App/TA:** Vendor TA or SNMP
- **Data Sources:** Array performance metrics (read_ops, write_ops, other_ops)
- **SPL:**
```spl
index=storage sourcetype="netapp:ontap:volume_perf"
| timechart span=15m sum(total_ops) as iops by volume_name
| sort -iops
```
- **Implementation:** Collect IOPS metrics per volume/LUN at 5-15 min intervals. Baseline normal patterns and alert on deviations exceeding 2× baseline. Correlate with application deployment events.
- **Visualization:** Line chart (IOPS trend by volume), Stacked bar (read vs write IOPS), Table (top IOPS consumers).
- **CIM Models:** N/A

---

### UC-6.1.4 · Disk Failure Alerts
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Fault
- **Value:** Immediate awareness of disk failures allows replacement before RAID degradation leads to data loss.
- **App/TA:** Vendor TA, SNMP traps
- **Data Sources:** Array event/alert logs, SNMP traps
- **SPL:**
```spl
index=storage sourcetype="netapp:ontap:ems" severity="EMERGENCY" OR severity="ALERT"
| search disk_fail* OR disk_broken OR disk_error
| table _time, node, disk, severity, message
```
- **Implementation:** Enable SNMP traps or syslog forwarding for disk failure events. Create high-priority alert with PagerDuty/ServiceNow integration. Track spare disk inventory to ensure replacements are available.
- **Visualization:** Single value (failed disk count), Table (failed disks with details), Timeline (failure events).
- **CIM Models:** N/A

---

### UC-6.1.5 · Replication Lag Monitoring
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Replication lag directly impacts RPO. Monitoring ensures DR readiness and compliance with data protection SLAs.
- **App/TA:** Vendor TA, REST API polling
- **Data Sources:** Array replication status (SnapMirror, RecoverPoint, etc.)
- **SPL:**
```spl
index=storage sourcetype="netapp:ontap:snapmirror"
| eval lag_minutes=lag_time/60
| where lag_minutes > 60
| table _time, source_volume, destination_volume, lag_minutes, state
```
- **Implementation:** Poll replication status every 15 minutes. Alert when lag exceeds RPO target (e.g., >60 min for hourly replication). Track replication state (idle, transferring, broken-off) and alert on non-healthy states.
- **Visualization:** Single value (max replication lag), Table (replication pairs with lag), Line chart (lag over time).
- **CIM Models:** N/A

---

### UC-6.1.6 · Controller Failover Events
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Controller failovers indicate hardware problems and may cause transient performance impact. Quick detection ensures rapid root cause analysis.
- **App/TA:** Vendor TA, syslog
- **Data Sources:** Array event logs, cluster status
- **SPL:**
```spl
index=storage sourcetype="netapp:ontap:ems"
| search "cf.takeover*" OR "cf.giveback*" OR failover
| table _time, node, event, message
```
- **Implementation:** Forward array event logs (syslog or API) to Splunk. Filter for failover/takeover events. Create critical alert with incident auto-creation. Track MTBF between failover events per controller.
- **Visualization:** Timeline (failover events), Single value (days since last failover), Table (event details).
- **CIM Models:** N/A

---

### UC-6.1.7 · Thin Provisioning Overcommit
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Capacity
- **Value:** Over-committed thin-provisioned storage can cause sudden outages when physical capacity is exhausted. Monitoring prevents surprise failures.
- **App/TA:** Vendor TA, API polling
- **Data Sources:** Aggregate/pool capacity metrics (logical vs physical)
- **SPL:**
```spl
index=storage sourcetype="netapp:ontap:aggregate"
| eval overcommit_ratio=logical_used/physical_used
| where overcommit_ratio > 1.5
| table aggregate, physical_used_pct, logical_used, overcommit_ratio
```
- **Implementation:** Poll aggregate/pool metrics showing logical vs physical capacity. Calculate overcommit ratio. Alert when physical utilization exceeds safe thresholds relative to committed capacity.
- **Visualization:** Gauge (overcommit ratio per pool), Table (aggregates with overcommit stats), Bar chart (logical vs physical).
- **CIM Models:** N/A

---

### UC-6.1.8 · Snapshot Space Consumption
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity
- **Value:** Runaway snapshot growth can consume all available space, causing volume and application outages.
- **App/TA:** Vendor TA, REST API
- **Data Sources:** Snapshot usage metrics per volume
- **SPL:**
```spl
index=storage sourcetype="netapp:ontap:volume"
| eval snap_pct=snapshot_used_bytes/size_total*100
| where snap_pct > 20
| table volume_name, snap_pct, snapshot_used_bytes, snapshot_count
| sort -snap_pct
```
- **Implementation:** Poll snapshot usage per volume. Alert when snapshot reserve exceeds threshold (e.g., >20% of volume). Track snapshot count and age. Create scheduled report for snapshot cleanup candidates.
- **Visualization:** Bar chart (snapshot usage by volume), Table (volumes with high snapshot usage), Line chart (snapshot growth trend).
- **CIM Models:** N/A

---

### UC-6.1.9 · Fibre Channel Port Errors
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** FC port errors cause storage performance degradation and potential path failovers. Early detection prevents cascading failures.
- **App/TA:** SNMP TA, FC switch syslog
- **Data Sources:** FC switch logs (Brocade, Cisco MDS), SNMP IF-MIB
- **SPL:**
```spl
index=network sourcetype="brocade:syslog" OR sourcetype="cisco:mds"
| search CRC_error OR link_failure OR signal_loss OR sync_loss
| stats count by switch, port, error_type
| where count > 10
```
- **Implementation:** Forward FC switch syslog to Splunk. Poll SNMP counters for FC error rates. Alert on error rate exceeding baseline. Correlate with storage latency spikes to identify fabric issues.
- **Visualization:** Table (ports with errors), Bar chart (error counts by type), Timeline (error events).
- **CIM Models:** N/A

---

### UC-6.1.10 · Storage Array Firmware Compliance
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Value:** Outdated firmware exposes arrays to known bugs and security vulnerabilities. Compliance tracking supports patching cadence.
- **App/TA:** Vendor TA, scripted inventory input
- **Data Sources:** Array system info (firmware version, model), vendor advisory feeds
- **SPL:**
```spl
index=storage sourcetype="netapp:ontap:system"
| stats latest(version) as firmware by node, model
| lookup approved_firmware_versions model OUTPUT approved_version
| where firmware!=approved_version
| table node, model, firmware, approved_version
```
- **Implementation:** Poll system version info periodically (daily). Maintain a lookup table of approved firmware versions per model. Alert when arrays are running non-approved versions. Report on fleet firmware distribution.
- **Visualization:** Table (arrays with firmware status), Pie chart (firmware version distribution), Single value (% compliant).
- **CIM Models:** N/A

---

### 6.2 Object Storage

**Primary App/TA:** Cloud provider TAs (`Splunk_TA_aws`, `Splunk_TA_microsoft-cloudservices`), MinIO webhook inputs, custom REST API inputs.

---

### UC-6.2.1 · Bucket Capacity Trending
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Capacity
- **Value:** Tracks storage growth for cost forecasting and lifecycle policy effectiveness. Prevents unexpected cloud bills.
- **App/TA:** `Splunk_TA_aws` (CloudWatch), Splunk_TA_microsoft-cloudservices
- **Data Sources:** CloudWatch S3 metrics (BucketSizeBytes), Azure Blob metrics
- **SPL:**
```spl
index=aws sourcetype="aws:cloudwatch" metric_name="BucketSizeBytes"
| timechart span=1d latest(Average) as size_bytes by bucket_name
| eval size_gb=size_bytes/1024/1024/1024
```
- **Implementation:** Enable S3 storage metrics in CloudWatch (request metrics may incur cost). Ingest via Splunk Add-on for AWS. Create trending reports by bucket and apply `predict` for growth forecasting.
- **Visualization:** Line chart (bucket size over time), Stacked area (total storage by bucket), Table (largest buckets).
- **CIM Models:** N/A

---

### UC-6.2.2 · Access Pattern Anomalies
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Security
- **Value:** Unusual access patterns may indicate data breaches, compromised credentials, or misconfigured applications.
- **App/TA:** `Splunk_TA_aws` (S3 access logs), Azure Blob diagnostics
- **Data Sources:** S3 access logs, Azure Blob analytics logs
- **SPL:**
```spl
index=aws sourcetype="aws:s3:accesslogs"
| stats count by bucket_name, requester, operation
| eventstats avg(count) as avg_ops, stdev(count) as stdev_ops by bucket_name, operation
| where count > avg_ops + 3*stdev_ops
```
- **Implementation:** Enable S3 server access logging to a dedicated logging bucket. Ingest via SQS-based S3 input. Baseline normal access patterns and alert on statistical outliers. Correlate with IAM changes.
- **Visualization:** Line chart (access volume over time), Table (anomalous access events), Bar chart (operations by requester).
- **CIM Models:** N/A

---

### UC-6.2.3 · Public Bucket Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
- **Value:** Public buckets are a top cloud security risk, leading to data breaches. Immediate detection is essential for compliance.
- **App/TA:** `Splunk_TA_aws` (Config), Azure Policy
- **Data Sources:** AWS Config rules, S3 ACL/policy evaluations
- **SPL:**
```spl
index=aws sourcetype="aws:config:rule"
| search configRuleName="s3-bucket-public-read-prohibited" OR configRuleName="s3-bucket-public-write-prohibited"
| where complianceType="NON_COMPLIANT"
| table _time, resourceId, configRuleName, complianceType
```
- **Implementation:** Enable AWS Config rules for S3 public access. Ingest Config compliance data. Create critical alert for any NON_COMPLIANT result. Also monitor S3 Block Public Access settings at account level.
- **Visualization:** Single value (public bucket count — should be 0), Table (non-compliant buckets), Status indicator (red/green).
- **CIM Models:** N/A

---

### UC-6.2.4 · Lifecycle Policy Compliance
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Configuration
- **Value:** Ensures storage cost optimization policies are working. Objects not transitioning per policy waste money.
- **App/TA:** Cloud provider TAs
- **Data Sources:** CloudWatch storage class metrics, lifecycle action logs
- **SPL:**
```spl
index=aws sourcetype="aws:cloudwatch" metric_name="BucketSizeBytes"
| stats latest(Average) as size by bucket_name, StorageType
| xyseries bucket_name StorageType size
```
- **Implementation:** Monitor storage class distribution per bucket over time. Compare against defined lifecycle policies. Alert when objects remain in expensive storage classes longer than policy dictates.
- **Visualization:** Stacked bar (storage class distribution per bucket), Table (policy violations), Pie chart (total storage by class).
- **CIM Models:** N/A

---

### UC-6.2.5 · Cross-Region Replication Lag
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Replication lag affects DR readiness. Monitoring ensures geo-redundant data meets RPO requirements.
- **App/TA:** Cloud provider TAs
- **Data Sources:** S3 replication metrics (ReplicationLatency, OperationsPendingReplication)
- **SPL:**
```spl
index=aws sourcetype="aws:cloudwatch" metric_name="ReplicationLatency"
| timechart span=1h avg(Average) as replication_lag_sec by bucket_name
| where replication_lag_sec > 3600
```
- **Implementation:** Enable S3 replication metrics in CloudWatch. Ingest and alert when replication latency or pending operations exceed thresholds. Correlate with data ingestion spikes that may cause temporary lag.
- **Visualization:** Line chart (replication lag over time), Single value (max lag), Table (buckets with lag exceeding SLA).
- **CIM Models:** N/A

---

### 6.3 Backup & Recovery

**Primary App/TA:** Vendor-specific TAs — Veeam TA (`TA-veeam`), Commvault TA, Veritas NetBackup TA; scripted inputs for API-based platforms (Rubrik, Cohesity).

---

### UC-6.3.1 · Backup Job Success Rate
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Compliance
- **Value:** Failed backups leave systems unprotected. Tracking success rate ensures recoverability and compliance with data protection policies.
- **App/TA:** Veeam App for Splunk, Commvault Splunk App, or scripted API input
- **Data Sources:** Backup server job logs (job name, status, start/end time, data size)
- **SPL:**
```spl
index=backup sourcetype="veeam:job"
| stats count(eval(status="Success")) as success, count(eval(status="Failed")) as failed, count as total by job_name
| eval success_rate=round(success/total*100,1)
| where success_rate < 100
| sort success_rate
```
- **Implementation:** Install vendor TA or configure scripted input to poll backup API. Ingest job completion events. Create daily report of job outcomes. Alert immediately on any failure for critical systems.
- **Visualization:** Single value (overall success rate %), Table (failed jobs with details), Bar chart (success/fail by job), Trend line (daily success rate).
- **CIM Models:** N/A

---

### UC-6.3.2 · Backup Job Duration Trending
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity
- **Value:** Increasing backup durations signal data growth, network congestion, or storage performance issues. Prevents backup window overruns.
- **App/TA:** Vendor TA
- **Data Sources:** Backup job logs (start/end timestamps, data transferred)
- **SPL:**
```spl
index=backup sourcetype="veeam:job" status="Success"
| eval duration_min=(end_time-start_time)/60
| timechart span=1d avg(duration_min) as avg_duration by job_name
```
- **Implementation:** Calculate job duration from start/end timestamps. Track trend over weeks/months. Alert when duration exceeds historical average by >50%. Correlate with data volume changes.
- **Visualization:** Line chart (duration trend per job), Table (longest running jobs), Bar chart (avg duration by job).
- **CIM Models:** N/A

---

### UC-6.3.3 · Missed Backup Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Compliance
- **Value:** A backup that doesn't run at all is worse than one that fails — it's invisible. Detection ensures no system is left unprotected.
- **App/TA:** Vendor TA, custom correlation
- **Data Sources:** Backup scheduler logs, expected schedule lookup
- **SPL:**
```spl
| inputlookup backup_schedule.csv
| join type=left job_name
    [search index=backup sourcetype="veeam:job" earliest=-24h
     | stats latest(_time) as last_run by job_name]
| where isnull(last_run) OR last_run < relative_time(now(), "-26h")
| table job_name, expected_schedule, last_run
```
- **Implementation:** Maintain a lookup table of expected backup schedules. Run a scheduled search comparing expected vs actual runs. Alert when any job misses its window. Correlate with backup server health events.
- **Visualization:** Table (missed jobs with schedule details), Single value (number of missed jobs), Status grid (job name × date).
- **CIM Models:** N/A

---

### UC-6.3.4 · Backup Storage Capacity
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Capacity
- **Value:** Running out of backup repository space causes all backup jobs to fail. Proactive monitoring prevents cascading failures.
- **App/TA:** Vendor TA, scripted input
- **Data Sources:** Backup repository/tape library capacity metrics
- **SPL:**
```spl
index=backup sourcetype="veeam:repository"
| eval pct_used=round(used_space/total_space*100,1)
| where pct_used > 80
| table repository_name, total_space_gb, used_space_gb, pct_used
```
- **Implementation:** Poll backup repository capacity via API or scripted input. Alert at 80% and 90% thresholds. Track growth rate and forecast when capacity will be exhausted using `predict`.
- **Visualization:** Gauge (% used per repository), Line chart (capacity trend), Table (repositories above threshold).
- **CIM Models:** N/A

---

### UC-6.3.5 · Restore Test Tracking
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Value:** Backups are worthless if restores fail. Tracking restore tests ensures confidence in recoverability and satisfies audit requirements.
- **App/TA:** Manual/scripted input, backup TA
- **Data Sources:** Restore test logs, manual test result entries
- **SPL:**
```spl
index=backup sourcetype="restore_test"
| stats latest(_time) as last_test, latest(result) as result by system_name
| eval days_since_test=round((now()-last_test)/86400)
| where days_since_test > 90 OR result!="Success"
| table system_name, last_test, result, days_since_test
```
- **Implementation:** Log all restore test results (automated or manual) to a dedicated index. Maintain a lookup of systems requiring quarterly restore tests. Alert when any system exceeds 90 days without a successful test.
- **Visualization:** Table (systems with test status), Single value (% tested in last 90d), Status grid (system × quarter).
- **CIM Models:** N/A

---

### UC-6.3.6 · Backup SLA Compliance
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Compliance
- **Value:** Consolidated view of backup coverage and RPO/RTO compliance. Essential for management reporting and audit evidence.
- **App/TA:** Combined backup data + CMDB lookup
- **Data Sources:** Backup job logs, CMDB/asset inventory
- **SPL:**
```spl
| inputlookup cmdb_systems.csv WHERE requires_backup="yes"
| join type=left system_name
    [search index=backup sourcetype="veeam:job" status="Success" earliest=-7d
     | stats latest(_time) as last_backup, max(data_size) as backup_size by system_name]
| eval compliant=if(isnotnull(last_backup),"Yes","No")
| stats count(eval(compliant="Yes")) as covered, count as total
| eval coverage_pct=round(covered/total*100,1)
```
- **Implementation:** Cross-reference CMDB inventory with backup job data. Identify systems with no backup coverage. Calculate RPO compliance (time since last successful backup vs required RPO). Produce weekly executive report.
- **Visualization:** Single value (SLA compliance %), Table (non-compliant systems), Pie chart (covered vs uncovered), Dashboard with filters by business unit.
- **CIM Models:** N/A

---

### UC-6.3.7 · Backup Data Volume Trending
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity
- **Value:** Tracks data growth rate for capacity planning of backup infrastructure. Identifies unexpected data surges early.
- **App/TA:** Vendor TA
- **Data Sources:** Backup job statistics (data transferred per job)
- **SPL:**
```spl
index=backup sourcetype="veeam:job" status="Success"
| timechart span=1d sum(data_transferred_gb) as daily_volume
| predict daily_volume as predicted future_timespan=30
```
- **Implementation:** Sum data transferred across all backup jobs daily. Track trend and apply predictive analytics for 30/60/90-day forecasts. Compare against available repository capacity.
- **Visualization:** Line chart (daily backup volume with prediction), Bar chart (volume by job type), Single value (total backed up today).
- **CIM Models:** N/A

---

### UC-6.3.8 · Tape Library Health
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Fault
- **Value:** Tape media and drive failures can silently corrupt backups. Monitoring ensures long-term archival reliability.
- **App/TA:** SNMP TA, vendor syslog
- **Data Sources:** Tape library logs, SNMP traps, drive error counters
- **SPL:**
```spl
index=backup sourcetype="tape_library"
| search media_error OR drive_error OR cleaning_required
| stats count by library, drive_id, error_type
| where count > 0
```
- **Implementation:** Forward tape library syslog to Splunk. Poll SNMP for drive error counters and media faults. Alert on drive errors, media faults, or cleaning cartridge expiration. Track tape media lifecycle.
- **Visualization:** Table (drive/media errors), Single value (drives needing attention), Timeline (error events).
- **CIM Models:** N/A

---

### 6.4 File Services

**Primary App/TA:** Splunk Add-on for Microsoft Windows (`Splunk_TA_windows`) for file audit events; NFS syslog; Varonis TA for advanced file analytics.

---

### UC-6.4.1 · File Access Audit
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Compliance
- **Value:** Provides full audit trail of file access for compliance (SOX, HIPAA, PCI-DSS). Enables investigation of data breaches and unauthorized access.
- **App/TA:** `Splunk_TA_windows` (Security Event Log)
- **Data Sources:** Windows Security Event Log (Event ID 4663 — object access), NFS access logs
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode=4663
| stats count by Account_Name, ObjectName, AccessMask
| sort -count
| head 50
```
- **Implementation:** Enable "Audit Object Access" via GPO on file servers. Configure SACLs on sensitive folders. Forward Security logs via Universal Forwarder. Filter high-volume events to focus on sensitive paths.
- **Visualization:** Table (user, file, access type, count), Bar chart (top accessed files), Timeline (access events for specific files).
- **CIM Models:** N/A

---

### UC-6.4.2 · Ransomware Indicator Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Ransomware causes mass file encryption in minutes. Detecting the pattern early can limit damage by triggering automated isolation.
- **App/TA:** `Splunk_TA_windows`, custom alert logic
- **Data Sources:** Windows Security Event Log (4663, 4656, 4659 — file create/modify/delete)
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode=4663
| bucket _time span=1m
| stats dc(ObjectName) as unique_files count by Account_Name, _time
| where unique_files > 100 AND count > 500
```
- **Implementation:** Enable file audit logging on critical file shares. Create high-urgency alert for mass file modification patterns (>100 unique files modified by one user in 1 minute). Integrate with SOAR for automated account disable/network isolation.
- **Visualization:** Single value (files modified per minute — current), Line chart (modification rate over time), Table (users with anomalous activity).
- **CIM Models:** N/A

---

### UC-6.4.3 · DFS Replication Health
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** DFS-R backlog and conflicts indicate replication failures that can lead to data inconsistency and user complaints.
- **App/TA:** `Splunk_TA_windows` (DFS-R event logs)
- **Data Sources:** DFS Replication event log (Event IDs 4012, 4302, 4304, 5002, 5008)
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:DFS Replication"
| search EventCode=4302 OR EventCode=4304 OR EventCode=5002
| stats count by EventCode, ComputerName, ReplicationGroupName
| sort -count
```
- **Implementation:** Forward DFS Replication event logs from all DFS servers. Monitor backlog size via `dfsrdiag backlog` scripted input. Alert on replication conflicts and high backlog counts. Track resolution time.
- **Visualization:** Table (replication groups with backlog), Line chart (backlog trend), Single value (total conflicts today).
- **CIM Models:** N/A

---

### UC-6.4.4 · Share Permission Changes
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security, Configuration
- **Value:** Unauthorized permission changes can expose sensitive data. Change detection supports compliance and security posture.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** Windows Security Event Log (Event IDs 4670 — permissions changed, 5143 — share modified)
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode=4670 OR EventCode=5143
| table _time, Account_Name, ObjectName, ObjectServer, ProcessName
| sort -_time
```
- **Implementation:** Enable "Audit Policy Change" and "Audit File System" via GPO. Forward Security events from file servers. Alert on any permission change to critical shares. Correlate with change management tickets.
- **Visualization:** Table (permission changes with details), Timeline (change events), Bar chart (changes by user).
- **CIM Models:** N/A

---

### UC-6.4.5 · Large File Transfer Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Unusually large file copies may indicate data exfiltration. Detection supports data loss prevention and insider threat programs.
- **App/TA:** `Splunk_TA_windows`, network flow data
- **Data Sources:** Windows file audit logs, SMB session logs
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode=4663 AccessMask="0x1"
| stats sum(Size) as total_bytes, dc(ObjectName) as file_count by Account_Name, src_ip
| eval total_gb=round(total_bytes/1024/1024/1024,2)
| where total_gb > 1
| sort -total_gb
```
- **Implementation:** Monitor file read events and correlate with SMB session data for volume estimates. Baseline normal transfer patterns per user. Alert when transfers exceed threshold (e.g., >1GB in single session). Correlate with HR/departure lists.
- **Visualization:** Table (users with large transfers), Bar chart (transfer volume by user), Line chart (daily transfer volume trend).
- **CIM Models:** N/A

---

