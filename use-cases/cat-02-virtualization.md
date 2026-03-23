# 2. Virtualization

## 2.1 VMware vSphere

**Primary App/TA:** Splunk Add-on for VMware (`Splunk_TA_vmware`, Splunkbase 3215) — Free on Splunkbase; Splunk App for VMware (optional, provides dashboards)

---

### UC-2.1.1 · ESXi Host CPU Contention
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** CPU ready time measures how long a VM waits for physical CPU. High values (>5%) mean the host is overcommitted and VMs are starved for compute.
- **App/TA:** `TA-vmware`
- **Data Sources:** `sourcetype=vmware:perf:cpu`, vCenter performance metrics
- **SPL:**
```spl
index=vmware sourcetype="vmware:perf:cpu" counter="cpu.ready.summation"
| eval ready_pct = round(Value / 20000 * 100, 2)
| stats avg(ready_pct) as avg_ready by host, vm_name
| where avg_ready > 5
| sort -avg_ready
```
- **References:** [Splunk Add-on for VMware](https://splunkbase.splunk.com/app/2913), [vSphere API](https://developer.vmware.com/)
- **Known false positives:** Short CPU ready spikes during boot or cloning; tune threshold or use rolling average.

- **Implementation:** Install `Splunk_TA_vmware` (Splunkbase 3215) on a Heavy Forwarder. Create a read-only vCenter service account with `System.View` and `VirtualMachine.Interact.ConsoleInteract` privileges. Configure collection intervals in the TA setup UI: 300s for performance metrics, 600s for inventory, 3600s for events. Set the `host_segment` to resolve ESXi hostnames. Verify data flow with `index=vmware sourcetype=vmware:perf:cpu | head 5`. Alert when CPU ready exceeds 5% per VM.
- **Visualization:** Heatmap (VMs vs. hosts, colored by ready %), Bar chart (top VMs by ready time), Line chart (trending).
- **CIM Models:** Performance
- **CIM SPL:**
```spl
| tstats `summariesonly` avg(Performance.cpu_load_percent) as avg_cpu
  from datamodel=Performance where nodename=Performance.CPU
  by Performance.host span=1h
| where avg_cpu > 90
```

---

### UC-2.1.2 · ESXi Host Memory Ballooning
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** Memory ballooning means the hypervisor is reclaiming memory from VMs. Swapping at the hypervisor level is worse — causes severe VM performance degradation invisible to the guest OS.
- **App/TA:** `TA-vmware`
- **Data Sources:** `sourcetype=vmware:perf:mem`, vCenter performance metrics
- **SPL:**
```spl
index=vmware sourcetype="vmware:perf:mem" (counter="mem.vmmemctl.average" OR counter="mem.swapped.average")
| eval metric=case(counter="mem.vmmemctl.average", "Balloon_KB", counter="mem.swapped.average", "Swap_KB")
| stats avg(Value) as avg_value by host, vm_name, metric
| where avg_value > 0
| sort -avg_value
```
- **Implementation:** Collected automatically by TA-vmware via vCenter API. Alert when balloon or swap values are >0 for extended periods. Investigate by comparing total VM memory allocation vs. host physical memory.
- **Visualization:** Line chart for balloon/swap trend over time per VM; stacked bar for top 10 VMs by current balloon size; table drill-down to worst offenders with columns for VM name, balloon MB, swap MB, and host.
- **CIM Models:** Performance
- **CIM SPL:**
```spl
| tstats `summariesonly` avg(Performance.mem_used_percent) as mem_pct
                        avg(Performance.swap_used_percent) as swap_pct
  from datamodel=Performance where nodename=Performance.Memory
  by Performance.host span=5m
| where mem_pct > 95 OR swap_pct > 20
```

---

### UC-2.1.3 · Datastore Capacity Trending
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** A full datastore prevents VM disk writes, causing crashes and corruption. Datastores fill gradually from VM growth, snapshots, and log accumulation.
- **App/TA:** `TA-vmware`
- **Data Sources:** `sourcetype=vmware:perf:datastore` or `sourcetype=vmware:inv:datastore`
- **SPL:**
```spl
index=vmware sourcetype="vmware:inv:datastore"
| eval used_pct = round((capacity - freeSpace) / capacity * 100, 1)
| stats latest(used_pct) as used_pct, latest(freeSpace) as free_GB by name
| eval free_GB = round(free_GB / 1073741824, 1)
| where used_pct > 80
| sort -used_pct
```
- **Implementation:** TA-vmware collects datastore inventory automatically. Set alerts at 80% (warning), 90% (high), 95% (critical). Use `predict` command for 30-day forecasting. Include snapshot size in the analysis.
- **Visualization:** Gauge per datastore, Table (name, capacity, free, % used), Line chart with predict trendline.
- **CIM Models:** Performance
- **CIM SPL:**
```spl
| tstats `summariesonly` avg(Performance.storage_used_percent) as disk_pct
  from datamodel=Performance where nodename=Performance.Storage
  by Performance.host Performance.mount span=1h
| where disk_pct > 85
```

---

### UC-2.1.4 · Datastore Latency Spikes
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Storage latency >20ms significantly impacts VM performance. Detects SAN issues, datastore contention, or storage path problems before applications are affected.
- **App/TA:** `TA-vmware`
- **Data Sources:** `sourcetype=vmware:perf:datastore`
- **SPL:**
```spl
index=vmware sourcetype="vmware:perf:datastore" (counter="datastore.totalReadLatency.average" OR counter="datastore.totalWriteLatency.average")
| eval latency_ms = Value
| stats avg(latency_ms) as avg_latency, max(latency_ms) as peak_latency by host, datastore, counter
| where avg_latency > 20
| sort -avg_latency
```
- **Implementation:** Collected via TA-vmware. Alert when average read/write latency exceeds 20ms over 10 minutes. Correlate with IOPS and throughput counters for full picture.
- **Visualization:** Line chart (latency over time), Heatmap (datastores vs. hosts), Table with avg/peak.
- **CIM Models:** Performance
- **CIM SPL:**
```spl
| tstats `summariesonly` avg(Performance.storage_used_percent) as disk_pct
  from datamodel=Performance where nodename=Performance.Storage
  by Performance.host Performance.mount span=1h
| where disk_pct > 85
```

---

### UC-2.1.5 · VM Snapshot Sprawl
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity
- **Value:** Old snapshots consume datastore space exponentially, degrade VM I/O performance, and complicate backups. Snapshots >72 hours old are generally a problem.
- **App/TA:** `TA-vmware`
- **Data Sources:** `sourcetype=vmware:inv:vm` (inventory data)
- **SPL:**
```spl
index=vmware sourcetype="vmware:inv:vm" snapshot_name=*
| eval snapshot_age_days = round((now() - strptime(snapshot_createTime, "%Y-%m-%dT%H:%M:%S")) / 86400, 0)
| where snapshot_age_days > 3
| table vm_name, host, snapshot_name, snapshot_age_days, snapshot_sizeBytes
| eval snapshot_size_GB = round(snapshot_sizeBytes / 1073741824, 2)
| sort -snapshot_age_days
```
- **Implementation:** TA-vmware collects VM inventory including snapshots. Run daily report identifying snapshots >72 hours old. Escalate snapshots >7 days to VM owners. Include snapshot size to show storage impact.
- **Visualization:** Table (VM, snapshot name, age, size), Bar chart (top VMs by snapshot size), Single value (total snapshots >3d).
- **CIM Models:** N/A

---

### UC-2.1.6 · vMotion Tracking
- **Criticality:** 🟢 Low
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Configuration
- **Value:** Tracks VM migrations for troubleshooting and change management. Excessive vMotion can indicate DRS instability or resource contention.
- **App/TA:** `TA-vmware`
- **Data Sources:** `sourcetype=vmware:events`, vCenter event data
- **SPL:**
```spl
index=vmware sourcetype="vmware:events" event_type="VmMigratedEvent" OR event_type="DrsVmMigratedEvent"
| table _time vm_name source_host dest_host user event_type
| sort -_time
```
- **Implementation:** TA-vmware collects vCenter events. Create a report for audit/change tracking. Alert on excessive vMotion frequency (>10 migrations per host per hour may indicate DRS instability).
- **Visualization:** Table (timeline), Sankey diagram (source to destination host), Count by host/hour.
- **CIM Models:** N/A

---

### UC-2.1.7 · HA Failover Events
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** HA failover means a host failed and VMs were restarted on surviving hosts. Indicates hardware failure and potential capacity risk on remaining hosts.
- **App/TA:** `TA-vmware`
- **Data Sources:** `sourcetype=vmware:events`
- **SPL:**
```spl
index=vmware sourcetype="vmware:events" (event_type="DasVmPoweredOnEvent" OR event_type="DasHostFailedEvent" OR event_type="ClusterFailoverActionTriggered")
| table _time event_type host vm_name message
| sort -_time
```
- **Implementation:** Collect vCenter events via TA-vmware. Create critical real-time alert on HA failover events. Correlate with host hardware health and ESXi syslog for root cause.
- **Visualization:** Events timeline (critical alert), Table of affected VMs, Host status panel.
- **CIM Models:** N/A

---

### UC-2.1.8 · DRS Imbalance Detection
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** DRS should keep clusters balanced. Frequent or failed DRS recommendations indicate resource constraints, affinity rule conflicts, or misconfiguration.
- **App/TA:** `TA-vmware`
- **Data Sources:** `sourcetype=vmware:events`
- **SPL:**
```spl
index=vmware sourcetype="vmware:events" event_type="DrsVmMigratedEvent"
| timechart span=1h count by cluster
| where count > 20
```
- **Implementation:** Monitor DRS migration frequency. High migration counts suggest oscillation. Also check for unapplied DRS recommendations (DRS set to manual mode). Correlate with CPU/memory utilization per host.
- **Visualization:** Line chart (migrations per hour), Table of DRS events, Cluster balance comparison chart.
- **CIM Models:** N/A

---

### UC-2.1.9 · VM Sprawl Detection
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity
- **Value:** Orphaned, powered-off, or idle VMs waste storage, IP addresses, backup capacity, and licenses. Regular cleanup frees significant resources.
- **App/TA:** `TA-vmware`
- **Data Sources:** `sourcetype=vmware:inv:vm`
- **SPL:**
```spl
index=vmware sourcetype="vmware:inv:vm"
| where power_state="poweredOff"
| eval days_off = round((now() - strptime(lastPowerOffTime, "%Y-%m-%dT%H:%M:%S")) / 86400, 0)
| where days_off > 30
| table vm_name, host, days_off, numCpu, memoryMB, storage_committed
| sort -days_off
```
- **Implementation:** Run weekly report on powered-off VMs >30 days. Also identify idle VMs: powered on but CPU usage <5% and network <1Kbps consistently. Send reports to VM owners for review.
- **Visualization:** Table (VM, state, days, resources), Pie chart (powered on vs. off), Bar chart (resource waste by team).
- **CIM Models:** N/A

---

### UC-2.1.10 · vSAN Health Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Fault
- **Value:** vSAN is the storage fabric for many VMware clusters. Degraded vSAN health can cause VM data loss and cluster-wide outages.
- **App/TA:** `TA-vmware`, vSAN health service
- **Data Sources:** `sourcetype=vmware:perf:vsan`, vSAN health checks
- **SPL:**
```spl
index=vmware sourcetype="vmware:perf:vsan"
| stats latest(health_status) as health by cluster, disk_group
| where health!="green"
| table cluster disk_group health
```
- **Implementation:** TA-vmware collects vSAN metrics. Also enable vSAN health checks in vCenter. Monitor disk group health, resync progress, and capacity. Alert on any non-green health status.
- **Visualization:** Status indicator per cluster, Table of health issues, Gauge (capacity).
- **CIM Models:** N/A

---

### UC-2.1.11 · ESXi Host Hardware Alerts
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Fault
- **Value:** CIM-based hardware health detects physical component failures (fans, PSU, temperature) at the hypervisor level before they cause host failure.
- **App/TA:** `TA-vmware`
- **Data Sources:** `sourcetype=vmware:events` (vCenter alarms)
- **SPL:**
```spl
index=vmware sourcetype="vmware:events" (event_type="AlarmStatusChangedEvent") alarm_name="Host hardware*"
| table _time host alarm_name old_status new_status
| where new_status="red" OR new_status="yellow"
| sort -_time
```
- **Implementation:** vCenter triggers hardware alarms via CIM providers on ESXi hosts. TA-vmware collects these alarm events. Alert on red/yellow hardware alarms. Ensure CIM providers are installed on ESXi (vendor-specific VIBs).
- **Visualization:** Host health grid (red/yellow/green), Events table, Alert panel.
- **CIM Models:** N/A

---

### UC-2.1.12 · VM Resource Over-Allocation
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Capacity
- **Value:** VMs consistently using <20% of allocated CPU/memory waste resources that other VMs could use. Right-sizing saves money and improves cluster capacity.
- **App/TA:** `TA-vmware`
- **Data Sources:** `sourcetype=vmware:perf:cpu`, `sourcetype=vmware:perf:mem`, `sourcetype=vmware:inv:vm`
- **SPL:**
```spl
index=vmware sourcetype="vmware:perf:cpu" counter="cpu.usage.average"
| stats avg(Value) as avg_cpu by vm_name
| join max=1 vm_name [search index=vmware sourcetype="vmware:inv:vm" | table vm_name numCpu memoryMB]
| where avg_cpu < 20
| sort avg_cpu
| table vm_name numCpu memoryMB avg_cpu
```
- **Implementation:** Analyze 30-day average CPU and memory utilization vs. allocated resources. Generate monthly right-sizing report. Include peak utilization to avoid right-sizing below burst needs.
- **Visualization:** Scatter plot (allocated vs. used), Table with recommendations, Bar chart of waste by team.
- **CIM Models:** Performance
- **CIM SPL:**
```spl
| tstats `summariesonly` avg(Performance.cpu_load_percent) as avg_cpu
  from datamodel=Performance where nodename=Performance.CPU
  by Performance.host span=1h
| where avg_cpu > 90
```

---

### UC-2.1.13 · vCenter Alarm Correlation
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Anomaly
- **Value:** Centralizing vCenter alarms in Splunk reduces mean-time-to-repair during compound failures (e.g. datastore latency + host memory pressure) that appear as separate alarms in vSphere. Alarm storm correlation by shared datastore or maintenance window prevents alert fatigue and highlights the root cause rather than symptoms.
- **App/TA:** `TA-vmware`
- **Data Sources:** `sourcetype=vmware:events`
- **SPL:**
```spl
index=vmware sourcetype="vmware:events" event_type="AlarmStatusChangedEvent"
| stats count by alarm_name, new_status
| sort -count
```
- **Implementation:** TA-vmware automatically collects vCenter events including alarm state changes. Create a dashboard showing all active alarms. Correlate with time of changes, DRS events, and host health.
- **Visualization:** Table of active alarms, Bar chart by alarm type, Timeline.
- **CIM Models:** N/A

---

### UC-2.1.14 · ESXi Patch Compliance
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Value:** Unpatched ESXi hosts have known vulnerabilities. Fleet-wide version tracking ensures consistent patching and audit compliance.
- **App/TA:** `TA-vmware`
- **Data Sources:** `sourcetype=vmware:inv:hostsystem`
- **SPL:**
```spl
index=vmware sourcetype="vmware:inv:hostsystem"
| stats latest(version) as esxi_version, latest(build) as build by host
| eval is_current = if(build="24585291", "Yes", "No")
| sort esxi_version
| table host esxi_version build is_current
```
- **Implementation:** TA-vmware collects host inventory including ESXi version and build number. Maintain a lookup of current expected builds. Dashboard showing compliance percentage and hosts needing updates.
- **Visualization:** Table (host, version, build, compliant), Pie chart (compliant %), Bar chart by version.
- **CIM Models:** N/A

---

### UC-2.1.15 · VM Creation/Deletion Audit
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance, Configuration
- **Value:** Tracks VM lifecycle for change management compliance and resource governance. Detects unauthorized VM creation or suspicious deletions.
- **App/TA:** `TA-vmware`
- **Data Sources:** `sourcetype=vmware:events`
- **SPL:**
```spl
index=vmware sourcetype="vmware:events" (event_type="VmCreatedEvent" OR event_type="VmRemovedEvent" OR event_type="VmClonedEvent")
| eval action=case(event_type="VmCreatedEvent","Created", event_type="VmRemovedEvent","Deleted", event_type="VmClonedEvent","Cloned")
| table _time action vm_name user host datacenter
| sort -_time
```
- **Implementation:** Collected automatically via TA-vmware vCenter events. Create daily report. Correlate with change management tickets. Alert on deletions of production VMs.
- **Visualization:** Table (timeline), Bar chart (create/delete by user), Line chart (VM count trending).
- **CIM Models:** N/A

---

### UC-2.1.16 · VM Network I/O and Dropped Packets
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Dropped packets at the vNIC level indicate network saturation, driver issues, or misconfigured traffic shaping policies. Unlike guest OS network stats, hypervisor-level counters capture drops the VM never sees — making this the only reliable way to detect silent packet loss that degrades application performance.
- **App/TA:** `Splunk_TA_vmware`
- **Data Sources:** `sourcetype=vmware:perf:net`, vCenter network performance metrics
- **SPL:**
```spl
index=vmware sourcetype="vmware:perf:net" (counter="net.droppedRx.summation" OR counter="net.droppedTx.summation" OR counter="net.usage.average")
| stats sum(eval(if(counter="net.droppedRx.summation", Value, 0))) as dropped_rx, sum(eval(if(counter="net.droppedTx.summation", Value, 0))) as dropped_tx, avg(eval(if(counter="net.usage.average", Value, 0))) as avg_kbps by host, vm_name
| where dropped_rx > 0 OR dropped_tx > 0
| sort -dropped_rx
| table vm_name, host, avg_kbps, dropped_rx, dropped_tx
```
- **Implementation:** Collected via Splunk_TA_vmware performance counters. Alert when any VM shows >0 dropped packets sustained over 5 minutes. Correlate with VM network usage to determine if drops correlate with saturation. Check dvSwitch traffic shaping policies and physical NIC utilization on the host.
- **Visualization:** Table (VM, host, throughput, drops), Line chart (drops over time), Bar chart (top VMs by drops).
- **CIM Models:** N/A

---

### UC-2.1.17 · VM Disk IOPS Trending and Throttling
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Tracks read/write IOPS per VM to identify storage-hungry workloads before they impact other VMs on the same datastore. When Storage I/O Control (SIOC) throttles a VM, it appears as increased latency inside the guest — this use case exposes the throttling at the hypervisor level.
- **App/TA:** `Splunk_TA_vmware`
- **Data Sources:** `sourcetype=vmware:perf:datastore`, vCenter disk performance metrics
- **SPL:**
```spl
index=vmware sourcetype="vmware:perf:datastore" (counter="datastore.numberReadAveraged.average" OR counter="datastore.numberWriteAveraged.average")
| eval metric=case(counter="datastore.numberReadAveraged.average", "read_iops", counter="datastore.numberWriteAveraged.average", "write_iops")
| stats avg(Value) as avg_val by vm_name, host, datastore, metric
| eval avg_val=round(avg_val, 0)
| stats sum(avg_val) as total_iops, values(eval(metric . "=" . avg_val)) as breakdown by vm_name, host, datastore
| where total_iops > 500
| sort -total_iops
| table vm_name, host, datastore, total_iops, breakdown
```
- **Implementation:** Collected via Splunk_TA_vmware. Baseline per-VM IOPS over 7 days. Alert when a VM exceeds 2x its baseline sustained for 15 minutes. Track SIOC injector latency counters to detect throttling. Correlate high-IOPS VMs with datastore latency spikes from UC-2.1.4.
- **Visualization:** Line chart (IOPS per VM over time), Stacked bar chart (read vs write), Table (top IOPS consumers).
- **CIM Models:** Performance
- **CIM SPL:**
```spl
| tstats `summariesonly` avg(Performance.storage_used_percent) as disk_pct
  from datamodel=Performance where nodename=Performance.Storage
  by Performance.host Performance.mount span=1h
| where disk_pct > 85
```

---

### UC-2.1.18 · VMware Tools Status and Version Compliance
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Compliance
- **Value:** Outdated or missing VMware Tools causes loss of guest-host integration — no graceful shutdown, no quiesced snapshots, no balloon driver, degraded network/disk performance, and inaccurate guest OS reporting. Tools must be current for vMotion to function optimally.
- **App/TA:** `Splunk_TA_vmware`
- **Data Sources:** `sourcetype=vmware:inv:vm` (inventory data)
- **SPL:**
```spl
index=vmware sourcetype="vmware:inv:vm"
| stats latest(toolsStatus) as tools_status, latest(toolsVersionStatus) as version_status, latest(toolsRunningStatus) as running_status by vm_name, host, guest_os
| where tools_status!="toolsOk" OR version_status!="guestToolsCurrent"
| sort tools_status
| table vm_name, host, guest_os, tools_status, version_status, running_status
```
- **Implementation:** Collected automatically via Splunk_TA_vmware inventory. Run daily compliance report. toolsStatus values: toolsOk, toolsOld, toolsNotInstalled, toolsNotRunning. Alert on toolsNotInstalled for production VMs. Track version_status to ensure Tools are current across the fleet.
- **Visualization:** Pie chart (Tools status distribution), Table (non-compliant VMs), Bar chart (by guest OS).
- **CIM Models:** N/A

---

### UC-2.1.19 · Distributed vSwitch Port Health and Errors
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault, Performance
- **Value:** VDS port errors indicate VLAN misconfiguration, MTU mismatches, uplink failures, or teaming policy problems. VDS health check results (available since vSphere 5.1) detect common misconfigurations that cause intermittent connectivity issues that are extremely hard to troubleshoot from the guest OS.
- **App/TA:** `Splunk_TA_vmware`
- **Data Sources:** `sourcetype=vmware:events`, VDS health check results, vCenter network events
- **SPL:**
```spl
index=vmware sourcetype="vmware:events" (event_type="*Dvs*" OR event_type="*dvPort*" OR event_type="*VmnicDisconnectedEvent*")
| stats count by event_type, host, dvs_name
| sort -count
| table event_type, host, dvs_name, count
```
- **Implementation:** Enable VDS health checks in vCenter (VLAN/MTU check, Teaming/Failover check). Collect vCenter events via Splunk_TA_vmware. Alert on VmnicDisconnectedEvent (physical uplink loss), DvsPortBlockedEvent, and any health check failure. Create a network topology dashboard showing VDS → uplink → VLAN mapping.
- **Visualization:** Status grid (VDS health per host), Events table, Network topology diagram.
- **CIM Models:** N/A

---

### UC-2.1.20 · Resource Pool Utilization and Limits
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity
- **Value:** Resource pools with hard limits can silently throttle VMs even when the cluster has spare capacity. Pools without reservations provide no guarantees during contention. Monitoring utilization vs. configured limits/reservations reveals misconfigurations that cause unpredictable performance.
- **App/TA:** `Splunk_TA_vmware`
- **Data Sources:** `sourcetype=vmware:inv:resourcepool`, `sourcetype=vmware:perf:cpu`
- **SPL:**
```spl
index=vmware sourcetype="vmware:inv:resourcepool"
| eval cpu_limit_ghz=if(cpuAllocation_limit=-1, "Unlimited", round(cpuAllocation_limit/1000, 1))
| eval mem_limit_gb=if(memoryAllocation_limit=-1, "Unlimited", round(memoryAllocation_limit/1024, 1))
| table name, cluster, cpuAllocation_reservation, cpu_limit_ghz, cpuAllocation_shares, memoryAllocation_reservation, mem_limit_gb, memoryAllocation_shares
| sort cluster, name
```
- **Implementation:** Collect resource pool inventory via Splunk_TA_vmware. Alert when resource pool utilization approaches its configured limit (>80%). Flag resource pools with unlimited limits and zero reservations in production — they offer no guarantees. Cross-reference with VM performance to detect pool-level throttling.
- **Visualization:** Table (pool hierarchy, limits, utilization), Tree map (pools by resource allocation), Gauge (utilization vs limit).
- **CIM Models:** N/A

---

### UC-2.1.21 · ESXi Host Unexpected Reboot Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Unexpected ESXi reboots indicate hardware failure (memory ECC errors, CPU machine checks), kernel panics (PSODs), or firmware bugs. Each reboot triggers HA failover of all VMs on that host, causing widespread service disruption. Early detection enables root cause analysis before the issue recurs.
- **App/TA:** `Splunk_TA_vmware`
- **Data Sources:** `sourcetype=vmware:events`, ESXi syslog
- **SPL:**
```spl
index=vmware sourcetype="vmware:events" (event_type="HostConnectionLostEvent" OR event_type="HostDisconnectedEvent" OR event_type="HostShutdownEvent")
| table _time, host, event_type, message, user
| sort -_time
```
- **Implementation:** Collect vCenter events via Splunk_TA_vmware. Also forward ESXi syslog directly to Splunk for boot-time messages. Alert immediately on HostConnectionLostEvent (ungraceful). Correlate with IPMI/iLO/iDRAC logs if available. Differentiate planned reboots (HostShutdownEvent with a user) from unplanned (HostConnectionLostEvent).
- **Visualization:** Timeline (host events), Status grid (host connectivity), Alert panel (critical).
- **CIM Models:** N/A

---

### UC-2.1.22 · vCenter Service Health
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** vCenter is the management plane for the entire VMware environment. If VPXD, SSO, or the content library service fails, you lose visibility into your VMs and cannot perform management operations. Monitoring vCenter appliance health ensures the control plane is operational.
- **App/TA:** `Splunk_TA_vmware`, vCenter syslog
- **Data Sources:** `sourcetype=vmware:events`, vCenter VAMI health API, vCenter syslog (`/var/log/vmware/vpxd/vpxd.log`)
- **SPL:**
```spl
index=vmware sourcetype="syslog" source="/var/log/vmware/vpxd/*" ("ERROR" OR "CRITICAL" OR "FATAL")
| stats count as errors by host, source
| where errors > 10
| sort -errors
| table host, source, errors
```
- **Implementation:** Forward vCenter appliance syslog to Splunk. Monitor VPXD, STS (SSO), content library, and PostgreSQL logs. Also create a scripted input to poll the VAMI health API (`https://vcsa:5480/rest/applmgmt/health`). Alert when any service reports unhealthy status. Monitor vCenter disk space (database growth).
- **Visualization:** Status grid (service health), Line chart (error rate over time), Table (recent errors).
- **CIM Models:** N/A

---

### UC-2.1.23 · VM Unexpected Power State Changes
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Unexpected VM shutdowns or resets indicate guest OS crashes, resource exhaustion, or unauthorized actions. Unlike planned maintenance, unplanned power state changes disrupt services without warning. Correlating with the initiating user distinguishes admin actions from automated or malicious changes.
- **App/TA:** `Splunk_TA_vmware`
- **Data Sources:** `sourcetype=vmware:events`
- **SPL:**
```spl
index=vmware sourcetype="vmware:events" (event_type="VmPoweredOffEvent" OR event_type="VmResettingEvent" OR event_type="VmGuestShutdownEvent" OR event_type="VmGuestRebootEvent")
| eval planned=if(match(user, "^(admin|svc_|scheduled)"), "Planned", "Unplanned")
| where planned="Unplanned"
| table _time, vm_name, host, event_type, user, message
| sort -_time
```
- **Implementation:** Collect vCenter events via Splunk_TA_vmware. Maintain a lookup of authorized service accounts and scheduled maintenance windows. Alert on any power-off or reset outside of maintenance windows or by non-authorized users. Cross-reference with guest OS event logs for crash evidence.
- **Visualization:** Timeline (power events), Table (unplanned shutdowns), Bar chart (by VM and user).
- **CIM Models:** Change

---

### UC-2.1.24 · ESXi Host NTP Clock Drift
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Value:** Clock drift on ESXi hosts causes VM time drift, Kerberos authentication failures, log correlation issues, and vSAN timing problems. NTP misconfiguration is a common root cause of intermittent authentication failures that are difficult to diagnose.
- **App/TA:** `Splunk_TA_vmware`, ESXi syslog
- **Data Sources:** ESXi syslog, `sourcetype=vmware:inv:hostsystem`
- **SPL:**
```spl
index=vmware sourcetype="vmware:inv:hostsystem"
| stats latest(ntpConfig_server) as ntp_servers, latest(dateTimeInfo_timeZone) as timezone by host
| eval ntp_configured=if(isnotnull(ntp_servers) AND ntp_servers!="", "Yes", "No")
| table host, ntp_configured, ntp_servers, timezone
| sort ntp_configured
```
- **Implementation:** Collect host inventory via Splunk_TA_vmware. Also monitor ESXi syslog for NTP daemon messages. Create a scripted input using `esxcli system time get` via PowerCLI to capture actual time offset. Alert when NTP is not configured or when time offset exceeds 1 second.
- **Visualization:** Table (host, NTP status, servers), Status grid (NTP health), Gauge (drift in ms).
- **CIM Models:** N/A

---

### UC-2.1.25 · Storage I/O Control (SIOC) Throttling
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance
- **Value:** SIOC throttles VM disk I/O when datastore latency exceeds thresholds (default 30ms). When SIOC activates, VMs experience injected latency that appears as slow storage from the guest perspective. Detecting SIOC activation reveals contention invisible from the guest OS.
- **App/TA:** `Splunk_TA_vmware`
- **Data Sources:** `sourcetype=vmware:perf:datastore`, vCenter events
- **SPL:**
```spl
index=vmware sourcetype="vmware:perf:datastore" counter="datastore.sizeNormalizedDatastoreLatency.average"
| stats avg(Value) as avg_latency by datastore, host
| where avg_latency > 25
| sort -avg_latency
| table datastore, host, avg_latency
```
- **Implementation:** Collected via Splunk_TA_vmware. SIOC triggers when datastore latency exceeds its configured threshold. Monitor the sizeNormalizedDatastoreLatency counter which SIOC uses for its decisions. Alert when latency approaches the SIOC threshold (default 30ms). Correlate with per-VM IOPS from UC-2.1.17 to identify the VM causing contention.
- **Visualization:** Line chart (datastore latency over time with SIOC threshold line), Table (datastores near threshold), Heatmap (datastores by latency).
- **CIM Models:** N/A

---

### UC-2.1.26 · VM Hardware Version Compliance
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Compliance
- **Value:** Older VM hardware versions lack support for newer features — vNVMe, UEFI secure boot, vTPM, higher vCPU/memory limits, and improved device emulation. Running mixed hardware versions complicates fleet management and limits what features you can enable cluster-wide.
- **App/TA:** `Splunk_TA_vmware`
- **Data Sources:** `sourcetype=vmware:inv:vm`
- **SPL:**
```spl
index=vmware sourcetype="vmware:inv:vm"
| stats latest(hw_version) as hw_version, latest(guest_os) as guest_os by vm_name, host
| eval hw_num=tonumber(replace(hw_version, "vmx-", ""))
| where hw_num < 19
| stats count by hw_version
| sort hw_version
| table hw_version, count
```
- **Implementation:** Collected via Splunk_TA_vmware inventory. Define target hardware version per cluster (e.g., vmx-19 for vSphere 7.0 U2+, vmx-20 for vSphere 8.0). Generate weekly compliance reports. Coordinate upgrades during maintenance windows as they require VM power cycle.
- **Visualization:** Pie chart (hardware version distribution), Table (VMs needing upgrade), Bar chart (versions by cluster).
- **CIM Models:** N/A

---

### UC-2.1.27 · VM Disk Consolidation Needed
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Fault
- **Value:** After a failed snapshot deletion, VMs can have orphaned delta disks that keep growing and degrading I/O performance. The "consolidation needed" flag indicates the disk chain is broken and needs manual intervention before it causes datastore exhaustion.
- **App/TA:** `Splunk_TA_vmware`
- **Data Sources:** `sourcetype=vmware:inv:vm`
- **SPL:**
```spl
index=vmware sourcetype="vmware:inv:vm" consolidationNeeded="true"
| table vm_name, host, datastore, consolidationNeeded
| sort vm_name
```
- **Implementation:** Collected via Splunk_TA_vmware inventory. Alert immediately on any VM with consolidationNeeded=true. Consolidation should be performed during low-I/O periods as it can temporarily stun the VM. Track datastore free space for affected VMs as orphaned deltas grow continuously.
- **Visualization:** Table (VMs needing consolidation), Single value (count), Status indicator.
- **CIM Models:** N/A

---

### UC-2.1.28 · Thin-Provisioned Disk Growth Rate
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity
- **Value:** Thin-provisioned disks start small but grow to their provisioned maximum as the guest writes data. If the total provisioned size of all thin disks on a datastore exceeds physical capacity (over-provisioning), the datastore can fill unexpectedly. Tracking actual growth rate predicts when this will happen.
- **App/TA:** `Splunk_TA_vmware`
- **Data Sources:** `sourcetype=vmware:inv:vm` (storage_committed, storage_uncommitted)
- **SPL:**
```spl
index=vmware sourcetype="vmware:inv:vm"
| eval committed_gb=round(storage_committed/1073741824, 1)
| eval provisioned_gb=round((storage_committed+storage_uncommitted)/1073741824, 1)
| eval thin_ratio=round(committed_gb/provisioned_gb*100, 1)
| stats latest(committed_gb) as used_gb, latest(provisioned_gb) as provisioned_gb, latest(thin_ratio) as thin_pct by vm_name, datastore
| where thin_pct < 80
| sort thin_pct
| table vm_name, datastore, used_gb, provisioned_gb, thin_pct
```
- **Implementation:** Collect VM storage inventory via Splunk_TA_vmware. Calculate total provisioned vs. total physical per datastore to determine over-provisioning ratio. Track committed bytes over time to calculate daily growth rate. Alert when datastore over-provisioning ratio exceeds 200% and growth rate will fill physical capacity within 30 days.
- **Visualization:** Table (VM, used vs provisioned), Gauge (datastore over-provisioning ratio), Line chart (growth trend with prediction).
- **CIM Models:** N/A

---

### UC-2.1.29 · VM Affinity and Anti-Affinity Rule Violations
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Value:** Anti-affinity rules ensure redundant VMs (e.g., HA pairs, database replicas) run on different hosts. Rule violations mean a single host failure can take down both instances. Affinity rules keep related VMs together for performance. DRS may violate rules when resources are constrained.
- **App/TA:** `Splunk_TA_vmware`
- **Data Sources:** `sourcetype=vmware:events`, cluster rule configuration
- **SPL:**
```spl
index=vmware sourcetype="vmware:events" event_type="DrsRuleViolatedEvent"
| table _time, cluster, rule_name, vm_name, host, message
| sort -_time
```
- **Implementation:** Collect vCenter events via Splunk_TA_vmware. DRS logs rule violations as events. Also create a scripted input using PowerCLI to enumerate cluster rules and check current VM placement. Alert immediately on anti-affinity violations in production. Review affinity rule compliance weekly.
- **Visualization:** Table (violated rules), Status grid (rule compliance), Alert panel.
- **CIM Models:** N/A

---

### UC-2.1.30 · Storage DRS Recommendations and Actions
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance, Capacity
- **Value:** Storage DRS (SDRS) balances VM storage across datastores within a datastore cluster. Frequent SDRS migrations indicate capacity or performance imbalance. Unapplied recommendations (when SDRS is in manual mode) mean datastores are unbalanced and latency may be inconsistent.
- **App/TA:** `Splunk_TA_vmware`
- **Data Sources:** `sourcetype=vmware:events`
- **SPL:**
```spl
index=vmware sourcetype="vmware:events" (event_type="StorageDrsRecommendation*" OR event_type="StorageMigratedEvent")
| eval action=case(match(event_type, "Recommendation"), "Recommended", event_type="StorageMigratedEvent", "Migrated")
| stats count by action, datastore_cluster
| sort -count
| table datastore_cluster, action, count
```
- **Implementation:** Collect vCenter events via Splunk_TA_vmware. Track SDRS migration frequency per datastore cluster. Alert when manual-mode SDRS has unapplied recommendations older than 24 hours. Monitor datastore cluster balance — alert when any datastore deviates >20% from the cluster average utilization.
- **Visualization:** Table (recommendations and actions), Bar chart (migrations per cluster), Line chart (cluster balance over time).
- **CIM Models:** N/A

---

### UC-2.1.31 · Fault Tolerance Status and Replication Lag
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** VMware Fault Tolerance provides zero-downtime protection by maintaining a live secondary copy of a VM. If FT replication falls behind or becomes disabled, the VM loses its zero-downtime protection. FT lag indicates network bandwidth or CPU contention on the secondary host.
- **App/TA:** `Splunk_TA_vmware`
- **Data Sources:** `sourcetype=vmware:inv:vm`, `sourcetype=vmware:events`
- **SPL:**
```spl
index=vmware sourcetype="vmware:inv:vm" ftInfo_role=*
| stats latest(ftInfo_role) as ft_role, latest(ftInfo_instanceUuid) as ft_pair by vm_name, host
| eval ft_status=if(isnotnull(ft_role), ft_role, "Not Configured")
| table vm_name, host, ft_status, ft_pair
| append [search index=vmware sourcetype="vmware:events" event_type="*FaultTolerance*" | stats count by event_type, vm_name | table event_type, vm_name, count]
```
- **Implementation:** Collect VM inventory and events via Splunk_TA_vmware. Monitor FT state changes (enabled, disabled, failover occurred). Alert when FT is disabled on a protected VM or when FT failover events occur. Track FT vMotion log latency counters to detect replication lag.
- **Visualization:** Status grid (FT-protected VMs), Events timeline (FT state changes), Table (FT configuration).
- **CIM Models:** N/A

---

### UC-2.1.32 · ESXi Host Certificate Expiration
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Value:** ESXi hosts use certificates for secure communication with vCenter and other hosts. Expired certificates cause vCenter disconnection, vMotion failures, and HA communication breakdowns. The VMCA-signed certificates have a 5-year default lifetime, but custom certificates may expire sooner.
- **App/TA:** `Splunk_TA_vmware`, custom scripted input
- **Data Sources:** Custom scripted input (PowerCLI certificate query)
- **SPL:**
```spl
index=vmware sourcetype="esxi_certificates"
| eval days_to_expiry=round((strptime(not_after, "%Y-%m-%dT%H:%M:%S") - now()) / 86400, 0)
| where days_to_expiry < 90
| sort days_to_expiry
| table host, subject, issuer, days_to_expiry, not_after
```
- **Implementation:** Create a PowerCLI scripted input: `Get-VMHost | Get-VMHostCertificate | Select VMHost, NotAfter, Subject, Issuer`. Run daily. Alert at 90 days (warning), 30 days (high), 7 days (critical). Also check vCenter VMCA certificate and STS signing certificate which cause widespread failures when expired.
- **Visualization:** Table (host, cert, expiry), Single value (certs expiring within 30 days), Timeline (upcoming expirations).
- **CIM Models:** N/A

---

### UC-2.1.33 · ESXi Host Lockdown Mode Compliance
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security, Compliance
- **Value:** Lockdown mode restricts direct ESXi access, forcing all management through vCenter. Hosts not in lockdown mode can be accessed directly via SSH or the DCUI, bypassing vCenter audit trails and RBAC. Required by security frameworks like CIS, DISA STIG, and PCI DSS.
- **App/TA:** `Splunk_TA_vmware`
- **Data Sources:** `sourcetype=vmware:inv:hostsystem`
- **SPL:**
```spl
index=vmware sourcetype="vmware:inv:hostsystem"
| stats latest(lockdownMode) as lockdown, latest(sshEnabled) as ssh by host, cluster
| where lockdown!="lockdownNormal" OR ssh="true"
| table host, cluster, lockdown, ssh
```
- **Implementation:** Collect host inventory via Splunk_TA_vmware. Define expected lockdown mode per cluster (lockdownNormal or lockdownStrict). Alert when any production host has lockdown disabled or SSH enabled outside a maintenance window. Generate weekly compliance reports for security audits.
- **Visualization:** Status grid (lockdown compliance), Table (non-compliant hosts), Pie chart (compliance rate).
- **CIM Models:** N/A

---

### UC-2.1.34 · Orphaned VMDK Files on Datastores
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Capacity
- **Value:** When VMs are deleted without cleaning up their disk files, or when snapshots leave behind delta VMDKs, orphaned files accumulate and waste datastore space. In large environments, orphaned files can consume terabytes of storage that cannot be identified through normal VM inventory.
- **App/TA:** `Splunk_TA_vmware`, custom scripted input
- **Data Sources:** Custom scripted input (datastore file browser vs VM inventory comparison)
- **SPL:**
```spl
index=vmware sourcetype="datastore_orphans"
| stats sum(size_gb) as total_waste_gb, count as orphan_count by datastore
| sort -total_waste_gb
| table datastore, orphan_count, total_waste_gb
```
- **Implementation:** Create a PowerCLI scripted input that lists all VMDK files on each datastore and compares against registered VM disk paths. Files not attached to any VM are orphans. Run weekly during off-peak hours (datastore browsing is I/O intensive). Alert when total orphan size exceeds 100GB per datastore.
- **Visualization:** Table (datastore, orphan count, wasted GB), Bar chart (waste by datastore), Single value (total waste).
- **CIM Models:** N/A

---

### UC-2.1.35 · VM Guest OS Disk Space via VMware Tools
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Capacity
- **Value:** VMware Tools reports guest OS filesystem utilization to vCenter, enabling disk space monitoring without an in-guest agent. Particularly valuable for appliances, embedded systems, and VMs where you cannot install a Splunk forwarder. Catches disk-full conditions before they crash applications.
- **App/TA:** `Splunk_TA_vmware`
- **Data Sources:** `sourcetype=vmware:inv:vm` (guest disk info)
- **SPL:**
```spl
index=vmware sourcetype="vmware:inv:vm" guest_disk_path=*
| eval used_pct=round((guest_disk_capacity - guest_disk_freeSpace) / guest_disk_capacity * 100, 1)
| where used_pct > 85
| sort -used_pct
| table vm_name, host, guest_disk_path, used_pct, guest_disk_capacity, guest_disk_freeSpace
```
- **Implementation:** Requires VMware Tools running in the guest. Splunk_TA_vmware collects guest disk info as part of VM inventory. Alert at 85% (warning) and 95% (critical). Note: this is less granular than an in-guest agent — it reports per-partition but with slower refresh intervals (typically 5-10 minutes).
- **Visualization:** Table (VM, disk, usage), Gauge per critical VM, Bar chart (top full disks).
- **CIM Models:** N/A

---

### UC-2.1.36 · VM Encryption and vTPM Compliance
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security, Compliance
- **Value:** VM encryption protects data at rest on shared storage. vTPM enables Credential Guard, BitLocker, and measured boot inside VMs. Compliance frameworks increasingly require encryption for workloads handling sensitive data. Tracking which VMs are encrypted vs. which should be ensures policy adherence.
- **App/TA:** `Splunk_TA_vmware`
- **Data Sources:** `sourcetype=vmware:inv:vm`
- **SPL:**
```spl
index=vmware sourcetype="vmware:inv:vm"
| stats latest(cryptoState) as encryption, latest(vtpm_present) as vtpm by vm_name, host, guest_os
| eval encrypted=if(encryption="encrypted", "Yes", "No")
| eval has_vtpm=if(vtpm_present="true", "Yes", "No")
| table vm_name, host, guest_os, encrypted, has_vtpm
| sort encrypted, has_vtpm
```
- **Implementation:** Collect VM inventory via Splunk_TA_vmware. Maintain a lookup defining which VMs require encryption (based on data classification). Cross-reference inventory with the requirements lookup. Alert when a VM that should be encrypted is not. Generate quarterly compliance reports for audit.
- **Visualization:** Table (VM encryption status), Pie chart (encrypted vs not), Bar chart (compliance by department).
- **CIM Models:** N/A

---

### UC-2.1.37 · VM Template Inventory and Staleness
- **Criticality:** 🟢 Low
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Compliance
- **Value:** Stale VM templates with outdated OS patches, expired certificates, or old application versions get deployed into production and immediately become vulnerable. Tracking template age and last update ensures new VMs start from a secure, current baseline.
- **App/TA:** `Splunk_TA_vmware`
- **Data Sources:** `sourcetype=vmware:inv:vm` (templates are VMs with isTemplate=true)
- **SPL:**
```spl
index=vmware sourcetype="vmware:inv:vm" isTemplate="true"
| eval age_days=round((now() - strptime(modifiedTime, "%Y-%m-%dT%H:%M:%S")) / 86400, 0)
| sort -age_days
| table vm_name, guest_os, hw_version, age_days, modifiedTime
```
- **Implementation:** Collect VM inventory via Splunk_TA_vmware (templates appear as VMs with isTemplate=true). Flag templates older than 30 days as needing refresh. Alert on templates older than 90 days. Track deployment frequency per template to identify popular templates that should be prioritized for updates.
- **Visualization:** Table (template, OS, age), Bar chart (templates by age bucket), Single value (templates >90 days).
- **CIM Models:** N/A

---

### UC-2.1.38 · ESXi Host Syslog Forwarding Health
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Compliance
- **Value:** If ESXi syslog forwarding breaks, you lose visibility into host-level events — PSOD messages, hardware errors, authentication attempts, and kernel warnings. Since syslog is often the only real-time data source from ESXi (vs. the polling-based TA), silent forwarding failures create dangerous blind spots.
- **App/TA:** `Splunk_TA_vmware`, ESXi syslog
- **Data Sources:** ESXi syslog, `sourcetype=vmware:inv:hostsystem`
- **SPL:**
```spl
index=vmware sourcetype="vmware:inv:hostsystem"
| stats latest(syslogConfig_logHost) as syslog_target by host
| eval syslog_configured=if(isnotnull(syslog_target) AND syslog_target!="", "Yes", "No")
| append [search index=esxi sourcetype=syslog | stats latest(_time) as last_seen by host]
| stats latest(syslog_configured) as configured, latest(last_seen) as last_event by host
| eval hours_silent=round((now()-last_event)/3600, 1)
| where configured="No" OR hours_silent > 2
| table host, configured, syslog_target, last_event, hours_silent
```
- **Implementation:** Verify syslog configuration via Splunk_TA_vmware host inventory. Monitor for gaps in syslog data per host — if a host stops sending syslog for >1 hour, investigate. Alert on hosts without syslog configured. Validate syslog protocol (UDP vs TCP vs TLS) meets security requirements.
- **Visualization:** Status grid (syslog health per host), Table (misconfigured hosts), Single value (hosts with gaps).
- **CIM Models:** N/A

---

### UC-2.1.39 · ESXi Host Firewall Rule Audit
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security, Compliance
- **Value:** ESXi has a built-in firewall that controls which services are accessible. Overly permissive rules (e.g., SSH from any IP, open NFC ports) expand the attack surface. CIS benchmarks and DISA STIGs require specific firewall configurations on ESXi hosts.
- **App/TA:** `Splunk_TA_vmware`, custom scripted input
- **Data Sources:** Custom scripted input (PowerCLI `Get-VMHostFirewallException`)
- **SPL:**
```spl
index=vmware sourcetype="esxi_firewall"
| where enabled="true" AND allowedAll="true"
| table host, rule_name, protocol, port, direction, allowedAll
| sort host, rule_name
```
- **Implementation:** Create a PowerCLI scripted input: `Get-VMHost | Get-VMHostFirewallException | Where Enabled | Select VMHost, Name, Enabled, IncomingPorts, OutgoingPorts, Protocols`. Run daily. Alert on rules with AllHosts=true for sensitive services (SSH, NFC, vSAN). Compare against a baseline lookup of approved rules.
- **Visualization:** Table (host, rule, ports, scope), Bar chart (rules allowing all IPs), Compliance percentage.
- **CIM Models:** N/A

---

### UC-2.1.40 · VM NUMA Alignment
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance
- **Value:** VMs that span NUMA nodes experience cross-node memory access latency — 2-3x slower than local access. Large VMs (8+ vCPUs or 32+ GB RAM) are most affected. Proper NUMA alignment can improve performance by 10-30% for memory-intensive workloads like databases and in-memory caches.
- **App/TA:** `Splunk_TA_vmware`, custom scripted input
- **Data Sources:** `sourcetype=vmware:perf:mem`, host NUMA topology
- **SPL:**
```spl
index=vmware sourcetype="vmware:perf:mem" counter="mem.llSwapUsed.average"
| stats avg(Value) as ll_swap_kb by vm_name, host
| join max=1 host [search index=vmware sourcetype="vmware:inv:hostsystem" | eval numa_nodes=numNumaNodes | table host, numa_nodes, numCpuCores]
| join max=1 vm_name [search index=vmware sourcetype="vmware:inv:vm" | table vm_name, numCpu, memoryMB]
| eval vcpus_per_node=round(numCpuCores/numa_nodes, 0)
| eval spans_numa=if(numCpu > vcpus_per_node, "Yes", "No")
| where spans_numa="Yes"
| table vm_name, host, numCpu, memoryMB, vcpus_per_node, numa_nodes, spans_numa, ll_swap_kb
| sort -memoryMB
```
- **Implementation:** Collect host NUMA topology from inventory and VM sizing. Flag VMs whose vCPU count exceeds a single NUMA node's core count. For critical workloads, set `numa.vcpu.preferHT=true` and consider vNUMA configuration. Monitor `mem.llSwapUsed` for cross-NUMA penalties.
- **Visualization:** Table (VM, vCPUs, NUMA alignment), Scatter plot (VM size vs NUMA fit), Single value (misaligned VMs).
- **CIM Models:** N/A

---

### UC-2.1.41 · ESXi Host Coredump Configuration
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Compliance
- **Value:** When an ESXi host experiences a PSOD (Purple Screen of Death), the coredump contains critical diagnostic information. Without a properly configured dump target (network or local), the coredump is lost on reboot and root cause analysis becomes impossible. Particularly important for diskless/boot-from-SAN hosts.
- **App/TA:** `Splunk_TA_vmware`, custom scripted input
- **Data Sources:** Custom scripted input (`esxcli system coredump`)
- **SPL:**
```spl
index=vmware sourcetype="esxi_coredump"
| stats latest(network_configured) as net_dump, latest(partition_configured) as part_dump by host
| eval dump_ok=if(net_dump="true" OR part_dump="true", "Yes", "No")
| where dump_ok="No"
| table host, net_dump, part_dump, dump_ok
```
- **Implementation:** Create scripted input via PowerCLI or SSH: `esxcli system coredump network get` and `esxcli system coredump partition get`. Run daily. Alert on hosts without any dump target configured. For stateless/diskless hosts, ensure network dump collector is configured and reachable.
- **Visualization:** Status grid (dump config per host), Table (unconfigured hosts), Compliance percentage.
- **CIM Models:** N/A

---

### UC-2.1.42 · VM CPU Ready Time Percentage
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance
- **Value:** Measures time VMs wait for physical CPU — distinct from host utilization. High CPU ready time indicates over-committed CPU; VMs are queued waiting for scheduler time even when host CPU % appears acceptable. Critical for identifying latent contention invisible from guest metrics.
- **App/TA:** `Splunk_TA_vmware`
- **Data Sources:** `sourcetype=vmware:perf:cpu` (counter=cpu.ready.summation)
- **SPL:**
```spl
index=vmware sourcetype="vmware:perf:cpu" counter="cpu.ready.summation"
| eval ready_pct = round(Value / 20000 * 100, 2)
| stats avg(ready_pct) as avg_ready_pct, max(ready_pct) as peak_ready_pct by host, vm_name
| where avg_ready_pct > 5
| sort -avg_ready_pct
| table vm_name, host, avg_ready_pct, peak_ready_pct
```
- **Implementation:** TA-vmware collects cpu.ready.summation (milliseconds VM waited per 20s interval). Formula: ready_pct = Value / 20000 * 100 (20s = 20000ms). Alert when avg_ready_pct >5% over 10 minutes. Use rolling 15-min average to smooth spikes. Correlate with cluster CPU utilization and DRS migrations.
- **Visualization:** Heatmap (VMs vs hosts, colored by ready %), Bar chart (top VMs by ready time), Line chart (ready % trend).
- **CIM Models:** N/A

---

### UC-2.1.43 · VM Disk I/O Latency per Datastore
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Correlate VM disk latency to specific datastores to identify storage bottlenecks. When multiple VMs on the same datastore show high latency, the datastore or underlying storage is the culprit rather than individual VM workload.
- **App/TA:** `Splunk_TA_vmware`
- **Data Sources:** `sourcetype=vmware:perf:datastore` (datastore.totalReadLatency.average, datastore.totalWriteLatency.average — per VM when object is VM)
- **SPL:**
```spl
index=vmware sourcetype="vmware:perf:datastore" (counter="datastore.totalReadLatency.average" OR counter="datastore.totalWriteLatency.average")
| eval read_latency = if(counter="datastore.totalReadLatency.average", Value, null())
| eval write_latency = if(counter="datastore.totalWriteLatency.average", Value, null())
| stats avg(read_latency) as avg_read_ms, avg(write_latency) as avg_write_ms by vm_name, host, datastore
| eval avg_latency = max(coalesce(avg_read_ms, 0), coalesce(avg_write_ms, 0))
| where avg_latency > 20
| sort -avg_latency
| table vm_name, host, datastore, avg_read_ms, avg_write_ms, avg_latency
```
- **Implementation:** TA-vmware collects per-VM disk latency. Use datastore dimension to group VMs by backing storage. Alert when any VM-datastore pair exceeds 20ms average latency over 10 minutes. Correlate with datastore-level latency (UC-2.1.4) to distinguish VM workload from shared storage contention.
- **Visualization:** Heatmap (VMs vs datastores, colored by latency), Table (top latency by VM/datastore), Line chart (latency trend per datastore).
- **CIM Models:** N/A

---

### UC-2.1.44 · ESXi Host Certificate Renewal Compliance
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security, Availability
- **Value:** ESXi hosts use SSL certificates for vCenter communication, vMotion, and HA. Expired certificates break vCenter connectivity, prevent migrations, and cause HA communication failures. Proactive monitoring prevents unexpected outages when certs expire.
- **App/TA:** Custom scripted input (openssl, ESXi API, or PowerCLI)
- **Data Sources:** Certificate expiry from ESXi hosts (scripted input querying host API or certificate store)
- **SPL:**
```spl
index=vmware sourcetype="esxi_certificates"
| eval days_to_expiry = round((strptime(not_after, "%Y-%m-%dT%H:%M:%S") - now()) / 86400, 0)
| eval severity = case(days_to_expiry < 0, "Expired", days_to_expiry < 7, "Critical", days_to_expiry < 30, "High", days_to_expiry < 90, "Warning", 1==1, "OK")
| where days_to_expiry < 90
| sort days_to_expiry
| table host, subject, issuer, not_after, days_to_expiry, severity
```
- **Implementation:** Create scripted input: use `openssl s_client -connect <host>:443 -servername <host> 2>/dev/null | openssl x509 -noout -enddate` or PowerCLI `Get-VMHost | Get-VMHostCertificate`. Run daily. Alert at 90 days (warning), 30 days (high), 7 days (critical). Include vCenter VMCA and STS certs — their expiry affects all hosts.
- **Visualization:** Table (host, cert, days to expiry), Single value (certs expiring within 30 days), Timeline (upcoming expirations).
- **CIM Models:** N/A

---

### UC-2.1.45 · VM Snapshot Age Alerting
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity, Fault
- **Value:** Snapshots older than N days degrade VM I/O performance and complicate backups — distinct from snapshot count or space. Old snapshots cause delta disk growth, extended backup windows, and increased risk of consolidation failures. Age-based alerting ensures timely cleanup.
- **App/TA:** `Splunk_TA_vmware`
- **Data Sources:** `sourcetype=vmware:inv:vm` (snapshot info: snapshot_createTime, snapshot_name)
- **SPL:**
```spl
index=vmware sourcetype="vmware:inv:vm" snapshot_name=*
| eval snapshot_age_days = round((now() - strptime(snapshot_createTime, "%Y-%m-%dT%H:%M:%S")) / 86400, 0)
| where snapshot_age_days > 7
| eval snapshot_size_gb = round(snapshot_sizeBytes / 1073741824, 2)
| sort -snapshot_age_days
| table vm_name, host, snapshot_name, snapshot_age_days, snapshot_size_gb, snapshot_createTime
```
- **Implementation:** TA-vmware collects VM inventory including snapshot metadata. Define policy: alert on snapshots >7 days (high), >3 days (warning). Run daily report. Escalate to VM owners. Include snapshot size to prioritize cleanup. Correlate with datastore capacity for storage impact.
- **Visualization:** Table (VM, snapshot, age, size), Bar chart (snapshots by age bucket), Single value (snapshots >7 days).
- **CIM Models:** N/A

---

### UC-2.1.46 · vCenter Alarm Acknowledgment Tracking
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Operational
- **Value:** Track alarms that remain unacknowledged for extended periods. Unacknowledged alarms indicate ignored issues — either operational gaps or alarm fatigue. Ensures critical alerts receive follow-up and supports SLA tracking for incident response.
- **App/TA:** `Splunk_TA_vmware`
- **Data Sources:** `sourcetype=vmware:events` (AlarmStatusChangedEvent)
- **SPL:**
```spl
index=vmware sourcetype="vmware:events" event_type="AlarmStatusChangedEvent"
| eval alarm_id = coalesce(alarm, alarm_name)
| stats latest(_time) as last_change, latest(new_status) as status, latest(acknowledged) as ack, latest(alarm_name) as alarm_name, latest(entity) as entity by alarm_id
| where status="red" OR status="yellow"
| eval hours_unack = round((now() - last_change) / 3600, 1)
| where ack!="true" AND hours_unack > 4
| sort -hours_unack
| table alarm_name, entity, status, last_change, hours_unack, ack
```
- **Implementation:** TA-vmware collects AlarmStatusChangedEvent. Parse acknowledged field if present; otherwise infer from event sequence. Alert when red/yellow alarms remain unacknowledged >4 hours. Maintain lookup of alarm ownership for escalation. Correlate with incident tickets.
- **Visualization:** Table (unacknowledged alarms, age), Timeline (alarm state changes), Single value (count unacknowledged >4h).
- **CIM Models:** N/A

---

### UC-2.1.47 · VM Network Packet Loss and Retransmit
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance
- **Value:** Per-VM network quality metrics including packet loss and retransmission. Dropped packets at the vNIC indicate congestion, driver issues, or misconfigured traffic shaping. Hypervisor-level counters capture drops invisible to the guest — essential for diagnosing application network issues.
- **App/TA:** `Splunk_TA_vmware`
- **Data Sources:** `sourcetype=vmware:perf:net` (net.droppedRx.summation, net.droppedTx.summation)
- **SPL:**
```spl
index=vmware sourcetype="vmware:perf:net" (counter="net.droppedRx.summation" OR counter="net.droppedTx.summation" OR counter="net.packetsRx.summation" OR counter="net.packetsTx.summation")
| stats sum(eval(if(counter="net.droppedRx.summation", Value, 0))) as dropped_rx, sum(eval(if(counter="net.droppedTx.summation", Value, 0))) as dropped_tx, sum(eval(if(counter="net.packetsRx.summation", Value, 0))) as packets_rx, sum(eval(if(counter="net.packetsTx.summation", Value, 0))) as packets_tx by vm_name, host
| eval total_packets = packets_rx + packets_tx
| eval loss_pct = if(total_packets > 0, round((dropped_rx + dropped_tx) / total_packets * 100, 4), 0)
| where dropped_rx > 0 OR dropped_tx > 0
| sort -dropped_rx
| table vm_name, host, dropped_rx, dropped_tx, total_packets, loss_pct
```
- **Implementation:** TA-vmware collects net.droppedRx/Tx.summation. Alert when any VM shows >0 dropped packets sustained over 5 minutes. Compute loss percentage when packet counters available. Correlate with net.usage.average for saturation. Check dvSwitch policies, physical NIC utilization, and VMXNET3 driver version.
- **Visualization:** Table (VM, host, drops, loss %), Line chart (drops over time), Bar chart (top VMs by packet loss).
- **CIM Models:** N/A

---

### UC-2.1.48 · VMware DRS Effectiveness
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance, Capacity
- **Value:** DRS migrations per hour, cluster imbalance score, and recommendations vs. applied. High migration frequency may indicate oscillation; low application of recommendations suggests manual mode or constraint conflicts. Tracks whether DRS is effectively balancing the cluster.
- **App/TA:** `Splunk_TA_vmware`
- **Data Sources:** `sourcetype=vmware:events` (DrsVmMigratedEvent, DrsVmPoweredOnEvent, DrsRecommendationAppliedEvent)
- **SPL:**
```spl
index=vmware sourcetype="vmware:events" (event_type="DrsVmMigratedEvent" OR event_type="DrsVmPoweredOnEvent")
| eval migration_type = case(event_type="DrsVmMigratedEvent", "Migration", event_type="DrsVmPoweredOnEvent", "PowerOn")
| bin _time span=1h
| stats count as migrations by _time, cluster
| eventstats avg(migrations) as avg_migrations, stdev(migrations) as stdev_migrations by cluster
| eval is_high = if(migrations > avg_migrations + (2 * coalesce(stdev_migrations, 0)) AND migrations > 10, 1, 0)
| where is_high = 1
| table _time, cluster, migrations, avg_migrations, stdev_migrations
```
- **Implementation:** Collect DRS events via TA-vmware. Baseline migrations per hour per cluster. Alert when migrations exceed 2 stdev above mean (possible oscillation). For recommendations: query DrsRecommendationAppliedEvent vs. total recommendations. Manual DRS mode will show recommendations without corresponding applied events.
- **Visualization:** Line chart (migrations per hour by cluster), Table (cluster, migrations, baseline), Bar chart (recommendations vs applied).
- **CIM Models:** N/A

---

## 2.2 Microsoft Hyper-V

**Primary App/TA:** Splunk Add-on for Microsoft Hyper-V, `Splunk_TA_windows` — Free on Splunkbase

---

### UC-2.2.1 · VM Performance Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Per-VM CPU, memory, and disk metrics identify resource contention and performance bottlenecks within the Hyper-V environment.
- **App/TA:** `Splunk_TA_windows` (Perfmon inputs for Hyper-V counters)
- **Data Sources:** `sourcetype=Perfmon:HyperV` (Hyper-V Virtual Machine Health Summary, Hyper-V Hypervisor Logical Processor)
- **SPL:**
```spl
index=perfmon sourcetype="Perfmon:HyperV" object="Hyper-V Hypervisor Virtual Processor" counter="% Guest Run Time"
| stats avg(Value) as avg_cpu by instance, host
| sort -avg_cpu
```
- **Implementation:** Configure Perfmon inputs on Hyper-V hosts for Hyper-V specific objects: `Hyper-V Hypervisor Virtual Processor`, `Hyper-V Dynamic Memory - VM`, `Hyper-V Virtual Storage Device`. Set interval=60.
- **Visualization:** Table (VM, CPU%, Memory%), Line chart per VM, Heatmap.
- **CIM Models:** Performance
- **CIM SPL:**
```spl
| tstats `summariesonly` avg(Performance.cpu_load_percent) as avg_cpu
  from datamodel=Performance where nodename=Performance.CPU
  by Performance.host span=1h
| where avg_cpu > 90
```

---

### UC-2.2.2 · Hyper-V Replication Health
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Replication lag means your DR site is behind. If replication breaks, you lose your recovery point objective (RPO).
- **App/TA:** `Splunk_TA_windows` (Hyper-V)
- **Data Sources:** `sourcetype=WinEventLog:Microsoft-Windows-Hyper-V-VMMS-Admin`
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:Microsoft-Windows-Hyper-V-VMMS-Admin" ("replication" AND ("error" OR "warning" OR "critical" OR "failed"))
| stats count by host, EventCode, Message
| sort -count
```
- **Implementation:** Enable Hyper-V VMMS event log collection. Also create a PowerShell scripted input: `Get-VMReplication | Select VMName, State, Health, LastReplicationTime`. Alert on replication state != Normal or health != Normal.
- **Visualization:** Table (VM, replication state, health, last sync), Status indicators, Events list.
- **CIM Models:** N/A

---

### UC-2.2.3 · Cluster Shared Volume Health
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Fault
- **Value:** CSV issues can cause VM storage access failures across the entire cluster. Redirected I/O mode significantly degrades performance.
- **App/TA:** `Splunk_TA_windows` (Hyper-V)
- **Data Sources:** `sourcetype=WinEventLog:Microsoft-Windows-FailoverClustering/Operational`
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:Microsoft-Windows-FailoverClustering/Operational" ("CSV" OR "Cluster Shared Volume") ("error" OR "redirected" OR "failed")
| table _time host Message
| sort -_time
```
- **Implementation:** Enable Failover Clustering operational log. Alert on CSV ownership changes, redirected I/O mode, and disk health issues. Monitor Perfmon counters for CSV latency.
- **Visualization:** Status panel per CSV, Events timeline, Table.
- **CIM Models:** N/A

---

### UC-2.2.4 · Live Migration Tracking
- **Criticality:** 🟢 Low
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Configuration
- **Value:** Audit trail for VM mobility. Excessive live migrations may indicate cluster imbalance or storage issues.
- **App/TA:** `Splunk_TA_windows` (Hyper-V)
- **Data Sources:** `sourcetype=WinEventLog:Microsoft-Windows-Hyper-V-VMMS-Admin`
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:Microsoft-Windows-Hyper-V-VMMS-Admin" "migration" ("completed" OR "started")
| rex "Virtual machine '(?<vm_name>[^']+)'"
| table _time host vm_name Message
| sort -_time
```
- **Implementation:** Collected via standard Hyper-V event log monitoring. Create an audit report. Alert on migration failures or excessive frequency.
- **Visualization:** Table (timeline), Count by host/day.
- **CIM Models:** N/A

---

### UC-2.2.5 · Integration Services Version
- **Criticality:** 🟢 Low
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Value:** Outdated integration services cause performance issues and prevent features like time sync, heartbeat, and data exchange from working correctly.
- **App/TA:** `Splunk_TA_windows` (Hyper-V), custom scripted input
- **Data Sources:** PowerShell scripted input (`Get-VMIntegrationService`)
- **SPL:**
```spl
index=hyperv sourcetype=integration_services
| stats latest(version) as ic_version by vm_name, host
| where ic_version != "latest"
```
- **Implementation:** Replace `"latest"` in the SPL with the actual expected integration services version. Create a PowerShell scripted input on Hyper-V hosts: `Get-VM | Get-VMIntegrationService | Select VMName, Name, Enabled, PrimaryOperationalStatus`. Run daily.
- **Visualization:** Table (VM, version, status), Pie chart (current vs. outdated).
- **CIM Models:** N/A

---

### UC-2.2.6 · Hyper-V Host Resource Utilization
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Host-level CPU and memory utilization across all VMs determines capacity headroom. Unlike per-VM monitoring, host-level metrics reveal when the hypervisor itself is under pressure — affecting all VMs simultaneously. Tracks the root partition overhead which is invisible from within VMs.
- **App/TA:** `Splunk_TA_windows` (Hyper-V Perfmon inputs)
- **Data Sources:** `sourcetype=Perfmon:HyperV` (Hyper-V Hypervisor Logical Processor, Memory counters)
- **SPL:**
```spl
index=perfmon sourcetype="Perfmon:HyperV" object="Hyper-V Hypervisor Logical Processor" instance="_Total" counter="% Total Run Time"
| bin _time span=5m
| stats avg(Value) as avg_cpu by host, _time
| where avg_cpu > 85
| table _time, host, avg_cpu
```
- **Implementation:** Configure Perfmon inputs for `Hyper-V Hypervisor Logical Processor` (% Total Run Time, % Hypervisor Run Time) and `Memory` (Available MBytes, Committed Bytes). Set interval=60. Alert when host CPU exceeds 85% or available memory drops below 10% of physical. Track root partition overhead separately.
- **Visualization:** Line chart (CPU/memory over time per host), Gauge (current utilization), Heatmap (hosts by load).
- **CIM Models:** Performance
- **CIM SPL:**
```spl
| tstats `summariesonly` avg(Performance.cpu_load_percent) as avg_cpu
  from datamodel=Performance where nodename=Performance.CPU
  by Performance.host span=1h
| where avg_cpu > 85
```

---

### UC-2.2.7 · Dynamic Memory Pressure and Effectiveness
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Dynamic Memory allows Hyper-V to adjust VM memory allocations based on demand. When memory pressure is high, the host reduces VM allocations below their startup RAM — causing in-guest paging. Monitoring reveals whether Dynamic Memory is helping or hurting, and which VMs are being starved.
- **App/TA:** `Splunk_TA_windows` (Hyper-V Perfmon inputs)
- **Data Sources:** `sourcetype=Perfmon:HyperV` (Hyper-V Dynamic Memory - VM)
- **SPL:**
```spl
index=perfmon sourcetype="Perfmon:HyperV" object="Hyper-V Dynamic Memory - VM" (counter="Current Pressure" OR counter="Average Pressure" OR counter="Guest Visible Physical Memory")
| stats avg(eval(if(counter="Current Pressure", Value, null()))) as pressure, avg(eval(if(counter="Guest Visible Physical Memory", Value, null()))) as visible_mb by instance, host
| where pressure > 100
| sort -pressure
| table instance, host, pressure, visible_mb
```
- **Implementation:** Configure Perfmon inputs for `Hyper-V Dynamic Memory - VM` counters. Pressure >100 means the VM wants more memory than it has. Track over time — sustained pressure >80 indicates the VM needs a higher minimum RAM setting. Alert when pressure exceeds 100 for production VMs.
- **Visualization:** Line chart (pressure over time per VM), Table (VMs under pressure), Gauge (average pressure).
- **CIM Models:** N/A

---

### UC-2.2.8 · Checkpoint Age and Sprawl
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Capacity
- **Value:** Hyper-V checkpoints (snapshots) accumulate AVHDX differencing disks that grow over time and degrade I/O performance. Old checkpoints complicate backup and recovery, consume unexpected storage, and cause merge storms when finally deleted. Production checkpoints are safer but still grow.
- **App/TA:** `Splunk_TA_windows` (Hyper-V), custom scripted input
- **Data Sources:** PowerShell scripted input (`Get-VMCheckpoint`)
- **SPL:**
```spl
index=hyperv sourcetype="hyperv_checkpoints"
| eval age_days=round((now() - strptime(creation_time, "%Y-%m-%dT%H:%M:%S")) / 86400, 0)
| where age_days > 3
| sort -age_days
| table vm_name, host, checkpoint_name, age_days, size_gb, checkpoint_type
```
- **Implementation:** Create scripted input: `Get-VM | Get-VMCheckpoint | Select VMName, Name, CreationTime, CheckpointType, @{N='SizeGB';E={[math]::Round((Get-VHD $_.HardDrives.Path).FileSize/1GB,2)}}`. Run daily. Alert on checkpoints >3 days old. Distinguish production checkpoints (application-consistent) from standard (crash-consistent).
- **Visualization:** Table (VM, checkpoint, age, size), Bar chart (checkpoints by age bucket), Single value (total checkpoint count).
- **CIM Models:** N/A

---

### UC-2.2.9 · Virtual Switch Dropped Packets and Network Errors
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Virtual switch dropped packets indicate congestion, misconfigured VLAN tagging, or bandwidth management policy throttling. Hyper-V Extensible Switch drops are invisible from within the VM, making hypervisor-level monitoring the only way to detect them.
- **App/TA:** `Splunk_TA_windows` (Hyper-V Perfmon inputs)
- **Data Sources:** `sourcetype=Perfmon:HyperV` (Hyper-V Virtual Switch, Hyper-V Virtual Network Adapter)
- **SPL:**
```spl
index=perfmon sourcetype="Perfmon:HyperV" object="Hyper-V Virtual Network Adapter" (counter="Dropped Packets Incoming" OR counter="Dropped Packets Outgoing")
| stats sum(Value) as total_drops by instance, host, counter
| where total_drops > 0
| sort -total_drops
| table instance, host, counter, total_drops
```
- **Implementation:** Configure Perfmon inputs for `Hyper-V Virtual Network Adapter` (Dropped Packets Incoming/Outgoing, Packets Received/Sent Errors) and `Hyper-V Virtual Switch` (Dropped Packets/sec). Alert when any adapter shows >0 dropped packets sustained over 5 minutes. Correlate with bandwidth usage to distinguish congestion from misconfiguration.
- **Visualization:** Table (adapter, host, drops), Line chart (drops over time), Bar chart (top adapters by drops).
- **CIM Models:** N/A

---

### UC-2.2.10 · Failover Cluster Node Health and Quorum
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Hyper-V failover clusters require quorum to operate. A node leaving the cluster reduces fault tolerance and can trigger mass VM failover. Quorum loss means the entire cluster stops, downing all VMs. Monitoring node health and quorum status prevents catastrophic cluster outages.
- **App/TA:** `Splunk_TA_windows` (Hyper-V)
- **Data Sources:** `sourcetype=WinEventLog:Microsoft-Windows-FailoverClustering/Operational`
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:Microsoft-Windows-FailoverClustering/Operational" (EventCode=1069 OR EventCode=1177 OR EventCode=1135 OR EventCode=1564 OR EventCode=1566)
| eval severity=case(EventCode=1135, "Node Down", EventCode=1177, "Quorum Lost", EventCode=1069, "Resource Failed", EventCode=1564, "Quorum Degraded", EventCode=1566, "Quorum Restored")
| table _time, host, EventCode, severity, Message
| sort -_time
```
- **Implementation:** Collect Failover Clustering operational event log. Key EventCodes: 1135 (node removed), 1177 (quorum lost), 1069 (cluster resource failed), 1564 (quorum degraded). Alert immediately on quorum events. Also create a PowerShell scripted input: `Get-ClusterNode | Select Name, State, StatusInformation`. Run every 60 seconds.
- **Visualization:** Status grid (node health), Events timeline, Single value (active nodes / total nodes), Alert panel.
- **CIM Models:** N/A

---

### UC-2.2.11 · Storage Spaces Direct (S2D) Health
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability, Performance
- **Value:** Storage Spaces Direct pools local storage across cluster nodes into a shared storage fabric. Disk failures, network partitions, or capacity exhaustion degrade the storage pool, risking data loss. S2D self-heals by rebuilding data on remaining disks, consuming significant I/O during repair.
- **App/TA:** `Splunk_TA_windows` (Hyper-V), custom scripted input
- **Data Sources:** PowerShell scripted input (`Get-StorageSubsystem`, `Get-PhysicalDisk`, `Get-StoragePool`)
- **SPL:**
```spl
index=hyperv sourcetype="s2d_health"
| stats latest(pool_health) as health, latest(pool_operational_status) as op_status, latest(capacity_pct) as capacity by pool_name, host
| where health!="Healthy" OR capacity > 80
| sort -capacity
| table pool_name, host, health, op_status, capacity
```
- **Implementation:** Create scripted inputs: `Get-StoragePool | Select FriendlyName, HealthStatus, OperationalStatus, Size, AllocatedSize` and `Get-PhysicalDisk | Select FriendlyName, HealthStatus, OperationalStatus, MediaType, Size, CanPool`. Run every 5 minutes. Alert on any non-Healthy status or capacity >80%.
- **Visualization:** Status grid (pool health), Table (disk status), Gauge (capacity utilization), Events (repair operations).
- **CIM Models:** N/A

---

### UC-2.2.12 · VM Generation and Secure Boot Compliance
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Compliance, Security
- **Value:** Generation 1 VMs use legacy BIOS and cannot support Secure Boot, vTPM, or UEFI features required by modern security policies. Generation 2 VMs with Secure Boot enabled prevent rootkits and bootkits from loading unauthorized firmware or OS loaders.
- **App/TA:** `Splunk_TA_windows` (Hyper-V), custom scripted input
- **Data Sources:** PowerShell scripted input (`Get-VM`)
- **SPL:**
```spl
index=hyperv sourcetype="hyperv_vm_config"
| stats latest(generation) as gen, latest(secure_boot) as secure_boot by vm_name, host
| eval compliant=if(gen=2 AND secure_boot="On", "Yes", "No")
| where compliant="No"
| table vm_name, host, gen, secure_boot, compliant
| sort gen
```
- **Implementation:** Create scripted input: `Get-VM | Select Name, Generation, @{N='SecureBoot';E={(Get-VMFirmware $_).SecureBoot}}`. Run daily. Define compliance policy — all new VMs should be Gen 2 with Secure Boot enabled. Generate weekly compliance reports. Note: Gen 1 → Gen 2 migration requires VM rebuild.
- **Visualization:** Pie chart (Gen 1 vs Gen 2), Table (non-compliant VMs), Bar chart (by host).
- **CIM Models:** N/A

---

### UC-2.2.13 · Hyper-V Event Log Error Trending
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Anomaly
- **Value:** Trending Hyper-V event log errors reveals emerging hardware issues, driver problems, and configuration drift. A sudden increase in VMMS, VMWP, or VID errors often precedes VM failures. Baseline comparison distinguishes noise from genuine problems.
- **App/TA:** `Splunk_TA_windows` (Hyper-V)
- **Data Sources:** `sourcetype=WinEventLog:Microsoft-Windows-Hyper-V-*`
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:Microsoft-Windows-Hyper-V-*" Type="Error"
| bin _time span=1h
| stats count by _time, host, sourcetype
| eventstats avg(count) as avg_errors, stdev(count) as stdev_errors by host, sourcetype
| eval upper=avg_errors + (2*stdev_errors)
| where count > upper AND count > 5
| table _time, host, sourcetype, count, avg_errors, upper
```
- **Implementation:** Collect all Hyper-V event log channels (VMMS-Admin, Worker-Admin, VID-Admin, Hypervisor-Admin). Baseline error rates over 30 days per host. Alert when error count exceeds 2 standard deviations above the mean. Investigate by drilling into specific EventCodes.
- **Visualization:** Line chart (errors over time), Table (anomalous periods), Bar chart (error types).
- **CIM Models:** N/A

---

### UC-2.2.14 · VM Resource Metering for Chargeback
- **Criticality:** 🟢 Low
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Hyper-V's built-in resource metering tracks per-VM CPU, memory, disk, and network consumption for chargeback and showback. Without metering data, cost allocation is based on allocation rather than actual usage — leading to disputes and over-provisioning.
- **App/TA:** `Splunk_TA_windows` (Hyper-V), custom scripted input
- **Data Sources:** PowerShell scripted input (`Measure-VM`)
- **SPL:**
```spl
index=hyperv sourcetype="hyperv_metering"
| bin _time span=1d
| stats avg(avg_cpu_mhz) as avg_cpu, avg(avg_memory_mb) as avg_mem, sum(disk_bytes_read) as disk_read, sum(disk_bytes_written) as disk_write, sum(network_bytes_in) as net_in, sum(network_bytes_out) as net_out by vm_name, host, _time
| eval disk_total_gb=round((disk_read+disk_write)/1073741824, 2)
| eval net_total_gb=round((net_in+net_out)/1073741824, 2)
| table _time, vm_name, host, avg_cpu, avg_mem, disk_total_gb, net_total_gb
```
- **Implementation:** Enable resource metering: `Enable-VMResourceMetering -VMName *`. Create scripted input: `Measure-VM | Select VMName, AvgCPU, AvgRAM, TotalDisk*, AggregatedAverageNormalizedIOPS, AggregatedDiskDataRead, AggregatedDiskDataWritten, NetworkMeteredTrafficReport`. Run hourly. Maintain cost-per-unit lookups for chargeback calculations.
- **Visualization:** Table (VM, resource usage, estimated cost), Bar chart (cost by department), Timechart (usage trending).
- **CIM Models:** N/A

---


### UC-2.2.15 · Hyper-V VM State Changes
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Unexpected VM power state changes (shutdowns, paused, critical saves) indicate host issues, resource contention, or unauthorized administrative actions.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:Microsoft-Windows-Hyper-V-VMMS-Admin` (EventCode 12320, 12322, 12324, 18304)
- **SPL:**
```spl
index=wineventlog source="WinEventLog:Microsoft-Windows-Hyper-V-VMMS*"
  EventCode IN (12320, 12322, 12324, 18304, 18310, 18312)
| eval action=case(EventCode=12320,"VM started",EventCode=12322,"VM stopped",EventCode=12324,"VM saved",EventCode=18304,"VM critical",EventCode=18310,"VM paused",EventCode=18312,"VM resumed")
| table _time, host, action, VmName, VmId
| sort -_time
```
- **Implementation:** Forward Hyper-V VMMS Admin logs from all Hyper-V hosts. EventCode 18304=VM entered critical state (memory pressure, lost storage), 18310=VM paused (out of disk, integration services failure). Alert on any critical state transitions. Track unexpected shutdowns (12322 without preceding 12320 by admin). Correlate with host-level resource monitoring to identify the root cause.
- **Visualization:** Timeline (VM state changes), Status grid (VM × state), Table (critical events), Single value (VMs in critical state).
- **CIM Models:** Change
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  by All_Changes.user All_Changes.object_category All_Changes.action span=1h
| sort -count
```

---

## 2.3 KVM / Proxmox / oVirt

**Primary App/TA:** Custom inputs via libvirt API, syslog

---

### UC-2.3.1 · Guest VM Resource Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Per-VM resource tracking for capacity planning and performance troubleshooting in KVM environments.
- **App/TA:** Custom scripted input (`virsh domstats`)
- **Data Sources:** Custom sourcetype from `virsh domstats` or `virt-top`
- **SPL:**
```spl
index=virtualization sourcetype=virsh_stats
| stats latest(cpu_pct) as cpu, latest(mem_used_mb) as memory by vm_name, host
| sort -cpu
```
- **Implementation:** Create scripted input: `virsh domstats --cpu-total --balloon --interface --block`. Run every 60 seconds. Parse per-VM CPU time, balloon current, block read/write, and net rx/tx.
- **Visualization:** Table, Line chart per VM, Heatmap.
- **CIM Models:** N/A

---

### UC-2.3.2 · Host Overcommit Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Capacity
- **Value:** Overcommitted KVM hosts cause all VMs to compete for resources. Unlike VMware, KVM doesn't have sophisticated DRS — manual balancing is needed.
- **App/TA:** Custom scripted input
- **Data Sources:** Custom sourcetype (`virsh nodeinfo` + `virsh list --all`)
- **SPL:**
```spl
index=virtualization sourcetype=kvm_capacity
| stats sum(vm_vcpus) as total_vcpus, sum(vm_memory_mb) as total_vm_mem, latest(host_cpus) as host_cpus, latest(host_memory_mb) as host_mem by host
| eval cpu_overcommit = round(total_vcpus / host_cpus, 2)
| eval mem_overcommit = round(total_vm_mem / host_mem, 2)
| where cpu_overcommit > 3 OR mem_overcommit > 1.2
```
- **Implementation:** Create scripted input combining `virsh nodeinfo` (host resources) with `virsh dominfo <vm>` for each VM. Calculate aggregate allocation vs. physical capacity. Alert when memory overcommit >1.2x or CPU >4x.
- **Visualization:** Table (host, allocated vs. physical), Gauge per host.
- **CIM Models:** N/A

---

### UC-2.3.3 · VM Lifecycle Events
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Configuration
- **Value:** Audit trail for VM start, stop, migrate, and crash events. Essential for troubleshooting and change management in open-source virtualization.
- **App/TA:** Syslog, libvirt logs
- **Data Sources:** `/var/log/libvirt/`, syslog
- **SPL:**
```spl
index=virtualization sourcetype=syslog source="/var/log/libvirt/*"
| search "shutting down" OR "starting up" OR "migrating" OR "crashed"
| rex "domain (?<vm_name>\S+)"
| table _time host vm_name _raw
| sort -_time
```
- **Implementation:** Forward `/var/log/libvirt/qemu/*.log` and libvirt system logs. Parse VM name and event type. Alert on unexpected VM shutdowns or crashes.
- **Visualization:** Events timeline, Table (VM, event, time).
- **CIM Models:** N/A

---

### UC-2.3.4 · KVM Guest Agent Heartbeat
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Guest agent (QEMU GA) unavailability prevents graceful shutdown, snapshot consistency, and time sync. Detecting agent loss ensures proper VM management.
- **App/TA:** Custom scripted input (virsh qemu-agent-command)
- **Data Sources:** `virsh qemu-agent-command <vm> '{"execute":"guest-ping"}'`
- **SPL:**
```spl
index=virtualization sourcetype=kvm_guest_agent host=*
| stats latest(agent_ok) as ok by host, vm_name
| where ok != 1
| table host vm_name _time
```
- **Implementation:** Script that iterates VMs and runs `virsh qemu-agent-command <domain> '{"execute":"guest-ping"}'`. Ingest result (0/1) per VM. Run every 60 seconds. Alert when agent stops responding.
- **Visualization:** Status grid (VM vs. agent OK), Table of VMs with no agent.
- **CIM Models:** N/A

---

### UC-2.3.5 · Libvirt Network Filter and Firewall Rule Audit
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Configuration, Security
- **Value:** VM-level firewall and filter rules can be changed accidentally or maliciously. Auditing ensures network isolation and compliance.
- **App/TA:** Custom scripted input (`virsh nwfilter-list`, `virsh dumpxml`)
- **Data Sources:** Libvirt XML dump, nwfilter definitions
- **SPL:**
```spl
index=virtualization sourcetype=libvirt_nwfilter host=*
| stats latest(rule_hash) as current by host, vm_name, filter_name
| inputlookup expected_nwfilter append=t
| eval drift=if(current!=expected_hash, "Yes", "No")
| where drift="Yes"
| table host vm_name filter_name
```
- **Implementation:** Periodically dump VM network filter config and compute hash. Compare to baseline lookup. Alert on change. Run after change windows or daily.
- **Visualization:** Table (host, VM, filter, drift), Compliance count.
- **CIM Models:** N/A

---

### UC-2.3.6 · Virtual Disk Backing Chain and Snapshot Age
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity, Fault
- **Value:** Long snapshot chains and old snapshots degrade I/O and complicate recovery. Monitoring supports snapshot hygiene and prevents runaway growth.
- **App/TA:** Custom scripted input (`virsh domblkinfo`, `qemu-img info`)
- **Data Sources:** Libvirt/QEMU disk info
- **SPL:**
```spl
index=virtualization sourcetype=kvm_disk_chain host=*
| stats latest(chain_depth) as depth, latest(oldest_snapshot_days) as snapshot_days by host, vm_name, disk
| where depth > 3 OR snapshot_days > 30
| table host vm_name disk depth snapshot_days
| sort -snapshot_days
```
- **Implementation:** Script to list VM disks and snapshot chains (e.g. `virsh snapshot-list`, `qemu-img info`). Compute chain depth and oldest snapshot age. Alert when depth >3 or oldest snapshot >30 days.
- **Visualization:** Table (VM, disk, depth, oldest snapshot), Bar chart of snapshot age.
- **CIM Models:** N/A

---

### UC-2.3.7 · KVM Host CPU Model and Migration Compatibility
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Configuration
- **Value:** Live migration fails or degrades when host CPU models differ. Tracking CPU compatibility avoids failed migrations and performance surprises.
- **App/TA:** Custom scripted input (`virsh capabilities`, `virsh dominfo`)
- **Data Sources:** Libvirt capabilities XML, VM CPU config
- **SPL:**
```spl
index=virtualization sourcetype=kvm_cpu_compat host=*
| stats latest(host_cpu_model) as host_model, values(vm_cpu_model) as vm_models by host
| eval compatible=if(match(vm_models, host_model), "Yes", "No")
| where compatible="No"
| table host host_model vm_models
```
- **Implementation:** Extract host CPU model from `virsh capabilities` and per-VM CPU from `virsh dumpxml`. Compare for migration compatibility. Document and alert when VMs use incompatible CPU.
- **Visualization:** Table (host, VM, CPU model, compatible), Migration readiness matrix.
- **CIM Models:** N/A

---

### UC-2.3.8 · Virtio Driver and Balloon Status in Guests
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Virtio drivers and balloon driver improve I/O and allow memory reclamation. Missing or inactive drivers cause poor performance and overcommit issues.
- **App/TA:** Custom scripted input (guest agent or in-guest script)
- **Data Sources:** QEMU guest agent, `virsh dommemstat`
- **SPL:**
```spl
index=virtualization sourcetype=kvm_balloon host=*
| stats latest(balloon_current_kb) as balloon_kb, latest(balloon_max_kb) as max_kb by host, vm_name
| eval balloon_ratio=round(balloon_kb/max_kb*100, 1)
| where balloon_ratio > 50
| table host vm_name balloon_kb max_kb balloon_ratio
```
- **Implementation:** Use `virsh dommemstat` to get balloon current and maximum. High ratio indicates host is reclaiming memory from the VM. Alert when ratio >50% for critical VMs.
- **Visualization:** Table (VM, balloon KB, ratio), Line chart (balloon over time).
- **CIM Models:** N/A

---

### UC-2.3.9 · QEMU Process Crash and Zombie Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Each KVM VM runs as a qemu-kvm process on the host. If the process crashes, the VM dies instantly without graceful shutdown. Zombie qemu processes consume resources without running a VM. Detecting crashes enables rapid restart, while zombie detection prevents resource leaks.
- **App/TA:** `Splunk_TA_nix`, custom scripted input
- **Data Sources:** Syslog, libvirt logs, process monitoring
- **SPL:**
```spl
index=os sourcetype=syslog ("qemu-kvm" AND ("killed" OR "segfault" OR "core dumped" OR "terminated"))
| rex "qemu-kvm\[(?<pid>\d+)\]"
| table _time, host, pid, _raw
| sort -_time
```
- **Implementation:** Monitor syslog and `/var/log/libvirt/qemu/*.log` for qemu-kvm crash messages. Create a scripted input to detect zombie processes: `ps aux | grep qemu-kvm | grep -v grep | awk '{if($8=="Z") print}'`. Alert immediately on crash events. Cross-reference with libvirt domain list to detect processes without corresponding VMs.
- **Visualization:** Timeline (crash events), Table (crashed VMs), Single value (active zombies).
- **CIM Models:** N/A

---

### UC-2.3.10 · Storage Pool Capacity Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Capacity
- **Value:** Libvirt storage pools (LVM, directory, NFS, Ceph, ZFS) provide disk backing for VMs. A full storage pool prevents new VM creation, snapshot operations, and can cause running VMs to pause when using thin provisioning. Monitoring pool capacity prevents VM outages.
- **App/TA:** Custom scripted input
- **Data Sources:** `virsh pool-info`, storage pool metrics
- **SPL:**
```spl
index=virtualization sourcetype=kvm_storage_pools
| eval used_pct=round(used_gb/capacity_gb*100, 1)
| where used_pct > 80
| sort -used_pct
| table host, pool_name, pool_type, capacity_gb, used_gb, used_pct
```
- **Implementation:** Create scripted input: `for pool in $(virsh pool-list --name); do virsh pool-info $pool; done`. Parse capacity, allocation, and available fields. Run every 5 minutes. Alert at 80% (warning) and 90% (critical). Include pool type in output — LVM pools cannot auto-extend, while directory pools grow with the filesystem.
- **Visualization:** Gauge (per pool), Table (pool status), Line chart (capacity trend with prediction).
- **CIM Models:** N/A

---

### UC-2.3.11 · Proxmox Backup Server Job Status
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Proxmox Backup Server (PBS) provides incremental, deduplicated VM backups. Failed backup jobs mean VMs have no recovery point. Monitoring backup status, duration, and deduplication ratio ensures recoverability and optimizes storage efficiency.
- **App/TA:** Custom API input, Proxmox syslog
- **Data Sources:** Proxmox Backup Server API, `/var/log/proxmox-backup/tasks/`
- **SPL:**
```spl
index=virtualization sourcetype="proxmox_backup"
| eval duration_min=round(duration_sec/60, 1)
| eval status_ok=if(status="OK", 1, 0)
| stats latest(status) as last_status, latest(duration_min) as last_duration_min, latest(backup_size_gb) as size_gb, latest(dedup_ratio) as dedup by vm_name, backup_type
| where last_status!="OK"
| table vm_name, backup_type, last_status, last_duration_min, size_gb, dedup
```
- **Implementation:** Poll the PBS API (`/api2/json/nodes/{node}/tasks`) or forward PBS task logs to Splunk. Track backup success/failure per VM, backup duration, transferred size, and deduplication factor. Alert on any failed backup. Also alert when no backup has been taken for a VM in >24 hours. Monitor datastore capacity on PBS.
- **Visualization:** Table (VM, status, duration, size), Bar chart (backup success rate), Timechart (backup duration trending).
- **CIM Models:** N/A

---

### UC-2.3.12 · Proxmox Cluster Corosync and Quorum Health
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Proxmox clusters use Corosync for node communication and quorum. A split-brain scenario can cause data corruption on shared storage. Nodes losing corosync connectivity cannot access cluster resources, and quorum loss stops all HA-protected VMs. Early detection of communication issues prevents cluster-wide outages.
- **App/TA:** Custom scripted input, syslog
- **Data Sources:** Corosync logs, `pvecm status`, Proxmox cluster API
- **SPL:**
```spl
index=virtualization sourcetype="proxmox_cluster"
| stats latest(quorate) as quorum, latest(total_nodes) as total, latest(online_nodes) as online by cluster_name
| eval quorum_ok=if(quorum="Yes", "OK", "CRITICAL")
| eval nodes_ok=if(online=total, "All Online", online . "/" . total . " Online")
| table cluster_name, quorum_ok, nodes_ok, total, online
```
- **Implementation:** Create scripted input: `pvecm status` to get quorum state, node count, and ring status. Also monitor Corosync syslog for retransmit failures and membership changes. Alert immediately on quorum loss. Alert when any node goes offline. Monitor Corosync ring latency — high latency indicates network issues between nodes.
- **Visualization:** Status grid (node health), Single value (quorum status), Timeline (membership changes).
- **CIM Models:** N/A

---

### UC-2.3.13 · Proxmox HA Group and Fence Status
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Proxmox HA automatically restarts VMs on surviving nodes when a host fails. If the HA manager cannot fence (isolate) a failed node, it cannot safely restart VMs — risking split-brain with shared storage. Monitoring HA state, fence status, and migration events ensures the safety net actually works.
- **App/TA:** Custom scripted input, syslog
- **Data Sources:** Proxmox HA manager logs, `ha-manager status`
- **SPL:**
```spl
index=virtualization sourcetype="proxmox_ha"
| stats latest(ha_state) as state, latest(node) as current_node, latest(request_state) as requested by vm_id, vm_name
| where state!="started" OR state!=requested
| table vm_id, vm_name, state, requested, current_node
```
- **Implementation:** Create scripted input: `ha-manager status` to enumerate all HA-managed resources and their states. Monitor HA manager log (`/var/log/pve/ha-manager/`) for fence operations and migration events. Alert on failed fencing (node isolation), VMs in error state, and HA resources that cannot reach their requested state.
- **Visualization:** Table (HA resources, state, node), Timeline (HA events), Status grid (resource health).
- **CIM Models:** N/A

---

### UC-2.3.14 · ZFS Pool Health for Proxmox/KVM
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability, Capacity
- **Value:** ZFS is the recommended storage backend for Proxmox and many KVM deployments. A degraded ZFS pool means a disk has failed and data is at risk until the pool is resilvered. ZFS capacity above 80% significantly degrades performance due to copy-on-write fragmentation.
- **App/TA:** `Splunk_TA_nix`, custom scripted input
- **Data Sources:** `zpool status`, `zpool list`, ZFS event daemon (ZED)
- **SPL:**
```spl
index=os sourcetype="zfs_pool_status"
| stats latest(health) as health, latest(capacity_pct) as capacity, latest(fragmentation) as frag_pct by host, pool_name
| where health!="ONLINE" OR capacity > 80
| sort -capacity
| table host, pool_name, health, capacity, frag_pct
```
- **Implementation:** Create scripted input: `zpool list -Hp` for capacity and `zpool status` for health. Parse pool name, size, allocated, free, fragmentation, capacity, dedup ratio, and health. Run every 5 minutes. Alert on any non-ONLINE health status. Alert at 80% capacity. Monitor ZFS Event Daemon (ZED) for disk failures and scrub errors.
- **Visualization:** Status grid (pool health), Gauge (capacity per pool), Table (pool details), Line chart (capacity trend).
- **CIM Models:** N/A

---

### UC-2.3.15 · VM Disk Cache Mode Audit
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Configuration, Security
- **Value:** The disk cache mode determines data safety vs. performance. `writeback` is fast but risks data loss on host crash. `none` (O_DIRECT) provides safe passthrough for guests with their own journaling. `writethrough` is safest but slowest. Incorrect cache modes cause either data loss or unnecessary performance penalties.
- **App/TA:** Custom scripted input
- **Data Sources:** `virsh dumpxml` disk configuration
- **SPL:**
```spl
index=virtualization sourcetype="kvm_disk_config"
| stats latest(cache_mode) as cache, latest(io_mode) as io, latest(discard) as discard by host, vm_name, disk_target
| eval risk=case(cache="writeback", "High - data loss risk on crash", cache="unsafe", "Critical - no fsync", cache="none", "Safe - direct I/O", cache="writethrough", "Safe - slow", 1==1, "Unknown")
| where cache="writeback" OR cache="unsafe"
| table host, vm_name, disk_target, cache, io, risk
```
- **Implementation:** Create scripted input: parse `virsh dumpxml <domain>` to extract `<driver cache='...' io='...' discard='...'/>` for each disk. Run daily. Alert on `cache='unsafe'` (never safe for production). Flag `cache='writeback'` for review — acceptable only if the host has battery-backed write cache. Recommend `cache='none'` for most production workloads.
- **Visualization:** Table (VM, disk, cache mode, risk), Pie chart (cache mode distribution), Bar chart (risky VMs by host).
- **CIM Models:** N/A

---

### UC-2.3.16 · Libvirt Daemon Health and Responsiveness
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** The libvirtd daemon is the management layer for all KVM operations — VM start/stop, migration, storage, networking. If libvirtd hangs or crashes, no VM management operations are possible. Existing VMs keep running but become unmanageable. Detecting libvirtd health issues enables proactive restart before they cascade.
- **App/TA:** `Splunk_TA_nix`, custom scripted input
- **Data Sources:** Syslog, systemd service status, libvirtd response time
- **SPL:**
```spl
index=os sourcetype=syslog "libvirtd" ("error" OR "warning" OR "failed" OR "timed out")
| stats count as errors by host, _time span=5m
| where errors > 5
| table _time, host, errors
```
- **Implementation:** Monitor libvirtd syslog output for errors. Create a scripted input that runs `virsh list` and measures response time — if it takes >5 seconds, libvirtd is likely overloaded. Also monitor the systemd service status: `systemctl is-active libvirtd`. Alert if libvirtd is not active or response time exceeds 10 seconds.
- **Visualization:** Status indicator (libvirtd per host), Line chart (response time), Events table (errors).
- **CIM Models:** N/A

---

### UC-2.3.17 · Proxmox VE Cluster Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability, Performance
- **Value:** Node status, storage usage, and HA fence events for Proxmox VE clusters. Ensures all nodes are online, storage is healthy, and HA operations complete successfully. Critical for multi-node Proxmox deployments.
- **App/TA:** Custom (Proxmox API input)
- **Data Sources:** Proxmox REST API (`/api2/json/cluster/status`), cluster resources, HA manager
- **SPL:**
```spl
index=virtualization sourcetype="proxmox_cluster_status"
| stats latest(node) as node, latest(status) as status, latest(quorum) as quorum, latest(name) as cluster_name by node
| eval node_ok = if(status="online", "OK", "CRITICAL")
| where node_ok="CRITICAL" OR quorum!="1"
| table cluster_name, node, status, quorum, node_ok
```
- **Implementation:** Create scripted input polling Proxmox API: `GET /api2/json/cluster/status` for node membership and quorum; `GET /api2/json/nodes/{node}/storage` for storage usage; `GET /api2/json/cluster/ha/status` for HA resources. Authenticate via API token or ticket. Run every 60 seconds. Alert on node offline, quorum loss, or storage >85% used. Correlate with Corosync logs for fence events.
- **Visualization:** Status grid (node health per cluster), Table (storage usage by node), Timeline (HA fence events).
- **CIM Models:** N/A

---

## 2.4 Cross-Platform Virtualization

**Primary App/TA:** Multiple — combines data from VMware, Hyper-V, KVM sources with CMDB/asset lookups

---

### UC-2.4.1 · Guest OS End-of-Life Tracking
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance, Security
- **Value:** VMs running end-of-life operating systems no longer receive security patches, creating unmitigated vulnerabilities. Tracking guest OS versions across all hypervisors against vendor EOL dates enables proactive migration planning before support ends. Required for PCI DSS, HIPAA, and SOC 2 compliance.
- **App/TA:** `Splunk_TA_vmware`, `Splunk_TA_windows`, custom OS inventory
- **Data Sources:** VM inventory from all hypervisors, OS EOL lookup table
- **SPL:**
```spl
index=vmware sourcetype="vmware:inv:vm"
| stats latest(guest_os) as os_name by vm_name
| append [search index=hyperv sourcetype="hyperv_vm_config" | stats latest(os_name) as os_name by vm_name]
| append [search index=virtualization sourcetype=kvm_guest_agent | stats latest(os_name) as os_name by vm_name]
| lookup os_eol_dates os_name OUTPUT eol_date, eol_status
| eval days_to_eol=round((strptime(eol_date, "%Y-%m-%d") - now()) / 86400, 0)
| where days_to_eol < 180 OR eol_status="EOL"
| sort days_to_eol
| table vm_name, os_name, eol_date, days_to_eol, eol_status
```
- **Implementation:** Collect guest OS information from all hypervisor platforms. Maintain a lookup table (`os_eol_dates.csv`) mapping OS names to vendor EOL dates (Microsoft, Red Hat, Canonical, etc.). Alert at 180 days before EOL (planning), 90 days (action required), and on any VM running an already-EOL OS. Generate quarterly reports for management.
- **Visualization:** Table (VM, OS, EOL date), Bar chart (VMs by EOL status), Timeline (upcoming EOL dates).
- **CIM Models:** N/A

---

### UC-2.4.2 · VM Backup Coverage Validation
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Value:** VMs without recent successful backups have no recovery point — a single failure causes permanent data loss. By comparing VM inventory across all hypervisors against backup job success records, this use case identifies VMs that have fallen through the cracks of the backup policy.
- **App/TA:** `Splunk_TA_vmware`, `Splunk_TA_windows`, backup vendor TA
- **Data Sources:** VM inventory from all hypervisors, backup job logs (Veeam, Commvault, Cohesity, PBS)
- **SPL:**
```spl
index=vmware sourcetype="vmware:inv:vm" power_state="poweredOn"
| stats latest(vm_name) as vm_name by vm_name
| append [search index=hyperv sourcetype="hyperv_vm_config" state="Running" | stats latest(vm_name) as vm_name by vm_name]
| sort 0 vm_name, -_time
| dedup vm_name
| join type=left max=1 vm_name [search index=backup sourcetype="backup_jobs" status="Success" earliest=-48h | stats latest(_time) as last_backup, latest(status) as backup_status by vm_name]
| eval backup_age_hours=if(isnotnull(last_backup), round((now()-last_backup)/3600, 0), 999)
| where backup_age_hours > 48 OR isnull(last_backup)
| sort -backup_age_hours
| table vm_name, backup_status, last_backup, backup_age_hours
```
- **Implementation:** Combine VM inventory from all hypervisors with backup job results from your backup product. Left-join to find VMs with no matching backup job. Alert on VMs with no backup in >24 hours (for daily policy) or >48 hours (with buffer). Exclude development/test VMs via a lookup if appropriate. Run daily and send report to backup administrators.
- **Visualization:** Table (unprotected VMs), Single value (backup coverage %), Pie chart (backed up vs unprotected), Bar chart (backup age distribution).
- **CIM Models:** N/A

---

### UC-2.4.3 · VM-to-Host Density Trending
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Capacity
- **Value:** VM density (VMs per host) is a key capacity metric. Rising density indicates growing consolidation ratios that may exceed host capacity. Density spikes after HA failovers reveal hosts running at unsustainable loads. Trending density over time supports procurement planning and workload distribution decisions.
- **App/TA:** `Splunk_TA_vmware`, `Splunk_TA_windows`
- **Data Sources:** VM inventory from all hypervisors
- **SPL:**
```spl
index=vmware sourcetype="vmware:inv:vm" power_state="poweredOn"
| stats dc(vm_name) as vm_count, sum(numCpu) as total_vcpus, sum(memoryMB) as total_mem_mb by host
| eval total_mem_gb=round(total_mem_mb/1024, 0)
| sort -vm_count
| table host, vm_count, total_vcpus, total_mem_gb
```
- **Implementation:** Count powered-on VMs per host from inventory data. Track daily for trend analysis. Calculate vcpu-to-pcpu ratio and memory overcommit per host. Alert when any host exceeds your density threshold (e.g., >30 VMs, >4:1 vCPU ratio, or >1.5:1 memory overcommit). Useful after HA events to verify surviving hosts aren't overloaded.
- **Visualization:** Bar chart (VMs per host), Line chart (density trend over months), Table (host, VM count, ratios), Heatmap (density by cluster).
- **CIM Models:** N/A

---

### UC-2.4.4 · VM Provisioning Time Tracking
- **Criticality:** 🟢 Low
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Measures the time from VM creation request to operational state. Long provisioning times indicate process bottlenecks — slow template deployment, manual approval delays, storage provisioning issues, or network configuration problems. Supports ITSM service level tracking and infrastructure automation improvement.
- **App/TA:** `Splunk_TA_vmware`, ITSM TA
- **Data Sources:** vCenter events, ITSM request logs
- **SPL:**
```spl
index=vmware sourcetype="vmware:events" event_type="VmCreatedEvent"
| eval create_time=_time
| join max=1 vm_name [search index=vmware sourcetype="vmware:events" event_type="VmPoweredOnEvent" | eval poweron_time=_time | table vm_name, poweron_time]
| eval provision_minutes=round((poweron_time-create_time)/60, 1)
| where provision_minutes > 0
| stats avg(provision_minutes) as avg_min, median(provision_minutes) as median_min, max(provision_minutes) as max_min by datacenter
| table datacenter, avg_min, median_min, max_min
```
- **Implementation:** Correlate VM creation events with first power-on events from vCenter. For full lifecycle tracking, also correlate with ITSM ticket creation time (when the request was submitted). Calculate time from request → approval → creation → power-on. Set SLA targets and alert when provisioning exceeds them.
- **Visualization:** Bar chart (average provisioning time by DC), Line chart (trend over time), Table (slowest provisions).
- **CIM Models:** N/A

---

### UC-2.4.5 · Virtualization License Compliance
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Value:** VMware licenses are per-CPU, Hyper-V licenses are per-core, and Windows Server Datacenter vs Standard determines VM rights. Running more physical CPUs or cores than licensed risks audit penalties. Tracking socket/core counts against entitlements prevents costly true-up surprises.
- **App/TA:** `Splunk_TA_vmware`, `Splunk_TA_windows`, license lookup
- **Data Sources:** Host inventory from all hypervisors, license entitlement lookup
- **SPL:**
```spl
index=vmware sourcetype="vmware:inv:hostsystem"
| stats latest(numCpuPkgs) as sockets, latest(numCpuCores) as cores, latest(version) as esxi_version by host, cluster
| eval license_units=sockets
| stats sum(license_units) as total_sockets, sum(cores) as total_cores, dc(host) as host_count by cluster
| lookup license_entitlements cluster OUTPUT licensed_sockets, license_edition
| eval compliant=if(total_sockets<=licensed_sockets, "Yes", "No")
| table cluster, host_count, total_sockets, total_cores, licensed_sockets, license_edition, compliant
```
- **Implementation:** Collect host hardware inventory (socket count, core count) from all hypervisors. Maintain a lookup table of license entitlements per cluster/site. Compare actual vs entitled. Alert when actual exceeds entitled. Generate monthly compliance reports. Track license utilization ratio — under-utilized licenses may be reassignable.
- **Visualization:** Table (cluster, sockets, entitled, compliant), Gauge (license utilization), Bar chart (compliance by cluster).
- **CIM Models:** N/A

---

### UC-2.4.6 · Multi-Hypervisor Fleet Inventory
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Configuration
- **Value:** Organizations running multiple hypervisors need a unified view of all VMs regardless of platform. A consolidated inventory enables accurate capacity planning, consistent policy enforcement, and complete asset tracking. Without it, VMs on different platforms become silos with inconsistent governance.
- **App/TA:** `Splunk_TA_vmware`, `Splunk_TA_windows`, custom KVM inputs
- **Data Sources:** VM inventory from VMware, Hyper-V, KVM/Proxmox
- **SPL:**
```spl
index=vmware sourcetype="vmware:inv:vm"
| eval platform="VMware", vcpus=numCpu, mem_gb=round(memoryMB/1024,0)
| table vm_name, platform, host, vcpus, mem_gb, power_state, guest_os
| append [search index=hyperv sourcetype="hyperv_vm_config" | eval platform="Hyper-V", mem_gb=round(memory_mb/1024,0) | table vm_name, platform, host, vcpus, mem_gb, state, os_name | rename state as power_state, os_name as guest_os]
| append [search index=virtualization sourcetype=kvm_capacity | eval platform="KVM", mem_gb=round(vm_memory_mb/1024,0) | table vm_name, platform, host, vm_vcpus, mem_gb, power_state, guest_os | rename vm_vcpus as vcpus]
| stats latest(platform) as platform, latest(host) as host, latest(vcpus) as vcpus, latest(mem_gb) as mem_gb, latest(power_state) as state, latest(guest_os) as os by vm_name
| sort platform, vm_name
| table vm_name, platform, host, vcpus, mem_gb, state, os
```
- **Implementation:** Normalize VM inventory fields across all hypervisor platforms into a common schema (vm_name, platform, host, vcpus, mem_gb, power_state, guest_os). Use a scheduled search to populate a summary index or KV store for fast lookups. Enrich with CMDB data (owner, department, environment) via lookup. Generate weekly fleet reports showing total VM count, resource allocation, and platform distribution.
- **Visualization:** Table (unified VM inventory), Pie chart (VMs by platform), Bar chart (resource allocation by platform), Treemap (VMs by department and platform).
- **CIM Models:** Inventory

---

### UC-2.4.7 · oVirt / RHV Data Center Health
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability, Fault
- **Value:** Data center and storage domain operational status for oVirt and Red Hat Virtualization (RHV). Detects storage domain maintenance mode, data center connectivity issues, and storage domain activation failures that prevent VM operations.
- **App/TA:** Custom (oVirt REST API input)
- **Data Sources:** oVirt REST API (`/api/datacenters`, `/api/storagedomains`)
- **SPL:**
```spl
index=virtualization sourcetype="ovirt_datacenter"
| stats latest(status) as dc_status, latest(local) as local_dc, latest(name) as dc_name by id
| where dc_status!="up"
| table dc_name, dc_status, local_dc
```
- **Implementation:** Create scripted input polling oVirt API: `GET /api/datacenters` and `GET /api/storagedomains`. Authenticate via oVirt SSO (username/password or token). Parse status (up/down/maintenance), active flag, and available space. Run every 5 minutes. Alert when data center status != "up" or storage domain status != "active". Create separate sourcetypes for datacenter and storagedomain events. Monitor storage domain available percentage for capacity. Correlate with oVirt engine logs for root cause.
- **Visualization:** Status grid (data centers and storage domains), Table (operational status), Gauge (storage domain capacity).
- **CIM Models:** N/A

---

