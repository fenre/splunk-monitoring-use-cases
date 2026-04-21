## 6. Storage & Backup

### 6.1 SAN / NAS Storage

**Primary App/TA:** Vendor-specific TAs — NetApp TA (`TA-netapp_ontap`), Dell EMC TA, Pure Storage TA; SNMP TA for generic arrays; scripted/API inputs for REST-based arrays.

---

### UC-6.1.1 · Volume Capacity Trending
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Wave:** 🐢 crawl
- **Monitoring type:** Capacity
- **Value:** Prevents application outages caused by full volumes. Enables proactive capacity planning and procurement.
- **App/TA:** Vendor TA (e.g., `TA-netapp_ontap`) or scripted API input
- **Data Sources:** Storage array REST API metrics, SNMP hrStorageTable
- **SPL:**
```spl
index=storage sourcetype="netapp:ontap:volume"
| stats latest(size_used_percent) as pct_used by volume_name
| where pct_used > 85
| sort -pct_used
```
- **Implementation:** Deploy vendor TA on a heavy forwarder. Configure REST API polling (every 15 min) for volume metrics. Create alert for >85% and >95% thresholds. Build capacity forecast using `predict` command.
- **Visualization:** Line chart (capacity trend per volume), Single value (current % used), Table (volumes above threshold).
- **CIM Models:** N/A
- **References:** [Splunk Add-on for NetApp](https://splunkbase.splunk.com/app/1664), vendor REST/SNMP documentation
- **Known false positives:** Temporary spikes during snapshots or replication; use rolling average or exclude known maintenance windows.

---

### UC-6.1.2 · Storage Latency Monitoring
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Wave:** 🐢 crawl
- **Monitoring type:** Fault
- **Value:** High storage latency directly impacts application performance. Early detection prevents SLA breaches and user experience degradation.
- **App/TA:** Vendor TA or SNMP polling
- **Data Sources:** Array performance metrics (avg_latency, read_latency, write_latency)
- **SPL:**
```spl
index=storage sourcetype="netapp:ontap:volume_perf"
| stats avg(avg_latency) as latency_ms by volume_name
| where latency_ms > 20
| sort -latency_ms
```
- **Implementation:** Poll latency metrics via REST or SNMP every 5 minutes. Set tiered alerts: warning >10ms, critical >20ms for production volumes. Correlate with IOPS spikes to distinguish overload from hardware issues.
- **Visualization:** Line chart (latency over time by volume), Heatmap (volume × time), Single value (current avg latency).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-6.1.4 · Disk Failure Alerts
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Wave:** 🐢 crawl
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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-6.1.6 · Controller Failover Events
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Wave:** 🐢 crawl
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
- **Implementation:** For NetApp ONTAP: ingest EMS events via syslog (UDP/TCP) or use `TA-netapp_ontap` for REST-based EMS polling. Key EMS message families: `cf.takeover`, `cf.giveback`, `ha.interconnect`. Alert on any takeover outside a scheduled change window, or any giveback failure. Include `cluster`, `node`, and `partner` fields in the alert for storage operations handoff.
- **Visualization:** Timeline (failover events), Single value (days since last failover), Table (event details).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-6.1.9 · Fibre Channel Port Errors
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** FC port errors cause storage performance degradation and potential path failovers. Early detection prevents cascading failures.
- **App/TA:** SNMP TA, FC switch syslog
- **Equipment Models:** Cisco MDS 9132T, MDS 9148T, MDS 9396T, MDS 9700, MDS 9706, MDS 9710
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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-6.1.11 · Isilon Cluster and Node Health
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault, Performance
- **Value:** Dell EMC Isilon (OneFS) is a scale-out NAS platform. Monitoring node and cluster health ensures availability and early detection of hardware or software issues before data access is impacted.
- **App/TA:** Splunk Add-on for Dell EMC Isilon (if available), or REST/API polling of OneFS platform API, syslog from Isilon nodes
- **Data Sources:** OneFS platform API (cluster/node status, events), Isilon syslog, SNMP (if enabled)
- **SPL:**
```spl
index=storage (sourcetype=isilon:syslog OR sourcetype=isilon:api) (node_down OR cluster_offline OR "degraded" OR "readonly")
| table _time, node, cluster, severity, message
```
- **Implementation:** Configure syslog from Isilon cluster to Splunk; optionally use OneFS REST API or vendor TA for node state, drive status, and cluster events. Alert on node down, pool degradation, or OneFS readonly conditions.
- **Visualization:** Single value (nodes down), Table (node/cluster status), Timeline (health events). Aligns with use cases in Splunk IT Essentials Learn (Storage – Isilon).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-6.1.12 · Isilon Capacity and Performance Trending
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity, Performance
- **Value:** Tracks Isilon cluster capacity and throughput (e.g. ops/sec, throughput MB/s) for capacity planning and performance troubleshooting. Matches IT Essentials Learn procedures for Isilon storage.
- **App/TA:** OneFS API or vendor add-on for Isilon metrics
- **Data Sources:** OneFS statistics (capacity by pool/node, read/write ops, network throughput)
- **SPL:**
```spl
index=storage sourcetype=isilon:metrics
| timechart span=1h avg(capacity_used_pct) as pct_used, avg(ops_per_sec) as iops by node
| where pct_used > 80
```
- **Implementation:** Poll OneFS stats API or use Isilon TA to collect capacity and performance metrics. Set alerts for pool capacity >85% and for sustained high latency or drop in throughput.
- **Visualization:** Line chart (capacity and IOPS over time by node/pool), Single value (cluster used %), Table (top consumers).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-6.1.13 · TrueNAS / FreeNAS Pool Health
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault, Availability
- **Value:** ZFS pool degradation, scrub results, and resilver progress directly impact data integrity. Early detection of unhealthy pools prevents data loss and enables timely intervention during rebuilds.
- **App/TA:** Custom (TrueNAS REST API)
- **Data Sources:** TrueNAS API (/api/v2.0/pool, /api/v2.0/pool/id/X)
- **SPL:**
```spl
index=storage sourcetype="truenas:pool"
| search status!="ONLINE" OR health!="HEALTHY" OR "resilver" OR "scrub"
| eval health_status=coalesce(health, status)
| table _time, pool_name, health_status, status, size, used_pct, resilver_progress, scrub_status
| sort -_time
```
- **Implementation:** Create scripted input or HTTP Event Collector (HEC) input that polls TrueNAS REST API every 5–15 minutes. Use `/api/v2.0/pool` for pool list and `/api/v2.0/pool/id/{id}` for detailed status including scrub/resilver. Authenticate with API key. Parse JSON response and index to Splunk with sourcetype `truenas:pool`. Alert on health != HEALTHY or status != ONLINE. Track resilver progress and ETA during rebuilds.
- **Visualization:** Single value (pools not healthy), Table (pool name, health, resilver %), Timeline (health change events), Gauge (resilver progress during rebuild).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-6.1.14 · Ceph Cluster Health and OSD Status
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Availability, Fault
- **Value:** Ceph health warnings, OSD down/out events, and placement group (PG) state issues can lead to data unavailability or loss. Monitoring ensures rapid response to cluster degradation.
- **App/TA:** Custom scripted input (ceph status --format json)
- **Data Sources:** ceph status JSON, ceph osd tree, ceph pg stat
- **SPL:**
```spl
index=storage sourcetype="ceph:status"
| search health!="HEALTH_OK" OR osd_down>0 OR osd_out>0 OR "degraded" OR "stuck"
| eval pg_degraded=if(match(pg_summary, "degraded"), 1, 0)
| table _time, health, health_detail, osd_down, osd_out, osd_up, pg_degraded, pg_summary
| sort -_time
```
- **Implementation:** Run `ceph status --format json` and `ceph osd tree --format json` via cron or Splunk scripted input every 5 minutes. Parse JSON and extract health, osd_map (num_up, num_in, num_down), and pg_summary. Index to Splunk. Alert on health != HEALTH_OK, osd_down > 0, osd_out > 0, or PG states containing "degraded" or "stuck". Correlate OSD events with disk failure logs.
- **Visualization:** Single value (cluster health status), Table (OSD up/down/out counts), Timeline (health and OSD events), Bar chart (PG states distribution).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-6.1.15 · NFS Export Availability
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** NFS mount point reachability and latency directly affect application availability. Monitoring from client perspective ensures end-to-end access validation.
- **App/TA:** Custom scripted input (showmount, mount probes)
- **Data Sources:** NFS mount probe results, rpcinfo output
- **SPL:**
```spl
index=storage sourcetype="nfs:probe"
| search status!="ok" OR latency_ms>500
| table _time, export_path, server, status, latency_ms, error_message
| sort -_time
```
- **Implementation:** Deploy scripted input on one or more probe hosts. Script performs `showmount -e <server>` and attempts `mount -t nfs <server>:<export> <mountpoint>` or uses `rpcinfo -p` and a simple read/write test. Measure latency and record success/failure. Run every 5–10 minutes. Index results with export_path, server, status, latency_ms. Alert on status != ok or latency > 500 ms.
- **Visualization:** Table (exports with status and latency), Single value (unreachable exports count), Line chart (latency trend per export), Status grid (export × server).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-6.1.16 · SMB / CIFS Share Availability
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Windows/SMB share reachability is critical for file-serving workloads. Monitoring ensures shares are accessible before users report issues.
- **App/TA:** Custom scripted input (smbclient, net use)
- **Data Sources:** SMB share probe results
- **SPL:**
```spl
index=storage sourcetype="smb:probe"
| search status!="ok" OR latency_ms>1000
| table _time, share_path, server, status, latency_ms, error_message
| sort -_time
```
- **Implementation:** Deploy scripted input on Windows or Linux probe host. Use `smbclient -L //server` or `net use \\server\share` (Windows) to test connectivity. Optionally perform read/write test and measure latency. Run every 5–10 minutes. Index share_path, server, status, latency_ms. Alert on status != ok or latency exceeding threshold. Use domain credentials with minimal read-only access.
- **Visualization:** Table (shares with status and latency), Single value (unreachable shares count), Line chart (latency trend per share), Status grid (share × server).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-6.1.17 · RAID Rebuild Progress and Estimated Completion
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** During array rebuilds, progress percentage and ETA help plan maintenance and detect stalled rebuilds. Stalled rebuilds increase risk of data loss if another disk fails.
- **App/TA:** Custom scripted input (mdadm, MegaCli, perccli)
- **Data Sources:** mdadm --detail, vendor RAID CLI output (MegaCli, perccli)
- **SPL:**
```spl
index=storage sourcetype="raid:rebuild"
| search state="rebuild" OR state="resync"
| eval progress_pct=if(isnum(progress), progress, tonumber(replace(progress, "%", "")))
| where progress_pct < 100
| table _time, array_name, state, progress_pct, speed_mb_s, eta_hours, spare_disk
| sort -_time
```
- **Implementation:** Create scripted input that runs `mdadm --detail /dev/md*` (Linux software RAID) or vendor CLIs (`MegaCli64 -AdpAllInfo -aAll`, `perccli64 /c0 show` for Dell PERC). Parse rebuild/resync state, progress %, speed, and ETA. Run every 5–15 minutes during rebuilds. Index to Splunk. Alert when rebuild is active and progress has not increased in 2+ hours (stalled). Track ETA for maintenance planning.
- **Visualization:** Gauge (rebuild progress %), Table (arrays in rebuild with ETA), Line chart (progress over time), Single value (hours until rebuild complete).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-6.1.18 · NetApp ONTAP Performance Counters
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Counter-based throughput, latency, and queue depth from ONTAP complement volume-level views. Trending counters catches node or aggregate saturation before user-visible latency spikes.
- **App/TA:** `TA-netapp_ontap`, REST API scripted input
- **Data Sources:** ONTAP REST `/api/cluster/counter/tables/*` or ZAPI `perf-object-get-list`
- **SPL:**
```spl
index=storage sourcetype="netapp:ontap:counter"
| where object_name="volume" OR object_name="lun"
| timechart span=5m avg(read_latency) as read_ms, avg(write_latency) as write_ms, avg(total_ops) as iops by instance_name
| where read_ms > 15 OR write_ms > 15
```
- **Implementation:** Enable performance counter polling (15m) for volumes/LUNs. Map instance to SVM and export. Baseline p95 latency and IOPS; alert on sustained deviation from baseline.
- **Visualization:** Line chart (latency and IOPS by object), Table (top latency contributors), Single value (max read/write ms).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-6.1.19 · Pure Storage Array Health
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault, Availability
- **Value:** Pure FA/FB controller, component, and capacity health events indicate hardware or software risk. Unified visibility supports proactive replacement and support cases.
- **App/TA:** Pure REST API (scripted input), Pure TA if deployed
- **Data Sources:** Pure REST `/api/2.x/arrays`, `/hardware`, `/alerts`
- **SPL:**
```spl
index=storage sourcetype="pure:array"
| search status!="healthy" OR component_status!="ok" OR severity IN ("critical","warning")
| stats latest(_time) as last_event, values(message) as messages by array_name, component
| sort -last_event
```
- **Implementation:** Poll array health and open alerts every 5–15 minutes. Ingest critical/warning alerts with component ID. Correlate with support bundle generation workflows.
- **Visualization:** Single value (open critical alerts), Table (array, component, status), Timeline (health transitions).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-6.1.20 · iSCSI Session Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Dropped or flapping iSCSI sessions cause path loss and I/O errors. Session count and login state trending validates host-to-array connectivity after network or firmware changes.
- **App/TA:** Vendor TA, Linux `iscsiadm` scripted input, array iSCSI session API
- **Data Sources:** Host `iscsiadm -m session`, array iSCSI session list
- **SPL:**
```spl
index=storage sourcetype="iscsi:session"
| bin _time span=5m
| stats dc(session_id) as sessions by host, target_iqn, _time
| eventstats avg(sessions) as baseline by host, target_iqn
| where sessions < baseline OR sessions=0
```
- **Implementation:** Scripted input on hosts or array API export of active sessions every 5m. Alert on session count drop to zero or vs baseline. Correlate with NIC/link events.
- **Visualization:** Line chart (sessions per host/target), Table (hosts with zero sessions), Single value (total active sessions).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-6.1.21 · Multipath Failover Events
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault, Availability
- **Value:** Path failovers indicate cable, SFP, HBA, or array port issues. Rapid detection limits prolonged single-path exposure and data loss risk.
- **App/TA:** Linux `multipathd` journal, Windows MPIO events, syslog
- **Data Sources:** `multipathd` logs, `mpathadm` status (Solaris), OS MPIO event logs
- **SPL:**
```spl
index=os (sourcetype=linux_syslog OR sourcetype=syslog) (multipath OR "path failed" OR "switching path" OR mpio)
| rex "(?i)path (?<path_id>\S+).*failed|(?i)switching.*path"
| bin _time span=1h
| stats count by host, path_id, _time
| where count > 0
```
- **Implementation:** Forward multipath daemon logs from all SAN-attached hosts. Tag events for failback/failover. Alert on any path down >5m or repeated failovers per hour.
- **Visualization:** Timeline (failover events), Table (host, path, count), Single value (failovers last 24h).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-6.1.22 · Fibre Channel Port Error Rate (Array)
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Array-side FC port CRCs, signal loss, and link failures differ from switch-only views. Port error rate trending isolates HBA/cable issues at the storage attachment point.
- **App/TA:** Vendor TA, SNMP FC port MIB
- **Data Sources:** Array FC port statistics (CRC, enc_in, enc_out, link_fail)
- **SPL:**
```spl
index=storage sourcetype="storage:fc_port"
| eval err_rate=crc_errors + link_failures + signal_loss
| timechart span=15m sum(err_rate) as errors by array_name, port_id
| where errors > 0
```
- **Implementation:** Poll FC port counters per array port every 15m. Baseline error rate; alert on non-zero sustained errors or step changes after maintenance.
- **Visualization:** Bar chart (errors by port), Line chart (error rate trend), Table (ports with errors).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-6.1.23 · LUN Latency Trending
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Per-LUN latency separates noisy neighbors and misaligned workloads from array-wide issues. Supports QoS and datastore placement decisions.
- **App/TA:** Vendor TA, VMware vSphere performance (if LUN mapped)
- **Data Sources:** Array LUN performance API, VMware `disk.latency` per datastore
- **SPL:**
```spl
index=storage sourcetype="storage:lun_perf"
| timechart span=5m perc95(read_latency_ms) as p95_read, perc95(write_latency_ms) as p95_write by lun_id, array_name
| where p95_read > 20 OR p95_write > 20
```
- **Implementation:** Ingest per-LUN latency at 5m granularity. Set SLA thresholds (e.g., p95 >20ms). Split by workload tier. Correlate with IOPS saturation.
- **Visualization:** Line chart (p95 read/write per LUN), Heatmap (LUN × hour), Table (worst LUNs).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-6.1.24 · Aggregate Space Forecasting
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Capacity
- **Value:** Forecasting aggregate free space prevents sudden write failures on thin-provisioned pools. Supports procurement and volume migration planning.
- **App/TA:** Vendor TA, REST API
- **Data Sources:** Aggregate used/total bytes, snapshot reserve
- **SPL:**
```spl
index=storage sourcetype="netapp:ontap:aggregate"
| timechart span=1d latest(physical_used_pct) as used_pct by aggregate_name
| predict used_pct as forecast future_timespan=30
```
- **Implementation:** Daily snapshot of aggregate utilization. Use `predict` or linear regression for 30/60-day runway. Alert when forecast crosses 85% within 30 days.
- **Visualization:** Line chart (used % with forecast band), Table (aggregates by days-to-full), Single value (soonest full date).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-6.1.25 · Snapshot Schedule Compliance
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Value:** Missed snapshot schedules break backup and rollback expectations. Verifying snapshot recency per policy supports operational and audit requirements.
- **App/TA:** Vendor TA, API
- **Data Sources:** Snapshot list with create time, policy name
- **SPL:**
```spl
index=storage sourcetype="storage:snapshot"
| stats latest(snapshot_time) as last_snap by volume_name, policy_name
| eval hours_since=round((now()-snapshot_time)/3600,1)
| lookup snapshot_policy_expected policy_name OUTPUT expected_hours_max
| where hours_since > expected_hours_max
```
- **Implementation:** Maintain lookup of expected max age per policy. Compare latest snapshot timestamp to policy. Alert on volumes with no snapshot within SLA window.
- **Visualization:** Table (non-compliant volumes), Single value (policy violations count), Timeline (snapshot completions).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-6.1.26 · Deduplication Savings Ratio
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Capacity
- **Value:** Deduplication ratio trending validates efficiency features and detects anomalies (sudden ratio drop may indicate new data types or misconfiguration).
- **App/TA:** Vendor TA (NetApp, Dell, Pure)
- **Data Sources:** Logical vs physical used, dedupe savings API fields
- **SPL:**
```spl
index=storage sourcetype="storage:dedupe"
| eval savings_ratio=round((logical_used_bytes-physical_used_bytes)/nullif(logical_used_bytes,0)*100,1)
| timechart span=1d avg(savings_ratio) as ratio by aggregate_name
| where ratio < 30
```
- **Implementation:** Poll dedupe stats weekly or daily. Baseline savings ratio per aggregate. Alert on significant drop vs 30-day average (e.g., >20% relative drop).
- **Visualization:** Line chart (savings ratio over time), Table (aggregate, logical, physical, ratio), Single value (fleet average ratio).
- **CIM Models:** N/A

- **References:** [Cisco DC Networking Application for Splunk](https://splunkbase.splunk.com/app/7777)

---

#### 6.1 Cisco MDS SAN Fabric

**Splunk Add-on:** Cisco DC Networking Application for Splunk (Splunkbase 7777), SNMP TA, MDS syslog (`cisco:mds`)

### UC-6.1.27 · MDS Inter-Switch Link (ISL) Utilization

- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance, Capacity
- **Value:** ISLs carry all inter-switch SAN traffic. Saturated ISLs cause frame queuing, slow drain propagation, and storage latency spikes. Proactive monitoring prevents cascading congestion before hosts see I/O timeouts.
- **App/TA:** SNMP TA, `cisco:mds` syslog
- **Equipment Models:** Cisco MDS 9132T, MDS 9148T, MDS 9396T, MDS 9700, MDS 9706, MDS 9710
- **Data Sources:** SNMP IF-MIB (ifHCInOctets/ifHCOutOctets on ISL ports), MDS syslog
- **SPL:**
```spl
index=network sourcetype="snmp:if" host="mds*" port_type="ISL"
| eval util_pct=round((ifHCInOctets_delta+ifHCOutOctets_delta)*8/speed/poll_interval*100,1)
| timechart span=5m avg(util_pct) as avg_util by switch, port
| where avg_util > 70
```
- **Implementation:** Poll ISL port counters via SNMP every 60 seconds. Tag ISL ports in a lookup. Alert at 70% sustained utilization (5-min average). Correlate with storage latency (UC-6.1.2) and FC port errors (UC-6.1.9).
- **Visualization:** Line chart (ISL utilization over time), Heatmap (switch x ISL port), Single value (peak ISL utilization), Topology map.
- **CIM Models:** Performance
- **CIM SPL:**
```spl
| tstats summariesonly=t avg(Performance.cpu_load_percent) as agg_value from datamodel=Performance.Network by Performance.host span=5m | sort - agg_value
```

- **References:** [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)

---

### UC-6.1.28 · MDS Slow Drain Detection

- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance
- **Value:** Slow drain occurs when a target device (storage or host) cannot accept frames fast enough, exhausting buffer-to-buffer credits and stalling the entire FC path. A single slow-drain device can impact hundreds of hosts sharing the same ISL. Early detection via TxWait and B2B credit metrics is essential.
- **App/TA:** `cisco:mds` syslog, SNMP TA, Cisco DC Networking Application (Splunkbase 7777)
- **Equipment Models:** Cisco MDS 9132T, MDS 9148T, MDS 9396T, MDS 9700 series
- **Data Sources:** MDS syslog (PORT-MONITOR, SLOW-DRAIN events), SNMP counters (TxWait, B2B credit zeros)
- **SPL:**
```spl
index=network sourcetype="cisco:mds" "SLOW_DRAIN" OR "PORT-5-IF_TXWAIT" OR "PORT-MONITOR"
| rex "port (?<port>\S+).*txwait=(?<txwait>\d+)"
| stats max(txwait) as max_txwait count by switch, port, _time
| where max_txwait > 100
| sort -max_txwait
```
- **Implementation:** Enable port-monitor policies on MDS switches with appropriate TxWait thresholds. Forward syslog to Splunk. Poll SNMP slow-drain counters. Alert immediately on sustained TxWait. Cross-reference with FLOGI database (UC-6.1.30) to identify the offending host or storage port.
- **Visualization:** Table (ports with slow drain), Line chart (TxWait over time), Topology (affected path highlighting).
- **CIM Models:** N/A

- **References:** [Cisco DC Networking Application](https://splunkbase.splunk.com/app/7777)

---

### UC-6.1.29 · MDS Zone Configuration Compliance

- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance, Change
- **Value:** Zoning controls which initiators can communicate with which targets. Misconfigured zones create security risks (unauthorized access) and operational risks (accidental data access). Tracking zone changes and validating against a known-good baseline prevents drift.
- **App/TA:** `cisco:mds` syslog, scripted input (MDS NX-API / CLI)
- **Equipment Models:** Cisco MDS 9132T, MDS 9148T, MDS 9396T, MDS 9700 series
- **Data Sources:** MDS syslog (zone change events), NX-API CLI (`show zone`, `show zoneset active`)
- **SPL:**
```spl
index=network sourcetype="cisco:mds" "ZONE" ("added" OR "removed" OR "activated" OR "changed")
| stats count by switch, vsan_id, zone_name, action, user
| append [| inputlookup mds_approved_zones | eval source="baseline"]
| stats values(source) as sources by vsan_id, zone_name
| where NOT match(sources,"baseline")
| table vsan_id, zone_name, sources
```
- **Implementation:** Export zone configuration periodically via NX-API. Maintain a baseline lookup of approved zones per VSAN. Detect zone additions, removals, and activations via syslog. Alert on any zone change outside change windows.
- **Visualization:** Table (zone changes), Timeline (change events), Diff view (current vs baseline).
- **CIM Models:** Change
- **CIM SPL:**
```spl
| tstats summariesonly=t count from datamodel=Change.All_Changes by All_Changes.action, All_Changes.user | sort - count
```

- **References:** [CIM: Change](https://docs.splunk.com/Documentation/CIM/latest/User/Change)

---

### UC-6.1.30 · MDS FLOGI Database Monitoring

- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Inventory, Security
- **Value:** The FLOGI (Fabric Login) database records every device that has logged into the SAN fabric. Monitoring FLOGI events detects rogue devices, unexpected host logins, and fabric login storms that indicate HBA or driver issues.
- **App/TA:** `cisco:mds` syslog, scripted input (NX-API)
- **Equipment Models:** Cisco MDS 9132T, MDS 9148T, MDS 9396T, MDS 9700 series
- **Data Sources:** MDS syslog (FLOGI/FDISC events), NX-API (`show flogi database`)
- **SPL:**
```spl
index=network sourcetype="cisco:mds" "FLOGI" OR "FDISC"
| stats count as login_count by switch, port, pwwn, nwwn
| lookup mds_known_hosts pwwn OUTPUT host_name, authorized
| where isnull(authorized) OR authorized!="yes"
| table switch, port, pwwn, nwwn, host_name, authorized, login_count
```
- **Implementation:** Forward MDS syslog and periodically poll FLOGI database via NX-API. Maintain a lookup of known/authorized WWNs. Alert on unknown WWN logins. Track FLOGI count trends to detect login storms.
- **Visualization:** Table (FLOGI entries with authorization status), Bar chart (logins per switch), Timeline (login events).
- **CIM Models:** Authentication
- **CIM SPL:**
```spl
| tstats summariesonly=t count from datamodel=Authentication.Authentication by Authentication.action, Authentication.user, Authentication.src | sort - count
```

- **References:** [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)

---

### UC-6.1.31 · MDS VSAN Health and Isolation Events

- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** VSANs provide logical SAN segmentation. VSAN isolation events (caused by ISL failures, misconfigured trunking, or merge failures) split the fabric and break host-to-storage paths. Detecting isolation within seconds is essential for maintaining storage availability.
- **App/TA:** `cisco:mds` syslog, SNMP TA
- **Equipment Models:** Cisco MDS 9132T, MDS 9148T, MDS 9396T, MDS 9700 series
- **Data Sources:** MDS syslog (VSAN state change, merge failure, isolation events), SNMP
- **SPL:**
```spl
index=network sourcetype="cisco:mds" "VSAN" ("isolated" OR "merge" OR "segmented" OR "down")
| stats count latest(_time) as last_event by switch, vsan_id, event_type
| where event_type IN ("isolated","segmented","merge_failure")
| table switch, vsan_id, event_type, count, last_event
| sort -last_event
```
- **Implementation:** Forward MDS syslog with facility-level logging. Alert immediately on VSAN isolation or segmentation events. Correlate with ISL link status (UC-6.1.27) and zone changes (UC-6.1.29) to identify root cause.
- **Visualization:** Status grid (VSAN health), Table (isolation events), Topology map (VSAN segmentation).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-6.1.32 · MDS SAN Fabric Oversubscription Ratio

- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity
- **Value:** The ratio of total edge port bandwidth to ISL bandwidth determines oversubscription. High oversubscription ratios (>7:1 for production, >20:1 for backup) increase the risk of congestion. Tracking this metric supports capacity planning and fabric expansion decisions.
- **App/TA:** SNMP TA, scripted input (NX-API)
- **Equipment Models:** Cisco MDS 9132T, MDS 9148T, MDS 9396T, MDS 9700 series
- **Data Sources:** SNMP IF-MIB (port speeds, port types), NX-API (`show interface brief`)
- **SPL:**
```spl
index=network sourcetype="snmp:if" host="mds*"
| stats sum(eval(if(port_type="F",speed,0))) as edge_bw sum(eval(if(port_type="E" OR port_type="TE",speed,0))) as isl_bw by switch
| eval oversubscription=round(edge_bw/isl_bw,1)
| where oversubscription > 7
| table switch, edge_bw, isl_bw, oversubscription
| sort -oversubscription
```
- **Implementation:** Poll interface inventory via SNMP or NX-API. Classify ports by type (F-port=edge, E/TE-port=ISL). Calculate oversubscription ratio per switch. Alert when ratio exceeds policy threshold. Report quarterly for capacity planning.
- **Visualization:** Table (switch oversubscription), Gauge (ratio per switch), Trend chart (ratio over quarters).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)

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

- **References:** [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)

---

### UC-6.2.3 · Public Bucket Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Wave:** 🐢 crawl
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

- **References:** [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-6.2.6 · S3 and Azure Blob Lifecycle Policy Compliance
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance, Configuration
- **Value:** Confirms lifecycle rules exist per bucket/container and that transitions match tagging/age rules. Reduces cost leakage from objects stuck in hot tiers.
- **App/TA:** `Splunk_TA_aws`, `Splunk_TA_microsoft-cloudservices`, Config/Policy inventory
- **Data Sources:** S3 bucket lifecycle XML inventory, Azure Blob management policy JSON, AWS Config
- **SPL:**
```spl
index=aws sourcetype="aws:s3:lifecycle_inventory"
| stats values(rule_id) as rules, latest(has_expiration) as exp by bucket_name, region
| where mvcount(rules)=0 OR exp=0
| table bucket_name region rules exp
```
- **Implementation:** Export bucket lifecycle configurations via API/Config daily. For Azure, ingest policy definitions from Activity/Resource Graph. Alert on production buckets missing lifecycle or expiration actions.
- **Visualization:** Table (buckets without compliant lifecycle), Pie chart (compliant vs non-compliant), Single value (non-compliant count).
- **CIM Models:** N/A

- **References:** [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876), [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)

---

### UC-6.2.7 · Cross-Region Replication Lag (SLA)
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Tracks replication backlog and oldest replicated object age for S3 CRR and Azure geo-replication. Complements byte-level lag with time-based SLA views.
- **App/TA:** Cloud TAs, CloudWatch, Azure Monitor
- **Data Sources:** S3 `OperationsPendingReplication`, Azure `GeoReplicationLag` (where available)
- **SPL:**
```spl
index=aws sourcetype="aws:cloudwatch" metric_name="OperationsPendingReplication"
| timechart span=1h max(Maximum) as pending_ops by bucket_name
| where pending_ops > 100000
```
- **Implementation:** Set thresholds from RPO (e.g., pending operations or max lag minutes). Alert when backlog grows for >1h. For Azure Blob, ingest replication health metrics from Monitor diagnostics.
- **Visualization:** Line chart (pending replication / lag), Table (buckets breaching SLA), Single value (max lag minutes).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-6.2.8 · Bucket Policy Change Audit
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security, Compliance
- **Value:** Unexpected bucket policy or IAM policy changes can expose data. Audit trail supports SOC2/PCI evidence and fast rollback.
- **App/TA:** `Splunk_TA_aws` (CloudTrail), Azure Activity Log
- **Data Sources:** `PutBucketPolicy`, `DeleteBucketPolicy`, `SetContainerAcl` (Azure equivalents)
- **SPL:**
```spl
index=aws sourcetype="aws:cloudtrail" eventName IN ("PutBucketPolicy","DeleteBucketPolicy","PutBucketAcl")
| table _time, requestParameters.bucketName, userIdentity.arn, sourceIPAddress, eventName
| sort -_time
```
- **Implementation:** Ingest CloudTrail S3 and IAM policy events. Enrich with CMDB owner. Alert on changes outside change windows or from non-break-glass principals.
- **Visualization:** Timeline (policy changes), Table (bucket, user, action), Single value (changes last 24h).
- **CIM Models:** N/A

- **References:** [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)

---

### UC-6.2.9 · Pre-Signed URL Abuse Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Security
- **Value:** Unusual volume of pre-signed GET/PUT or access from unexpected IPs may indicate credential theft or insider abuse.
- **App/TA:** `Splunk_TA_aws` (S3 access logs), CloudTrail data events
- **Data Sources:** S3 server access logs with `queryString` containing `X-Amz-`, `Signature`
- **SPL:**
```spl
index=aws sourcetype="aws:s3:accesslogs"
| search query_string="*X-Amz-*" OR query_string="*Signature*"
| stats count by bucket_name, requester, remote_ip
| eventstats avg(count) as avg_c, stdev(count) as stdev_c by bucket_name
| where count > avg_c + 3*stdev_c
```
- **Implementation:** Parse query string for presigned parameters. Baseline requests per requester/IP. Alert on spikes or geo anomalies. Correlate with IAM changes.
- **Visualization:** Table (top presigned requesters), Line chart (presigned request rate), Map (remote_ip).
- **CIM Models:** N/A

- **References:** [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)

---

### UC-6.2.10 · Storage Class Transition Tracking
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity, Cost
- **Value:** Validates that objects move to IA/Glacier/Archive per policy. Stalled transitions indicate rule gaps or unsupported objects.
- **App/TA:** S3 Inventory, Azure Blob inventory, CloudWatch storage class metrics
- **Data Sources:** S3 Inventory reports (CSV), `BucketSizeBytes` by `StorageType`
- **SPL:**
```spl
index=aws sourcetype="aws:s3:inventory" OR sourcetype="aws:cloudwatch" metric_name="BucketSizeBytes"
| stats sum(size_bytes) as bytes by bucket_name, storage_class
| eventstats sum(bytes) as total by bucket_name
| eval pct=round(bytes/total*100,1)
| where storage_class="STANDARD" AND pct > 40
```
- **Implementation:** Ingest periodic inventory or CloudWatch breakdown. Compare STANDARD % vs policy targets. Report buckets with excessive STANDARD after expected transition age.
- **Visualization:** Stacked bar (storage class % per bucket), Table (buckets with high STANDARD %), Line chart (class mix over time).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-6.2.11 · Object Versioning Compliance
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Compliance, Configuration
- **Value:** Buckets without versioning risk unrecoverable overwrites. Monitoring ensures critical buckets remain versioned per data policy.
- **App/TA:** AWS Config, Azure Policy compliance states
- **Data Sources:** `GetBucketVersioning`, Config rule compliance
- **SPL:**
```spl
index=aws sourcetype="aws:config:rule"
| search configRuleName="*s3-bucket-versioning*" OR resourceType="AWS::S3::Bucket"
| spath output=versioning resource.configuration.versioning.status
| where versioning!="Enabled" AND complianceType="NON_COMPLIANT"
| table resourceId, complianceType, versioning
```
- **Implementation:** Map critical buckets via lookup. Alert when versioning is suspended or never enabled on tagged buckets. Include MFA delete status in extended implementation.
- **Visualization:** Table (non-compliant buckets), Single value (buckets without versioning), Status grid (bucket × region).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-6.2.12 · Object Lock Integrity
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security, Compliance
- **Value:** WORM/immutability protects against ransomware and deletion. Verifies Object Lock retention mode and legal hold on regulated buckets.
- **App/TA:** AWS Config, S3 API inventory
- **Data Sources:** `GetObjectLockConfiguration`, Config compliance, S3 Inventory `ObjectLockEnabled`
- **SPL:**
```spl
index=aws sourcetype="aws:s3:object_lock_audit"
| where object_lock_enabled!=1 OR retention_mode="null" OR compliance_gap=1
| stats latest(_time) as last_check by bucket_name, region
| table bucket_name region object_lock_enabled retention_mode compliance_gap
```
- **Implementation:** Scripted audit comparing required lock settings from lookup to actual API responses. Alert on drift or disabled lock. Log tamper-evident checksum of policy JSON if stored in Splunk.
- **Visualization:** Table (buckets failing lock check), Single value (drift count), Timeline (audit runs).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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
- **Implementation:** For Veeam: use the Veeam App for Splunk or ingest via HEC from Enterprise Manager REST (`/api/v1/jobSessions`); normalize `job_name`, `result`, `end_time` fields. For Veritas NetBackup: forward master/media server syslog or use the OpsCenter REST export. Alert when `result!=Success` for jobs flagged as `backup_tier=critical` in a lookup. Throttle per `job_name` to avoid alert storms during infrastructure outages.
- **Visualization:** Single value (overall success rate %), Table (failed jobs with details), Bar chart (success/fail by job), Trend line (daily success rate).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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
| join type=left max=1 job_name
    [search index=backup sourcetype="veeam:job" earliest=-24h
     | stats latest(_time) as last_run by job_name]
| where isnull(last_run) OR last_run < relative_time(now(), "-26h")
| table job_name, expected_schedule, last_run
```
- **Implementation:** Maintain a lookup table of expected backup schedules. Run a scheduled search comparing expected vs actual runs. Alert when any job misses its window. Correlate with backup server health events.
- **Visualization:** Table (missed jobs with schedule details), Single value (number of missed jobs), Status grid (job name × date).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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
| join type=left max=1 system_name
    [search index=backup sourcetype="veeam:job" status="Success" earliest=-7d
     | stats latest(_time) as last_backup, max(data_size) as backup_size by system_name]
| eval compliant=if(isnotnull(last_backup),"Yes","No")
| stats count(eval(compliant="Yes")) as covered, count as total
| eval coverage_pct=round(covered/total*100,1)
```
- **Implementation:** Cross-reference CMDB inventory with backup job data. Identify systems with no backup coverage. Calculate RPO compliance (time since last successful backup vs required RPO). Produce weekly executive report.
- **Visualization:** Single value (SLA compliance %), Table (non-compliant systems), Pie chart (covered vs uncovered), Dashboard with filters by business unit.
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-6.3.9 · Veeam Backup Job Monitoring
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Job success/failure/warning status, duration, and data transferred are essential for backup reliability. Immediate visibility into job outcomes ensures data protection SLAs are met and enables rapid troubleshooting.
- **App/TA:** Custom (Veeam Enterprise Manager REST API, PowerShell output)
- **Data Sources:** Veeam job session data (REST API or PowerShell Get-VBRSession)
- **SPL:**
```spl
index=backup sourcetype="veeam:job_session"
| stats latest(_time) as last_run, latest(status) as status, latest(duration_min) as duration_min, latest(data_transferred_gb) as data_gb by job_name
| where status!="Success" OR duration_min>480
| table job_name, last_run, status, duration_min, data_gb
| sort last_run
```
- **Implementation:** Use Veeam Enterprise Manager REST API (`/api/sessionMgr`) or PowerShell script invoking `Get-VBRSession` to collect job session data. Poll every 15–30 minutes or trigger on job completion. Extract job_name, status (Success/Failed/Warning), start/end time (for duration), and data transferred. Index to Splunk with sourcetype `veeam:job_session`. Alert immediately on status=Failed; warning on status=Warning. Alert when duration exceeds backup window (e.g., >8 hours).
- **Visualization:** Table (job, status, duration, data transferred), Single value (failed jobs count), Bar chart (duration by job), Status grid (job × date).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-6.3.10 · Backup Data Growth Rate
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity
- **Value:** Backup repository consumption trending enables capacity planning and prevents surprise exhaustion. Proactive forecasting supports budget and procurement decisions.
- **App/TA:** Custom (backup software API/CLI)
- **Data Sources:** Backup repository size over time
- **SPL:**
```spl
index=backup sourcetype="veeam:repository" OR sourcetype="backup:repository"
| eval used_pct=round(used_bytes/capacity_bytes*100, 1)
| timechart span=1d latest(used_bytes) as used, latest(capacity_bytes) as capacity by repository_name
| eval used_pct=round(used/capacity*100, 1)
| predict used as predicted future_timespan=30
```
- **Implementation:** Poll backup repository capacity via vendor API (Veeam, Commvault, etc.) or scripted input (filesystem df, REST endpoint). Collect used_bytes and capacity_bytes per repository daily. Index to Splunk. Use `predict` or `trendline` for 30/60/90-day forecasts. Alert when projected full date is within 90 days. Correlate growth rate with backup job data volume trends.
- **Visualization:** Line chart (repository usage % over time with prediction), Table (repositories with growth rate and ETA to full), Single value (days until first repository full).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-6.3.11 · Veeam Backup Job Status Summary
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Compliance
- **Value:** Roll-up of last job result per workload (Success/Warning/Failed/Running) for executive and NOC dashboards. Complements session-level detail with a single row per protected entity.
- **App/TA:** Veeam App for Splunk, Enterprise Manager API
- **Data Sources:** `veeam:job` or `veeam:job_session` with `job_name`, `status`, `end_time`
- **SPL:**
```spl
index=backup sourcetype="veeam:job_session"
| stats latest(_time) as last_end, latest(status) as status, latest(duration_sec) as duration by job_name
| where status IN ("Failed","Warning") OR duration > 28800
| table job_name last_end status duration
```
- **Implementation:** Schedule hourly. Map Warning to ticket for review. Escalate Failed immediately. Track Running jobs exceeding expected window as Warning.
- **Visualization:** Status grid (job × last status), Single value (failed count), Table (jobs needing attention).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-6.3.12 · Commvault Job Completion
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Value:** Failed or incomplete Commvault backup jobs leave subclients unprotected. Job-level success tracking is required for audit and restore confidence.
- **App/TA:** Commvault Splunk App, Commvault REST/CLI export
- **Data Sources:** Commvault job history (subclient, status, error code)
- **SPL:**
```spl
index=backup sourcetype="commvault:job"
| where status!="Completed" OR job_status="Failed"
| stats latest(_time) as last_run, latest(error_code) as err by job_name, subclient_name
| table job_name subclient_name last_run err
```
- **Implementation:** Ingest completed job events from Commvault. Normalize status values. Alert on Failed; report Partial with same severity as policy dictates.
- **Visualization:** Table (failed jobs), Single value (failed jobs 24h), Bar chart (failures by error code).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-6.3.13 · Backup RPO and RTO Compliance
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Compliance
- **Value:** Compares actual backup completion time and restore test duration against business RPO/RTO targets per application tier.
- **App/TA:** Backup TA + CMDB lookup
- **Data Sources:** Last successful backup time, last restore test duration
- **SPL:**
```spl
| inputlookup cmdb_systems.csv WHERE backup_tier=*
| join system_name max=0
    [search index=backup sourcetype="veeam:job" status="Success" earliest=-7d
     | stats latest(_time) as last_ok by system_name]
| eval hours_since_ok=round((now()-last_ok)/3600,1)
| lookup backup_rpo_hours tier OUTPUT rpo_hours
| where hours_since_ok > rpo_hours
| table system_name tier hours_since_ok rpo_hours
```
- **Implementation:** Maintain lookup of RPO hours per tier. Join to last successful backup. Alert when hours_since_ok exceeds RPO. Add parallel search for restore drill duration vs RTO.
- **Visualization:** Table (systems breaching RPO), Gauge (% RPO compliant), Line chart (hours since backup by tier).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-6.3.14 · Tape Library Robotics and Drive Health
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** Mechanical faults, barcode read errors, and drive cleaning states cause failed backups before media errors. Dedicated robotics metrics reduce MTTR for tape operations.
- **App/TA:** Vendor SNMP, backup software tape events
- **Data Sources:** Library element status, picker errors, drive cleaning required flags
- **SPL:**
```spl
index=backup sourcetype="tape_library:robot"
| search (robot_error OR slot_unavailable OR "inventory failed" OR cleaning_required="true")
| stats count by library_name, component, error_code
| where count > 0
```
- **Implementation:** Augment generic tape syslog with SNMP polls for robotics status. Alert on inventory failures or slot errors. Schedule cleaning when `cleaning_required` is set.
- **Visualization:** Table (library, component, errors), Timeline (robotics faults), Single value (libraries with open faults).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-6.3.15 · DR Rehearsal Tracking
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Value:** Tabletop and technical DR tests must occur on schedule. Tracking rehearsal outcomes and dates supports audit and readiness scoring.
- **App/TA:** Custom (ITSM, spreadsheet ingest, HEC)
- **Data Sources:** DR test results, DR runbook completion events
- **SPL:**
```spl
index=backup sourcetype="dr_rehearsal"
| stats latest(test_date) as last_test, latest(result) as result by system_name, scenario
| eval days_since=round((now()-strptime(last_test,"%Y-%m-%d"))/86400)
| where days_since > 365 OR result!="Pass"
| table system_name scenario last_test result days_since
```
- **Implementation:** Log each rehearsal with scenario, duration, pass/fail. Alert when annual test is overdue or result is not Pass. Correlate with actual restore tests from backup tools.
- **Visualization:** Table (overdue systems), Calendar (scheduled tests), Single value (% scenarios current).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-6.3.16 · Backup Window Utilization
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity
- **Value:** Jobs that consume most of the backup window risk overlap with production or fail to finish. Utilization % guides schedule tuning and parallel job limits.
- **App/TA:** Vendor job logs
- **Data Sources:** Job start/end, defined backup window start/end per policy
- **SPL:**
```spl
index=backup sourcetype="veeam:job" status="Success"
| eval duration_min=(end_time-start_time)/60
| lookup backup_policy job_name OUTPUT window_start_hour window_end_hour
| eval window_min=(window_end_hour-window_start_hour)*60
| eval util_pct=round(duration_min/window_min*100,1)
| where util_pct > 85
| table job_name duration_min window_min util_pct
```
- **Implementation:** Define backup window per policy in lookup. Compare job duration to window length. Alert when utilization >85% or job end exceeds window end.
- **Visualization:** Bar chart (utilization % by job), Line chart (duration trend vs window), Table (jobs at risk of overrun).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-6.3.17 · Incremental Backup Chain Integrity
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Compliance
- **Value:** Broken increment chains (missing full or corrupted metadata) make restores impossible. Vendor-specific checks detect chain gaps before a failure at restore time.
- **App/TA:** Veeam/Commvault verification APIs, catalog exports
- **Data Sources:** Backup chain metadata, `Verify` job results
- **SPL:**
```spl
index=backup sourcetype="backup:chain_verify"
| where chain_ok=0 OR missing_restore_point=1 OR verify_status="Failed"
| stats latest(_time) as last_check by job_name, vm_name
| table job_name vm_name chain_ok missing_restore_point verify_status last_check
```
- **Implementation:** Ingest synthetic full verification or chain validation jobs. Alert on any `chain_ok=0`. Weekly full verification of random samples for large environments.
- **Visualization:** Table (broken chains), Single value (VMs with integrity issues), Timeline (verify jobs).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-6.3.18 · Backup Data Growth Trending by Workload
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity
- **Value:** Per-workload front-end bytes backed up trend identifies data sprawl, VM growth, or unexpected database growth before repository exhaustion.
- **App/TA:** Vendor TA
- **Data Sources:** Job statistics `data_transferred_bytes` or `processed_size` per job/run
- **SPL:**
```spl
index=backup sourcetype="veeam:job" status="Success"
| timechart span=1d sum(data_transferred_gb) as daily_gb by job_name
| predict daily_gb as forecast future_timespan=30
```
- **Implementation:** Sum data per job daily. Use `predict` for growth. Alert when week-over-week growth exceeds threshold (e.g., 25%). Compare to repository free space.
- **Visualization:** Line chart (daily GB with forecast per job), Table (fastest-growing jobs), Top values (growth %).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---


### UC-6.3.19 · Windows Backup Job Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Compliance
- **Value:** Windows Server Backup failures mean the server has no recovery point. Silent failures create a false sense of protection.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:Microsoft-Windows-Backup` (EventCode 4, 5, 8, 9, 14, 17, 22)
- **SPL:**
```spl
index=wineventlog source="WinEventLog:Microsoft-Windows-Backup"
  EventCode IN (4, 5, 8, 9, 14)
| eval status=case(EventCode=4,"Backup completed",EventCode=5,"Backup failed",EventCode=8,"Backup failed (VSS)",EventCode=9,"Warning",EventCode=14,"Backup completed with warnings")
| table _time, host, status, EventCode, BackupTarget
| sort -_time
```
- **Implementation:** Forward Windows Backup event logs. EventCode 4=success, 5=failure, 8=VSS failure. Alert on any backup failure (EventCode 5, 8). Also monitor for missing backups — if a server stops reporting EventCode 4, the backup job may have been disabled or deleted. Compare actual backup frequency against RTO/RPO requirements. Escalate servers with no successful backup in 48+ hours.
- **Visualization:** Status grid (host × backup status), Table (failures), Line chart (backup success rate over time), Single value (hours since last backup).
- **CIM Models:** N/A

- **References:** [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)

---

### UC-6.3.20 · Backup Target Capacity and Growth Rate
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Capacity
- **Value:** Backup destination (disk, dedup appliance, object storage) that fills up causes backup failures and retention gaps. Tracking growth and remaining capacity prevents surprise outages.
- **App/TA:** Backup vendor API, storage array metrics, S3/CloudWatch
- **Data Sources:** Backup catalog size, target filesystem capacity, object storage metrics
- **SPL:**
```spl
index=backup sourcetype=backup_capacity
| eval used_pct=round(used_bytes/capacity_bytes*100, 1)
| stats latest(used_pct) as pct, latest(used_bytes) as used by target_name
| where pct > 85
| table target_name pct used capacity_bytes
```
- **Implementation:** Poll backup target capacity (vendor API or filesystem/object metrics). Ingest used and total. Alert at 85% (warning) and 95% (critical). Compute week-over-week growth rate for capacity planning.
- **Visualization:** Gauge per target, Line chart (usage % over time), Table (target, %, growth rate).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-6.3.21 · Restore Job Success and Duration Trending
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Restore failures or abnormally long restores indicate corrupt backups, network issues, or misconfiguration. Tracking ensures recovery procedures are validated and RTO is achievable.
- **App/TA:** Backup vendor logs, job status API
- **Data Sources:** Restore job status, duration, bytes restored
- **SPL:**
```spl
index=backup sourcetype=backup_restore job_type=restore
| bin _time span=1d
| stats count(eval(status="failed")) as failures, count(eval(status="success")) as success, avg(duration_sec) as avg_duration by job_name, _time
| eval fail_rate=round(failures/(failures+success)*100, 1)
| where failures > 0 OR avg_duration > 3600
```
- **Implementation:** Ingest restore job completion events. Track success/failure and duration. Alert on any restore failure. Baseline restore duration by job type; alert when duration exceeds 2x baseline. Run periodic test restores and log results.
- **Visualization:** Table (job, success, failures, avg duration), Line chart (restore duration trend), Single value (last 7d fail rate).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-6.3.22 · Backup Job Overlap and Schedule Conflict Detection
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** Overlapping full backups or too many concurrent jobs overload the backup infrastructure and extend backup windows. Detecting overlap supports schedule tuning and resource sizing.
- **App/TA:** Backup vendor logs or API
- **Data Sources:** Backup job start/end timestamps, job type (full/incremental)
- **SPL:**
```spl
index=backup sourcetype=backup_job
| eval start_epoch=_time end_epoch=_time+duration_sec
| stats values(job_name) as jobs by host, _time
| where mvcount(jobs) > 3
| table _time host jobs
```
- **Implementation:** Ingest job start and duration. For each time window, count concurrent jobs per host or media server. Alert when more than N full backups run concurrently or when backup window is exceeded.
- **Visualization:** Timeline (jobs by start/end), Table (overlapping jobs), Single value (max concurrent).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-6.3.23 · Immutable Backup and Ransomware Recovery Readiness
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Security, Availability
- **Value:** Immutable or air-gapped copies are the last line of defense against ransomware. Verifying immutability and recovery procedure readiness ensures backups cannot be deleted or encrypted by an attacker.
- **App/TA:** Backup vendor API, object lock compliance check
- **Data Sources:** Backup copy retention lock status, object lock (S3), backup integrity checksum
- **SPL:**
```spl
index=backup sourcetype=backup_immutable
| stats latest(immutable_ok) as ok, latest(last_checksum_verify) as last_verify by copy_name
| where ok != 1 OR (now()-last_verify) > 604800
| table copy_name ok last_verify
```
- **Implementation:** Poll backup copy configuration for retention lock or immutable flag. Optionally run periodic checksum or catalog validation. Alert when any critical copy is not immutable or when last verification is older than 7 days. Document and test recovery runbook.
- **Visualization:** Status grid (copy, immutable, last verify), Table (non-compliant copies), Single value (ready for recovery %).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-6.3.24 · Tape Library Slot Utilization
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity
- **Value:** Tape library capacity and media expiration tracking prevent backup failures when slots are exhausted or tapes expire. Supports capacity planning and media lifecycle management.
- **App/TA:** Custom scripted input (tape library SNMP, vendor API)
- **Data Sources:** Tape library management interface (SNMP/API)
- **SPL:**
```spl
index=backup sourcetype="tape_library:capacity"
| eval slot_util_pct=round(slots_used/total_slots*100, 1)
| eval media_expiring_30d=if(media_expiration_days<=30, 1, 0)
| stats latest(slot_util_pct) as pct_used, latest(slots_used) as used, latest(total_slots) as total, sum(media_expiring_30d) as expiring_soon by library_name
| where pct_used > 85 OR expiring_soon > 0
| table library_name, used, total, pct_used, expiring_soon
```
- **Implementation:** Poll tape library via SNMP (MIB-II, vendor-specific MIBs for slot counts) or vendor REST/CLI API. Collect total_slots, slots_used, and optionally media expiration dates. Run scripted input every 1–4 hours. Index to Splunk. Alert when slot utilization exceeds 85% or when media expiring within 30 days is detected. Maintain lookup of media barcodes and expiration for lifecycle tracking.
- **Visualization:** Gauge (slot utilization % per library), Table (libraries with slot counts and expiring media), Line chart (slot usage trend), Single value (libraries near capacity).
- **CIM Models:** N/A

- **References:** [Splunk Add-on for Microsoft Windows](https://splunkbase.splunk.com/app/742)

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

- **References:** [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)

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

- **References:** [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)

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

- **References:** [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)

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

- **References:** [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)

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
| stats sum(Size) as total_bytes, dc(ObjectName) as file_count by Account_Name, src
| eval total_gb=round(total_bytes/1024/1024/1024,2)
| where total_gb > 1
| sort -total_gb
```
- **Implementation:** Monitor file read events and correlate with SMB session data for volume estimates. Baseline normal transfer patterns per user. Alert when transfers exceed threshold (e.g., >1GB in single session). Correlate with HR/departure lists.
- **Visualization:** Table (users with large transfers), Bar chart (transfer volume by user), Line chart (daily transfer volume trend).
- **CIM Models:** N/A

- **References:** [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)

---

### UC-6.4.6 · Backup Encryption and Key Access Audit
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security, Compliance
- **Value:** Backup encryption keys must be used only by authorized backup jobs. Unusual key access or decryption attempts may indicate theft or ransomware. Auditing supports compliance and incident response.
- **App/TA:** Backup vendor logs, KMS/HSM audit logs
- **Data Sources:** Backup software audit log, AWS KMS CloudTrail, Azure Key Vault audit
- **SPL:**
```spl
index=backup sourcetype=backup_audit (event="key_access" OR event="decrypt")
| bin _time span=1h
| stats count by user, key_id, event, _time
| where count > 20
| sort -count
```
- **Implementation:** Forward backup software audit logs and cloud KMS/key vault audit logs. Extract key ID, user, and action. Alert on high volume of decrypt or key access from unexpected principal or outside backup window.
- **Visualization:** Table (user, key, count), Timeline of key access, Bar chart by principal.
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-6.4.12 · DFS Replication Backlog and Connectivity Health
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** Backlog size and partner connectivity state predict replication stalls before user-visible file divergence. Complements event-only monitoring with quantitative backlog trending.
- **App/TA:** `Splunk_TA_windows`, scripted `dfsrdiag` / WMI
- **Data Sources:** DFS-R backlog metrics per replicated folder, Event ID 4012/5002
- **SPL:**
```spl
index=storage sourcetype="dfsr:backlog"
| where backlog_files > 100 OR connected=0
| timechart span=15m max(backlog_files) as backlog by replication_group, member
| where backlog > 500
```
- **Implementation:** Ingest backlog count from PowerShell `Get-DfsrState` or scheduled dfsrdiag output every 15m. Alert on rising backlog trend or disconnected partners.
- **Visualization:** Line chart (backlog files over time), Table (RG, member, backlog), Single value (max backlog).
- **CIM Models:** N/A

- **References:** [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)

---

### UC-6.4.13 · NFS Export Capacity and Client Load
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity, Performance
- **Value:** Export-level capacity and NFS operations/sec highlight hot exports and approaching full filesystems on NAS heads.
- **App/TA:** NetApp/Isilon API, Linux `nfsstat`, `exportfs -v` metrics
- **Data Sources:** Per-export bytes used, NFS op counters
- **SPL:**
```spl
index=storage sourcetype="nas:nfs_export"
| eval used_pct=round(used_bytes/capacity_bytes*100,1)
| timechart span=5m sum(ops_per_sec) as ops, avg(used_pct) as pct by export_path, host
| where pct > 85 OR ops > 10000
```
- **Implementation:** Poll export statistics from NAS API or aggregated nfsd metrics. Alert on high used % or abnormal ops vs baseline.
- **Visualization:** Table (export, used %, ops/s), Line chart (ops and capacity trend), Bar chart (top exports by ops).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-6.4.14 · SMB Share Access Audit
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security, Compliance
- **Value:** Summarizes successful and denied access to sensitive shares for insider threat and access reviews. Extends object-level 4663 views with share-level rollups.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** Security Event ID 5140 (share accessed), 4663 for sensitive paths
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode=5140
| stats count by Share_Name, Account_Name, ComputerName
| where count > 1000
| sort -count
```
- **Implementation:** Enable share auditing on critical shares. Tune volume to avoid noise; focus on privileged groups. Alert on access to “restricted” shares from unexpected subnets via lookup.
- **Visualization:** Table (share, user, count), Bar chart (top shares by access count), Heatmap (share × hour).
- **CIM Models:** N/A

- **References:** [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)

---

### UC-6.4.15 · File Server Capacity Trending
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Capacity
- **Value:** Volume-level free space trending on Windows file servers prevents user and application outages from full disks.
- **App/TA:** `Splunk_TA_windows` (PerfDisk), scripted `Get-Volume`
- **Data Sources:** Logical disk free MB/%, WMI volume metrics
- **SPL:**
```spl
index=os sourcetype="Perfmon:LogicalDisk" counter="% Free Space"
| timechart span=1h latest(InstanceValue) as free_pct by host, instance
| where free_pct < 15
```
- **Implementation:** Collect % Free Space every 5–15m. Alert at 15% (warning) and 10% (critical). Use `predict` on large shares for procurement lead time.
- **Visualization:** Line chart (free % trend), Gauge (current free %), Table (volumes below threshold).
- **CIM Models:** N/A

- **References:** [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)

---

### UC-6.4.16 · Ransomware File Extension Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Detects mass renames or creates with known ransomware extensions (e.g., `.locked`, `.encrypted`) faster than generic mass-modify heuristics in some campaigns.
- **App/TA:** `Splunk_TA_windows`, EDR feeds
- **Data Sources:** File create/rename events 4663 with ObjectName ending in suspicious extensions
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode=4663
| rex field=ObjectName "(?i)\.(locked|encrypted|crypt|ryuk|lockbit)(\"|$)"
| stats dc(ObjectName) as files count by Account_Name, host
| where files > 20
```
- **Implementation:** Maintain lookup of ransomware extensions from threat intel. Combine with mass-delete and entropy signals. Integrate SOAR for host isolation.
- **Visualization:** Table (user, host, files affected), Timeline (detection), Single value (distinct suspicious files).
- **CIM Models:** N/A

- **References:** [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)

---

### UC-6.4.17 · CIFS Connection Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance, Availability
- **Value:** Tracks concurrent SMB sessions and failed session setups per file server. Spikes may indicate brute force, misconfigured apps, or server resource limits.
- **App/TA:** `Splunk_TA_windows`, SMB server audit
- **Data Sources:** Event ID 5140/5145, Perfmons `Server Sessions`, `Server Rejects`
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode=5140 OR EventCode=5145
| bucket _time span=5m
| stats count as sessions by ComputerName, _time
| eventstats avg(sessions) as avg_s by ComputerName
| where sessions > avg_s * 3
```
- **Implementation:** Baseline sessions per 5m window per server. Alert on 3× baseline or on SMB error events (551, 552) if enabled. Correlate with auth failures.
- **Visualization:** Line chart (session rate per server), Table (spike windows), Single value (current sessions).
- **CIM Models:** N/A

- **References:** [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)

---

### UC-6.4.18 · File Deletion Volume Anomaly
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Security
- **Value:** Sudden spike in delete operations may indicate ransomware preparation, malicious insider, or script error. Complements mass-modify ransomware use cases.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** Event ID 4660 (object deleted), 4663 with Delete access
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode IN (4660,4663) AccessMask="*DELETE*"
| bucket _time span=1m
| stats count as deletes by Account_Name, ShareName, _time
| eventstats avg(deletes) as avg_d, stdev(deletes) as stdev_d by Account_Name
| where deletes > avg_d + 4*stdev_d AND deletes > 50
```
- **Implementation:** Enable auditing on delete for sensitive trees. Baseline deletes per user/share. Alert on statistical outliers. Exclude known maintenance accounts via lookup.
- **Visualization:** Timeline (delete bursts), Table (user, share, delete count), Line chart (deletes per minute).
- **CIM Models:** N/A

- **References:** [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)

---

