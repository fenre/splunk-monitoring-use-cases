## 2. Virtualization

### 2.1 VMware vSphere

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
- **References:** [Splunk Add-on for VMware](https://splunkbase.splunk.com/app/3215), [vSphere API](https://developer.vmware.com/)
- **Known false positives:** Short CPU ready spikes during boot or cloning; tune threshold or use rolling average.

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

- **References:** [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)

---

### UC-2.1.3 · Datastore Capacity Trending
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Wave:** 🐢 crawl
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

- **References:** [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)

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
| tstats `summariesonly` avg(Performance.read_latency) as read_ms avg(Performance.write_latency) as write_ms
  from datamodel=Performance where nodename=Performance.Storage
  by Performance.host Performance.mount span=5m
| eval worst_ms=max(read_ms, write_ms)
| where worst_ms > 20
```

- **References:** [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-2.1.7 · HA Failover Events
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Wave:** 🐢 crawl
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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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
| bin _time span=1h
| stats count by _time, cluster
| where count > 20
```
- **Implementation:** Monitor DRS migration frequency. High migration counts suggest oscillation. Also check for unapplied DRS recommendations (DRS set to manual mode). Correlate with CPU/memory utilization per host.
- **Visualization:** Line chart (migrations per hour), Table of DRS events, Cluster balance comparison chart.
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-2.1.10 · vSAN Health Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Wave:** 🐢 crawl
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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-2.1.11 · ESXi Host Hardware Alerts
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Wave:** 🐢 crawl
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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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
  by Performance.host span=1d
| where avg_cpu < 20
```

- **References:** [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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
| tstats `summariesonly` sum(Performance.read_ops) as read_ops sum(Performance.write_ops) as write_ops
  from datamodel=Performance where nodename=Performance.Storage
  by Performance.host Performance.mount span=15m
| eval total_iops=read_ops + write_ops
| where total_iops > 500
```

- **References:** [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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
- **CIM SPL:**
```spl
| tstats summariesonly=t count from datamodel=Change.All_Changes by All_Changes.action, All_Changes.object_category, All_Changes.user | sort - count
```

- **References:** [CIM: Change](https://docs.splunk.com/Documentation/CIM/latest/User/Change)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-2.1.46 · vCenter Alarm Acknowledgment Tracking
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Operations
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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### 2.2 Microsoft Hyper-V

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

- **References:** [Splunk_TA_windows](https://splunkbase.splunk.com/app/742), [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)

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

- **References:** [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)

---

### UC-2.2.3 · Cluster Shared Volume Health
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Wave:** 🐢 crawl
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

- **References:** [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)

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

- **References:** [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)

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

- **References:** [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)

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

- **References:** [Splunk_TA_windows](https://splunkbase.splunk.com/app/742), [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)

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

- **References:** [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)

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

- **References:** [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)

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

- **References:** [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)

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

- **References:** [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)

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

- **References:** [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)

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

- **References:** [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)

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

- **References:** [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)

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

- **References:** [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)

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

- **References:** [Splunk_TA_windows](https://splunkbase.splunk.com/app/742), [CIM: Change](https://docs.splunk.com/Documentation/CIM/latest/User/Change)

---

### 2.3 KVM / Proxmox / oVirt

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk_TA_nix](https://splunkbase.splunk.com/app/833)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk_TA_nix](https://splunkbase.splunk.com/app/833)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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
| bin _time span=5m
| stats count as errors by host, _time
| where errors > 5
| table _time, host, errors
```
- **Implementation:** Monitor libvirtd syslog output for errors. Create a scripted input that runs `virsh list` and measures response time — if it takes >5 seconds, libvirtd is likely overloaded. Also monitor the systemd service status: `systemctl is-active libvirtd`. Alert if libvirtd is not active or response time exceeds 10 seconds.
- **Visualization:** Status indicator (libvirtd per host), Line chart (response time), Events table (errors).
- **CIM Models:** N/A

- **References:** [Splunk_TA_nix](https://splunkbase.splunk.com/app/833)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### 2.4 Cross-Platform Virtualization

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

- **References:** [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)

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

- **References:** [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)

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

- **References:** [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)

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
- **CIM Models:** Compute_Inventory
- **CIM SPL:**
```spl
| tstats summariesonly=t count from datamodel=Compute_Inventory.Hypervisor by Hypervisor.dest, Hypervisor.status | sort - count
```
- **References:** [Splunk_TA_windows](https://splunkbase.splunk.com/app/742), [CIM: Compute_Inventory](https://docs.splunk.com/Documentation/CIM/latest/User/Compute_Inventory)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### 2.5 End-User Computing / VDI Endpoints

**Primary App/TA:** Custom scripted inputs polling IGEL UMS REST API (IMI v3), Splunk Universal Forwarder monitoring UMS security log files, IGEL OS rsyslog forwarding via TLS

**Data Sources:** IGEL UMS REST API inventory (`/v3/thinclients`, `/v3/firmwares`), UMS check-status endpoint, UMS security audit logs (`ums-server-security.log`), ICG security logs (`icg-security.log`), IGEL OS syslog (rsyslog via TLS)

---

### UC-2.5.1 · IGEL Device Fleet Online/Offline Status
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** IGEL thin clients are the primary interface for VDI users in healthcare, finance, and enterprise environments. When a device goes offline, the user cannot access virtual desktops or published applications. Monitoring fleet-wide online/offline ratios and identifying persistently offline devices enables rapid remediation before users are affected at scale.
- **App/TA:** Custom scripted input polling IGEL UMS REST API (`GET /v3/thinclients`)
- **Data Sources:** `index=endpoint` `sourcetype="igel:ums:inventory"` fields `device_name`, `online_status`, `last_ip`, `site`, `directory_path`
- **SPL:**
```spl
index=endpoint sourcetype="igel:ums:inventory"
| stats latest(online_status) as status, latest(last_ip) as last_ip, latest(directory_path) as site by device_name
| eval status_label=if(status="true", "Online", "Offline")
| stats count as total, sum(eval(if(status="true",1,0))) as online_count by site
| eval offline_count=total-online_count
| eval online_pct=round(online_count/total*100,1)
| table site, total, online_count, offline_count, online_pct
| sort -offline_count
```
- **Implementation:** Create a scripted input that polls `GET /v3/thinclients` from the IGEL UMS REST API (IMI v3) every 5 minutes. Authenticate using a dedicated UMS service account with read-only permissions. Parse each device's `unitID`, `name`, `lastIP`, `movedToBin`, and online status. Index as JSON events. Group by UMS directory path (used as site/location). Alert when fleet-wide online percentage drops below 90% or when more than 10 devices at a single site go offline simultaneously.
- **Visualization:** Single value (fleet online %), Table (sites ranked by offline count), Status grid (device online/offline by site).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-2.5.2 · IGEL Firmware Version Compliance
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Value:** Running outdated or unapproved IGEL OS firmware exposes endpoints to known vulnerabilities and breaks standardized VDI session configurations. Tracking firmware versions across the fleet against an approved baseline ensures compliance with patch policies and simplifies troubleshooting by eliminating version drift as a variable.
- **App/TA:** Custom scripted input polling IGEL UMS REST API (`GET /v3/thinclients?facets=details`, `GET /v3/firmwares`)
- **Data Sources:** `index=endpoint` `sourcetype="igel:ums:inventory"` fields `device_name`, `firmware_id`, `firmware_version`, `product_name`, `directory_path`
- **SPL:**
```spl
index=endpoint sourcetype="igel:ums:inventory"
| stats latest(firmware_id) as fw_id, latest(firmware_version) as fw_version, latest(device_name) as device_name by unit_id
| lookup igel_approved_firmware fw_version OUTPUT approved, target_version
| eval compliant=if(approved="yes", "Compliant", "Non-Compliant")
| stats count as device_count by fw_version, compliant, target_version
| sort -device_count
| table fw_version, compliant, target_version, device_count
```
- **Implementation:** Poll `GET /v3/thinclients?facets=details` to retrieve firmware IDs per device, and `GET /v3/firmwares` to resolve firmware IDs to version strings and product names. Maintain a lookup table (`igel_approved_firmware.csv`) with columns `fw_version`, `approved`, `target_version` mapping each known firmware version to its compliance status. Run the lookup enrichment as a scheduled search daily. Alert when non-compliant device percentage exceeds 20% or when any device runs a firmware version flagged as critical-vulnerability.
- **Visualization:** Pie chart (compliant vs non-compliant), Table (firmware versions with device counts), Single value (compliance %).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-2.5.3 · IGEL UMS Server Health Monitoring
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** The IGEL UMS server is the central management plane for all IGEL endpoints. If UMS goes down or enters an error state, administrators cannot push policies, update firmware, or manage device configurations. Monitoring the built-in health endpoint provides immediate alerting on database connectivity failures, HA issues, or service degradation.
- **App/TA:** Custom scripted input polling UMS check-status endpoint
- **Data Sources:** `index=endpoint` `sourcetype="igel:ums:health"` fields `ums_server`, `status`, `message`
- **SPL:**
```spl
index=endpoint sourcetype="igel:ums:health"
| stats latest(status) as current_status, latest(message) as message, latest(_time) as last_check by ums_server
| eval status_age_min=round((now()-last_check)/60,0)
| where current_status!="ok" OR status_age_min > 5
| table ums_server, current_status, message, status_age_min
```
- **Implementation:** Create a scripted input that polls `https://[server]:[port]/ums/check-status` every 60 seconds. The endpoint returns JSON with a `status` field (values: `init`, `ok`, `warn`, `err`) and optional `message` describing the issue. Parse the response and index as events. Alert immediately on `err` status (database connection failure, device communication port not ready). Alert on `warn` status (HA update mode, cloud gateway disconnection, certificate sync issues). Also alert if no health check event has been received in 5 minutes (endpoint unreachable).
- **Visualization:** Single value (current status with color coding), Timeline (status changes over time), Table (all UMS servers with status).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-2.5.4 · IGEL Device Heartbeat Loss Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** IGEL OS 12 devices send periodic heartbeat signals to the UMS server to report operational status. When heartbeats stop, the device may be powered off, network-disconnected, or experiencing a crash loop. Detecting heartbeat loss within a configurable window enables proactive remediation before users report issues at shift start.
- **App/TA:** Custom scripted input polling IGEL UMS REST API (`GET /v3/thinclients?facets=details`)
- **Data Sources:** `index=endpoint` `sourcetype="igel:ums:inventory"` fields `device_name`, `last_contact`, `directory_path`, `last_ip`
- **SPL:**
```spl
index=endpoint sourcetype="igel:ums:inventory"
| stats latest(last_contact) as last_contact, latest(last_ip) as last_ip, latest(directory_path) as site by device_name
| eval contact_epoch=strptime(last_contact, "%Y-%m-%dT%H:%M:%S")
| eval hours_since_contact=round((now()-contact_epoch)/3600, 1)
| where hours_since_contact > 4
| sort -hours_since_contact
| table device_name, site, last_ip, last_contact, hours_since_contact
```
- **Implementation:** Poll the UMS API with `facets=details` to retrieve `lastContact` timestamps per device. Convert to epoch and compare against current time. Devices that have not contacted UMS within the configured threshold (default 4 hours, adjust for shift patterns) are flagged. Exclude devices in the UMS recycle bin (`movedToBin=true`). Correlate with site/directory to identify location-specific network outages. Trigger escalation if more than 5 devices at the same site lose heartbeat simultaneously.
- **Visualization:** Table (stale devices sorted by hours since contact), Bar chart (devices per site with lost heartbeat), Single value (total devices with lost heartbeat).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-2.5.5 · IGEL OS Endpoint Syslog Error Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** IGEL OS endpoints forward syslog messages via rsyslog with TLS encryption to centralized collectors. Monitoring for error and critical severity messages across the fleet surfaces hardware failures, driver issues, network connectivity problems, and application crashes that users may not report until they become workflow-blocking.
- **App/TA:** Splunk syslog input (TCP/TLS) receiving IGEL OS rsyslog
- **Data Sources:** `index=endpoint` `sourcetype="igel:os:syslog"` fields `host`, `severity`, `facility`, `process`, `message`
- **SPL:**
```spl
index=endpoint sourcetype="igel:os:syslog" (severity="err" OR severity="crit" OR severity="alert" OR severity="emerg")
| bin _time span=1h
| stats count as error_count, dc(host) as affected_devices, values(process) as processes by severity, _time
| where error_count > 10
| table _time, severity, error_count, affected_devices, processes
```
- **Implementation:** Configure IGEL OS syslog forwarding via UMS profile: System > Logging > Remote mode = Client, with TLS enabled and CA certificate at `/wfs/ca-certs/ca.pem`. Point to Splunk TCP/TLS input on port 6514. Create a props.conf entry for `sourcetype=igel:os:syslog` to parse syslog priority into `severity` and `facility` fields. Alert on cluster patterns (same error across many devices = systemic issue, repeated errors on one device = hardware fault). Exclude known benign messages via a lookup filter.
- **Visualization:** Timechart (error count by severity), Table (top errors by frequency), Bar chart (affected devices by error type).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-2.5.6 · IGEL UMS Security Audit Log Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security, Audit
- **Value:** IGEL UMS security audit logs capture critical administrative actions: user logins, failed authentication, password changes, device policy assignments, configuration modifications, and administrator account lifecycle events. Monitoring these events is essential for detecting unauthorized administrative access, policy tampering, and insider threats targeting the endpoint management plane.
- **App/TA:** Splunk Universal Forwarder monitoring UMS security log files
- **Data Sources:** `index=endpoint` `sourcetype="igel:ums:security"` fields `source_tag`, `event_type`, `user`, `target`, `result`, `detail`
- **SPL:**
```spl
index=endpoint sourcetype="igel:ums:security"
| eval event_category=case(
    match(event_type, "(?i)logon|login|logoff|authentication"), "Authentication",
    match(event_type, "(?i)password"), "Password Change",
    match(event_type, "(?i)assignment|profile|policy"), "Policy Change",
    match(event_type, "(?i)account|user.*creat|user.*delet"), "Account Lifecycle",
    match(event_type, "(?i)shutdown|restart"), "Service Lifecycle",
    1=1, "Other"
  )
| stats count by event_category, source_tag, result
| sort -count
| table event_category, source_tag, result, count
```
- **Implementation:** Deploy a Splunk Universal Forwarder on the UMS server (Windows or Linux). Monitor the security log files: `ums-server-security.log`, `ums-admin-security.log`, `wums-app-security.log`. Enable remote security logging in UMS Administration > Global Configuration > Logging. Parse events using source tags (`UMS-Server`, `ICG`, `IMI`, `UMS-Webapp`). Alert on: failed login attempts exceeding 5 within 10 minutes, administrator account creation/deletion, device factory reset commands, and off-hours policy modifications.
- **Visualization:** Bar chart (events by category), Timeline (authentication events), Table (failed logins by user and source IP).
- **CIM Models:** Authentication, Change
- **CIM SPL:**
```spl
| tstats summariesonly=t count from datamodel=Authentication.Authentication by Authentication.action, Authentication.user, Authentication.src | sort - count
```

- **References:** [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)

---

### UC-2.5.7 · IGEL Device Resource Utilization
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** IGEL thin clients have constrained hardware resources (CPU, memory, flash storage). Monitoring resource utilization across the fleet identifies devices that are under-provisioned for their workload, approaching flash storage capacity, or experiencing performance issues that degrade the VDI user experience. Proactive capacity trending prevents user complaints and supports hardware refresh planning.
- **App/TA:** Custom scripted input polling IGEL UMS REST API (`GET /v3/thinclients?facets=details`)
- **Data Sources:** `index=endpoint` `sourcetype="igel:ums:inventory"` fields `device_name`, `cpu_speed_mhz`, `mem_size_mb`, `flash_size_mb`, `battery_level`, `network_speed`
- **SPL:**
```spl
index=endpoint sourcetype="igel:ums:inventory"
| stats latest(cpu_speed_mhz) as cpu_mhz, latest(mem_size_mb) as mem_mb, latest(flash_size_mb) as flash_mb, latest(battery_level) as battery, latest(device_name) as device_name by unit_id
| eval mem_tier=case(mem_mb<2048, "Under 2GB", mem_mb<4096, "2-4GB", mem_mb<8192, "4-8GB", 1=1, "8GB+")
| eval flash_tier=case(flash_mb<4096, "Under 4GB", flash_mb<8192, "4-8GB", 1=1, "8GB+")
| stats count as device_count by mem_tier, flash_tier
| sort mem_tier, flash_tier
| table mem_tier, flash_tier, device_count
```
- **Implementation:** Poll `GET /v3/thinclients?facets=details` to retrieve hardware specifications for each device. The API returns CPU speed, memory size, flash storage, battery level (mobile devices), and network speed. Index these as inventory events with the device `unitID` as a unique key. Build a fleet hardware profile to identify under-provisioned devices. Alert when battery level drops below 20% on mobile IGEL devices. Use trending to forecast flash storage exhaustion. Cross-reference hardware specs against minimum requirements for the VDI workload (e.g., Citrix Workspace App, VMware Horizon Client).
- **Visualization:** Heatmap (memory tier x flash tier), Bar chart (devices by hardware class), Table (devices below minimum specs).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-2.5.8 · IGEL Device Unscheduled Reboot Detection
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** Unexpected reboots on thin clients disrupt active VDI sessions, causing users to lose unsaved work and requiring re-authentication. Detecting unscheduled reboots — those not preceded by an administrator-initiated reboot command or firmware update — helps identify hardware failures, power issues, or kernel panics across the fleet before they become widespread.
- **App/TA:** Splunk syslog input (TCP/TLS) receiving IGEL OS rsyslog
- **Data Sources:** `index=endpoint` `sourcetype="igel:os:syslog"` fields `host`, `process`, `message`
- **SPL:**
```spl
index=endpoint sourcetype="igel:os:syslog" process="kernel" ("Linux version" OR "Booting" OR "Command line:")
| stats count as boot_events, earliest(_time) as first_boot, latest(_time) as last_boot by host
| join type=left host [search index=endpoint sourcetype="igel:ums:security" event_type="*reboot*" OR event_type="*restart*" | stats latest(_time) as scheduled_reboot by target]
| eval unscheduled=if(isnull(scheduled_reboot) OR last_boot > scheduled_reboot + 600, "Yes", "No")
| where unscheduled="Yes"
| eval last_boot_fmt=strftime(last_boot, "%Y-%m-%d %H:%M:%S")
| table host, last_boot_fmt, boot_events
| sort -boot_events
```
- **Implementation:** IGEL OS kernel boot messages appear in syslog when the device starts. Cross-reference boot events against UMS security audit logs for administrator-initiated reboot commands. Boots that occur without a matching reboot command within a 10-minute window are classified as unscheduled. Alert when a single device has more than 3 unscheduled reboots in 24 hours (possible hardware failure) or when more than 5 devices at the same site reboot unexpectedly within 30 minutes (possible power event).
- **Visualization:** Table (devices with unscheduled reboots), Timechart (reboot events over time), Single value (unscheduled reboot count last 24h).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-2.5.9 · IGEL Cloud Gateway Connection Health
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** The IGEL Cloud Gateway (ICG) enables remote management of IGEL devices outside the corporate network — essential for work-from-home and branch office deployments. If ICG connectivity fails, remote devices cannot receive policy updates, firmware upgrades, or administrative commands, creating a management blind spot. Monitoring ICG health from both the UMS and ICG perspectives ensures continuous remote device manageability.
- **App/TA:** Splunk Universal Forwarder monitoring ICG security log, custom scripted input for UMS health
- **Data Sources:** `index=endpoint` `sourcetype="igel:icg:security"` fields `event_type`, `user`, `result`, `source_ip`; `sourcetype="igel:ums:health"` for ICG connection warnings
- **SPL:**
```spl
index=endpoint sourcetype="igel:icg:security"
| bin _time span=15m
| stats count as total_events,
  sum(eval(if(match(event_type, "(?i)auth.*fail"), 1, 0))) as failed_auth,
  sum(eval(if(match(event_type, "(?i)auth.*success"), 1, 0))) as success_auth,
  dc(source_ip) as unique_sources by _time
| eval fail_pct=if(total_events>0, round(failed_auth/total_events*100,1), 0)
| where failed_auth > 5 OR fail_pct > 20
| table _time, total_events, success_auth, failed_auth, fail_pct, unique_sources
```
- **Implementation:** Deploy a Splunk Universal Forwarder on the ICG server to monitor `/opt/IGEL/icg/usg/logs/icg-security.log`. The ICG security log records authentication events (success/failure), user creation/deletion, and file uploads. Also monitor the UMS check-status endpoint for ICG-related warnings (cloud gateway disconnection). Alert on: sustained authentication failures from ICG (possible certificate mismatch), ICG going offline (no events for 15+ minutes), or UMS reporting ICG disconnection in its health status.
- **Visualization:** Timechart (ICG auth success vs failure), Single value (current ICG status), Table (failed auth sources).
- **CIM Models:** Authentication
- **CIM SPL:**
```spl
| tstats summariesonly=t dc(Authentication.src) as agg_value from datamodel=Authentication.Authentication by Authentication.action, Authentication.user, Authentication.src span=15m | sort - agg_value
```

- **References:** [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)

---

### UC-2.5.10 · IGEL Device Configuration Drift Detection
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Value:** IGEL UMS manages device configurations through profiles and priority profiles assigned to devices or directories. Unauthorized or unintended configuration changes — profile reassignments, priority profile overrides, or direct device settings modifications — can break VDI session configurations, disable security controls, or create inconsistent user experiences. Detecting configuration drift from the approved baseline ensures fleet standardization.
- **App/TA:** Splunk Universal Forwarder monitoring UMS security log files
- **Data Sources:** `index=endpoint` `sourcetype="igel:ums:security"` fields `source_tag`, `event_type`, `user`, `target`, `detail`
- **SPL:**
```spl
index=endpoint sourcetype="igel:ums:security" source_tag="UMS-Webapp" OR source_tag="UMS-Server"
  (event_type="*profile*" OR event_type="*assignment*" OR event_type="*settings*" OR event_type="*configuration*")
| eval change_type=case(
    match(event_type, "(?i)priority.*profile"), "Priority Profile Change",
    match(event_type, "(?i)profile"), "Profile Change",
    match(event_type, "(?i)assign"), "Assignment Change",
    1=1, "Settings Change"
  )
| stats count as changes, dc(target) as affected_devices, values(user) as changed_by by change_type, _time
| where changes > 0
| sort -_time
| table _time, change_type, changes, affected_devices, changed_by
```
- **Implementation:** The UMS security audit log records all profile assignments, priority profile updates, and device configuration modifications with the acting administrator's username. Monitor for: bulk profile reassignments (more than 10 devices in 5 minutes — could be intentional rollout or accidental), off-hours configuration changes, changes by unauthorized users, and removal of security-related profiles (e.g., syslog forwarding, USB lockdown). Maintain a lookup of approved change windows and authorized administrators. Alert on changes outside approved windows or by non-authorized users.
- **Visualization:** Timeline (configuration changes), Bar chart (changes by type), Table (recent changes with user and target details).
- **CIM Models:** Change
- **CIM SPL:**
```spl
| tstats summariesonly=t count from datamodel=Change.All_Changes by All_Changes.action, All_Changes.object_category, All_Changes.user | sort - count
```

- **References:** [uberAgent indexer app](https://splunkbase.splunk.com/app/2998), [Splunkbase app 1448](https://splunkbase.splunk.com/app/1448), [Splunk Add-on for Microsoft Windows](https://splunkbase.splunk.com/app/742), [CIM: Change](https://docs.splunk.com/Documentation/CIM/latest/User/Change)

---

### 2.6 Citrix Virtual Apps & Desktops

**Primary App/TA:** uberAgent UXM for Splunk (Splunkbase 1448, searchhead app) + uberAgent indexer app (Splunkbase 2998), Template for Citrix XenDesktop 7 (`TA-XD7-Broker`, `TA-XD7-VDA`), Splunk Add-on for Microsoft Windows, Splunk Add-on for Microsoft IIS (StoreFront), Citrix Monitor Service OData API scripted inputs

**Data Sources:** uberAgent endpoint telemetry via HEC (`uberAgent:*` sourcetypes — session, logon, application, machine, browser, Citrix site metrics), Citrix Broker Service event logs (indexes: `xd`, `xd_winevents`, `xd_alerts`), VDA performance counters (`xd_perfmon`), Citrix StoreFront IIS W3C logs, Citrix Monitor Service OData API (session/logon/machine data), Citrix Licensing logs, Citrix PVS streaming logs, Citrix Profile Management logs, Citrix FAS certificate events

---

### UC-2.6.1 · Citrix Session Logon Duration Breakdown
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance
- **Value:** Slow Citrix logon times are the most common user complaint in CVAD environments. Logon duration is composed of multiple sequential phases — brokering, VM start, HDX connection, authentication, profile load, GPO processing, and script execution. Identifying which phase contributes to slow logons enables targeted remediation rather than broad troubleshooting. A 60-second logon target is typical; exceeding it degrades user satisfaction and productivity.
- **App/TA:** uberAgent UXM (Splunkbase 1448) — recommended; or Template for Citrix XenDesktop 7 (`TA-XD7-Broker`), Citrix Monitor Service OData API
- **Data Sources:** uberAgent: `sourcetype="uberAgent:Logon:LogonDetail"` (phase-level breakdown including GPO, profile, shell, scripts); or `index=xd` `sourcetype="citrix:broker:events"` fields `logon_duration_ms`, `brokering_duration_ms`, `vm_start_duration_ms`, `hdx_connection_ms`, `authentication_ms`, `profile_load_ms`, `gpo_ms`, `logon_scripts_ms`, `user`, `delivery_group`
- **SPL:**
```spl
index=xd sourcetype="citrix:broker:events" event_type="SessionLogon"
| eval total_logon_sec=logon_duration_ms/1000
| bin _time span=1h
| stats avg(total_logon_sec) as avg_logon, perc95(total_logon_sec) as p95_logon,
  avg(brokering_duration_ms) as avg_broker, avg(vm_start_duration_ms) as avg_vmstart,
  avg(hdx_connection_ms) as avg_hdx, avg(profile_load_ms) as avg_profile,
  avg(gpo_ms) as avg_gpo, count as logon_count by delivery_group, _time
| where p95_logon > 60
| table _time, delivery_group, logon_count, avg_logon, p95_logon, avg_broker, avg_vmstart, avg_hdx, avg_profile, avg_gpo
```
- **Implementation:** **Preferred:** Deploy uberAgent UXM on VDAs — the Logon Duration dashboard provides automatic phase breakdown (userinit, shell, GPO, profile, scripts) with no OData polling required, and captures per-user detail. **Alternative:** Collect session logon events from the Citrix Broker Service event log on Delivery Controllers using the `TA-XD7-Broker` add-on, or poll the Monitor Service OData API endpoint `Sessions` for `LogOnDuration` breakdown. Alert when p95 logon exceeds 60 seconds for any delivery group. Trend logon duration over weeks to detect gradual regression after GPO or profile changes. Segment by delivery group to isolate problem areas. Common root causes by phase: brokering (controller load), VM start (hypervisor contention), profile load (large profiles or slow file shares), GPO (excessive policies).
- **Visualization:** Stacked bar chart (logon phases), Line chart (logon duration trending), Table (slowest delivery groups).
- **CIM Models:** N/A

- **References:** [uberAgent UXM](https://splunkbase.splunk.com/app/1448)

---

### UC-2.6.2 · ICA/HDX Session Latency and Quality
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** ICA Round Trip Time (RTT) is the primary measure of Citrix session responsiveness — the time from a user keystroke to the response appearing on screen. Citrix defines 0–150ms as optimal, 150–300ms as acceptable, and above 300ms as degraded. Poor ICA latency causes sluggish typing, delayed screen updates, and broken audio/video, directly impacting user productivity. Monitoring ICA RTT across the fleet detects network issues, overloaded session hosts, and endpoint problems.
- **App/TA:** uberAgent UXM (Splunkbase 1448) — recommended; or Template for Citrix XenDesktop 7 (`TA-XD7-VDA`), Citrix Monitor Service OData API
- **Data Sources:** uberAgent: `sourcetype="uberAgent:Session:SessionDetail"` (ICA RTT, ICA latency, bandwidth, protocol, session quality); or `index=xd_perfmon` `sourcetype="citrix:vda:perfmon"` fields `ica_rtt_ms`, `ica_latency_ms`, `ica_bandwidth_in`, `ica_bandwidth_out`, `session_id`, `user`, `vda_host`
- **SPL:**
```spl
index=xd_perfmon sourcetype="citrix:vda:perfmon" counter_name="ICA RTT"
| bin _time span=5m
| stats avg(counter_value) as avg_rtt, perc95(counter_value) as p95_rtt, max(counter_value) as max_rtt by vda_host, _time
| eval quality=case(p95_rtt<=150, "Optimal", p95_rtt<=300, "Acceptable", 1=1, "Degraded")
| where quality="Degraded"
| table _time, vda_host, avg_rtt, p95_rtt, max_rtt, quality
```
- **Implementation:** Collect ICA RTT performance counters from VDAs using the `TA-XD7-VDA` add-on (Citrix ICA Session performance object). Alternatively, poll the Monitor Service OData API `SessionMetrics` endpoint. The difference between ICA RTT and ICA Latency indicates application processing time on the session host — if ICA Latency is high but network latency is low, the VDA is overloaded. Alert on sustained p95 RTT above 300ms. Segment by delivery group and VDA host to identify whether the issue is endpoint-specific (user's network), VDA-specific (overloaded host), or site-wide (network infrastructure).
- **Visualization:** Line chart (ICA RTT over time by VDA), Heatmap (VDA x hour), Single value (fleet average RTT with color threshold).
- **CIM Models:** N/A

- **References:** [uberAgent UXM](https://splunkbase.splunk.com/app/1448)

---

### UC-2.6.3 · Citrix Connection Failure Analysis
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Connection failures prevent users from launching virtual desktops or published applications. Failures can occur at multiple stages: brokering (no available machines), power management (VM failed to start), registration (VDA not registered with controller), or HDX connection (protocol failure). Categorizing failures by type and correlating with infrastructure state enables rapid root-cause identification.
- **App/TA:** Template for Citrix XenDesktop 7 (`TA-XD7-Broker`), Citrix Monitor Service OData API
- **Data Sources:** `index=xd` `sourcetype="citrix:broker:events"` fields `connection_state`, `failure_reason`, `failure_type`, `delivery_group`, `machine_name`, `user`
- **SPL:**
```spl
index=xd sourcetype="citrix:broker:events" event_type="ConnectionFailure"
| bin _time span=15m
| stats count as failures, dc(user) as affected_users, values(failure_reason) as reasons by failure_type, delivery_group, _time
| where failures > 3
| sort -failures
| table _time, delivery_group, failure_type, failures, affected_users, reasons
```
- **Implementation:** Collect Broker Service events (Event IDs 1100–1199 for connection lifecycle) from Delivery Controllers. The Monitor Service OData API `ConnectionFailureLogs` endpoint provides structured failure data with `FailureType` (ClientConnectionFailure, MachineFailure, etc.) and `FailureReason`. Alert on: more than 3 failures in 15 minutes for any delivery group, any `MachineFailure` type (indicates infrastructure problem), or rising failure rates across the site. Correlate with machine power state and VDA registration status for root cause.
- **Visualization:** Bar chart (failures by type), Timeline (failure events), Table (recent failures with user and machine details).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-2.6.4 · VDA Machine Registration Health
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Virtual Delivery Agents must register with a Delivery Controller to receive user sessions. Unregistered VDAs are effectively offline — they cannot serve users and reduce available capacity. Mass deregistration events indicate controller failures, network issues, or VDA crashes. Monitoring the ratio of registered to total machines ensures session hosting capacity meets demand.
- **App/TA:** Template for Citrix XenDesktop 7 (`TA-XD7-Broker`), Citrix Monitor Service OData API
- **Data Sources:** `index=xd` `sourcetype="citrix:broker:events"` fields `machine_name`, `registration_state`, `delivery_group`, `catalog_name`, `fault_state`
- **SPL:**
```spl
index=xd sourcetype="citrix:broker:events" event_type="MachineStatus"
| stats latest(registration_state) as reg_state, latest(fault_state) as fault by machine_name, delivery_group
| stats count as total,
  sum(eval(if(reg_state="Registered", 1, 0))) as registered,
  sum(eval(if(reg_state="Unregistered", 1, 0))) as unregistered,
  sum(eval(if(fault!="None" AND fault!="", 1, 0))) as faulted by delivery_group
| eval reg_pct=round(registered/total*100,1)
| where reg_pct < 95 OR faulted > 0
| table delivery_group, total, registered, unregistered, faulted, reg_pct
```
- **Implementation:** Poll machine status from the Broker Service or Monitor Service OData API `Machines` endpoint. Track `RegistrationState` (Registered, Unregistered, Initializing) and `FaultState` (None, FailedToStart, StuckOnBoot, Unregistered, MaxCapacity). Alert when registration percentage drops below 95% for any delivery group. Alert immediately when more than 5 machines deregister within 5 minutes (mass deregistration = infrastructure problem). Correlate with controller health and hypervisor connectivity.
- **Visualization:** Single value (registration % with color), Bar chart (registered vs unregistered by delivery group), Table (unregistered machines with fault state).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-2.6.5 · Citrix Delivery Controller Service Health
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Citrix Delivery Controllers run multiple critical Windows services: Broker Service, Configuration Service, Host Service, Machine Creation Service, and others. If the Broker Service stops, no new sessions can be brokered. If both controllers in a site fail, the entire Citrix environment becomes unavailable. Monitoring service health on all controllers ensures rapid detection and failover.
- **App/TA:** Splunk Add-on for Microsoft Windows
- **Data Sources:** `index=xd_winevents` `sourcetype="WinEventLog:System"` fields `EventCode`, `service_name`, `service_state`, `host`
- **SPL:**
```spl
index=xd_winevents sourcetype="WinEventLog:System" EventCode=7036
  (service_name="Citrix Broker Service" OR service_name="Citrix Configuration Service"
  OR service_name="Citrix Host Service" OR service_name="CitrixMachineCreationService"
  OR service_name="Citrix Storefront*")
| eval status=if(match(Message, "running"), "Running", "Stopped")
| stats latest(status) as current_state, latest(_time) as last_change by host, service_name
| where current_state="Stopped"
| eval last_change_fmt=strftime(last_change, "%Y-%m-%d %H:%M:%S")
| table host, service_name, current_state, last_change_fmt
```
- **Implementation:** Deploy Splunk Universal Forwarder on all Delivery Controllers and monitor Windows System Event Log. Windows Event ID 7036 records service state changes ("entered the running/stopped state"). Track all Citrix-specific services. Alert immediately when any critical Citrix service enters the stopped state. Correlate across controllers — if the Broker Service stops on all controllers simultaneously, escalate as P1. Also monitor Event IDs 7031 (service crash) and 7034 (unexpected termination).
- **Visualization:** Status grid (service x controller), Timeline (state change events), Table (stopped services).
- **CIM Models:** N/A

- **References:** [Splunk Add-on for Microsoft Windows](https://splunkbase.splunk.com/app/742)

---

### UC-2.6.6 · Citrix Machine Power State Management
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability, Performance
- **Value:** Citrix Delivery Controllers manage VM power states through power policy schedules — powering on machines before business hours and off after hours to save resources. Failed power actions (VM failed to start, hypervisor timeout, stuck in boot) reduce available session capacity during peak hours. Monitoring power action success rates and queue depth ensures machines are ready when users arrive.
- **App/TA:** Template for Citrix XenDesktop 7 (`TA-XD7-Broker`)
- **Data Sources:** `index=xd` `sourcetype="citrix:broker:events"` fields `power_action`, `power_state`, `machine_name`, `delivery_group`, `action_result`
- **SPL:**
```spl
index=xd sourcetype="citrix:broker:events" event_type="PowerAction"
| bin _time span=1h
| stats sum(eval(if(action_result="Success", 1, 0))) as success,
  sum(eval(if(action_result="Failed", 1, 0))) as failed,
  sum(eval(if(action_result="Pending", 1, 0))) as pending,
  count as total by power_action, delivery_group, _time
| eval fail_pct=if(total>0, round(failed/total*100,1), 0)
| where failed > 0 OR pending > 10
| table _time, delivery_group, power_action, total, success, failed, pending, fail_pct
```
- **Implementation:** The Broker Service logs power management actions with Event IDs in the 2000–3000 range. Track power actions (TurnOn, TurnOff, Shutdown, Reset, Restart) and their results (Success, Failed, Pending, Canceled). The Broker throttles power actions per hypervisor connection to avoid overloading — a large pending queue indicates throttling bottleneck or hypervisor slowness. Alert on: any failed power actions, pending queue exceeding 10 actions (backlog), or power-on failures during scheduled scale-out windows. Use `Get-BrokerHostingPowerAction` via PowerShell scripted input for real-time queue visibility.
- **Visualization:** Timechart (power actions by result), Bar chart (failures by delivery group), Single value (pending queue depth).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-2.6.7 · ICA/HDX Virtual Channel Bandwidth Consumption
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance, Capacity
- **Value:** HDX sessions use multiple virtual channels — graphics, audio, video, printer redirection, drive mapping, clipboard, and USB. Excessive bandwidth consumption on specific channels (e.g., large print jobs, multimedia redirection, USB device streaming) degrades the session experience for all users on the same VDA or network segment. Identifying bandwidth-heavy channels enables targeted policy optimization.
- **App/TA:** Template for Citrix XenDesktop 7 (`TA-XD7-VDA`)
- **Data Sources:** `index=xd_perfmon` `sourcetype="citrix:vda:perfmon"` fields `counter_name`, `counter_value`, `instance_name`, `vda_host`
- **SPL:**
```spl
index=xd_perfmon sourcetype="citrix:vda:perfmon"
  (counter_name="Output Bandwidth*" OR counter_name="Input Bandwidth*")
| bin _time span=15m
| stats avg(counter_value) as avg_bw_bps by instance_name, counter_name, vda_host, _time
| eval avg_bw_kbps=round(avg_bw_bps/1024, 1)
| where avg_bw_kbps > 500
| sort -avg_bw_kbps
| table _time, vda_host, instance_name, counter_name, avg_bw_kbps
```
- **Implementation:** Collect HDX virtual channel performance counters from VDAs. The Citrix ICA Session performance object exposes per-channel bandwidth metrics (Graphics, Audio, Printing, Drive Mapping, Clipboard, etc.). Alert on abnormal channel bandwidth: graphics channel above 5 Mbps sustained (possible unoptimized video), printing channel spikes (large print jobs), or drive mapping spikes (file copy operations). Use to tune HDX policies: enable adaptive transport, configure video codec, set print quality limits.
- **Visualization:** Stacked area chart (bandwidth by channel), Table (top bandwidth consumers), Bar chart (channel comparison by VDA).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-2.6.8 · Citrix Provisioning Services (PVS) vDisk Streaming Health
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Availability, Performance
- **Value:** In PVS-provisioned environments, target devices boot and run entirely from vDisk images streamed over the network. If PVS streaming degrades — due to network congestion, PVS server overload, or storage bottlenecks — target devices experience slow boot times, application hangs, and blue screens. Monitoring PVS streaming health ensures the foundation of the VDI environment remains solid. Write cache exhaustion on target devices is particularly dangerous as it causes immediate device failure.
- **App/TA:** Splunk Universal Forwarder on PVS servers, PowerShell scripted input via PVS MCLI
- **Data Sources:** `index=xd` `sourcetype="citrix:pvs:stream"` fields `pvs_server`, `target_device`, `vdisk_name`, `boot_time_sec`, `retries`, `cache_used_pct`, `cache_type`, `status`
- **SPL:**
```spl
index=xd sourcetype="citrix:pvs:stream"
| stats latest(status) as device_status, latest(boot_time_sec) as boot_sec, latest(retries) as retries, latest(cache_used_pct) as cache_pct by target_device, pvs_server, vdisk_name
| where device_status!="Active" OR boot_sec > 120 OR retries > 50 OR cache_pct > 80
| eval risk=case(cache_pct>90, "Critical-CacheExhaustion", device_status!="Active", "Offline", boot_sec>120, "SlowBoot", retries>50, "HighRetries", 1=1, "Warning")
| sort -cache_pct
| table target_device, pvs_server, vdisk_name, device_status, boot_sec, retries, cache_pct, risk
```
- **Implementation:** Deploy a Splunk Universal Forwarder on PVS servers and collect Stream Service event logs (enable event logging on each PVS server's Stream Service). Additionally, create a PowerShell scripted input using PVS MCLI commands (`Mcli-Get Device`, `Mcli-Get DiskVersion`) to collect target device status, boot times, retry counts, and write cache utilization. Alert on: boot times exceeding 120 seconds, stream retry counts above 50 (network/disk issues), write cache utilization above 80% (imminent exhaustion), or target devices dropping to inactive status. Monitor vDisk lock status to detect orphan locks preventing updates.
- **Visualization:** Table (target devices with health metrics), Gauge (write cache utilization), Bar chart (boot times by PVS server).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-2.6.9 · Citrix Profile Management Load Time
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Citrix User Profile Management (UPM) loads user profiles at session logon — including registry hives, application settings, and redirected folders. Large or corrupted profiles cause logon delays that can extend login times by minutes. Profile streaming can significantly reduce load times (from 54 seconds to 20 seconds in Citrix tests), but only if properly configured. Monitoring profile load times identifies users with bloated profiles and validates that profile optimization features are effective.
- **App/TA:** Splunk Universal Forwarder on VDAs, Citrix UPM log collection
- **Data Sources:** `index=xd` `sourcetype="citrix:upm:log"` fields `user`, `profile_load_time_sec`, `profile_size_mb`, `streaming_enabled`, `error_message`, `vda_host`
- **SPL:**
```spl
index=xd sourcetype="citrix:upm:log" event_type="ProfileLoad"
| bin _time span=1h
| stats avg(profile_load_time_sec) as avg_load, perc95(profile_load_time_sec) as p95_load, avg(profile_size_mb) as avg_size, count as loads by vda_host, _time
| where p95_load > 15
| table _time, vda_host, loads, avg_load, p95_load, avg_size
```
- **Implementation:** Citrix Profile Management logs to `%SystemRoot%\System32\LogFiles\UserProfileManager` on each VDA. Configure centralized log storage via UPM policy (store logs on a network share). Forward these logs to Splunk via Universal Forwarder. Parse for profile load/unload timing events. Track profile size growth per user over time. Alert on: p95 profile load time exceeding 15 seconds, individual profiles exceeding 500 MB, or UPM errors indicating profile corruption ("Error while processing profile" events). Validate that profile streaming is enabled and effective by comparing load times with/without streaming.
- **Visualization:** Line chart (profile load time trending), Bar chart (top users by profile size), Table (slow profile loads with user details).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-2.6.10 · Citrix StoreFront Authentication and Enumeration Health
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability, Performance
- **Value:** Citrix StoreFront authenticates users and enumerates available applications and desktops before the session launch process even begins. StoreFront failures manifest as users seeing a blank application list or receiving authentication errors. Since StoreFront runs on IIS, monitoring IIS response codes, authentication success rates, and enumeration latency provides early warning of issues that block all user access.
- **App/TA:** Splunk Add-on for Microsoft IIS
- **Data Sources:** `index=xd` `sourcetype="ms:iis:auto"` fields `cs_uri_stem`, `sc_status`, `time_taken`, `cs_username`, `s_computername`
- **SPL:**
```spl
index=xd sourcetype="ms:iis:auto" s_sitename="*StoreFront*"
| bin _time span=5m
| stats sum(eval(if(sc_status>=500, 1, 0))) as server_errors,
  sum(eval(if(sc_status=401, 1, 0))) as auth_failures,
  sum(eval(if(sc_status>=200 AND sc_status<400, 1, 0))) as success,
  avg(time_taken) as avg_response_ms, count as total by s_computername, _time
| eval error_pct=round(server_errors/total*100,1)
| eval auth_fail_pct=round(auth_failures/total*100,1)
| where error_pct > 5 OR auth_fail_pct > 20 OR avg_response_ms > 5000
| table _time, s_computername, total, success, server_errors, error_pct, auth_failures, auth_fail_pct, avg_response_ms
```
- **Implementation:** Install the Splunk Add-on for Microsoft IIS on StoreFront servers. StoreFront uses a custom IIS log field order — adjust the `auto_kv_for_iis_default` transform field list per Splunk's Content Pack documentation. Monitor HTTP status codes: 401 (authentication failure), 500+ (server errors), and response times. Key URIs to track: `/Citrix/StoreWeb/` (web interface), `/Citrix/Store/resources/` (resource enumeration), `/Citrix/Authentication/` (auth endpoint). Alert on server error rate exceeding 5% or authentication failure rate exceeding 20%. Correlate StoreFront errors with Active Directory health and Delivery Controller connectivity.
- **Visualization:** Timechart (requests by status code), Bar chart (error rates by StoreFront server), Table (slowest requests).
- **CIM Models:** Web
- **CIM SPL:**
```spl
| tstats summariesonly=t count from datamodel=Web.Web by Web.status, Web.http_method, Web.dest span=5m | sort - count
```

- **References:** [CIM: Web](https://docs.splunk.com/Documentation/CIM/latest/User/Web)

---

### UC-2.6.11 · Citrix License Server Utilization and Compliance
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity, Compliance
- **Value:** Citrix licensing is capacity-based — concurrent user/device licenses or per-user/per-device named licenses. Approaching license limits during peak hours causes session launch failures with "no licenses available" errors. While Citrix provides a grace period, operating within grace period indicates a compliance gap. Trending license utilization supports procurement planning and ensures continuous service availability.
- **App/TA:** Splunk Universal Forwarder on License Server, PowerShell scripted input
- **Data Sources:** `index=xd` `sourcetype="citrix:licensing"` fields `license_type`, `in_use`, `total`, `available`, `grace_period_active`, `expiration_date`
- **SPL:**
```spl
index=xd sourcetype="citrix:licensing"
| stats latest(in_use) as used, latest(total) as total, latest(available) as available, latest(grace_period_active) as grace, latest(expiration_date) as expiry by license_type
| eval utilization_pct=round(used/total*100,1)
| eval days_to_expiry=round((strptime(expiry, "%Y-%m-%d")-now())/86400,0)
| where utilization_pct > 80 OR grace="true" OR days_to_expiry < 90
| table license_type, used, total, available, utilization_pct, grace, days_to_expiry
```
- **Implementation:** Create a PowerShell scripted input on the Citrix License Server that queries license usage via `Get-LicInventory` and `Get-LicUsage` cmdlets or the Citrix Licensing WMI provider. Collect total licenses, in-use count, available count, grace period status, and license expiration dates. Run every 15 minutes. Alert at 80% utilization (capacity planning), 90% (operational warning), and immediately if grace period becomes active. Also alert 90 days before license expiration. Track peak utilization by hour and day of week for procurement planning.
- **Visualization:** Gauge (license utilization %), Timechart (license usage over time), Table (license types with expiry dates).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-2.6.12 · Citrix Application Usage and Popularity Analytics
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Capacity, Analytics
- **Value:** Understanding which published applications are most used, by which user groups, and at what times enables informed capacity planning, application retirement decisions, and license optimization. Applications with zero usage can be decommissioned to reduce attack surface and management overhead. High-usage applications may need dedicated delivery groups or additional server capacity.
- **App/TA:** Template for Citrix XenDesktop 7 (`TA-XD7-Broker`), Citrix Monitor Service OData API
- **Data Sources:** `index=xd` `sourcetype="citrix:broker:events"` fields `app_name`, `user`, `delivery_group`, `session_duration_min`
- **SPL:**
```spl
index=xd sourcetype="citrix:broker:events" event_type="ApplicationLaunch"
| bin _time span=1d
| stats dc(user) as unique_users, count as launches, avg(session_duration_min) as avg_duration by app_name, _time
| sort -unique_users
| table _time, app_name, unique_users, launches, avg_duration
```
- **Implementation:** Collect application launch events from the Broker Service event log or Monitor Service OData API `ApplicationInstances` endpoint. Track application name, launching user, delivery group, and session duration. Generate weekly reports showing: most-used applications (by unique users and total launches), least-used applications (candidates for retirement), peak usage hours per application, and average session duration. Correlate with license costs per application for ROI analysis.
- **Visualization:** Bar chart (top applications by users), Heatmap (application usage by hour), Table (unused applications).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-2.6.13 · Citrix Federated Authentication Service (FAS) Certificate Health
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Security, Availability
- **Value:** Citrix FAS dynamically issues short-lived certificates that allow users to log on to VDA sessions as if they had a smart card — enabling passwordless SSO from StoreFront via SAML or other federated identity providers. If FAS cannot reach the Certificate Authority or certificate signing takes too long, user authentication fails entirely. FAS is a privileged component with access to private keys, making its security monitoring equally critical.
- **App/TA:** Splunk Universal Forwarder on FAS servers
- **Data Sources:** `index=xd` `sourcetype="citrix:fas:events"` fields `event_type`, `user`, `certificate_status`, `signing_time_ms`, `ca_server`, `error_message`
- **SPL:**
```spl
index=xd sourcetype="citrix:fas:events"
| bin _time span=15m
| stats sum(eval(if(certificate_status="Issued", 1, 0))) as issued,
  sum(eval(if(certificate_status="Failed", 1, 0))) as failed,
  avg(signing_time_ms) as avg_sign_ms, max(signing_time_ms) as max_sign_ms by ca_server, _time
| eval fail_pct=if((issued+failed)>0, round(failed/(issued+failed)*100,1), 0)
| where failed > 0 OR avg_sign_ms > 2000
| table _time, ca_server, issued, failed, fail_pct, avg_sign_ms, max_sign_ms
```
- **Implementation:** Deploy a Splunk Universal Forwarder on FAS servers and collect the Citrix FAS application event log. FAS logs certificate issuance attempts, CA connectivity status, and certificate signing operations. Monitor for: certificate issuance failures (CA unreachable, template misconfigured), slow certificate signing (>2 seconds impacts logon), RA certificate expiration (FAS's own registration authority certificate), and unauthorized certificate requests. FAS PowerShell cmdlets (`Get-FasRaCertificateMonitor`, `Test-FasUserCertificateCrypto`) can be used via scripted inputs for proactive health checks. Alert immediately on any certificate issuance failure as it blocks user authentication.
- **Visualization:** Timechart (certificate issuance success vs failure), Single value (current CA reachability), Table (failed certificate requests with error details).
- **CIM Models:** Authentication
- **CIM SPL:**
```spl
| tstats summariesonly=t count from datamodel=Authentication.Authentication by Authentication.action, Authentication.user, Authentication.src span=15m | sort - count
```

- **References:** [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)

---

### UC-2.6.14 · Citrix Workspace Environment Management (WEM) Optimization Effectiveness
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Citrix WEM uses CPU spike protection and CPU clamping to prevent individual processes from monopolizing session host resources. Monitoring WEM optimization actions reveals which processes trigger CPU throttling, how often protection engages, and whether the configured thresholds are appropriate. Excessive WEM interventions may indicate undersized VDAs or resource-hungry applications that need attention.
- **App/TA:** Splunk Universal Forwarder on VDAs, WEM agent logs
- **Data Sources:** `index=xd` `sourcetype="citrix:wem:agent"` fields `action_type`, `process_name`, `cpu_threshold`, `duration_sec`, `user`, `vda_host`
- **SPL:**
```spl
index=xd sourcetype="citrix:wem:agent" (action_type="CpuSpikeProtection" OR action_type="CpuClamping")
| bin _time span=1h
| stats count as interventions, dc(process_name) as unique_processes, dc(user) as affected_users, values(process_name) as throttled_processes by action_type, vda_host, _time
| where interventions > 10
| table _time, vda_host, action_type, interventions, unique_processes, affected_users, throttled_processes
```
- **Implementation:** Collect WEM agent logs from VDAs. The WEM agent logs CPU spike protection events (process priority lowered) and CPU clamping events (process throttled) with the offending process name, CPU threshold that was exceeded, and duration of the intervention. Alert when a single VDA experiences more than 10 WEM interventions per hour (indicates capacity issue). Track the most frequently throttled processes — these are candidates for application optimization, isolation to dedicated delivery groups, or VDA resource increases. Compare WEM intervention frequency before and after VDA resource changes to validate capacity additions.
- **Visualization:** Bar chart (top throttled processes), Timechart (WEM interventions over time), Table (VDAs with most frequent interventions).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-2.6.15 · Citrix Session Recording Compliance Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance, Security
- **Value:** Citrix Session Recording captures video recordings of user sessions for compliance auditing in regulated industries (healthcare, finance, government). Monitoring ensures that recording policies are consistently applied — sessions that should be recorded are being recorded, storage capacity is adequate, and recordings maintain integrity via digital signatures. Gaps in recording coverage represent compliance violations.
- **App/TA:** Splunk Universal Forwarder on Session Recording servers
- **Data Sources:** `index=xd` `sourcetype="citrix:sessionrecording"` fields `recording_status`, `session_id`, `user`, `policy_name`, `file_size_mb`, `storage_used_pct`, `signed`
- **SPL:**
```spl
index=xd sourcetype="citrix:sessionrecording"
| stats sum(eval(if(recording_status="Recording", 1, 0))) as active_recordings,
  sum(eval(if(recording_status="Failed", 1, 0))) as failed_recordings,
  sum(file_size_mb) as total_storage_mb, latest(storage_used_pct) as storage_pct,
  sum(eval(if(signed="false", 1, 0))) as unsigned by policy_name
| eval fail_pct=if((active_recordings+failed_recordings)>0, round(failed_recordings/(active_recordings+failed_recordings)*100,1), 0)
| where failed_recordings > 0 OR storage_pct > 80 OR unsigned > 0
| table policy_name, active_recordings, failed_recordings, fail_pct, total_storage_mb, storage_pct, unsigned
```
- **Implementation:** Deploy a Splunk Universal Forwarder on Session Recording servers to collect session recording events and storage metrics. Monitor for: recording failures (disk full, agent disconnected, policy misconfiguration), storage capacity approaching limits (>80%), unsigned recordings (integrity concern), and sessions matching recording policy criteria that were not actually recorded (coverage gap). Generate daily compliance reports listing all recorded sessions by user, duration, and policy applied. Required for PCI DSS, HIPAA, and SOX environments where privileged access monitoring is mandated.
- **Visualization:** Single value (recording compliance %), Gauge (storage utilization), Table (failed recordings with error details).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-2.6.16 · Citrix Cloud Connector Health
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** For Citrix DaaS (cloud-managed) deployments, Cloud Connectors are the link between on-premises resources and Citrix Cloud. If all Cloud Connectors in a resource location fail, the site enters Local Host Cache (LHC) mode with limited functionality — no new machine registrations, no power management, and no access to cloud-hosted services. Monitoring connector health ensures continuous cloud management connectivity.
- **App/TA:** Splunk Universal Forwarder on Cloud Connector hosts
- **Data Sources:** `index=xd` `sourcetype="citrix:cloudconnector"` fields `connector_host`, `connectivity_status`, `last_contact`, `service_status`, `resource_location`
- **SPL:**
```spl
index=xd sourcetype="citrix:cloudconnector"
| stats latest(connectivity_status) as cloud_status, latest(service_status) as svc_status, latest(_time) as last_seen by connector_host, resource_location
| eval hours_since_contact=round((now()-last_seen)/3600, 1)
| where cloud_status!="Connected" OR svc_status!="Running" OR hours_since_contact > 1
| table connector_host, resource_location, cloud_status, svc_status, hours_since_contact
```
- **Implementation:** Deploy a Splunk Universal Forwarder on Cloud Connector hosts and monitor Windows Event Logs for Citrix Cloud Connector events. Also run the Cloud Health Check utility via scheduled PowerShell scripted input to validate connectivity to Citrix Cloud services. Track connectivity status (Connected, Disconnected), service health, and last successful cloud contact time. Alert when: any connector loses cloud connectivity for more than 15 minutes, all connectors in a resource location become disconnected (LHC mode imminent), or Cloud Connector services stop. Ensure at least 2 connectors per resource location for redundancy.
- **Visualization:** Status grid (connector x resource location), Timeline (connectivity events), Single value (connected connectors count).
- **CIM Models:** N/A

- **References:** [uberAgent indexer app](https://splunkbase.splunk.com/app/2998), [Splunkbase app 1448](https://splunkbase.splunk.com/app/1448)

---

#### 2.6 uberAgent UXM — Digital Employee Experience

**Splunk App:** uberAgent UXM (Splunkbase 1448, searchhead), uberAgent indexer app (Splunkbase 2998), uberAgent Helpdesk App (free). uberAgent is now a Citrix product and the recommended endpoint monitoring agent for CVAD environments. Deployed on VDAs and endpoints, it sends telemetry to Splunk via HEC or Universal Forwarder.

### UC-2.6.17 · uberAgent Experience Score Monitoring

- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** uberAgent's Experience Score is a composite 0–10 metric that summarises the end-user experience across multiple dimensions — session responsiveness, application performance, logon speed, and machine health. A single score per user per session makes it possible to answer "how is the Citrix experience right now?" without inspecting dozens of individual metrics. Score drops correlate directly with helpdesk call volume.
- **App/TA:** uberAgent UXM (Splunkbase 1448)
- **Equipment Models:** Windows VDAs, Citrix CVAD / DaaS
- **Data Sources:** `index=score_uberagent_uxm` — Experience Scores are calculated by saved searches on the search head and stored in a dedicated Splunk index.
- **SPL:**
```spl
index=score_uberagent_uxm earliest=-4h
| search ScoreType="overall"
| bin _time span=30m
| stats avg(Score) as avg_score perc10(Score) as p10_score dc(Host) as hosts by _time
| eval quality=case(avg_score>=7, "Good", avg_score>=4, "Medium", 1=1, "Bad")
| table _time, avg_score, p10_score, hosts, quality
```
- **Implementation:** uberAgent UXM calculates Experience Scores via saved searches that run every 30 minutes on the search head, evaluating machine, session, and application health. Scores are stored in the `score_uberagent_uxm` index. No additional agent configuration is required beyond uberAgent deployment. Alert when the fleet-wide average drops below 4 (bad) or when p10 drops below 4. The score dashboard is the default entry point of the uberAgent UXM Splunk app. Score thresholds can be customised via lookup files (`score_machine_configuration.csv`, `score_session_configuration.csv`, `score_application_configuration.csv`).
- **Visualization:** Line chart (score over time), Gauge (fleet average), Heatmap (delivery group x hour), Table (worst-scoring users).
- **CIM Models:** N/A

- **References:** [uberAgent UXM](https://splunkbase.splunk.com/app/1448)

---

### UC-2.6.18 · Application Unresponsiveness (UI Hangs) Detection

- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Application hangs — where the UI becomes unresponsive and shows "Not Responding" — are a major source of user frustration in CVAD sessions. Unlike crashes, hangs don't generate Windows Error Reporting events and are invisible to most monitoring tools. uberAgent detects them in real-time by monitoring message pump responsiveness, capturing which application hung, for how long, and what the user was doing.
- **App/TA:** uberAgent UXM (Splunkbase 1448)
- **Equipment Models:** Windows VDAs, Windows endpoints
- **Data Sources:** `sourcetype="uberAgent:Application:UIDelay"`
- **SPL:**
```spl
index=uberagent sourcetype="uberAgent:Application:UIDelay" earliest=-24h
| stats count as hang_count avg(UIDelayDurationMs) as avg_hang_ms max(UIDelayDurationMs) as max_hang_ms dc(User) as affected_users by AppName, AppVersion
| where hang_count > 5
| eval avg_hang_sec=round(avg_hang_ms/1000,1)
| sort -hang_count
| table AppName, AppVersion, hang_count, avg_hang_sec, affected_users
```
- **Implementation:** uberAgent detects UI unresponsiveness automatically. No special configuration required. Use the data to identify problematic applications, correlate hangs with VDA resource contention (CPU, memory), and prioritise application remediation. Alert when a single application generates more than 20 hangs per hour across the fleet.
- **Visualization:** Bar chart (hangs by application), Line chart (hang frequency over time), Table (worst applications with user impact).
- **CIM Models:** N/A

- **References:** [uberAgent UXM](https://splunkbase.splunk.com/app/1448)

---

### UC-2.6.19 · Application Startup Duration Tracking

- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** How long applications take to become usable after launch directly impacts perceived performance. A user launching Outlook, SAP, or a browser expects it within seconds. uberAgent measures the time from process start to the application window being interactive, capturing real user-perceived startup times rather than just process creation. Slow startups indicate disk I/O contention, antivirus interference, or application configuration issues.
- **App/TA:** uberAgent UXM (Splunkbase 1448)
- **Equipment Models:** Windows VDAs, Windows endpoints
- **Data Sources:** `sourcetype="uberAgent:Process:ProcessStartup"`
- **SPL:**
```spl
index=uberagent sourcetype="uberAgent:Process:ProcessStartup" earliest=-24h
| stats avg(StartupTimeMs) as avg_startup_ms perc95(StartupTimeMs) as p95_startup_ms count as launches dc(User) as users by AppName
| eval avg_startup_sec=round(avg_startup_ms/1000,1), p95_startup_sec=round(p95_startup_ms/1000,1)
| where p95_startup_sec > 10
| sort -p95_startup_sec
| table AppName, launches, users, avg_startup_sec, p95_startup_sec
```
- **Implementation:** uberAgent measures startup duration automatically for all applications. Baseline normal startup times per application. Alert when p95 startup exceeds thresholds (e.g., >10s for Outlook, >15s for SAP). Trend over time to detect regression after updates or image changes.
- **Visualization:** Bar chart (p95 startup by app), Line chart (startup trending), Table (slowest applications).
- **CIM Models:** N/A

- **References:** [uberAgent UXM](https://splunkbase.splunk.com/app/1448)

---

### UC-2.6.20 · Browser Performance per Web Application

- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Many Citrix-delivered workloads are browser-based (SaaS applications, internal portals). uberAgent's browser extensions measure page load time, network latency, and rendering performance per website/URL. This reveals whether slow web application performance is due to the Citrix session, the network, or the web application itself — a critical distinction for troubleshooting.
- **App/TA:** uberAgent UXM (Splunkbase 1448) + browser extension (Chrome, Edge, Firefox)
- **Equipment Models:** Windows VDAs with Chrome, Edge, or Firefox
- **Data Sources:** `sourcetype="uberAgent:Application:BrowserWebRequests2"`
- **SPL:**
```spl
index=uberagent sourcetype="uberAgent:Application:BrowserWebRequests2" earliest=-24h
| stats avg(PageLoadTotalDurationMs) as avg_load_ms perc95(PageLoadTotalDurationMs) as p95_load_ms count as page_loads dc(User) as users by Host
| eval avg_load_sec=round(avg_load_ms/1000,1), p95_load_sec=round(p95_load_ms/1000,1)
| where p95_load_sec > 5
| sort -p95_load_sec
| table Host, page_loads, users, avg_load_sec, p95_load_sec
```
- **Implementation:** Deploy the uberAgent browser extension via Group Policy or Citrix Studio. The extension collects W3C Navigation Timing API data per page load. Alert when key internal web applications (intranet, CRM, EHR) exceed acceptable page load thresholds. Segment by Citrix delivery group vs physical endpoint to compare performance.
- **Visualization:** Table (slowest websites), Line chart (page load trending), Bar chart (comparison by browser).
- **CIM Models:** N/A

- **References:** [uberAgent UXM](https://splunkbase.splunk.com/app/1448)

---

### UC-2.6.21 · Machine Boot and Shutdown Duration Analysis

- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** VDA boot time directly impacts how quickly machines become available after power-on events triggered by Citrix power management schedules. Slow boots delay session availability for early-morning users. uberAgent decomposes boot duration into phases (BIOS/firmware, kernel, drivers, services, boot processes) to identify bottlenecks — antivirus scans at boot, slow driver initialisation, or disk contention during mass power-on.
- **App/TA:** uberAgent UXM (Splunkbase 1448)
- **Equipment Models:** Windows VDAs (physical and virtual)
- **Data Sources:** `sourcetype="uberAgent:OnOffTransition:BootDetail2"`, `sourcetype="uberAgent:OnOffTransition:BootProcessDetail"`
- **SPL:**
```spl
index=uberagent sourcetype="uberAgent:OnOffTransition:BootDetail2" earliest=-7d
| stats avg(TotalBootTimeMs) as avg_boot_ms perc95(TotalBootTimeMs) as p95_boot_ms count as boots by Host
| eval avg_boot_sec=round(avg_boot_ms/1000,1), p95_boot_sec=round(p95_boot_ms/1000,1)
| where p95_boot_sec > 120
| sort -p95_boot_sec
| table Host, boots, avg_boot_sec, p95_boot_sec
```
- **Implementation:** uberAgent captures boot duration automatically on all endpoints. Correlate boot times with Citrix power management schedules (UC-2.6.6) to validate machines are ready when users arrive. Alert on VDAs with p95 boot time exceeding 2 minutes. Use boot process detail data to identify specific services or drivers causing delays.
- **Visualization:** Bar chart (boot time by VDA), Stacked bar (boot phases), Line chart (boot time trending).
- **CIM Models:** N/A

- **References:** [uberAgent UXM](https://splunkbase.splunk.com/app/1448)

---

### UC-2.6.22 · Per-Application CPU and Memory Consumption

- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance, Capacity
- **Value:** Identifying which applications consume the most CPU and memory on shared VDAs is essential for capacity planning and noisy-neighbour detection. A single user running an unoptimised macro or media-heavy application can degrade performance for all other sessions on the same VDA. uberAgent provides per-process, per-user resource consumption with application-level attribution.
- **App/TA:** uberAgent UXM (Splunkbase 1448)
- **Equipment Models:** Windows VDAs
- **Data Sources:** `sourcetype="uberAgent:Process:ProcessDetail"`
- **SPL:**
```spl
index=uberagent sourcetype="uberAgent:Process:ProcessDetail" earliest=-4h
| stats avg(ProcCPUPercent) as avg_cpu avg(WorkingSetMB) as avg_ram_mb by AppName, User, Host
| where avg_cpu > 25 OR avg_ram_mb > 500
| sort -avg_cpu
| table Host, User, AppName, avg_cpu, avg_ram_mb
```
- **Implementation:** uberAgent collects process-level resource metrics continuously. Identify top resource consumers per VDA and per user. Alert when a single user's process exceeds thresholds that impact co-hosted sessions. Feed into capacity planning: if average RAM per user session is 2 GB and VDAs have 64 GB, the safe session density is ~28 sessions.
- **Visualization:** Table (top consumers), Bar chart (CPU by application), Heatmap (user x VDA).
- **CIM Models:** Performance
- **CIM SPL:**
```spl
| tstats summariesonly=t avg(Performance.cpu_load_percent) as agg_value from datamodel=Performance.CPU by Performance.host | sort - agg_value
```

- **References:** [uberAgent UXM](https://splunkbase.splunk.com/app/1448), [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)

---

### UC-2.6.23 · Application Crash and Error Reporting

- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Fault
- **Value:** Application crashes in Citrix sessions cause data loss, user frustration, and helpdesk calls. uberAgent captures Windows Error Reporting (WER) crash data including the faulting module, exception code, and application version, enabling crash trending and root-cause identification across the fleet. Crash rate spikes after application or image updates indicate problematic deployments.
- **App/TA:** uberAgent UXM (Splunkbase 1448)
- **Equipment Models:** Windows VDAs, Windows endpoints
- **Data Sources:** `sourcetype="uberAgent:Application:Errors"`
- **SPL:**
```spl
index=uberagent sourcetype="uberAgent:Application:Errors" earliest=-7d
| stats count as crashes dc(User) as affected_users values(ExceptionCode) as exception_codes by AppName, AppVersion
| sort -crashes
| table AppName, AppVersion, crashes, affected_users, exception_codes
```
- **Implementation:** uberAgent captures crash data automatically from WER. Trend crash rates per application version to detect regressions. Alert on crash rate spikes (>200% increase over 7-day baseline). Correlate exception codes with known bugs and vendor advisories. Track crash resolution over time after patching.
- **Visualization:** Bar chart (crashes by application), Line chart (crash rate trending), Table (faulting modules).
- **CIM Models:** N/A

- **References:** [uberAgent UXM](https://splunkbase.splunk.com/app/1448)

---

### UC-2.6.24 · Citrix Site Delivery Group Capacity and Health

- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Capacity, Availability
- **Value:** uberAgent's Citrix Site Monitoring queries the Broker Service directly to provide real-time visibility into delivery group capacity — total machines, registered machines, active sessions, load index, and machines in maintenance mode. When available capacity drops below a threshold, new user connections may fail or be delayed.
- **App/TA:** uberAgent UXM (Splunkbase 1448) with Citrix Site Monitoring enabled
- **Equipment Models:** Citrix CVAD / DaaS site
- **Data Sources:** `sourcetype="uberAgent:Citrix:DesktopGroups"`
- **SPL:**
```spl
index=uberagent sourcetype="uberAgent:Citrix:DesktopGroups"
| stats latest(MachinesTotal) as total, latest(MachinesRegistered) as registered, latest(SessionsActive) as active, latest(MachinesInMaintenanceMode) as maint by DeliveryGroupName
| eval available=registered-active-maint, avail_pct=round(available/total*100,1)
| where avail_pct < 20 OR registered < total*0.8
| table DeliveryGroupName, total, registered, maint, active, available, avail_pct
| sort avail_pct
```
- **Implementation:** Enable uberAgent's Citrix Site Monitoring feature, which queries the Citrix Broker Service at configurable intervals. Alert when available capacity drops below 20% of total machines for any delivery group. Track session density trends for capacity planning. Correlate with VDA registration health (UC-2.6.4) for root cause.
- **Visualization:** Table (delivery group capacity), Gauge (available capacity %), Bar chart (session counts by group).
- **CIM Models:** N/A

- **References:** [uberAgent UXM](https://splunkbase.splunk.com/app/1448)

---

### UC-2.6.25 · Citrix NetScaler ADC Performance via uberAgent

- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance, Availability
- **Value:** uberAgent can monitor Citrix NetScaler (ADC) appliances via NITRO API without requiring a separate add-on on the ADC itself. This provides gateway session counts, SSL TPS, HTTP request rates, and system resource utilisation alongside endpoint and session data in the same Splunk index, enabling end-to-end correlation from ADC to VDA to application.
- **App/TA:** uberAgent UXM (Splunkbase 1448) with NetScaler Monitoring enabled
- **Equipment Models:** Citrix NetScaler / ADC (VPX, MPX, SDX, CPX)
- **Data Sources:** `sourcetype="uberAgent:CitrixADC:AppliancePerformance"`, `sourcetype="uberAgent:CitrixADC:vServer"`
- **SPL:**
```spl
index=uberagent sourcetype="uberAgent:CitrixADC:AppliancePerformance"
| stats latest(CPUUsagePct) as cpu latest(MemUsagePct) as mem latest(HttpRequestsPerSec) as http_rps latest(SSLTransactionsPerSec) as ssl_tps by ADCHost
| where cpu > 70 OR mem > 80
| table ADCHost, cpu, mem, http_rps, ssl_tps
```
- **Implementation:** Configure uberAgent's NetScaler monitoring with NITRO API credentials. This provides a unified data source — VDA performance, user sessions, and ADC health all in one index. Correlate ADC gateway session counts with VDA session capacity. Alert on ADC resource utilisation exceeding thresholds.
- **Visualization:** Single value (CPU, memory), Line chart (SSL TPS over time), Table (ADC fleet health).
- **CIM Models:** N/A

- **References:** [uberAgent UXM](https://splunkbase.splunk.com/app/1448)

---

### UC-2.6.26 · Per-Application Network Performance

- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** uberAgent measures network latency, data volume, and connection quality per application and per target host. This reveals which applications are generating the most network traffic, connecting to slow endpoints, or experiencing high latency — critical for optimising CVAD network policies and WAN bandwidth allocation.
- **App/TA:** uberAgent UXM (Splunkbase 1448) with Per-Application Network Monitoring
- **Equipment Models:** Windows VDAs, Windows endpoints
- **Data Sources:** `sourcetype="uberAgent:Process:NetworkTargetPerformance"`
- **SPL:**
```spl
index=uberagent sourcetype="uberAgent:Process:NetworkTargetPerformance" earliest=-4h
| stats avg(ConnectDurationMs) as avg_latency_ms sum(DataVolumeSentBytes) as bytes_sent sum(DataVolumeReceivedBytes) as bytes_rcvd dc(User) as users by AppName, NetworkTargetName
| eval total_mb=round((bytes_sent+bytes_rcvd)/1048576,1)
| where avg_latency_ms > 100 OR total_mb > 500
| sort -total_mb
| table AppName, NetworkTargetName, avg_latency_ms, total_mb, users
```
- **Implementation:** Enable uberAgent's per-application network monitoring feature. Identify bandwidth-heavy applications and high-latency network targets. Use to validate that HDX redirection policies are routing multimedia traffic efficiently. Detect applications bypassing proxy or connecting to unexpected external hosts.
- **Visualization:** Table (top bandwidth consumers), Bar chart (latency by target), Sankey diagram (app to network target flow).
- **CIM Models:** Network_Traffic
- **CIM SPL:**
```spl
| tstats summariesonly=t count from datamodel=Network_Traffic.All_Traffic by All_Traffic.action, All_Traffic.src, All_Traffic.dest, All_Traffic.dest_port | sort - count
```

- **References:** [uberAgent UXM](https://splunkbase.splunk.com/app/1448), [CIM: Network Traffic](https://docs.splunk.com/Documentation/CIM/latest/User/Network_Traffic)

---

### UC-2.6.27 · Endpoint Security Analytics (ESA) Threat Detection

- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Security
- **Value:** uberAgent ESA provides endpoint-level threat detection within Citrix sessions using Sigma rules, LOLBAS detection, process tampering monitoring, and file system activity analysis. In multi-user CVAD environments, a compromised session can laterally move to shared resources. ESA detects threats inside the session that network-based security tools cannot see.
- **App/TA:** uberAgent ESA (included with uberAgent UXM, Splunkbase 1448)
- **Equipment Models:** Windows VDAs, Windows endpoints
- **Data Sources:** `sourcetype="uberAgentESA:ActivityMonitoring:ProcessTagging"`, `sourcetype="uberAgent:Process:ProcessStartup"`
- **SPL:**
```spl
index=uberagent sourcetype="uberAgentESA:ActivityMonitoring:ProcessTagging" earliest=-24h
| stats count by RuleName, RuleSeverity, User, Host, ProcessName
| where RuleSeverity IN ("critical","high")
| sort -RuleSeverity, -count
| table Host, User, ProcessName, RuleName, RuleSeverity, count
```
- **Implementation:** Enable uberAgent ESA with default Sigma rule pack. Customise rules for Citrix-specific threats (e.g., lateral movement via published apps, credential dumping in shared sessions). Forward ESA events to Splunk Enterprise Security as notable events. The MITRE ATT&CK integration maps detections to tactics and techniques for SOC workflows.
- **Visualization:** Table (threat detections), Bar chart (by MITRE tactic), Timeline (detection events), Single value (critical alerts).
- **CIM Models:** Intrusion_Detection, Endpoint
- **CIM SPL:**
```spl
| tstats summariesonly=t count from datamodel=Intrusion_Detection.IDS_Attacks by IDS_Attacks.dest | sort - count
```

- **References:** [Splunkbase app 1448](https://splunkbase.splunk.com/app/1448), [Splunk Enterprise Security](https://splunkbase.splunk.com/app/263), [CIM: Intrusion Detection](https://docs.splunk.com/Documentation/CIM/latest/User/Intrusion_Detection)

---

### UC-2.6.28 · Local Host Cache (LHC) Sync Status and Mode Transitions
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Availability
- **Value:** Local Host Cache (LHC) allows Delivery Controllers to broker sessions when the site database is unreachable. Failures in sync, unexpected mode changes (to or from LHC), or lagging replication indicate risk of logon/brokering issues and split-brain scenarios. Alerting on Citrix High Availability Service events and correlating with broker events surfaces site-database outages and recovery before users see widespread failures.
- **App/TA:** Splunk Add-on for Microsoft Windows, Template for Citrix XenDesktop 7 (TA-XD7-Broker)
- **Data Sources:** `index=windows` (or your controller log index) `sourcetype="WinEventLog:Application"` `source="Citrix High Availability Service"`; optional correlation: `index=xd` `sourcetype="citrix:broker:events"` for controller health and brokering errors during outages
- **SPL:**
```spl
index=windows sourcetype="WinEventLog:Application" source="Citrix High Availability Service" earliest=-24h
| rex field=Message "(?i)mode[\s:]*(?<lhc_mode>\w+)|synchroni[sz]e|sync\s+lag|Local\s*Host\s*Cache|HA\s*state"
| eval ha_event=if(match(Message, "(?i)entering|switched|transition|outage|split.?brain|sync"), 1, 0)
| where ha_event=1
| stats count, earliest(_time) as first_seen, latest(_time) as last_seen by host, EventCode, Message
| sort - count
```
- **Implementation:** Ingest Windows Application log from all Delivery Controllers; confirm `source` and `sourcetype` for Citrix High Availability Service. Add field extractions for sync state, mode transition, and error text if Message format varies by version. Correlate with `citrix:broker:events` for registration and brokering errors. Tune noise from planned failovers. Document expected behavior during site DB maintenance so alerts can be suppressed via lookup.
- **Visualization:** Timeline (HA and mode events), Table (host, event text, first/last seen), Single value (count of critical HA errors).
- **CIM Models:** Change
- **Known false positives:** Planned site database maintenance and rehearsed LHC failovers intentionally flip the Citrix High Availability Service between modes and log transitions. Suppress on published SQL maintenance, then correlate with broker 'database unavailable' and controller pairing before a Sev-1 bridge.
- **Last reviewed:** 2026-04-24

- **References:** [Local Host Cache in Citrix Virtual Apps and Desktops](https://docs.citrix.com/en-us/citrix-virtual-apps-desktops-2112/manage-deployment/broker.html), [Splunk Add-on for Microsoft Windows](https://splunkbase.splunk.com/app/742)

---

### UC-2.6.29 · Machine Catalog Image Pipeline Health
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Machine Catalog health depends on current master images, successful preparation or rollout jobs, and timely rollouts. Stale images (>90 days without refresh), pending rollouts stuck in queue, and provisioning errors reduce pool reliability and can leave machines on vulnerable or non-compliant images. Polling the Monitor `MachineCatalog` OData feed gives a single place to see catalog-level status when broker events do not list every field.
- **App/TA:** Citrix Monitor Service OData API, Template for Citrix XenDesktop 7 (TA-XD7-Broker)
- **Data Sources:** `index=xd` `sourcetype="citrix:monitor:odata"` with OData entity scoping to `MachineCatalog` (e.g. `ODataEntity=MachineCatalog` or `entity_type=MachineCatalog`); fields may include `Name`, `MasterImageVhd`, `ProvisioningType`, `LastApplyImageDate`, `UsedCount`, `PendingTaskCount` depending on your TA field mapping
- **SPL:**
```spl
index=xd sourcetype="citrix:monitor:odata" (ODataEntity=MachineCatalog OR entity_type=MachineCatalog OR Name=*)
| eval master_age_days=if(isnotnull(LastImageUpdateTime) OR isnotnull(LastMasterImageTime), round((now()-coalesce(LastImageUpdateTime, LastMasterImageTime, _time)) / 86400, 1), null())
| eval rollout_pending=coalesce(PendingImageRollout, PendingUpdateCount, 0)
| where master_age_days > 90 OR rollout_pending > 0 OR match(coalesce(ProvisioningStatus, State, ErrorState), "(?i)fail|error")
| table _time, Name, ProvisioningType, master_age_days, rollout_pending, ProvisioningStatus, State, ErrorState, MasterImageVhd, host
| sort - master_age_days
```
- **Implementation:** Enable OData collection for Machine Catalog. Align field names to your add-on; use `fieldalias` in `props.conf` if the vendor uses `LastImageTime` instead of `LastMasterImageTime`. Set thresholds: image age 90+ days, any non-empty pending rollout counter for more than 24 hours, and any `Fail` in provisioning. Join to change tickets for image updates. Cross-check MCS/PVS UCs for prep failures on the same image name.
- **Visualization:** Table (catalogs at risk), Line chart (pending rollout trend), Single value (catalogs with stale images).
- **CIM Models:** Endpoint
- **Known false positives:** Large catalog republishes, image rollouts, and overnight MCS/PVS rewrites can emit sustained 'pipeline' errors while machines churn. Time-box alerts to the change ticket window and key on a failure rate that exceeds the last three similar publishes.
- **Last reviewed:** 2026-04-24

- **References:** [Monitor Citrix with OData](https://docs.citrix.com/en-us/citrix-virtual-apps-desktops-221/operations/monitor/odata-connector.html)

---

### UC-2.6.30 · MCS Provisioning and Identity Disk Health
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Availability
- **Value:** MCS relies on correct identity disk creation, image preparation queues, and healthy snapshot or differencing disk chains. Symptoms include rising provisioning task failures, deep snapshot chains, machines stuck in preparation, and mismatches between on-demand and power-managed capacity that stress storage and identity state. Correlating broker and Monitor data with platform metrics isolates whether Citrix, hypervisor, or storage is the bottleneck.
- **App/TA:** Citrix Monitor Service OData API, Template for Citrix XenDesktop 7 (TA-XD7-Broker), Citrix VDA/Monitor TA field mappings
- **Data Sources:** `index=xd` `sourcetype="citrix:monitor:odata"` (`Machines` / machine provisioning fields), `sourcetype="citrix:broker:events"` for `ProvisioningTask` / prep failures, `sourcetype="citrix:vda:events"` for identity or disk attach issues; `index=hyperv` or `index=vmware` optional for underlying snapshot/chain data if you collect it
- **SPL:**
```spl
index=xd (sourcetype="citrix:broker:events" event_type=Provisioning* OR match(_raw, "(?i)identity|prep|snapshot|MCS|Provision"))
     OR (sourcetype="citrix:monitor:odata" (ODataEntity=Machines OR ODataEntity=Machine) match(_raw, "(?i)identity|disk|provisioning|task"))
| eval fail=if(match(coalesce(result, ProvisioningState, State), "(?i)fail|error") OR match(_raw, "(?i)identity.*(fail|error)|disk.*(fail|error)"), 1, 0)
| bin _time span=15m
| stats count as evts, sum(fail) as fail_cnt, dc(host) as hosts, values(machine_name) as sample_machines by _time, catalog_name, delivery_group
| eval fail_rate=if(evts>0, round(100*fail_cnt/evts,2), 0)
| where fail_cnt>0 OR fail_rate > 5
| table _time, catalog_name, delivery_group, evts, fail_cnt, fail_rate, hosts, sample_machines
```
- **Implementation:** Ingest broker provisioning and OData machine rows. Normalize `machine_name`, `catalog_name`, and task outcome fields. For snapshot chain bloat, use hypervisor or storage feeds if available; otherwise track prep duration percentiles. Alert on sustained fail rate, queue depth, or `identity`/`prep` error strings. Segment by delivery group to assign ownership.
- **Visualization:** Stacked area (fail count over time by catalog), Table (top failing prep reasons), Bar chart (on-demand vs power-managed pool sizes).
- **CIM Models:** Endpoint
- **Known false positives:** Mass re-provision after a template update, identity disk reseal, or storage migration spikes MCS and identity disk errors in parallel. Correlation with the catalog job ID and the service account that runs image refresh is usually a planned burst, not random corruption.
- **Last reviewed:** 2026-04-24

- **References:** [Machine Creation Services (Citrix) - Provisioning](https://docs.citrix.com/en-us/citrix-virtual-apps-desktops-service/install-configure/mcs.html)

---

### UC-2.6.31 · Citrix Zone Topology and Zone Preference Failover
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Availability
- **Value:** Multi-zone CVAD sites route users to preferred zones; controllers and resources must register and broker in the right order. Unplanned failover traffic, inter-zone brokering storms, or machines registering outside their zone hint at network partitions, site misconfiguration, or loss of a preferred data path. Tracking zone-related broker events and preferred versus failover path selection shows topology stress before end-user latency spikes.
- **App/TA:** Template for Citrix XenDesktop 7 (TA-XD7-Broker), Citrix Monitor Service OData API
- **Data Sources:** `index=xd` `sourcetype="citrix:broker:events"` (zone change, brokering path, `ZoneName`, `PreferredController`, `Failover*`), `sourcetype="citrix:monitor:odata"` for `Zones` / `Controllers` if collected; `sourcetype="citrix:netscaler:syslog"` optional for GSLB/health probe correlation
- **SPL:**
```spl
index=xd sourcetype="citrix:broker:events" (match(_raw, "(?i)zone|failover|preferred|registration|chassis|data.?store|inter.?zone") OR event_type IN ("Zone*", "Registration", "Configuration"))
| eval zone=coalesce(ZoneName, zone_name, Zone)
| eval path=if(match(_raw, "(?i)failover|secondary|not.?preferred|alternate"), "failover_path", if(match(_raw, "(?i)preferred|primary|home.?zone"), "preferred_path", "other"))
| where isnotnull(zone) OR path!="other"
| bin _time span=5m
| stats count, values(event_type) as event_types, dc(host) as controller_count by _time, zone, path, delivery_group
| sort -_time, zone, path
```
- **Implementation:** Standardize `ZoneName` and delivery group in broker events. Create lookups for expected zone–delivery-group mappings. Alert when failover_path volume exceeds baseline, when zone membership churn appears, or when a zone has zero registered workers during business hours. Enrich with NetScaler or WAN metrics if you need proof of network cause.
- **Visualization:** Sankey or flow (preferred vs failover), Timeline (zone events), Table (anomalous delivery groups by zone).
- **CIM Models:** Change
- **Known false positives:** Disaster recovery drills, intentional zone-preference changes, and datacenter evacuations are supposed to move traffic between zones. Use a change or DR test calendar and compare against expected zone order before calling an unexpected topology fault.
- **Last reviewed:** 2026-04-24

- **References:** [Zones in Citrix Virtual Apps and Desktops](https://docs.citrix.com/en-us/citrix-virtual-apps-desktops/221/manage-deployment/zones.html)

---

### UC-2.6.32 · Hypervisor Connection Health Monitoring
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Delivery Controllers use hypervisor connections to start, stop, and snapshot virtual machines. VMware vCenter loss, Hyper-V/SCVMM permission errors, certificate trust issues, and storage path failures surface as brokering or power-management failures. Early detection from broker `hosting connection` events, combined with a thin layer of hypervisor health, prevents large-scale session capacity loss during certificate rotations or vCenter maintenance.
- **App/TA:** Template for Citrix XenDesktop 7 (TA-XD7-Broker), Splunk Add-on for VMware, Splunk Add-on for Microsoft Windows (Hyper-V)
- **Data Sources:** `index=xd` `sourcetype="citrix:broker:events"` fields `hosting_connection_name`, `hypervisor_type`, `connection_state`, `ssl_error`, `certificate`, `hostingunit`, `ErrorMessage` (naming may vary by TA); `index=vmware` `sourcetype="vmware:inv:host"` or vCenter health for `index=hyperv` `sourcetype="hyperv_host_health"` as optional corroboration
- **SPL:**
```spl
index=xd sourcetype="citrix:broker:events" match(_raw, "(?i)host(ing)?\s*connection|hypervisor|vCenter|Nutanix|XenServer|scvmm|cert|ssl|storage|connectivity")
| eval conn_state=coalesce(connection_state, ConnectionState, hypervisor_state, State)
| eval hc_name=coalesce(hosting_connection_name, HostingUnitName, HostConnection, catalog_hosting_unit)
| where match(coalesce(conn_state, ""), "(?i)unknown|unavail|error|down|loss|denied|auth|fail|cert|ssl") OR match(coalesce(ErrorMessage, Message, _raw), "(?i)ssl|cert|permission|unauthorized|down|unreachable|storage")
| stats earliest(_time) as first_evt, latest(_time) as last_evt, count, values(ErrorMessage) as last_errors by hc_name, host, conn_state
| sort - count
```
- **Implementation:** Map hosting connection event fields from your broker TA. For each `hosting_connection_name`, maintain a lookup for owner team and service window. Add optional append searches from `vmware` and `hyperv` indexes to enrich with upstream platform state. Alert on any new critical error type or sustained connection_state not `OK`.
- **Visualization:** Table (connection, state, first/last event), Map or swimlane (by hosting unit and hypervisor), Single value (count of bad connections).
- **CIM Models:** Application_State
- **Known false positives:** vCenter or Hyper-V host rolling reboots, storage path failover tests, and hypervisor agent upgrades can briefly sever host connections. Layer hypervisor and storage change records on top; treat Citrix-only warnings as false positives when hosts were in a known cluster upgrade.
- **Last reviewed:** 2026-04-24

- **References:** [Citrix - Connections and management interfaces](https://docs.citrix.com/en-us/citrix-virtual-apps-desktops/221/install-configure/connections-hypervisor.html)

---

### UC-2.6.33 · Citrix Autoscale Capacity Events
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity
- **Value:** Autoscale adjusts powered-on machine counts against load and time schedules. Stuck scale-out, aggressive scale-in, schedule drift, or throttled power actions create either idle unassigned capacity (cost) or under-provisioned pools (poor user experience). Aggregating autoscale- and power-related broker events and comparing with powered-on session counts from Monitor highlights drift and failed automation.
- **App/TA:** Template for Citrix XenDesktop 7 (TA-XD7-Broker), Citrix Monitor Service OData API
- **Data Sources:** `index=xd` `sourcetype="citrix:broker:events"` for autoscale, power, and schedule-related actions, `sourcetype="citrix:monitor:odata"` for `Autoscale*`, `DeliveryGroup`, or `Session` machine counts; optional `sourcetype="citrix:vda:events"` for power-on success after scale-out
- **SPL:**
```spl
index=xd sourcetype="citrix:broker:events" (match(_raw, "(?i)autoscale|power.?on|turn.?on|turn.?off|scale.?in|scale.?out|power.?action|capaci") OR event_type=Power* OR event_type=Autoscale*)
| eval direction=if(match(_raw, "(?i)scale.?out|turn.?on|add.*machine|increase"), "scale_out", if(match(_raw, "(?i)scale.?in|turn.?off|remove.*reduce"), "scale_in", "other"))
| eval dg=coalesce(delivery_group, DeliveryGroup, CatalogName)
| eval success=if(match(coalesce(result, action_result, state), "(?i)success|complete"), 1, if(match(coalesce(result, action_result, state), "(?i)fail|error|throttl|denied|pending"), 0, null()))
| bin _time span=15m
| stats count, sum(eval(if(success=1,1,0))) as success_hits, sum(eval(if(success=0,1,0))) as fail_hits, dc(machine_name) as machine_moves by _time, dg, direction
| where fail_hits>0 OR count>100
| table _time, dg, direction, count, success_hits, fail_hits, machine_moves
```
- **Implementation:** Confirm event strings for your CVAD/Cloud version. Build baselines of scale_out vs load per delivery group. Join OData `InUse*`, `Registered*`, and `Unassigned*`-style fields when available. Alert on high fail_hits, zero scale_out during a ramp when usage rises, and sustained unassigned high-water marks outside policy.
- **Visualization:** Column chart (scale events by direction), Timechart (in-use vs registered machines), Table (failed power actions with delivery group).
- **CIM Models:** Change, Performance
- **Known false positives:** Autoscale scale-out and scale-in during real peak logins and pilot capacity tests is normal economics, not a storm. Fire when scale is denied, pools hit a hard ceiling, or the schedule conflicts with a disabled or mis-set policy, not for every off-hours scale event.
- **Last reviewed:** 2026-04-24

- **References:** [Autoscale in Citrix DaaS](https://docs.citrix.com/en-us/citrix-daas-service/monitor/health-data/autoscale.html)

---

### UC-2.6.34 · Maintenance Mode and Drain Operations Tracking
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Maintenance mode and drain protect users during image updates, hypervisor work, and migrations. A large, unexpected, or long-lived maintenance footprint can silently reduce session capacity, especially if paired with autoscale. Tracking machines and delivery groups in maintenance and correlating with available capacity highlights operational drains versus true outages.
- **App/TA:** Template for Citrix XenDesktop 7 (TA-XD7-Broker), Citrix Monitor Service OData API
- **Data Sources:** `index=xd` `sourcetype="citrix:broker:events"` or `sourcetype="citrix:monitor:odata"` for `Machine` with `InMaintenanceMode`, `drain*`, or maintenance flags; `sourcetype="citrix:monitor:odata"` for `Session` or capacity counts to correlate drops
- **SPL:**
```spl
index=xd (sourcetype="citrix:monitor:odata" (ODataEntity=Machine* OR match(_raw, "(?i)Maintenance|drain|suspend")))
| eval mmode=if(match(coalesce(InMaintenanceMode, maintenance_mode, raw_flags), "(?i)true|1|yes|on"), 1, 0)
| eval dg=coalesce(delivery_group, DeliveryGroup, CatalogName)
| where mmode=1
| timechart span=1h sum(mmode) as machines_in_maint, dc(dg) as affected_groups, dc(MachineName) as affected_machines
```
- **Implementation:** Prefer OData or broker inventory that exposes maintenance state per machine. Add a change lookup to label known maintenance. Compare hourly capacity against baseline when `machines_in_maint` rises. Alert on maintenance outside approved windows or when drain exceeds a percentage of a delivery group without a ticket.
- **Visualization:** Stacked area (machines in maintenance by group), Bar chart (duration by catalog), Table (open maintenance with owner from lookup).
- **CIM Models:** Change
- **Known false positives:** Wide drain and maintenance windows for OS patching can flood the index with 'session not accepting' style messages across many machines. Suppress on maint tags per machine and escalate only on drain failures outside an approved change window or with rising broker reject errors.
- **Last reviewed:** 2026-04-24

- **References:** [Put machines in maintenance - Citrix](https://docs.citrix.com/en-us/citrix-daas/deployment-guides/put-machines-into-maintenance.html)

---

### UC-2.6.35 · Pre-Launch and Lingering Session Management
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Pre-launched and lingering sessions keep apps warm and retain user context, but they consume memory, session licenses, and power-managed capacity. Misconfigured idle timers, excessive pre-launch, or sessions stuck in disconnected state can exhaust pools and look like a capacity outage. Tuning visibility from broker and VDA events shows where session lifecycle policy diverges from design.
- **App/TA:** uberAgent UXM (Splunkbase 1448), Template for Citrix XenDesktop 7 (TA-XD7-Broker)
- **Data Sources:** `index=xd` `sourcetype="citrix:broker:events"` (session, idle, prelaunch, `SessionState`), `sourcetype="citrix:vda:events"` (disconnect, idle timer), `index=uberagent` `sourcetype="uberAgent:Session:SessionInfo"` or `sourcetype="uberAgent:Process:ProcessStartup"` for per-session process counts
- **SPL:**
```spl
index=xd sourcetype="citrix:broker:events" (match(_raw, "(?i)pre[\s-]*launch|lingering|ghost|idle|disc") OR event_type IN ("SessionDisconnect", "SessionInfo") OR match(event_type, "(?i)SessionPreLaunch"))
| eval session_type=if(match(_raw, "(?i)pre[\s-]*launch|prelaunch"), "prelaunch", if(match(_raw, "(?i)linger|disconnected|idle"), "idle_linger", "other"))
| where session_type!="other"
| bin _time span=1h
| stats count, dc(user) as users, values(session_id) as sample_sessions by _time, session_type, delivery_group, published_app
| table _time, session_type, delivery_group, published_app, count, users, sample_sessions
```
- **Implementation:** Map published app and user fields. For ghost capacity, also pull uberAgent session or host CPU to correlate pre-launch with sustained resource use. Compare counts against GPO- or policy-driven idle and disconnect timers. Alert when pre-launch or linger counts exceed rolling baselines, or when idle sessions outnumber active sessions in a business hour window.
- **Visualization:** Area chart (prelaunch vs idle_linger by group), Table (top published apps with linger), Donut (session type mix).
- **CIM Models:** Network_Sessions
- **Known false positives:** Pre-launch, disconnected-session timeout, and idle policies can leave long-lived sessions that look 'stuck' or 'lingering' by design. Baseline per delivery group, then alert when sessions exceed the documented GPO/Studio cap or when broker and VDA state disagree.
- **Last reviewed:** 2026-04-24

- **References:** [uberAgent UXM for Citrix](https://splunkbase.splunk.com/app/1448)

---

### UC-2.6.36 · Session Reliability and Auto Client Reconnect
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Session Reliability and Auto Client Reconnect mask brief network blips, but a rising ratio of full disconnects to successful reconnects indicates unstable paths, bad Wi-Fi, or gateway issues. VDA and broker events that mention WCF, keep-alives, reliability channels, and EDT/TCP flips, correlated with network-side syslogs, separate client-side noise from data-center incidents.
- **App/TA:** Template for Citrix XenDesktop 7 (TA-XD7-Broker), NetScaler/ADC syslog TA, uberAgent UXM (Splunkbase 1448) optional
- **Data Sources:** `sourcetype="citrix:vda:events"` and `sourcetype="citrix:broker:events"` for `Session`, `WCF`, or connection reset messages; `index=netscaler` or `sourcetype="citrix:netscaler:syslog"` for ICA/EDT drops on the gateway; optional `index=uberagent` for network and virtual channel health
- **SPL:**
```spl
index=xd (sourcetype="citrix:vda:events" OR sourcetype="citrix:broker:events") match(_raw, "(?i)session reliability|reconnect|WCF|keep.?alive|auto.?client|ACR|ICA.*reset|edt|tcp.*(drop|reset)|udp")
| eval evt=if(match(_raw, "(?i)reconnect|re.?establish|re.?connected|back online"), "reconnect", if(match(_raw, "(?i)disconnect|drop|reset|fail|unreachable"), "disrupt", "other"))
| where evt!="other"
| eval user=coalesce(user, UserName, ClientName)
| bin _time span=5m
| stats count, dc(user) as users by _time, evt, host, delivery_group
| sort -_time, count
```
- **Implementation:** Normalize VDA and broker time zones. For Citrix Cloud or hybrid, ensure universal forwarders label site id. Add optional `append` to NetScaler `citrix:netscaler:syslog` for the same time window. Compute reconnect success ratio: `reconnect` counts vs `disrupt` counts per 5m per delivery group, alert when disrupt exceeds baseline by 2x for 3 intervals.
- **Visualization:** Multi-series line (disrupt vs reconnect), Timeline (outages), Map or table of affected delivery groups per site.
- **CIM Models:** Network_Sessions
- **Known false positives:** Home users on WiFi, travel VPNs, and unstable cellular paths trigger Session Reliability and auto-reconnect in bulk during benign conditions. Split by site or network profile and raise on sustained reconnection failure for landline and office cohorts, not a single flapping home office.
- **Last reviewed:** 2026-04-24

- **References:** [Session Reliability in CVAD / HDX](https://docs.citrix.com/en-us/citrix-virtual-apps-desktops/221/hdx/session-reliability.html)

---

### UC-2.6.37 · HDX Adaptive Transport (EDT) and Graphics Mode
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance
- **Value:** HDX Adaptive Transport prefers UDP (EDT) for interactive traffic when the network is healthy, falling back to TCP when loss or delay is high. High packet loss, RTT, or constant fallback reduces perceived responsiveness and can force CPU-biased H.264/HEVC or software rendering, stressing hosts and user experience. uberAgent’s EDT and HDX remoting metrics complement Citrix VDA event strings on encoder choice and display pipeline pressure.
- **App/TA:** uberAgent UXM (Splunkbase 1448), optional Template for Citrix XenDesktop 7 (TA-XD7-Broker)
- **Data Sources:** `index=uberagent` `sourcetype="uberAgent:Network:NetworkPerformanceEDT"`, `sourcetype="uberAgent:Remoting:HDX*"` or `sourcetype="uberAgent:GPU:*"` for encoder or GPU use; `index=xd` `sourcetype="citrix:vda:events"` for graphics and transport fallback messages; optional `sourcetype="citrix:netscaler:syslog"` for UDP/ICA profile stats
- **SPL:**
```spl
index=uberagent (sourcetype="uberAgent:Network:NetworkPerformanceEDT" OR sourcetype="uberAgent:Remoting:HDX*") earliest=-1h
| eval loss_pct=coalesce(UDPPacketLossPercent, UdpPacketLoss, PacketLoss), latency_ms=coalesce(UDPRTTms, AvgRttMs, Latency), fallback=if(match(coalesce(Transport, Protocol), "(?i)tcp"),1,0)
| where loss_pct>2 OR latency_ms>150 OR fallback=1
| bin _time span=5m
| stats avg(loss_pct) as avg_loss, avg(latency_ms) as avg_rtt, sum(fallback) as fallbacks, dc(user) as users by _time, host, SessionId
| table _time, host, users, avg_loss, avg_rtt, fallbacks
```
- **Implementation:** Deploy uberAgent on VDAs with network and remoting data enabled. Add field extractions for your exact uberAgent 7.x/8.x field names. Side-by-side: run a VDA search for 'policy', 'H264', 'HEVC', or 'YUV' in `citrix:vda:events` for policy-driven changes. Set threshold bands by site (WAN vs LAN).
- **Visualization:** Dual-axis chart (loss vs RTT), Heatmap (hosts by time), Table (top sessions with fallback).
- **CIM Models:** Network_Traffic
- **Known false positives:** GPU driver rollouts, EDT pilot toggles, and switching graphics modes during golden-image updates can change transport and rendering counters without user-facing outage. Join to build or driver change tickets before treating EDT fallback as a production performance incident.
- **Last reviewed:** 2026-04-24

- **References:** [uberAgent documentation - HDX/EDT](https://uberagent.com/docs/)

---

### UC-2.6.38 · Universal Print Server Health and Printing Failures
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Citrix Universal Print Server offloads and compresses print traffic, but spooler instability, bad drivers, and printer auto-creation or mapping errors still break end-user print jobs. Monitoring Application and VDA event streams for spooler failures, print manager errors, and user-visible mapping failures differentiates a single bad queue from a site-wide print outage.
- **App/TA:** Splunk Add-on for Microsoft Windows, Template for Citrix XenDesktop 7 (TA-XD7-Broker), Citrix Universal Print Server documentation-based field extractions
- **Data Sources:** `sourcetype="citrix:vda:events"` (`WinEventLog:Application` or CtxPrint / spooler events on VDA/UPS), `sourcetype="WinEventLog:Application"` for Citrix Print Manager Service, `sourcetype="WinEventLog:System"` for spooler service stops; `index=windows` for Universal Print forwarders if used
- **SPL:**
```spl
index=windows OR index=xd (sourcetype="WinEventLog:Application" OR sourcetype="citrix:vda:events") (match(_raw, "(?i)Citrix.*Print|Universal Print|spooler|CtxPrint|render|driver|UPS") OR match(_raw, "(?i)printer.*(map|fail|error|offline)")) OR EventCode=808
| eval fail=if(match(_raw, "(?i)fail|error|not found|denied|offline|stuck|abort") OR match(Message, "(?i)fail|error"), 1, 0)
| eval role=if(match(_raw, "(?i)Universal Print Server|Citrix.*Print"),"UPS_VDA", "print_stack")
| where fail=1
| stats count, values(Message) as sample_msg, values(host) as hosts, earliest(_time) as first_seen, latest(_time) as last_seen by role, user, client_name, printer_name, EventCode
```
- **Implementation:** Ingest VDA/UPS and brokering hosts into indexes with CIM-agnostic `props.conf` for long Message fields. Add printer allow/deny list lookups. Correlate with NetScaler/ADC only if you split print by site. Throttle on EventCode+printer driver hash to find systemic driver regressions. Alert when distinct hosts with fail=1 in 15m exceeds 3.
- **Visualization:** Table (failures with sample message), Pie chart (fail by driver or queue), Bar chart (failures per site).
- **CIM Models:** Application_State
- **Known false positives:** Print driver upgrades, spooler restarts, and file-server maintenance on universal print or print servers can look like mass print failures. Align spikes with print infrastructure change windows; exclude known patch waves before rerouting a Citrix SEV to the EUC team alone.
- **Last reviewed:** 2026-04-24

- **References:** [Universal Print Server - Citrix](https://docs.citrix.com/en-us/citrix-virtual-apps-desktops/221/print/ups.html)

---

### UC-2.6.39 · USB and Peripheral Redirection Failures
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** USB, scanner, and smart card redirection, plus client drive mapping and clipboard, depend on VDA services, client versions, and Citrix/Windows policies. Failures are often per-device or per-user but can spike when a new policy, endpoint agent, or firmware change blocks channels. VDA and Application logs capture the denial reason, while optional uberAgent peripheral metrics confirm drop-off in hardware attach success rates.
- **App/TA:** Template for Citrix XenDesktop 7 (TA-XD7-Broker), Splunk Add-on for Microsoft Windows, optional uberAgent UXM (Splunkbase 1448)
- **Data Sources:** `sourcetype="citrix:vda:events"` (USB, TWAIN, WIA, `CtxUsb`, `CtxCam`), `sourcetype="WinEventLog:Application"` for Citrix ICA client driver messages, `index=windows` for Group Policy/clipboard blocks if forwarded; optional `sourcetype="uberAgent:Peripheral:USB*"` if you enable end-point visibility
- **SPL:**
```spl
(index=xd sourcetype="citrix:vda:events" OR (index=windows (sourcetype="WinEventLog:Application" OR sourcetype="citrix:vda:events")) OR (index=uberagent sourcetype="uberAgent:Peripheral*"))
| search match(_raw, "(?i)USB|TWAIN|WIA|redirect|peripheral|smart.?card|scard|clipboard|mapped drive|clpb|device.*(fail|deny|block|stop|stall)")
| eval channel=if(match(_raw, "(?i)twain|wia|scan"), "imaging", if(match(_raw, "(?i)clipboard|clip"), "clipboard", if(match(_raw, "(?i)drive|mapped"), "drives", "usb_usb")))
| where match(_raw, "(?i)fail|error|block|deny|policy|restric|not supported|time.?out|stall")
| stats count, values(Message) as sample, earliest(_time) as first_t, latest(_time) as last_t, dc(user) as users by host, channel, user
| sort - count
```
- **Implementation:** Ingest a broad slice of VDA logs with USB/TWAIN categories enabled. Add policy lookup by AD group. Separate Help Desk false positives (unsupported devices) with `NOT match(device_class,"(legacy)")` style filters where fields exist. Correlate with NetScaler/ADC app flow only if the channel is not negotiated locally. Alert on new denial strings in a 24h compare.
- **Visualization:** Table (users and channels with sample errors), Pareto chart (error text top 10), Bar chart (failed channel by delivery group if joined).
- **CIM Models:** Endpoint
- **Known false positives:** Kiosk, engineering, and healthcare use cases with heavy USB or peripheral redirection are expected. Tune with delivery-group baselines, device-class allow/deny, and a pilot OU so legitimate redirected devices do not page as a blanket exfil risk.
- **Last reviewed:** 2026-04-24

- **References:** [HDX features - USB, TWAIN, drives](https://docs.citrix.com/en-us/citrix-virtual-apps-desktops-2112/hdx/hdx-features-2112.html)

---

### UC-2.6.40 · Citrix App Layering Health and Layer Attach Status
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Availability
- **Value:** Citrix App Layering delivers OS and application layers to MCS, PVS, and elastic deployments. The elastic appliance, packaging connector, and on-VDA mount stack must all stay healthy; a failed package cache, attach timeout, or ELM/connector outage blocks user desktops at boot or sign-in. Windows Application logs on the ELM and connector roles plus VDA layer messages paint an end-to-end path from packaging through attach.
- **App/TA:** Splunk Add-on for Microsoft Windows, custom scripted or HEC input for App Layering management API, Template for Citrix XenDesktop 7 (TA-XD7-Broker) for VDA
- **Data Sources:** `sourcetype="WinEventLog:Application"` on ELM/connector servers (`unifltr`, `pvs`, `svmgr`), `sourcetype="citrix:vda:events"` for layer attach, `sourcetype="citrix:pvs:events"` when App Layering pairs with PVS, HTTP(S) or scripted inputs from App Layering ELM APIs if you export jobs to text
- **SPL:**
```spl
index=windows OR index=xd (sourcetype="WinEventLog:Application" OR sourcetype="citrix:vda:events" OR sourcetype="citrix:pvs:events") match(_raw, "(?i)App\s*Layer|layering|unifl|svmgr|ELM|layer (attach|mount|roll|package|not found|fail|cache)")
| eval component=if(match(host, "(?i)elm|layering|manager"), "elm", if(match(_raw, "(?i)PVS|vDisk"), "pvs", "vda"))
| where match(_raw, "(?i)fail|error|timeout|unavail|mismatch|cache.*(miss|full|corrupt)|not mounted")
| bin _time span=15m
| stats count, values(Message) as msg_sample, dc(host) as hosts, dc(user) as users by _time, component, host
| sort - count
```
- **Implementation:** Classify hosts by `elm|connector|vda` using a host lookup. When ELM is Linux-only, push syslog or a JSON HEC path instead of `WinEventLog`. Track cache disk usage for packaging machines via a separate capacity UC. Deduplicate noisy retry loops with `streamstats` or by trimming `count`>100/min bursts.
- **Visualization:** Swimlane (ELM vs VDA issues), Table (message samples), Single value (open critical errors in 24h).
- **CIM Models:** Change
- **Known false positives:** Elastic layering attach on first logon, layer pack upgrades, and user-driven layer repair can show transient 'not ready' or attach warnings. Correlate with a new published layer version and first-boot after publish before assuming broken layering infrastructure.
- **Last reviewed:** 2026-04-24

- **References:** [Citrix App Layering - Monitor and troubleshoot](https://docs.citrix.com/en-us/citrix-app-layering/4/monitor/monitor.html)

---

### UC-2.6.41 · FSLogix and Profile Container Health
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** FSLogix profile and Office container disks live on fast SMB file shares. Slow attach, VHD reconnection failures, runaway VHDX growth, and share latency surface as long logon times or read-only profiles. Correlating FSLogix Application events with the profile phase in uberAgent logon data isolates the share path versus client-side issues faster than GPO review alone.
- **App/TA:** Splunk Add-on for Microsoft Windows, uberAgent UXM (Splunkbase 1448), Microsoft FSLogix policy documentation
- **Data Sources:** `sourcetype="WinEventLog:Application"` source=FSLogix* or `Message=*FSLogix*`, `Perfmon:LogicalDisk` on profile share, `sourcetype="WinEventLog:System"` for VHD/Filter Manager; `index=uberagent` `sourcetype="uberAgent:Logon:LogonDetail"` for profile phase timing; optional SMB `\Server\path` path latency with synthetic scripts into `sourcetype=fslogix:synthetic`
- **SPL:**
```spl
index=windows (sourcetype="WinEventLog:Application" (source="*FSLogix*" OR source="*frx*")) OR (sourcetype="WinEventLog:System" EventCode=50)
| search match(_raw, "(?i)FSLogix|frx|profile|containe|VHDX|VHD |reparse|reconnect|load.*fail|attach.*fail|size|quota|latency")
| eval severity=if(match(_raw, "(?i)fail|error|could not|denied|timeout|locked|reparse"), "error", if(match(_raw, "(?i)warn|slow|throttl|retry"), "warning", "info"))
| where severity!="info"
| join type=left user [search index=uberagent sourcetype="uberAgent:Logon:LogonDetail" earliest=-4h | stats latest(ProfileLoad) as uem_profile_s by user]
| table _time, host, user, Message, severity, uem_profile_s
```
- **Implementation:** Ingest all FSLogix-related Application events and enable logical disk or SMB perf counters for share volumes. Set alerts on new error text patterns and on profile time >30s p95. Track VHD file size with a daily scripted inventory if not in events. For multi-site, tag share names with region and add synthetic SMB probes. Join carefully on `user` to avoid overmatching service accounts.
- **Visualization:** Timeline (FSLogix errors), Line chart (profile phase from uberAgent), Table (VHD size growth if inventoried).
- **CIM Models:** Endpoint
- **Known false positives:** Antivirus on-access scans, profile container rehydration, and one-off VHDX compact jobs spike FSLogix I/O errors briefly on large profiles. Use a short time window, exclude the backup hours job class, and check FSLogix filter and driver version against the last Windows LCU.
- **Last reviewed:** 2026-04-24

- **References:** [FSLogix documentation - Microsoft](https://learn.microsoft.com/en-us/fslogix/)

---

### UC-2.6.42 · Citrix Configuration Change Audit Trail
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security, Compliance
- **Value:** Unplanned or unauthorized changes to published resources, machine catalogs, entitlements, and policies are high-impact in VDI. Collecting a tamper-resistant trail from Windows process creation and Citrix admin audit events, plus any broker-side configuration events you expose, gives security and change teams evidence for investigations and attestation, not only for ITIL tickets.
- **App/TA:** Splunk Add-on for Microsoft Windows, Template for Citrix XenDesktop 7 (TA-XD7-Broker), optional Splunk Enterprise Security for correlation
- **Data Sources:** `sourcetype="WinEventLog:Security"` (4688, 4702) for `powershell*`, `mmc.exe`, `BrokerPowerShell.exe`, `Citrix*Studio*`, `index=xd` `sourcetype="citrix:broker:events"` for admin/audit and publish changes, `sourcetype="linux_audit"` or container logs for Cloud connectors if you separate admin API calls
- **SPL:**
```spl
index=windows sourcetype="WinEventLog:Security" (EventCode=4688 OR EventCode=4702)
| search match(_raw, "(?i)BrokerPowerShell|CVAD|XD.*Catalog|XenDesktop|Studio|Publish|Delivery.?Group|Machine.?Catalog|GPO|Broker\\bin|Get-Broker|Set-Broker|New-Broker|Remove-Broker")
| eval account=coalesce(Security_ID, user, src_user, Account_Name)
| eval process=New_Process_Name
| table _time, host, account, process, EventCode, CommandLine
| append [search index=xd sourcetype="citrix:broker:events" match(_raw, "(?i)admin|audit|publish|unpublish|add.?desktop|change.?entitlement|polic|Studio")]
| sort - _time
```
- **Implementation:** Send Security logs from admin jump hosts and all Delivery Controllers. Enable command-line process auditing (4688) per Microsoft guidance. Harden: lock down who can run `BrokerPowerShell`. Enrich with asset identity for admin accounts. For Citrix DaaS, pipe Cloud Director API audit to Splunk. Retention: align to your compliance schedule (e.g. 1 year online).
- **Visualization:** Timeline (change events by admin), Table (raw command line), Bar chart (changes per day by team via lookup).
- **CIM Models:** Change
- **Known false positives:** Studio automation, Terraform, GitOps, and regular scheduled exports to documentation systems generate many configuration diffs. Diff against the automation identity and approved change ID; the false positive is 'noise from script', not a silent attacker edit.
- **MITRE ATT&CK:** T1078, T1098
- **Last reviewed:** 2026-04-24

- **References:** [Citrix audit logging and reporting](https://docs.citrix.com/en-us/citrix-virtual-apps-desktops-2112/operations/audit/audit-logging.html)

---

### UC-2.6.43 · Citrix Site Database Connectivity from Controllers
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** The Citrix site database is the single source of truth for registrations, entitlements, and broker decisions. If Delivery Controllers cannot reach the site database, users experience brokering failures, registration storms, and eventual site-wide service degradation. Proactively detecting connection retries, timeout errors, and authentication failures to the data store is essential before session launch capacity collapses. Correlate controller Application log events with `citrix:broker:events` to distinguish transient network blips from persistent connectivity loss.
- **App/TA:** Splunk Add-on for Microsoft Windows; Template for Citrix XenDesktop 7 (`TA-XD7-Broker`) for broker event normalization
- **Data Sources:** `index=windows` `sourcetype="WinEventLog:Application"` from Delivery Controllers for Citrix site database and configuration services; optional `index=xd` `sourcetype="citrix:broker:events"` for correlated broker health, `EventCode` / `EventID` and `Message` text for connection timeouts and failure reasons
- **SPL:**
```spl
index=windows sourcetype="WinEventLog:Application" (source="*Citrix*" OR source="*Broker*" OR Message="*site database*" OR Message="*Site database*")
| search (Message="*connection*" OR Message="*timeout*" OR Message="*failed*" OR Message="*unavailable*") (Message="*database*" OR Message="*SQL*" OR Message="*data store*")
| bin _time span=5m
| stats count as evt_count, values(EventCode) as event_codes, values(Message) as sample_msgs by host, _time
| where evt_count > 0
| sort -_time
| table _time, host, event_codes, evt_count, sample_msgs
```
- **Implementation:** Forward Windows Application logs from every Delivery Controller. Add field extractions or `rex` to normalize database connection error text, SQL connectivity codes, and timeout indicators. Ingest or schedule-query `index=xd` broker events to correlate. Alert when any controller reports repeated site database connection failures in a five-minute window, or when a single error pattern exceeds your baseline. Suppress during planned database maintenance using a time-bound lookup. Document escalation to the DBA and Citrix site recovery runbooks.
- **Visualization:** Single value (open critical events), timechart of database-related errors by controller, table of recent error text with host, linked drilldown to broker event timeline.
- **CIM Models:** Databases
- **Known false positives:** SQL Always On failovers, index rebuilds, backup locks, and network ACL or firewall change tests can make controller database checks fail for seconds. Suppress on DBA and network maintenance, then look at SQL listener and firewall logs before a site-down declaration.
- **Last reviewed:** 2026-04-24

- **References:** [Citrix Databases — CVAD](https://docs.citrix.com/en-us/citrix-virtual-apps-desktops/technical-overview/databases.html), [uberAgent UXM (optional correlation on endpoints)](https://splunkbase.splunk.com/app/1448)

---

### UC-2.6.44 · VDA Disk IOPS and Write Cache Utilization
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** MCS, image management service I/O optimization, and PVS all rely on local cache volumes. When the write cache fills or RAM cache spills to disk under burst load, users see freezes, logon failures, and even blue screens. Tracking per-host disk read/write IOPS, queue time, and write-cache utilization on session hosts shows capacity and misconfiguration (undersized cache disk, wrong cache mode, storage latency) before user-visible outages. Combine endpoint metrics with PVS or MCS-specific events to explain growth versus a noisy neighbor on shared storage.
- **App/TA:** uberAgent UXM (Splunkbase 1448) — recommended for disk and volume metrics; plus Universal Forwarder for `citrix:vda:events` if you stream VDA service events
- **Data Sources:** `index=uberagent` `sourcetype="uberAgent:Volume:DiskPerformance"` (per-volume read/write IOPS, queue depth, percent busy); `index=xd` `sourcetype="citrix:vda:events"` for MCS or image management cache overflow and RAM cache handoff messages; optional `sourcetype="citrix:pvs:stream"` for PVS write-cache percent when you run Provisioning Services
- **SPL:**
```spl
index=uberagent sourcetype="uberAgent:Volume:DiskPerformance"
| where match(VolumeName, "Cache|WCD|MCS|WriteCache|PVS|Differencing", "i") OR 1=1
| bin _time span=15m
| stats avg(ReadIops) as read_iops, avg(WriteIops) as write_iops, avg(PercentDiskTime) as pct_busy, latest(WriteCacheUtilizationPct) as write_cache_util by host, VolumeName, _time
| where write_cache_util > 80 OR read_iops > 20000 OR write_iops > 15000 OR pct_busy > 85
| table _time, host, VolumeName, read_iops, write_iops, pct_busy, write_cache_util
```
- **Implementation:** Deploy uberAgent on session hosts. Confirm `uberAgent:Volume:DiskPerformance` (or the equivalent volume performance sourcetype in your build) lands in `index=uberagent`. Add optional scripted or log collection for VDA and PVS cache messages into `index=xd`. Create rolling baselines per hardware tier. Alert when write-cache use crosses a two-tier threshold (for example, 60% warning, 80% critical) or when IOPS and disk busy time together indicate saturation. Group by host and catalog to find mis-sized machines.
- **Visualization:** Timechart of read/write IOPS and disk busy %, single value for max write-cache use in fleet, table of worst hosts with volume name and cache utilization.
- **CIM Models:** Performance
- **Known false positives:** PVS vDisk merge, storage vMotion, antivirus full scans, and large patch installs spike disk IOPS and write cache usage together. Key on hosts running those jobs in a job lookup and compare to a same-hour baseline from last week, not a fixed raw cap.
- **Last reviewed:** 2026-04-24

- **References:** [uberAgent volume and disk performance](https://docs.uberagent.com/), [Cache for MCS — Citrix CVAD](https://docs.citrix.com/en-us/citrix-virtual-apps-desktops-service/manage-deployment/mcs/mcs-storage.html)

---

### UC-2.6.45 · Machine Boot Storm Detection and Mitigation
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance, Capacity
- **Value:** A boot storm is a sudden, correlated surge of machine start and registration activity — for example at shift change or after maintenance — that can flood the hypervisor, storage, and broker queues. It causes long queue times, failed registrations, and slow logon even when per-machine health is good. You need a detection that works on the rate of starts per minute per catalog and delivery group, not only on a static machine count, plus a view of whether staggered start configurations are honored. The goal is to trigger proactive throttling, schedule spreading, and communications before users pile into failures.
- **App/TA:** Template for Citrix XenDesktop 7 (`TA-XD7-Broker`); optional uberAgent UXM (Splunkbase 1448) for boot duration on guests
- **Data Sources:** `index=xd` `sourcetype="citrix:broker:events"` (machine start, registration, power-on, brokering milestones); `index=xd` hypervisor or cloud audit if forwarded (optional burst correlation); `index=uberagent` `sourcetype="uberAgent:Machine:Boot"` or host boot time metrics if you collect them
- **SPL:**
```spl
index=xd sourcetype="citrix:broker:events" (event_type="VmPowerOn" OR event_type="MachineStart" OR event_type="MachineRegistration" OR match(_raw, "(power.?on|start|registration|boot)", "i"))
| eval boot_phase=coalesce(power_state, event_type, "Unknown")
| bin _time span=1m
| stats dc(machine_name) as machines_in_min, count as events_in_min, values(delivery_group) as dgs by _time, catalog_name
| eventstats median(machines_in_min) as med_boots, stdev(machines_in_min) as stdev_boots by catalog_name
| eval z_score=if(isnull(stdev_boots) OR stdev_boots=0, 0, (machines_in_min - med_boots) / stdev_boots)
| where machines_in_min > 20 OR z_score > 3
| sort - machines_in_min
| table _time, catalog_name, dgs, machines_in_min, events_in_min, z_score
```
- **Implementation:** Ingest broker events with consistent `machine_name`, `catalog_name`, and `delivery_group` fields. Set absolute thresholds (e.g. more than 20 unique machines starting per minute) and relative thresholds (Z-score on the per-catalog rate versus the same time-of-day baseline). Add a secondary search that lists scheduled start tags or autoscale events if you model them. Integrate the alert with power-management policy owners so they can lengthen stagger windows or cap concurrent power operations. For proof, compare to hypervisor CPU ready time and storage latency dashboards.
- **Visualization:** Overlay timechart: machines started per minute by catalog, optional second axis for failed registrations, table of top peaks with z-score, Sankey or flow optional for maintenance window correlation.
- **CIM Models:** Performance
- **Known false positives:** Monday open, school-term starts, and single large batch logon events naturally concentrate boot load. Use adaptive or same-weekday seasonality; alert when boot time or queuing outlasts the historical peak for that calendar pattern or is paired with VDA registration failures only.
- **Last reviewed:** 2026-04-24

- **References:** [Citrix autoscale and scheduled actions](https://docs.citrix.com/en-us/citrix-virtual-apps-desktops-service/manage-deployments/citrix-autoscale/about-autoscale.html), [Load management — brokering context](https://docs.citrix.com/en-us/citrix-virtual-apps-desktops/technical-overview/manage-load-balancing.html)

---

### UC-2.6.46 · Citrix Monitor OData Load Index Trending
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance, Capacity
- **Value:** The Citrix load evaluator reports a load index (0 to 10,000) that combines session count, application load, and other factors per machine. Trending that index at the machine and delivery group level shows who is overassigned before new sessions fail, validates load-balancing policy effectiveness, and helps capacity planning. Spikes in average or peak load index that persist across hours point to too few hosts, heavy users, or runaway published applications, not one-off blips. Pair this with session counts to separate genuine saturation from a broken load metric source.
- **App/TA:** Citrix Monitor Service OData poller (custom scripted input) or a supported Splunk Citrix add-on that writes `citrix:monitor:odata`
- **Data Sources:** `index=xd` `sourcetype="citrix:monitor:odata"` (Machines, Sessions, and LoadIndex fields from the Citrix Monitor Service OData collection); field aliases such as `load_index` or `LoadIndex` depending on the collector; `MachineName` / `CatalogName` / `DesktopGroupName` for grouping
- **SPL:**
```spl
index=xd sourcetype="citrix:monitor:odata" odata_resource="Machines"
| eval li=tonumber(coalesce(load_index, LoadIndex, 0))
| eval machine=coalesce(machine_name, MachineName, host)
| eval dg=coalesce(delivery_group, DesktopGroupName, "Unknown")
| where li >= 0
| bin _time span=1h
| stats latest(li) as load_index, max(li) as peak_li by machine, dg, _time
| where peak_li > 5000
| timechart max(peak_li) by dg
```
- **Implementation:** Stand up a scheduled OData poll with authentication to the on-premises Monitor service and persist JSON into `citrix:monitor:odata` with a stable `odata_resource` field. Map OData property names to lowercase Splunk fields for `LoadIndex` and `MachineName`. Create hourly or fifteen-minute baselines. Alert when peak load index exceeds 5,000 (tunable) for any machine for more than two consecutive samples, or when the delivery group average crosses your internal green/yellow line. Onboard a dashboard of top ten machines by load index with drilldowns to process and session data.
- **Visualization:** Line chart of max load index by delivery group, heatmap of machines over time, table of current worst offenders with load index and session count if joined.
- **CIM Models:** Performance
- **Known false positives:** Third-party monitoring exporters, Monitor OData version upgrades, and dashboard refreshes can change call patterns to the load index. Match software and connector releases; a sustained small drift without user KPI regression is usually tuning noise, not capacity doom.
- **Last reviewed:** 2026-04-24

- **References:** [Monitor Service and OData in CVAD](https://docs.citrix.com/en-us/citrix-virtual-apps-desktops/technical-overview/monitor-service.html), [Citrix — load management overview](https://docs.citrix.com/en-us/citrix-virtual-apps-desktops/technical-overview/manage-load-balancing.html)

---

### UC-2.6.47 · Workspace App Client Version Distribution
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Compliance
- **Value:** Citrix Workspace app versions and platforms drift quickly — users defer upgrades, some branches are blocked by legacy tools, and mobile platforms patch on different cadences. A wide long tail of old clients increases your support cost, security exposure, and feature inconsistency. Reporting client version share by platform (Windows, Mac, Linux, iOS, Android) supports compliance with internal standards, tells you which upgrade campaigns worked, and highlights obsolete builds that should be blocked at the gateway. This is not a one-time audit; you want scheduled visibility after every gateway or StoreFront change.
- **App/TA:** Template for Citrix XenDesktop 7 (`TA-XD7-Broker`) and optional Citrix Monitor OData poller for session details
- **Data Sources:** `index=xd` `sourcetype="citrix:broker:events"` (session or connection events that carry `ClientVersion`, `ClientProductId`, and `ClientAddress` or platform tags); `index=xd` `sourcetype="citrix:monitor:odata"` `Sessions` resource if the broker event lacks detail
- **SPL:**
```spl
index=xd sourcetype="citrix:broker:events" (event_type="SessionConnection" OR event_type="ConnectionLogon" OR event_type="SessionInfo")
| eval cv=coalesce(client_version, ClientVersion, workspace_version, "unknown")
| eval platform=coalesce(client_platform, os_type, client_os, "unknown")
| where cv!="unknown"
| stats count as sessions, dc(user) as users, dc(host) as hosts by cv, platform
| eventstats sum(sessions) as total_sessions
| eval pct=round(100 * sessions / total_sessions, 2)
| sort - sessions
| table cv, platform, users, sessions, pct
```
- **Implementation:** Ensure client version fields are present on at least one reliable event (often session start from broker or a Monitor OData `Sessions` backfill). Build a `lookup` of approved `client_version` per platform. Schedule a weekly or daily report, not an alert, unless a version is explicitly banned — then alert when `pct` for that version is nonzero. For executive views, show stacked percentage bars by platform. Feed the data into your software-asset and endpoint-management teams for package targeting.
- **Visualization:** Pie or treemap of versions, stacked bar by platform, table of versions with percent of sessions, optional single value for count of unapproved clients via lookup match.
- **CIM Models:** Endpoint
- **Known false positives:** Ring-based Workspace app rollouts, Intune staged deployments, and pilot AD groups will skew the version mix from week to week. Chart by update channel and OU, not a single org-wide 'must be 100% latest' line that will never hold during pilots.
- **Last reviewed:** 2026-04-24

- **References:** [Citrix Workspace app lifecycle matrix](https://docs.citrix.com/en-us/citrix-workspace-app-for-windows/whats-new.html), [Session data from Monitor (context)](https://docs.citrix.com/en-us/citrix-virtual-apps-desktops/technical-overview/monitor-service.html)

---

### UC-2.6.48 · Published Application Inventory Drift
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance, Security
- **Value:** The published application catalog and delivery group assignments define what users can launch and from where. Unplanned additions — for example, an overly broad group entitlement — expand attack surface. Silent removals can break a department. Drift is often caught only after help desk tickets. Collecting and comparing app inventory over time, including who made the last change, supports change management, recertification, and quick forensic review if suspicious publishing appears. The goal is the same as infrastructure drift detection, but for desktop and app entitlements in Citrix rather than for cloud IaaS tags alone.
- **App/TA:** Template for Citrix XenDesktop 7 (`TA-XD7-Broker`); optional scripted OData application inventory; Splunk add-on for Windows security audit if you capture privileged Citrix admin accounts
- **Data Sources:** `index=xd` `sourcetype="citrix:broker:events"` (admin and configuration change events, published application and delivery group membership changes if forwarded); `index=xd` `sourcetype="citrix:monitor:odata"` optional periodic snapshot of `Applications` and `ApplicationGroups` for diffing; Windows security or FMA audit if you consolidate admin actions
- **SPL:**
```spl
index=xd sourcetype="citrix:broker:events"
| where event_type IN ("PublishedAppChange", "AppGroupChange", "AdminAction") OR match(_raw, "(?i)(publish|unpublish|application|delivery\s*group|entitlement)")
| eval app=coalesce(app_name, ApplicationName, published_name, "Unknown")
| eval change=coalesce(change_type, action, operation, event_type, "change")
| eval actor=coalesce(admin_user, Actor, user, "unknown")
| bin _time span=1d
| stats count as changes, values(change) as change_types, values(delivery_group) as dgs by _time, app, actor
| where changes>0
| sort - _time
| table _time, app, actor, change_types, dgs, changes
```
- **Implementation:** If native broker `event_type` values are not present, use daily OData `Applications` and `Outputlookup` a baseline table, then `diff` the next run with a scripted or Splunk custom command. For real-time, parse admin audit entries that include the admin SID or UPN. Alert when an application appears or disappears without a linked change record in your ITSM, or when `Actor` is not a known automation account. For security, pay special care to new publish actions to all-authenticated users or to broad Active Directory groups.
- **Visualization:** Changelog table with old versus new, timeline of app count by delivery group, single value for new apps in last 24 hours with drilldown to detail.
- **CIM Models:** Change
- **Known false positives:** Application packaging sprints, bulk adds during catalog migrations, and nightly sync jobs from automation move published inventory counts. Scope alerts to changes outside a catalog publish or job ID, not every packaging weekend.
- **MITRE ATT&CK:** T1098, T1078
- **Last reviewed:** 2026-04-24

- **References:** [Publish applications in CVAD](https://docs.citrix.com/en-us/citrix-virtual-apps-desktops/technical-overview/publish.html), [Delegating administration and role-based access](https://docs.citrix.com/en-us/citrix-virtual-apps-desktops/technical-overview/delegated-administration.html)

---

### UC-2.6.49 · Stuck Sessions and Ghost Session Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Sessions that sit disconnected beyond policy, that never complete logoff, or that remain in broker state when the session host is already gone, consume user licenses, load index, and file handles; they are common precursors to ghost or orphaned sessions. Ghost sessions that survive past the machine that hosted them complicate support and can block new connections for the same user. You want detection that works off authoritative session records and time-in-state, with thresholds aligned to your group policy and Citrix session reliability settings, plus a path to session host or broker session reset actions.
- **App/TA:** Template for Citrix XenDesktop 7 (`TA-XD7-Broker`); optional uberAgent UXM (Splunkbase 1448); optional Citrix Monitor OData
- **Data Sources:** `index=xd` `sourcetype="citrix:broker:events"` (session state, logoff, disconnect, reconnect); `index=xd` `sourcetype="citrix:monitor:odata"` `Sessions` for `SessionState`, `ClientName`, and `LogoffDuration` when broker feed is thin; `index=uberagent` `sourcetype="uberAgent:Session:SessionDetail"` for per-session end-to-end state
- **SPL:**
```spl
index=xd sourcetype="citrix:broker:events" (event_type="SessionState" OR event_type="SessionDisconnect" OR event_type="SessionLogoff")
| eval state=coalesce(session_state, SessionState, status, "Unknown")
| eval sess=coalesce(session_key, session_id, Uid, "unknown")
| eval user=coalesce(user, UserName, "unknown")
| eval machine=coalesce(machine_name, VDA, host, "Unknown")
| where state IN ("Disconnected", "StuckOnBroker", "PendingLogoff", "PreparingSession", "PreparingApplication")
| eval idle_sec=coalesce(idle_time_sec, disconnect_duration_sec, 0)
| where idle_sec>28800
| bin _time span=1h
| stats count as bad_sessions, values(state) as states, max(idle_sec) as max_idle_sec, dc(user) as affected_users by machine, _time
| where bad_sessions>0
| table _time, machine, bad_sessions, affected_users, max_idle_sec, states
```
- **Implementation:** Align `idle_sec` and disconnect timers with GPO: disconnected session limit, logoff on disconnect, and session linger. Eight hours in the example SPL is a placeholder. Join broker and Monitor OData so you can see broker versus VDA truth; mismatch flags ghosts. For automation, use a runbook with Citrix `Get-BrokerSession` and reset cmdlets, not blind reboots. Alert on a machine with many long-lived disconnected states or a single user with repeated ghosts after migrations.
- **Visualization:** Table of long-lived sessions, heatmap of affected machines, sparkline of ghost count over time, optional link to a Director-equivalent view.
- **CIM Models:** Network_Sessions
- **Known false positives:** Disconnected session and idle policies leave sessions that NOCs label ghost while they are still within policy. Escalate when the same user or machine stays beyond the documented threshold or when broker and VDA last-seen times diverge, not a single 'old' row.
- **Last reviewed:** 2026-04-24

- **References:** [Session reliability and reconnection (Citrix)](https://docs.citrix.com/en-us/citrix-virtual-apps-desktops/technical-overview/ica-session-reliability.html), [Troubleshoot user issues — session disconnect](https://docs.citrix.com/en-us/citrix-virtual-apps-desktops/technical-overview/troubleshoot-user-issues.html)

---

### UC-2.6.50 · VDA BSOD and Machine Stability Tracking
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Blue screens, hard hangs, and unexpected reboots on session hosts are disproportionately disruptive: many users and published apps can fail in one incident. A single bugcheck may be a driver or GPU edge case; a cluster of the same stop code in one catalog points to a bad image, firmware, or policy rollout. You need a unified stream that captures bugcheck parameters from the System log, correlates with Citrix VDA and agent state when available, and enriches with uberAgent reboot analytics so you can trend stability per catalog, per hardware generation, and after every monthly patch. Treat recurring hosts as a candidate for maintenance mode and root-cause with vendor tools.
- **App/TA:** Splunk Add-on for Microsoft Windows; uberAgent UXM (Splunkbase 1448); optional Template for Citrix XenDesktop 7 for `citrix:vda:events`
- **Data Sources:** `index=windows` (session hosts) `sourcetype="WinEventLog:System"` bugcheck events, unexpected shutdowns, kernel power events; `index=xd` `sourcetype="citrix:vda:events"` for VDA and agent service restarts tied to host instability; `index=uberagent` `sourcetype="uberAgent:Machine:Boot"` and related stability or boot sourcetypes for unexpected reboots and stop codes normalized by uberAgent
- **SPL:**
```spl
index=windows sourcetype="WinEventLog:System" (EventCode=1001 OR EventCode=41 OR EventCode=6008)
| rex field=Message max_match=0 "(?<bugcheck>0x[0-9A-Fa-f]+)"
| append [ search index=uberagent sourcetype="uberAgent:Machine:Boot" unexpected_reboot=1 | eval EventCode=9999 | eval host=coalesce(host, dest_host) ]
| bin _time span=1d
| stats count as instabilities, values(EventCode) as event_codes, values(bugcheck) as stop_codes by host, _time
| where instabilities>0
| sort - instabilities
| table _time, host, instabilities, event_codes, stop_codes
```
- **Implementation:** Ingest the full System channel from all session hosts. For bugcheck 1001, parse `Message` to extract the stop code. Join `host` to a CMDB or lookup that supplies `catalog_name` and `delivery_group`. In uberAgent, confirm unexpected reboots flow with the same `host` key. Alert when any host has more than one bugcheck in seven days, or when a new stop code appears in more than 10% of a catalog in a week. Exclude planned reboot windows via a change lookup. For GPU images, add NVIDIA or AMD field extractions in a child search.
- **Visualization:** Choropleth of stability rate by data center, bar chart of top stop codes, timeline of restarts, table of worst hosts with catalog and patch level.
- **CIM Models:** Endpoint
- **Known false positives:** Patch Tuesday, driver hotfix waves, and pool-wide golden-image replays can produce a short burst of per-host BSODs during rollout. Require multiple distinct hosts, repeat crashes, or a driver signature tied to a bad patch, not a one-off on a single noisy VM.
- **Last reviewed:** 2026-04-24

- **References:** [Windows bug check reference (Microsoft Learn)](https://learn.microsoft.com/en-us/windows-hardware/drivers/debugger/bug-check-code-reference2), [uberAgent unexpected reboots](https://docs.uberagent.com/)

---

### UC-2.6.51 · Citrix StoreFront Server IIS Health
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** StoreFront is the first hop for many users after the gateway. If IIS app pools recycle frequently, if worker processes crash, or if HTTP 401/500/503 rates climb, every receiver update, resource enumeration, and single sign-on call suffers — often before the broker shows pressure. You should monitor the IIS access log error mix, time-taken (latency) percentiles, and the Windows event trail for `W3SVC`, `IIS*`, and app pool `Application pool * stopped` or rapid recycling on each StoreFront node. A healthy farm shows symmetric latency across members; asymmetry is a sign of broken authentication provider settings or a sick node still receiving traffic from the load balancer.
- **App/TA:** Splunk Add-on for Microsoft Windows; enable IIS and HTTP logging on StoreFront servers; consider Splunk add-on for Microsoft IIS for field extraction
- **Data Sources:** `index=windows` `sourcetype="iis"` and `iis:access` or W3C for StoreFront web traffic; `sourcetype="WinEventLog:System"` and `sourcetype="WinEventLog:Application"` for IIS and Microsoft-Windows-IIS* worker process and app pool recycles; optional `sourcetype="WinEventLog:Security"` for authentication noise correlation
- **SPL:**
```spl
index=windows (sourcetype="iis" OR sourcetype="W3C*" OR source="*u_ex*.log")
| eval site=coalesce(s_sitename, "default")
| search cs_uri_stem="*Authentication*" OR cs_uri_stem="*Resources*" OR cs_uri_stem="*Icon*" OR like(lower(cs_uri_stem), "%citrix%")
| eval sc=tonumber(sc_status)
| eval is_err=if(sc>=400,1,0)
| bin _time span=5m
| stats count as total, sum(is_err) as http_err, avg(timetaken) as avg_ms, perc95(timetaken) as p95_ms by site, _time
| eval err_pct=if(total>0, round(100*http_err/total,2), 0)
| where err_pct>1 OR p95_ms>2000
| table _time, site, total, err_pct, avg_ms, p95_ms
```
- **Implementation:** Enable W3C extended logging on StoreFront with `time-taken`, `sc-status`, and `cs-uri-stem` at minimum. Ingest in near real time. Add a second scheduled search on Application/System for IIS worker crashes. Baseline 401 rates versus known maintenance. Alert when 5xx exceeds 0.2% of requests for 15 minutes, or p95 time-taken exceeds 2,000 ms for authentication and resource endpoints, or on app pool recycles more than one per hour per site. De-dupe load-balanced pairs by `cs-host` to avoid double counting a single user action.
- **Visualization:** Timechart of 4xx/5xx counts, timechart of p95 time-taken by virtual directory, table of app pool recycles, single value for 503 spike.
- **CIM Models:** Web
- **Known false positives:** IIS app pool recycles, certificate binding touch-ups, and .NET or URL rewrite module updates on StoreFront are routine. Correlate 5xx with app pool or SSL maintenance; sustained unrecoverable pool failure across nodes is the real signal.
- **Last reviewed:** 2026-04-24

- **References:** [Citrix StoreFront 1912 and later (planning and networking)](https://docs.citrix.com/en-us/storefront/1912/plan/considerations.html), [Microsoft: IIS log fields](https://learn.microsoft.com/en-us/iis/get-started/whats-new-in-iis-85/iis-85-rewrite-module-logging-rewrite-tracing)

---

### UC-2.6.52 · VDA Software and OS Version Lifecycle Tracking
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Compliance
- **Value:** Citrix releases new VDA builds regularly. Microsoft retires Windows 10/11 builds on a predictable schedule. Running an inventory of `vda_version` and `os_build` per session host supports compliance with internal standard images, tells you which catalogs are still on long-term servicing versus current channel, and highlights stragglers before support tickets or Citrix Cloud health checks flag them. Feed the same list into patch windows, upgrade rings, and golden-image promotion. A simple scheduled report that lists any host not on the approved pair is enough for many organizations; add lookups for end-of-life dates you maintain in a CSV.
- **App/TA:** Template for Citrix XenDesktop 7 (`TA-XD7-VDA`); optional uberAgent UXM (Splunkbase 1448) for operating system build and patch level
- **Data Sources:** `index=xd` `sourcetype="citrix:vda:events"` (VDA agent version, component build, plug-in status); `index=uberagent` host inventory sourcetypes if you standardize on uberAgent for OS build; optional Windows `sourcetype="WinEventLog:Application"` for Citrix installer success or failure audit
- **SPL:**
```spl
index=xd sourcetype="citrix:vda:events" (event_type="AgentInfo" OR event_type="Registration" OR event_type="Heartbeat")
| eval vda_ver=coalesce(vda_version, agent_version, VdaVersion, "unknown")
| eval os_b=coalesce(os_build, windows_build, OSBuild, "unknown")
| eval machine=coalesce(machine_name, host, "Unknown")
| where vda_ver!="unknown"
| stats dc(machine) as host_count, max(_time) as last_seen by vda_ver, os_b
| rename vda_ver as vda_version, os_b as os_build_value
| sort vda_version, os_build_value
| table vda_version, os_build_value, host_count, last_seen
```
- **Implementation:** Emit a heartbeat or registration event at least daily that includes VDA and OS build. Create `lookup citrix_supported_vda.csv` with columns `vda_version`, `supported`, `eol_date`. Version the lookup with change control. Schedule the report weekly; alert only for rows on the critical path (for example, Internet-facing or regulated worker pools). Combine with your configuration management database to auto-close when a host is decommissioned.
- **Visualization:** Bar chart of hosts by VDA version, table of unsupported rows, treemap by catalog if you join a lookup from machine to catalog.
- **CIM Models:** Endpoint
- **Known false positives:** Long tails of older VDA or OS versions are normal during phased EOL and site-by-site upgrades. Track trend toward a published deadline; avoid flat 'any old version' alerts that fire every day of a 12-month migration.
- **Last reviewed:** 2026-04-24

- **References:** [Citrix Virtual Apps and Desktops — product matrix and lifecycle](https://docs.citrix.com/en-us/citrix-virtual-apps-desktops/technical-overview/product-lifecycle.html), [Current release VDA requirements](https://docs.citrix.com/en-us/citrix-virtual-apps-desktops/technical-overview/system-requirements.html)

---

### UC-2.6.53 · Citrix Delivery Group Desktop Assignment Changes
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Compliance, Security
- **Value:** Desktop and machine assignments determine who can reach which host pool, including support jump boxes and high-risk clinical or trading desktops. A mistaken assignment can grant a broad security group direct access to a gold image, or remove access during an incident. You should log add/remove actions on assignments with the acting admin, delivery group, user or group principal, and machine where applicable. Day-to-day automation may drive many rows — the control is the unexpected actor, off-hours change, or assignment outside an approved list of groups, not the volume alone.
- **App/TA:** Template for Citrix XenDesktop 7 (`TA-XD7-Broker`); optional Citrix Monitor OData for snapshot-based diff
- **Data Sources:** `index=xd` `sourcetype="citrix:broker:events"` (desktop assignment, entitlement, and machine assignment changes; admin actions); `index=xd` `sourcetype="citrix:monitor:odata"` `Machines` or `Assignments` if you take periodic inventory snapshots; optional Microsoft-365/Entra sign-in or AD audit for correlating the same `user` principal
- **SPL:**
```spl
index=xd sourcetype="citrix:broker:events"
| where event_type IN ("DesktopAssignmentChange", "MachineAssignment", "EntitlementChange") OR match(_raw, "(?i)(assignment|entitlement|desktop.?.?user|user.?.?machine)")
| eval user_key=coalesce(user, UPN, sam_account, "unknown")
| eval dg=coalesce(delivery_group, desktop_group, "Unknown")
| eval machine=coalesce(machine_name, machine, "Unassigned")
| eval change=coalesce(change_type, action, event_type, "change")
| eval actor=coalesce(admin_user, Admin, "unknown")
| bin _time span=1h
| stats count as changes, values(change) as change_types, values(user_key) as users_touched, values(machine) as machines by dg, _time, actor
| where changes>0
| sort - _time
| table _time, actor, dg, change_types, users_touched, machines, changes
```
- **Implementation:** Map broker admin events into `citrix:broker:events` with stable field names. Create a `lookup` of approved automation service accounts. Alert when `actor` is not in the list and the hour is outside change windows, or when a new Active Directory group is added to a sensitive delivery group. If your broker is quiet, supplement with hourly OData `Machines` output diffed in a saved search. Feed results to the identity and access team for recertification evidence.
- **Visualization:** Timeline of changes by admin, table of the last 50 events with before/after if your feed includes it, single value of changes in last 24 h compared to 30-day average.
- **CIM Models:** Change
- **Known false positives:** HR bulk moves, department restructuring, and large hiring batches legitimately reassign many desktops the same day. Join to the HR feed or the bulk ticket before treating mass assignment as malicious admin action.
- **MITRE ATT&CK:** T1098
- **Last reviewed:** 2026-04-24

- **References:** [Assign machines to users in CVAD](https://docs.citrix.com/en-us/citrix-virtual-apps-desktops/technical-overview/delivery-groups-machines.html), [Manage machine catalogs and delivery groups](https://docs.citrix.com/en-us/citrix-virtual-apps-desktops/technical-overview/manage-cds.html)

---

### UC-2.6.54 · RDS Licensing Validation for Multi-Session Hosts
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Value:** Session hosts that offer multiple concurrent RDP and Citrix sessions need valid Remote Desktop Services client access licenses, healthy communication with the license server list, and clear visibility into per-device versus per-user mode and any grace period. A host in grace can appear healthy until a deadline passes and new sessions are refused. A broken license server list string — wrong DNS, firewall, or certificate — is a common misconfiguration. Collect license warnings from Application and the Remote Desktop service channels on each multi-session VDA, and aggregate the same on license servers. Pair with your Citrix per-user and Microsoft RDS-CAL entitlements in procurement, not in Splunk, but use Splunk to prove the runtime state matches policy.
- **App/TA:** Splunk Add-on for Microsoft Windows on session hosts and on Remote Desktop License Servers; optional scripted WMI or `Get-CimInstance` poll for `Win32_TerminalServiceSetting` and grace period on hosts
- **Data Sources:** `index=windows` `sourcetype="WinEventLog:Application"` with `Source="*TerminalServices*"` or `Microsoft-Windows-TerminalServices-LSM*`, Windows license service events, Remote Desktop license server events (42, 4105, 22, 23, 25, 28); `index=windows` on the license server and `sourcetype="WinEventLog:RemoteDesktopServices*"` where available; `index=xd` `sourcetype="citrix:broker:events"` for multi-session brokering context
- **SPL:**
```spl
index=windows (sourcetype="WinEventLog:Application" OR sourcetype="WinEventLog:RemoteDesktopServices*" OR source="*TerminalServices*")
| where EventCode IN (22, 23, 25, 28, 38, 4105) OR like(lower(_raw),"%license%") OR like(lower(_raw),"%grace%") OR like(lower(_raw),"%remote desktop%") OR like(lower(_raw),"%rd licen%")
| eval kind=if(like(lower(_raw),"%grace%"),"grace", if(like(lower(_raw),"%expir%"),"expiry","license_event"))
| eval server=coalesce(license_server, LicenseServer, host)
| bin _time span=1d
| stats count as daily_events, values(EventCode) as codes, values(kind) as kinds by server, _time
| where daily_events>0
| sort - daily_events
| table _time, server, daily_events, codes, kinds
```
- **Implementation:** Enable verbose Remote Desktop license logging in Windows where supported. Add a small scripted input to dump `HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\Terminal Server\RCM\Licensing` or PowerShell `Get-RDLicense` output daily on license servers. Alert on any `grace` or `0-day` grace start, any event that says license server is unreachable, and any 4105 with severity error. Deduplicate license servers. Document which Citrix and Microsoft agreements cover which host pools. Tune out duplicate Windows noise per build.
- **Visualization:** Table of last license error per host, timechart of daily_events by server, single value of hosts in grace, network diagram optional with manual overlay.
- **CIM Models:** Endpoint
- **Known false positives:** License key renewals, grace period during true-up, and a temporary license server failover can log RDS or Citrix session licensing warnings. Map to the license key expiry calendar and only escalate when users are actually blocked at session connection.
- **Last reviewed:** 2026-04-24

- **References:** [Remote Desktop Services and licensing (Microsoft Learn)](https://learn.microsoft.com/en-us/troubleshoot/windows-server/remote/remote-desktop-services-terms), [Citrix — supported operating systems and RDS context](https://docs.citrix.com/en-us/citrix-virtual-apps-desktops/technical-overview/system-requirements.html)

---

### UC-2.6.55 · GPU Driver Version and License Status (NVIDIA GRID / vGPU)
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance, Availability
- **Value:** NVIDIA vGPU and GRID licensing tie guest driver versions, hypervisor, and a license service together. A guest can boot but fall back to a restricted mode, lose hardware encode, or see session failures if the license server is unreachable, the wrong `driverVersion` is paired with a host driver, or ECC errors pass a threshold. Citrix 3D workloads, Teams optimization, and browser video offload all depend on a healthy, licensed GPU path. This use case unifies uberAgent (or an equivalent) GPU performance and license state with optional Citrix VDA hardware health. Treat driver skew across a catalog as an image problem; treat isolated license loss as a network or license server problem.
- **App/TA:** uberAgent UXM (Splunkbase 1448) with GPU monitoring enabled; NVIDIA vGPU on supported hypervisors; optional Splunk add-on for Windows for NVIDIA-sourced events
- **Data Sources:** `index=uberagent` `sourcetype="uberAgent:GPU:Performance"`, `sourcetype="uberAgent:GPU:NVIDIA"`, or host inventory GPU sourcetypes for `driverVersion`, vGPU name, `licenseState`, and utilization; `index=xd` `sourcetype="citrix:vda:events"` for Citrix agent–reported hardware state when the hypervisor and NVIDIA vGPU have integration events; `index=windows` `sourcetype="WinEventLog:System"` for NVIDIA service failures
- **SPL:**
```spl
index=uberagent (sourcetype="uberAgent:GPU:NVIDIA" OR sourcetype="uberAgent:GPU:Performance")
| eval host_name=coalesce(host, dest_host, machine)
| eval driver=coalesce(driverVersion, driver_version, nvidia_driver_version, "unknown")
| eval lic=lower(coalesce(licenseState, license_state, vgpu_license_state, "unknown"))
| eval vgpu_name=coalesce(vgpuType, vgpu_type, vgpu, "Unknown")
| eval errs=tonumber(coalesce(fatal_count, 0)) + tonumber(coalesce(uncorrectable_ecc, 0))
| where (lic!="licensed" AND lic!="ok" AND lic!="n/a" AND lic!="active") OR like(lic, "%unlic%") OR like(lic, "%fail%") OR errs>0
| stats latest(driver) as driver_version, max(lic) as license_state, latest(vgpu_name) as vgpu, max(errs) as err_signals by host_name
| table host_name, driver_version, vgpu, license_state, err_signals
```
- **Implementation:** Enable the GPU-related uberAgent options that match your hypervisor. Confirm `index=uberagent` has one row per host per minute at minimum. Build a `lookup` of approved `driverVersion` for each vGPU type and image generation. Alert when `licenseState` is not `Licensed` for more than 15 minutes, or when `driverVersion` is not in the approved list, or when fatal GPU errors increment. Excluded dedicated physical GPUs from vGPU license logic if you run mixed modes. For Citrix, tag hosts that run HDX 3D Pro policies so the alert is routed to the DaaS and NVIDIA contact points.
- **Visualization:** Table of hosts with `driverVersion`, vGPU type, and license; heatmap of license problems over time; line chart of GPU utilization for affected hosts, linked to a Citrix app session panel.
- **CIM Models:** Endpoint
- **Known false positives:** Host driver upgrades, vGPU rebalancing, and cluster rolling reboots can trip NVIDIA GRID license or driver state checks for minutes. Use host maintenance and GPU cluster change windows, with persistence after the last reboot, before a fleet GPU incident.
- **Last reviewed:** 2026-04-24

- **References:** [NVIDIA vGPU software documentation](https://docs.nvidia.com/grid/index.html), [HDX 3D Pro — Citrix (context for GPU use)](https://docs.citrix.com/en-us/citrix-virtual-apps-desktops/technical-overview/hdx-3d-pro.html)

---

### UC-2.6.56 · Citrix Cloud Service Health Status Monitoring
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Citrix Cloud publishes health for core services such as Virtual Apps and Desktops service, StoreFront-related cloud services, and Gateway components. Regional incidents or degraded subcomponents can shrink capacity, break brokering, or strand users before your internal monitors move. Ingesting normalized status events (API or add-on) into a single timeline lets operations correlate internal session drops with upstream Citrix Cloud issues, route communication faster, and avoid fruitless VDI war rooms when the root cause is provider-side.
- **App/TA:** Citrix Analytics Add-on for Splunk (Splunkbase 6280) for aggregated analytics data. For raw Cloud service data, use the Citrix Cloud System Log Add-on (open-source, see citrix/cc-system-log-addon-for-splunk repository) or poll the Monitor Service OData API (https://api.cloud.com/monitorodata) with a custom scripted input.
- **Data Sources:** `index=citrix` `sourcetype="citrix:cloud:status"` or `sourcetype="citrix:status:api"` with `component_name`, `region`, `impact`, `status`; optional HEC feed from Citrix Cloud Status page or third-party mirroring; `index=xd` `sourcetype="citrix:analytics:health"` when using Citrix Analytics Add-on for Splunk (Splunkbase 6280) for correlated service signals Note: field names in SPL are suggested conventions for custom ingestion; actual field names depend on your parsing configuration in props.conf/transforms.conf.
- **SPL:**
```spl
index=citrix (sourcetype="citrix:cloud:status" OR sourcetype="citrix:status:api")
| eval comp=coalesce(component_name, service, product, "unknown")
| eval st=lower(coalesce(status, overall_status, health, "unknown"))
| eval sev=lower(coalesce(impact, incident_severity, "none"))
| where st!="operational" AND st!="none" AND st!="healthy" OR match(sev, "(major|critical|degraded|partial)")
| stats latest(st) as status, latest(sev) as impact, latest(_time) as last_update by comp, region
| sort - last_update
| table comp, region, status, impact, last_update
```
- **Implementation:** Stand up a collector that polls the Citrix Cloud status API or streams change events at a steady interval (for example every 60 seconds) and writes one event per component per region. Normalize field names across regions. Create a lookup of business-critical components for your tenant (for example brokering, workspace, gateway). Alert when any monitored component leaves an operational state or when incident severity matches major or critical. Feed the same index from the Citrix Analytics Add-on if you use it so internal health metrics and public status share a dashboard. Document a comms template that names the component and region.
- **Visualization:** Single-value strip of red or yellow components; timeline of status flips by region; table of open incidents with start time and blast radius; overlay with session-failure rate from VDA or gateway logs.
- **CIM Models:** Application_State
- **Known false positives:** Citrix public cloud sub-service blips in one region or short vendor incidents can spike 'service down' without internal cause. Correlation with the official status page and a multi-region health check avoids paging for a 5-minute green-yellow-green flip.
- **Last reviewed:** 2026-04-24

- **References:** [Citrix Analytics Add-on for Splunk (Splunkbase 6280)](https://splunkbase.splunk.com/app/6280), [Citrix Cloud service health (product documentation)](https://docs.citrix.com/en-us/citrix-cloud/overview/citrix-cloud-service-availability.html)

---

### UC-2.6.57 · Citrix Cloud Connector Deep Health (HealthData API)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Availability
- **Value:** Basic connector heartbeats (see UC-2.6.16) prove the service is up; deep health from the HealthData API exposes resource starvation, time drift, failed outbound checks to cloud dependencies, and registration edge cases that still leave the connector process running. These conditions cause intermittent brokering delays, policy refresh gaps, and mysterious registration churn on VDAs. Aggregating API snapshots per connector gives an early, concrete signal to patch, scale out, or fix DNS and TLS paths before a resource location loses effective cloud control.
- **App/TA:** Citrix Analytics Add-on for Splunk (Splunkbase 6280) for aggregated analytics data. For raw Cloud service data, use the Citrix Cloud System Log Add-on (open-source, see citrix/cc-system-log-addon-for-splunk repository) or poll the Monitor Service OData API (https://api.cloud.com/monitorodata) with a custom scripted input.
- **Data Sources:** `index=xd` `sourcetype="citrix:cloudconnector:healthdata"` with `connector_id`, `cpu_percent`, `alert_state`, `cloud_registration`, `time_sync_status`, `dependency_check`, `failed_outbound` fields parsed from the Citrix HealthData API or Cloud Connector local health snapshots forwarded on a short interval; complementary `sourcetype="citrix:cloudconnector"` for baseline connectivity from UC-2.6.16 Note: field names in SPL are suggested conventions for custom ingestion; actual field names depend on your parsing configuration in props.conf/transforms.conf.
- **SPL:**
```spl
index=xd sourcetype="citrix:cloudconnector:healthdata"
| eval reg_ok=if(match(lower(coalesce(cloud_registration, registration_status, "")), "(registered|ok|success)"), 1, 0)
| eval sync_ok=if(match(lower(coalesce(time_sync_status, ntp_status, "")), "(synced|ok|in\ssync)"), 1, 0)
| eval dep_ok=if(tonumber(coalesce(failed_outbound, failed_dependencies, 0))=0, 1, 0)
| eval cpu=tonumber(coalesce(cpu_percent, cpu, 0))
| where reg_ok=0 OR sync_ok=0 OR dep_ok=0 OR cpu>90 OR like(lower(coalesce(alert_state, health_alert, "")), "%fail%") OR like(lower(coalesce(alert_state, health_alert, "")), "%error%")
| stats latest(cpu) as cpu_pct, latest(alert_state) as alert_state, latest(cloud_registration) as registration, latest(time_sync_status) as time_sync, max(failed_outbound) as failed_deps by host, connector_id, resource_location
| sort - cpu_pct
```
- **Implementation:** Deploy a least-privilege scheduled collector on each Cloud Connector (or a shared runner that iterates member hosts) that calls the HealthData API and emits JSON events every one to five minutes. Normalize numeric CPU and map alert flags to a small enum. Create correlation searches that ignore brief CPU spikes under two minutes. Require dual-connector hot-spares: alert when the worst two hosts in a site both show dependency failures. Retain 30 days of history for post-incident review. Co-watch with 2.6.16 so disconnections and deep health anomalies appear on one dashboard.
- **Visualization:** Connector matrix (CPU, registration, NTP, dependency failures); sparklines of failed outbound tests; overlay with VDA registration errors in the same resource location.
- **CIM Models:** Application_State
- **Known false positives:** Connector upgrades, Azure or AWS zone maintenance, and rolling Cloud Connector restarts can dip HealthData API or registration checks briefly. Require minimum healthy connector count and align with a published connector maintenance schedule.
- **Last reviewed:** 2026-04-24

- **References:** [Citrix Cloud Connector — system and connectivity requirements](https://docs.citrix.com/en-us/citrix-cloud/citrix-cloud-resource-locations/citrix-cloud-connector-installation.html), [Cloud Connector advanced functionality (troubleshooting context)](https://docs.citrix.com/en-us/citrix-cloud/citrix-cloud-resource-locations/connector-technical-details.html)

---

### UC-2.6.58 · Citrix Analytics for Performance Data Export
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance
- **Value:** Citrix Analytics for Performance scores sessions and surfaces machine and session lifecycle events with modeled user-experience metrics. When those streams land in a dedicated index, you can trend score regressions by delivery group, catch rising ICA round trip before the help desk floods, and separate image issues from home-network problems. This use case focuses on continuous performance observability and capacity-driven tuning, not on raw security forensics (see related security export use case).
- **App/TA:** Citrix Analytics Add-on for Splunk (Splunkbase 6280)
- **Data Sources:** `index=citrix` `sourcetype="citrix:analytics:performance"` with `session_id`, `user_principal`, `ux_score`, `logon_duration_ms`, `ica_rtt`, `vda_name`, `machine_event_type` from the Citrix Analytics for Performance data export via Citrix Analytics Add-on for Splunk (Splunkbase 6280); optional join to `sourcetype="citrix:vda:events"` for on-host correlation
- **SPL:**
```spl
index=citrix sourcetype="citrix:analytics:performance"
| eval score=tonumber(coalesce(ux_score, user_experience_score, session_score, -1))
| eval rtt=tonumber(coalesce(ica_rtt, round_trip_ms, 0))
| eval logon=tonumber(coalesce(logon_duration_ms, logon_ms, 0))
| where (score>0 AND score<70) OR rtt>300 OR logon>15000
| eval reason=case(score>0 AND score<70, "low_ux_score", rtt>300, "high_ica_rtt", logon>15000, "slow_logon", true(), "other")
| timechart span=1h count by reason, user_principal
| fillnull value=0
```
- **Implementation:** Complete Citrix Cloud onboarding for Analytics, enable the Performance export, and install Splunkbase 6280 on a test search head. Map exported fields to a stable schema: prefer `user_principal` and `session_id` as join keys. Build baseline weekly medians of UX score and logon time per app group. Alert on a sustained drop in median score (for example 15 points for two hours) or on percentile shifts of ICA RTT. Route reports to EUC and network teams. Mask or hash identifiers if exports leave regulated regions. Keep raw exports within retention that matches your DLP policy.
- **Visualization:** Time chart of median UX score by delivery group; scatter of logon time versus ICA RTT; table of worst sessions in the last hour with drill to machine name and region.
- **CIM Models:** Performance
- **Known false positives:** Toggling performance analytics, rebinding a tenant, or a connector upgrade can pause or reshape export volume. Check entitlements and connector version before a zero-data alert; lab toggles and pilot tenants should be in an exclusion list.
- **Last reviewed:** 2026-04-24

- **References:** [Citrix Analytics Add-on for Splunk (Splunkbase 6280)](https://splunkbase.splunk.com/app/6280), [Citrix Analytics for Performance (overview)](https://docs.citrix.com/en-us/citrix-analytics/performance.html)

---

### UC-2.6.59 · Citrix Analytics for Security Risk Indicators
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Security
- **Value:** Citrix Analytics for Security aggregates behavioral signals on access to virtual apps and data: anomalous authentication patterns, data-exfiltration heuristics, and composite insider-threat style scores. Forwarding these indicators into a security operations index lets analysts create high-fidelity detections, hunt across users and risk types, and tune response playbooks (step-up, session recording review, or account disable) without only relying on raw gateway noise. The goal is to surface the risk-ranked narrative Microsoft and Citrix already compute, enriched with your corporate identity context in downstream workflows.
- **App/TA:** Citrix Analytics Add-on for Splunk (Splunkbase 6280) — imports risk insights and associated events from Citrix Analytics for Security. Supports both Performance and Security analytics data.
- **Data Sources:** `index=citrix` `sourcetype="citrix:analytics:security"` with `risk_score`, `risk_type`, `user_principal`, `threat_vector`, `event_subtype` (anomalous sign-in, data exfiltration heuristics, compromised credential signals, insider-risk scores) ingested through Citrix Analytics Add-on for Splunk (Splunkbase 6280); optional append of `sourcetype="citrix:gateway:syslog"` for corroboration
- **SPL:**
```spl
index=citrix sourcetype="citrix:analytics:security"
| eval risk=tonumber(coalesce(risk_score, score, 0))
| eval rtype=lower(coalesce(risk_type, event_subtype, category, "unknown"))
| where risk>=70 OR like(rtype, "%exfil%") OR like(rtype, "%anomal%auth%") OR like(rtype, "%insider%")
| stats latest(risk) as max_risk, values(threat_vector) as vectors, count as event_count by user_principal, rtype
| sort - max_risk
| head 200
```
- **Implementation:** Enable the Security data export in Citrix Cloud and connect Splunkbase 6280 with least-privilege API credentials. Classify `risk_type` into SOC tiers: authentication anomalies versus exfiltration signals versus insider risk. Send critical scores (for example 85 plus) to your incident queue with a direct link to Citrix Cloud investigation. Deduplicate on `user_principal` and five-minute windows to control noise. Add identity context from your directory or HR feed via lookup. Comply with privacy review before storing raw risk text in long retention.
- **Visualization:** Stacked bar of risk events by type; top risky users table; Sankey or sequence chart from sign-in to risk event when fields allow.
- **CIM Models:** Alerts
- **Known false positives:** Purple-team, pen-test, and synthetic risk scenarios feed Citrix security analytics the same spiky indicators as real attack. Add project tags, test user lists, and time-bound exercise windows, then tune severity when only analytics risk score moves without corroboration.
- **MITRE ATT&CK:** T1078, T1110
- **Last reviewed:** 2026-04-24

- **References:** [Citrix Analytics Add-on for Splunk (Splunkbase 6280)](https://splunkbase.splunk.com/app/6280), [Citrix Analytics for Security](https://docs.citrix.com/en-us/citrix-analytics/security-analytics.html)

---

### UC-2.6.60 · Identity Provider (SAML/AAD) Integration Failures
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Availability, Security
- **Value:** Workspace and StoreFront sign-ins that rely on SAML or Microsoft Entra ID can fail when federation certificates roll without coordination, when conditional access policies block legacy protocols, or when NameID/UPN mapping between directories drifts. Users experience intermittent or total login failure while infrastructure monitors still show green VDAs. Correlating Citrix-side assertion errors with Entra sign-in results isolates the owning team (identity vs Citrix) quickly and prevents prolonged outages during certificate and trust changes.
- **App/TA:** Citrix Analytics Add-on for Splunk (Splunkbase 6280) for aggregated analytics data. For raw Cloud service data, use the Citrix Cloud System Log Add-on (open-source, see citrix/cc-system-log-addon-for-splunk repository) or poll the Monitor Service OData API (https://api.cloud.com/monitorodata) with a custom scripted input.
- **Data Sources:** `index=xd` `sourcetype="citrix:cloud:connector:saml"` or `sourcetype="citrix:workspace:saml:diag"` with `error_code`, `idp_name`, `cert_subject`, `assertion_user`; `index=azure` `sourcetype="azure:aad:signin"` for conditional access failures, certificate-based auth issues, and UPN mismatch; `index=citrix` `sourcetype="citrix:analytics:security"` optional risk layer Note: field names in SPL are suggested conventions for custom ingestion; actual field names depend on your parsing configuration in props.conf/transforms.conf.
- **SPL:**
```spl
index=xd (sourcetype="citrix:workspace:saml:diag" OR sourcetype="citrix:cloud:connector:saml")
| eval err=lower(coalesce(error_code, error, message, "")), src="citrix_saml", user=coalesce(user_principal, saml_nameid, subject)
| where like(err, "%cert%") OR like(err, "%signature%") OR like(err, "%nameid%") OR like(err, "%audience%") OR like(err, "%mismatch%") OR match(err, "(AADSTS|MSIS)")
| eval userPrincipalName=user, errorCode=err
| append [
  search index=azure sourcetype="azure:aad:signin" result!="Success"
  (resourceDisplayName="*citrix*" OR resourceDisplayName="*Citrix*" OR appDisplayName="Citrix Workspace")
  | eval src="entra_signin"
  | fields _time, userPrincipalName, result, conditionalAccessStatus, errorCode, src
  ]
| stats count by userPrincipalName, result, errorCode, src
| sort - count
```
- **Implementation:** Ingest Citrix Workspace or connector SAML diagnostic logs to a dedicated sourcetype and map certificate expiry fields. Ingest Microsoft Entra sign-in logs for applications matching Citrix. Build a time-synced join on user and a five-minute window, not a naive transaction. Alert when SAML signature or certificate errors exceed a small baseline, or when Entra returns conditional access block codes for the Citrix app only. Add change tickets for cert rotations with automatic suppression. Document IdP cert fingerprints in a lookup for drift detection. Review privacy before storing full assertion bodies.
- **Visualization:** Side-by-side timeline: Citrix SAML errors versus Entra failure codes; table of UPNs with both streams; single value of unique users blocked in one hour.
- **CIM Models:** Authentication
- **Known false positives:** IdP certificate rollover, Azure AD B2B guest quirks, and MFA enrollment bursts create transient SAML or token errors that look like integration failure. Use IdP health feeds, cert expiry lead time, and directory maintenance; ignore sub-minute blips at login peaks.
- **MITRE ATT&CK:** T1556
- **Last reviewed:** 2026-04-24

- **References:** [Citrix Cloud identity providers and authentication](https://docs.citrix.com/en-us/citrix-cloud/citrix-cloud-management/identity-providers-in-citrix-cloud.html), [Splunk add-on: Microsoft Cloud Services (Entra / Azure data)](https://splunkbase.splunk.com/app/3110)

---

### UC-2.6.61 · Citrix HDX Rendezvous Protocol Path Selection
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance
- **Value:** HDX Rendezvous lets sessions establish through direct UDP paths with STUN when possible, and fall back to relayed transport when firewalls, symmetric NAT, or port blocks get in the way. A high relay ratio or STUN failure clusters often point to home-router settings, guest Wi-Fi, or data-center egress rules rather than the VDA image. Monitoring path selection, Rendezvous v2 adoption, and UDP blockage patterns helps the right team tune Gateway, DTLS, and client policy before remote users see chronic latency, dropped multimedia, and unstable Teams inside sessions.
- **App/TA:** Citrix Analytics Add-on for Splunk (Splunkbase 6280) for aggregated analytics data. For raw Cloud service data, use the Citrix Cloud System Log Add-on (open-source, see citrix/cc-system-log-addon-for-splunk repository) or poll the Monitor Service OData API (https://api.cloud.com/monitorodata) with a custom scripted input.
- **Data Sources:** `index=xd` `sourcetype="citrix:hdx:rendezvous"` or VDA/Session diagnostics with `rendezvous_path` (`direct` vs `relay`), `stun_status`, `udp_blocked`, `nat_type`, `rendezvous_version`; optional `sourcetype="citrix:gateway:connection"` for combined path; uberAgent or IP flow telemetry in parallel for home-office ISP issues Note: field names in SPL are suggested conventions for custom ingestion; actual field names depend on your parsing configuration in props.conf/transforms.conf.
- **SPL:**
```spl
index=xd (sourcetype="citrix:hdx:rendezvous" OR (sourcetype="citrix:vda:events" event_type="*rendezvous*"))
| eval path=lower(coalesce(rendezvous_path, path_mode, connection_path, "unknown"))
| eval stun=lower(coalesce(stun_status, stun, "unknown"))
| eval udp_block=if(match(lower(coalesce(udp_blocked, "")), "(true|yes|1|blocked)"), 1, 0)
| eval ver=coalesce(rendezvous_version, rv2_version, "na")
| where path="relay" OR udp_block=1 OR stun!="ok" OR match(lower(coalesce(nat_type, "")), "(sym|symmetric|strict)")
| stats count by host, user, path, stun, udp_block, nat_type, ver
| sort - count
```
- **Implementation:** Enable the enhanced rendezvous or HDX connection diagnostics in Citrix that emit path mode. Forward those events to `index=xd` with a stable sourcetype. Parse boolean UDP-block flags when present. Create weekly baselines: percentage relay versus direct by region and by client build. Alert when relay share jumps more than 20 points versus the rolling median for a region, or when symmetric NAT count spikes after a home-router firmware wave. Work with network teams to document required UDP and DTLS allow rules. Pair with Citrix Workspace app version compliance.
- **Visualization:** Stacked 100% bar: direct vs relay by region; map of STUN failure counts; time chart of rendezvous v2 share across clients.
- **CIM Models:** Network_Traffic
- **Known false positives:** Firewall and routing changes during rendezvous and EDT pilots deliberately shift 'direct' versus 'cloud' path. Document expected path per group; alert when production cohorts fall back across both paths without a matching change, not a single pilot user.
- **Last reviewed:** 2026-04-24

- **References:** [HDX direct connections (Rendezvous) — product documentation](https://docs.citrix.com/en-us/citrix-virtual-apps-desktops/technical-overview/hdx-direct-connections.html), [Citrix Gateway and rendezvous (deployment context)](https://docs.citrix.com/en-us/citrix-gateway/13-1-citrix-gateway-federation-integration.html)

---

### UC-2.6.62 · Citrix Workspace Service Feed Availability
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** The Citrix Workspace service must enumerate feeds, aggregate resources from brokering and cloud sources, and stay responsive over HTTPS. Certificate problems, API throttling, or connector outages can produce empty start menus, missing apps, or flapping resource lists that mimic client bugs. Synthetics and server-side feed diagnostics measure availability and latency to the user-facing document endpoints and tie failures to a specific store, region, or IDP, shortening mean time to restore before broad ticket spikes.
- **App/TA:** Citrix Analytics Add-on for Splunk (Splunkbase 6280) for aggregated analytics data. For raw Cloud service data, use the Citrix Cloud System Log Add-on (open-source, see citrix/cc-system-log-addon-for-splunk repository) or poll the Monitor Service OData API (https://api.cloud.com/monitorodata) with a custom scripted input.
- **Data Sources:** `index=xd` `sourcetype="citrix:workspace:feed"` with `feed_url`, `http_status`, `latency_ms`, `store_name`, `resource_count`, `error_code`; client-side or synthetic probe events from StoreFront/Workspace; optional `sourcetype="citrix:cloud:connector:svc"` for dependency failures affecting aggregation Note: field names in SPL are suggested conventions for custom ingestion; actual field names depend on your parsing configuration in props.conf/transforms.conf.
- **SPL:**
```spl
index=xd sourcetype="citrix:workspace:feed"
| eval ok=if(match(coalesce(http_status, status, "200"), "^(200|204)$"), 1, 0)
| eval lat=tonumber(coalesce(latency_ms, response_time_ms, 0))
| where ok=0 OR lat>2000 OR tonumber(coalesce(resource_count, -1))=0
| eval issue=case(ok=0, "http_or_feed_error", lat>2000, "high_latency", tonumber(coalesce(resource_count,0))=0, "empty_catalog", true(), "other")
| timechart span=5m count by issue, store_name
| fillnull value=0
```
- **Implementation:** Deploy both passive logs (if available from Citrix) and a lightweight synthetic that requests the same feed entry points the clients use, tagged by region. Send results to a dedicated index with five-minute resolution. Set SLOs (for example 99.9 percent under one second) per region. Alert on two consecutive non-200 responses, zero resources returned for any active directory group, or latency above two seconds. Pair alerts with 2.6.16 and 2.6.60 when the failure is identity-related. Keep separate dashboards for on-premises stores versus cloud Workspace.
- **Visualization:** Uptime and latency SLO by region; heatmap of feed errors; single value: resources returned versus expected baseline from yesterday same hour.
- **CIM Models:** Application_State
- **Known false positives:** CDN or public DNS hiccups and Workspace app cache refresh during brand changes can depress feed availability for everyone. External synthetic and provider status, plus internal app publishing, separate vendor blips from StoreFront or broker issues.
- **Last reviewed:** 2026-04-24

- **References:** [Citrix Workspace app — technical overview and connectivity](https://docs.citrix.com/en-us/citrix-workspace-app-for-windows.html), [Configure Workspace experience (Citrix DaaS)](https://docs.citrix.com/en-us/citrix-daas-service/integrate-identity-serve-apps-and-data.html)

---

### UC-2.6.63 · DaaS Autoscale Cloud Economics Tracking
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Capacity
- **Value:** DaaS autoscale can chase session demand, but public-cloud bills reflect clock time, instance families, and lingering powered-on capacity as much as user counts. Blending host-pool or delivery-group session peaks with tag-aligned cloud spend shows scale-out efficiency, expensive idle headroom, and cost-per-active-session trends. Finance and platform teams get a defensible way to right-size buffer percentages, change instance SKUs, or tune shutdown aggressiveness without only trusting static dashboards in the admin consoles.
- **App/TA:** Citrix Analytics Add-on for Splunk (Splunkbase 6280) for aggregated analytics data. For raw Cloud service data, use the Citrix Cloud System Log Add-on (open-source, see citrix/cc-system-log-addon-for-splunk repository) or poll the Monitor Service OData API (https://api.cloud.com/monitorodata) with a custom scripted input.
- **Data Sources:** `index=cloud` or `index=azure` `sourcetype="azure:consume:export"` with `cost`, `resource_id`, `tag_pool`, `meter`; `index=xd` `sourcetype="citrix:mc:autoscale"` with `power_action`, `machine_count`, `session_count`, `host_pool`; `index=xd` `sourcetype="citrix:brokering:summary"` for active sessions; optional FinOps CSV via `inputlookup`
- **SPL:**
```spl
index=cloud sourcetype="azure:consume:export" (resource_type="*compute*" OR resource_type="*virtual*")
| eval tag_pool=if(isnotnull(citrix_host_pool) AND citrix_host_pool!="", citrix_host_pool, coalesce(resource_name, resource_id, "unmapped"))
| bin _time span=1d
| stats sum(tonumber(cost,0)) as daily_cost by _time, tag_pool
| join type=left _time, tag_pool [
  search index=xd (sourcetype="citrix:mc:autoscale" OR sourcetype="citrix:brokering:summary")
  | eval tag_pool=coalesce(host_pool, delivery_group, catalog_name, "unmapped")
  | bin _time span=1d
  | stats max(session_count) as peak_sessions, latest(machine_count) as reported_machines by _time, tag_pool
  ]
| eval cost_per_session=if(peak_sessions>0, round(daily_cost/peak_sessions,3), null())
| where isnotnull(daily_cost) AND daily_cost>0
| table _time, tag_pool, daily_cost, peak_sessions, reported_machines, cost_per_session
```
- **Implementation:** Tag or label cloud VMs with a stable `citrix_host_pool` value matching Splunk's brokering or MCS data. Ingest a daily (or hourly) cost feed with the same key. Build weekly reports: cost per session by pool, unused powered-on hours, and autoscale event counts versus cost deltas. Set soft alerts for sudden jumps in cost-per-session or sustained idle high-water marks after scale events. Engage FinOps to validate currency and amortization. Never alert on cost alone without a session denominator except for obvious billing anomalies. Document that bursty test traffic can skew short windows.
- **Visualization:** Line chart of cost per session by pool; stacked area of instance hours paid versus sessions; table of autoscale power actions and next-day cost impact.
- **CIM Models:** Performance
- **Known false positives:** Reserved instances, committed use, and org-wide 'always on' capacity for compliance can make idle-looking cloud spend look 'bad' in a simple dollars-per-day cap. Join FinOps baselines and the business minimum seat count, not a lone threshold.
- **Last reviewed:** 2026-04-24

- **References:** [Autoscale in Citrix DaaS](https://docs.citrix.com/en-us/citrix-daas-service-delivery-machines/delivery-groups/autoscale-daas.html), [Microsoft Cost Management (export cost data to external tools)](https://learn.microsoft.com/en-us/azure/cost-management-billing/costs/analyze-cost-data-azure)

---

### UC-2.6.64 · Citrix Endpoint Management Device Enrollment Failures
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Citrix Endpoint Management (CEM) enrollments that fail by Azure AD, identity-provider, or gateway-based flows strand devices without the policies and secure channels you expect. A rising failure rate in one method (for example AAD) often foreshadows certificate or conditional-access changes rather than a bad device. Tracking failures by method and MDM versus MAM split, with hourly trends, helps operations separate widespread identity drift from a flaky Wi-Fi at one site, and it pairs naturally with the certificate and compliance use cases in the same runbooks.
- **App/TA:** No official Splunk TA for Citrix Endpoint Management. Ingest via syslog from XenMobile Server, or use the Citrix Analytics Add-on for Splunk (Splunkbase 6280) which imports CEM risk indicators from Citrix Analytics for Security. For on-premises XenMobile, forward syslog and JMX metrics via Universal Forwarder. Suggested custom sourcetypes follow the `citrix:endpoint:*` convention.
- **Data Sources:** `index=mdm` or `index=xd` `sourcetype="citrix:endpoint:enrollment"` with `enrollment_method` (`AAD`, `idp`, `gateway`, `scep`), `mdms_scope` (full MDM vs MAM), `outcome` (`success`/`failed`), `error_code`, `device_platform`, `user_id`; server logs from Citrix Endpoint Management (on-premises or cloud connector) forwarded with stable timestamps Note: field names in SPL are suggested conventions for custom ingestion; actual field names depend on your parsing configuration in props.conf/transforms.conf.
- **SPL:**
```spl
index=xd sourcetype="citrix:endpoint:enrollment" outcome!="success"
| eval method=upper(coalesce(enrollment_method, channel, "UNKNOWN"))
| eval mode=coalesce(mdms_scope, mdm_mam, enrollment_mode, "unknown")
| eval platform=coalesce(device_platform, os_type, "unknown")
| bin _time span=1h
| stats count as failures, dc(error_code) as unique_errors by _time, method, mode, platform
| where failures>=5
| sort - _time, failures
```
- **Implementation:** Stream enrollment transactions from the CEM service or appliance into a dedicated index and sourcetype. Normalize `outcome` to lower case. Add a small lookup of acceptable error rates per platform. Alert when hourly non-success events exceed a rolling four-hour baseline by 300 percent, or any single error code appears more than 50 times in an hour. Provide a dashboard by enrollment method and region. Separate corporate-owned and BYOD cohorts if your data model supports it. Coordinate with the identity team when AAD- or IdP-tagged failures lead the chart.
- **Visualization:** Time chart: enrollment failures by method; bar chart: MDM versus MAM failure share; drill table with top error_code and last device sample IDs (masked).
- **CIM Models:** Change
- **Known false positives:** New device season, OS refresh, and OTA mass pushes spike enrollment errors in absolute count. Use success-rate floors and the enrollment campaign ID; raw failure counts without cohort size are often false volume.
- **Last reviewed:** 2026-04-24

- **References:** [Citrix Endpoint Management product documentation](https://docs.citrix.com/en-us/citrix-endpoint-management.html)

---

### UC-2.6.65 · Citrix Endpoint Management MDM/MAM Policy Compliance
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance, Security
- **Value:** MDM and MAM policies express your minimum security bar: no jailbreak or root, current OS patch bands, a real passcode, and no disallowed applications. CEM can emit compliance state per device and per policy package. A rising non-compliant population after an OS release, or a sudden bloom of blacklisted app hits, is often your first sign of shadow IT or stolen devices on the same fleet as your regulated data. This use case drives executive-friendly compliance rate charts and high-severity security alerts in one place.
- **App/TA:** No official Splunk TA for Citrix Endpoint Management. Ingest via syslog from XenMobile Server, or use the Citrix Analytics Add-on for Splunk (Splunkbase 6280) which imports CEM risk indicators from Citrix Analytics for Security. For on-premises XenMobile, forward syslog and JMX metrics via Universal Forwarder. Suggested custom sourcetypes follow the `citrix:endpoint:*` convention.
- **Data Sources:** `index=xd` `sourcetype="citrix:endpoint:compliance"` with `jailbreak_flag`, `root_flag`, `os_patch_level`, `passcode_compliant`, `blacklisted_app_hit`, `device_id`, `compliance_state`; CEM device inventory or compliance export jobs Note: field names in SPL are suggested conventions for custom ingestion; actual field names depend on your parsing configuration in props.conf/transforms.conf.
- **SPL:**
```spl
index=xd sourcetype="citrix:endpoint:compliance"
| eval jf=if(match(lower(coalesce(jailbreak_flag, jailbroken, is_compromised, "no")), "(1|true|yes)"), 1, 0)
| eval rf=if(match(lower(coalesce(root_flag, rooted, "no")), "(1|true|yes)"), 1, 0)
| eval pc=if(match(lower(coalesce(passcode_compliant, has_pin, "yes")), "(0|false|no)"), 0, 1)
| eval bad_app=if(tonumber(coalesce(blacklisted_app_hit, blocked_app, 0))>0, 1, 0)
| where jf=1 OR rf=1 OR pc=0 OR bad_app=1 OR lower(coalesce(compliance_state, ""))!="compliant"
| eval reason=case(jf=1, "jailbreak", rf=1, "root", pc=0, "passcode", bad_app=1, "blacklist_app", true(), "other")
| stats values(device_id) as sample_devices, latest(os_patch_level) as patch_level, count as events by user_id, reason
| sort - events
```
- **Implementation:** Ingest a daily (or more frequent) compliance snapshot, not only raw real-time if volume is high. Map vendor booleans to consistent integer flags. Create an overall `compliance_percent` for managed devices. Alert on any jailbreak or root true, any blacklisted app install on a corporate-owned tag, and sustained passcode false on more than five percent of a business unit. Pair with asset ownership lookups. For regulated industries, route evidence exports to your GRC archive with retention that matches policy. Reconcile counts with the CEM admin console during rollout.
- **Visualization:** Donut: compliant versus not; bar: reasons for failure; line: compliance percent by OS major version across months.
- **CIM Models:** Endpoint
- **Known false positives:** Grace periods after a new compliance or passcode policy and BYOD catch-up can lag for days. Compare event rate to the policy version rollout and exclude a 24–48 h post-push window; BYOD in the lookup needs different baselines than corporate fully managed.
- **MITRE ATT&CK:** T1562
- **Last reviewed:** 2026-04-24

- **References:** [Compliance policies in Citrix Endpoint Management](https://docs.citrix.com/en-us/citrix-endpoint-management/citrix-endpoint-mdm-mam.html)

---

### UC-2.6.66 · Citrix Endpoint Management App Distribution Failures
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Pushing in-house, store, and volume-purchase programs (VPP) apps through CEM depends on correct tokens, licenses, and platform-specific constraints. A burst of VPP or enterprise install failures is often an Apple Business Manager or Google side issue; steady enterprise failures can point to signing or package corruption. This use case breaks down failures by channel so mobile operations can open the right vendor ticket, roll back a bad build, or fix token drift without re-imaging the whole estate.
- **App/TA:** No official Splunk TA for Citrix Endpoint Management. Ingest via syslog from XenMobile Server, or use the Citrix Analytics Add-on for Splunk (Splunkbase 6280) which imports CEM risk indicators from Citrix Analytics for Security. For on-premises XenMobile, forward syslog and JMX metrics via Universal Forwarder. Suggested custom sourcetypes follow the `citrix:endpoint:*` convention.
- **Data Sources:** `index=xd` `sourcetype="citrix:endpoint:app:deploy"` with `app_id`, `app_name`, `action` (`install`/`update`), `outcome`, `error_category` (`VPP`, `app_store`, `enterprise`, `mdm_push`), `device_platform`, `user_id`, `vpp_code` when available Note: field names in SPL are suggested conventions for custom ingestion; actual field names depend on your parsing configuration in props.conf/transforms.conf.
- **SPL:**
```spl
index=xd sourcetype="citrix:endpoint:app:deploy" outcome!="success"
| eval cat=lower(coalesce(error_category, failure_bucket, app_source, "unknown"))
| eval app=coalesce(app_name, app_id, "unknown")
| eval plat=coalesce(device_platform, os_type, "unknown")
| where like(cat, "%vpp%") OR like(cat, "%app%store%") OR like(cat, "%enterprise%") OR like(cat, "%push%") OR isnotnull(vpp_code)
| timechart span=1h count by cat, plat
| fillnull value=0
```
- **Implementation:** Ingest CEM app deployment or command-result logs. Tag errors into coarse buckets (VPP, public store, enterprise/internal). Mask user identifiers in shared dashboards. Alert when failures for a specific `app_id` cross a threshold in two consecutive hours, or when VPP-scoped errors exceed the prior week at the same time of day. Keep a runbook for common codes (license exhausted, not compatible OS, app removed from store). Pair with app owners so version bumps are not silent. Rate-limit noisy beta cohorts in test rings.
- **Visualization:** Stacked area of failures by error bucket; top failing apps table; link from `vpp_code` to Apple’s code reference where applicable.
- **CIM Models:** Change
- **Known false positives:** Mass in-house app signings, App Store re-releases, and line-of-business app updates can fail in parallel for reasons unrelated to attack. Time-correlate with MAM app version publish and the signing cert rotation ticket before user-level malware assumptions.
- **Last reviewed:** 2026-04-24

- **References:** [Distribute and manage mobile apps in Citrix Endpoint Management](https://docs.citrix.com/en-us/citrix-endpoint-management/mdm-mam/endpoint-management-mdm-mam-mdx-apps.html)

---

### UC-2.6.67 · Citrix Endpoint Management Device Certificate Expiry
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Value:** Managed devices rely on short-lived user certificates, profile-managed identities, and sometimes enterprise signing or SCEP-issued device identities. A missed renewal quietly breaks Wi-Fi, per-app data protection, and secure mail—often showing up as vague connectivity tickets. CEM and PKI can expose `not_after` and renewal attempts. This use case finds certificates inside a 30-day window, flags renewal failures, and gives compliance teams a defensible, time-bounded list of devices to retire or re-enroll before hard outages.
- **App/TA:** No official Splunk TA for Citrix Endpoint Management. Ingest via syslog from XenMobile Server, or use the Citrix Analytics Add-on for Splunk (Splunkbase 6280) which imports CEM risk indicators from Citrix Analytics for Security. For on-premises XenMobile, forward syslog and JMX metrics via Universal Forwarder. Suggested custom sourcetypes follow the `citrix:endpoint:*` convention.
- **Data Sources:** `index=xd` `sourcetype="citrix:endpoint:cert"` with `cert_type` (`user`, `scep`, `profile`, `signing`), `not_after`, `not_before`, `device_id`, `template_name`, `renewal_status`, `error_on_renew`; CEM or SCEP gateway logs; optional public PKI event stream Note: field names in SPL are suggested conventions for custom ingestion; actual field names depend on your parsing configuration in props.conf/transforms.conf.
- **SPL:**
```spl
index=xd sourcetype="citrix:endpoint:cert"
| eval expire_epoch=strptime(coalesce(not_after, expiry_utc, ""), "%Y-%m-%dT%H:%M:%S%Z")
| eval days_left=floor((expire_epoch-now())/86400)
| eval renew_ok=if(match(lower(coalesce(renewal_status, "")), "(ok|success|pending)"), 1, 0)
| where (days_left<=30 OR isnull(expire_epoch)) OR renew_ok=0 OR like(lower(coalesce(error_on_renew, "")), "%fail%")
| sort days_left
| table device_id, cert_type, template_name, days_left, renewal_status, error_on_renew, _time
```
- **Implementation:** Ingest a daily export of all managed certificates, or event-driven renewal logs. Standardize to UTC. Build sliding windows: critical at 7 days, warning at 30 days. Alert on any renewal error with a non-empty `error_on_renew`. Join to asset ownership to email queue owners, not the whole org. Reconcile with your PKI or SCEP service logs; dual-source if possible. If `not_after` is sometimes missing, fall back to last-known `template_name` and schedule forced re-pushes. Document emergency procedures for wide-scale root rotation.
- **Visualization:** Gantt or bar of devices by days to expiry; single value: count of certs under 7 days; table of failed renewals in the last 24 hours.
- **CIM Models:** Certificates
- **Known false positives:** Staged cert rotation and renewed SCEP profiles on a device subset look like a sudden expiry cluster. Per-profile expected renewal dates in a lookup separate planned rotation from a real expiration crisis.
- **Last reviewed:** 2026-04-24

- **References:** [Certificate security in Citrix Endpoint Management (modeled overview)](https://docs.citrix.com/en-us/citrix-endpoint-management/citrix-endpoint-mdm-mam.html)

---

### UC-2.6.68 · Citrix Endpoint Management Remote Wipe/Lock Action Tracking
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Remote lock and wipe are the last line when a device is lost or a user leaves under duress. Stalled, failed, or abnormally slow commands can leave data exposed longer than policy allows, while repeated failures may indicate a rooted device or network blocks. CEM can emit the MDM command lifecycle. This use case reports success rate, median latency, and long-tail timeouts by action type, and it feeds security and audit teams a durable trail of who requested each destructive action and whether it completed.
- **App/TA:** No official Splunk TA for Citrix Endpoint Management. Ingest via syslog from XenMobile Server, or use the Citrix Analytics Add-on for Splunk (Splunkbase 6280) which imports CEM risk indicators from Citrix Analytics for Security. For on-premises XenMobile, forward syslog and JMX metrics via Universal Forwarder. Suggested custom sourcetypes follow the `citrix:endpoint:*` convention.
- **Data Sources:** `index=xd` `sourcetype="citrix:endpoint:mdm:command"` with `action` (`wipe`, `lock`, `reset`, `unenroll`), `outcome` (`acknowledged`, `completed`, `failed`, `timeout`), `latency_ms`, `device_id`, `requester`, `incident_id`; CEM admin audit of remote actions if emitted separately to `sourcetype="citrix:endpoint:audit"` Note: field names in SPL are suggested conventions for custom ingestion; actual field names depend on your parsing configuration in props.conf/transforms.conf.
- **SPL:**
```spl
index=xd sourcetype="citrix:endpoint:mdm:command" action IN ("wipe","lock","reset","unenroll")
| eval ok=if(match(lower(coalesce(outcome, status, "")), "(completed|acknowledged|success)"), 1, 0)
| eval late=if(tonumber(coalesce(latency_ms, 0))>120000, 1, 0)
| where ok=0 OR late=1
| eval action=upper(action)
| timechart span=1h count by action, outcome
| fillnull value=0
```
- **Implementation:** Ensure both the command result stream and a tamper-resistant admin audit of `requester` and business justification (ticket id) are present. Set RTO expectations (for example lock within two minutes on cellular). Page security operations on any `wipe` or `unenroll` that fails or exceeds latency SLO, with device last-seen time for triage. Weekly review of counts versus HR-driven terminations. Retain 13 months in line with HR and privacy counsel. Suppress test-lab device IDs. Never send full device payloads to a shared room without masking sensitive fields.
- **Visualization:** Gauge: success rate by action; timeline of long-running commands; table of failed devices with `requester` and `incident_id`.
- **CIM Models:** Endpoint
- **Known false positives:** HR terminations, lost-device workflows, and security-driven remote lock are legitimate high-volume events. Join HR tickets or service desk 'lost device' cases; a wipe without a ticket in the batch window is the real finding.
- **MITRE ATT&CK:** T1485
- **Last reviewed:** 2026-04-24

- **References:** [Device security actions (enterprise mobility — Apple/Android context)](https://docs.citrix.com/en-us/citrix-endpoint-management/citrix-endpoint-mdm-mam/endpoint-management-mdm-mam-cio.html)

---

### UC-2.6.69 · Citrix Endpoint Management Server Health
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Availability
- **Value:** The Citrix Endpoint Management application tier sits on a JVM, a relational database, and background schedulers that push policy and app commands. Thread starvation, pool exhaustion, or a stuck job queue can surface as flapping device check-ins and mass policy drift before a simple `ping` fails. Server-side health metrics plus SSL and database utilization give a root-cause-friendly picture that complements per-device UCs. Certificate expiry on the CEM public endpoint is a classic near-miss that full-stack monitoring should never leave to an annual calendar reminder alone.
- **App/TA:** No official Splunk TA for Citrix Endpoint Management. Ingest via syslog from XenMobile Server, or use the Citrix Analytics Add-on for Splunk (Splunkbase 6280) which imports CEM risk indicators from Citrix Analytics for Security. For on-premises XenMobile, forward syslog and JMX metrics via Universal Forwarder. Suggested custom sourcetypes follow the `citrix:endpoint:*` convention.
- **Data Sources:** `index=main` or `index=app` with `sourcetype="citrix:endpoint:server:health"` or JMX/log-derived metrics: `jvm_thread_blocked`, `db_pool_in_use`, `db_pool_max`, `scheduler_backlog`, `queue_depth`, `ssl_cert_expiry_date`; `sourcetype="WinEventLog:Application"` for Java and database errors on Windows-hosted CEM; `localhost_access_log` (application server) sourcetype if applicable; Linux `sourcetype="syslog"` for appliances Note: field names in SPL are suggested conventions for custom ingestion; actual field names depend on your parsing configuration in props.conf/transforms.conf.
- **SPL:**
```spl
index=app (sourcetype="citrix:endpoint:server:health" OR sourcetype="citrix:cep:jmx")
| eval blocked=tonumber(coalesce(jvm_thread_blocked, blocked_threads, 0))
| eval db_use=tonumber(coalesce(db_pool_in_use, db_active, 0))
| eval db_max=tonumber(coalesce(db_pool_max, db_total, 1))
| eval back=tonumber(coalesce(scheduler_backlog, job_queue, async_queue, 0))
| eval cert_days=if(isnotnull(ssl_cert_expiry_date), round((strptime(ssl_cert_expiry_date,"%Y-%m-%d")-now())/86400,0), null())
| eval db_pct=if(db_max>0, round(100*db_use/db_max,1), 0)
| where blocked>50 OR back>1000 OR db_pct>90 OR (isnotnull(cert_days) AND cert_days<=30)
| stats latest(blocked) as blocked, latest(db_pct) as db_pool_util_pct, latest(back) as queue_backlog, latest(cert_days) as ssl_cert_days_left by host, role
| sort - db_pool_util_pct
```
- **Implementation:** Instrument each CEM node: JVM thread dumps on alert, JDBC pool via JMX, scheduler backlog from application logs, and a synthetic login or API every five minutes. Forward Windows or Linux system logs. Alert in stages: queue backlog over a static threshold, DB pool over 90 percent for ten minutes, blocked threads over 50 for two samples, and SSL cert under 30 days. Pair with database server KPIs. Document rolling patch windows and scale-out when a single node saturates. Keep an HA pair or cluster view so you alert on the worst node and the cluster average.
- **Visualization:** Node grid: pool percent, queue depth, blocked threads; line chart: backlog with deploy markers; cert countdown single value for public VIP.
- **CIM Models:** Application_State
- **Known false positives:** EMM database maintenance, index jobs, and load balancer or SSL work on the CEM server tier can return slow or error responses that resemble outage. EMM maint tags on app and DB, plus a sustained 5xx rate, filter single blips.
- **Last reviewed:** 2026-04-24

- **References:** [Citrix Endpoint Management — supported topologies and sizing context](https://docs.citrix.com/en-us/citrix-endpoint-management/citrix-endpoint-mdm-mam.html)

---

### UC-2.6.70 · Citrix ShareFile Storage Zone Controller Health
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** ShareFile content collaboration depends on healthy Storage Zone Controllers and connectors. Monitoring zone online state, synchronization backlog, split between on-premises and cloud-hosted zones, and connector health early exposes outages, replication stalls, and hybrid path failures that block file access, uploads, and business workflows.
- **App/TA:** No official Splunk TA for ShareFile. Ingest audit trail via ShareFile REST API (https://api.sharefile.com) to HEC with a custom scripted input or Splunk Add-on Builder. Suggested custom sourcetype: `citrix:sharefile:audit`. Optionally correlate with Citrix Analytics Add-on for Splunk (Splunkbase 6280) for aggregated risk indicators.
- **Data Sources:** `index=sharefile` `sourcetype="citrix:sharefile:storagezone"` (zone state, service heartbeat, sync queue depth, connector status); optional `sourcetype="citrix:sharefile:connector"` for Storage Zone Connectors; fields like `zone_id`, `zone_state`, `sync_backlog`, `hosting_mode` (on_prem|cloud), `connector_health` Note: field names in SPL are suggested conventions for custom ingestion; actual field names depend on your parsing configuration in props.conf/transforms.conf.
- **SPL:**
```spl
index=sharefile (sourcetype="citrix:sharefile:storagezone" OR sourcetype="citrix:sharefile:connector")
| eval zone_ok=if(match(lower(zone_state),"(?i)online|healthy|up"),1,0), backlog=tonumber(coalesce(sync_backlog, queue_depth, 0)), conn_ok=if(match(lower(connector_health),"(?i)ok|up|connected") OR isnull(connector_health),1,0)
| bin _time span=5m
| stats min(zone_ok) as min_zone, max(backlog) as max_backlog, min(conn_ok) as min_connector, values(hosting_mode) as hosting by zone_id, _time
| where min_zone=0 OR max_backlog>10000 OR min_connector=0
| table _time, zone_id, hosting, min_zone, max_backlog, min_connector
```
- **Implementation:** Ingest Storage Zone Controller and Storage Zone Connector logs (syslog, file, or API export) with consistent timestamps and time zones. Tag each zone with `hosting_mode` to separate on-prem vs customer-managed cloud. Define backlog thresholds from your baseline; alert when a zone is not online, backlog grows beyond an agreed cap, or any connector is unhealthy. Pair with Citrix Cloud status and network path tests for the control plane if applicable.
- **Visualization:** Single-value: zones unhealthy count; timechart: max sync backlog by zone; table: zone_id, hosting_mode, min zone state, max backlog, connector health; pie or bar: on-prem vs cloud event volume (sanity for split reporting).
- **CIM Models:** Application_State
- **Known false positives:** Storage zone controller OS patching, SSL updates, and LB health flaps can look like a storage outage when both nodes bounce. A planned maintenance flag on the SZC pair and a dual-node quorum check avoid false SEV-1s on a rolling upgrade.
- **Last reviewed:** 2026-04-24

- **References:** [Citrix — StorageZones Controller](https://docs.citrix.com/en-us/citrix-content-collaboration/storage-zones-controller/4-storage-zones-controllers.html)

---

### UC-2.6.71 · Citrix ShareFile DLP Policy Violation Tracking
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Security, Compliance
- **Value:** Data loss prevention in ShareFile surfaces policy hits, enforcements (block vs warn), and classification outcomes. Tracking hit volume, block and warn rates, trends that look like false positives, and file classification mismatches helps security and privacy teams prove control effectiveness, tune policies, and respond before regulated data leaves approved channels.
- **App/TA:** No official Splunk TA for ShareFile. Ingest audit trail via ShareFile REST API (https://api.sharefile.com) to HEC with a custom scripted input or Splunk Add-on Builder. Suggested custom sourcetype: `citrix:sharefile:audit`. Optionally correlate with Citrix Analytics Add-on for Splunk (Splunkbase 6280) for aggregated risk indicators.
- **Data Sources:** `index=sharefile` `sourcetype="citrix:sharefile:dlp"` or DLP/secure collaboration feed; fields `action` (block|warn|audit), `policy_id`, `policy_name`, `classification_mismatch`, `file_path`, `user`, `false_positive` (if your feed tags analyst overrides) Note: field names in SPL are suggested conventions for custom ingestion; actual field names depend on your parsing configuration in props.conf/transforms.conf.
- **SPL:**
```spl
index=sharefile sourcetype="citrix:sharefile:dlp" earliest=-24h
| eval action=lower(coalesce(action, outcome, "unknown")), is_fp=if(match(lower(false_positive),"(?i)true|yes|1"),1,0), mismatch=if(match(lower(classification_mismatch),"(?i)true|yes|1"),1,0)
| bin _time span=1h
| stats count as hits, sum(eval(action="block")) as blocks, sum(eval(action="warn")) as warns, sum(is_fp) as fp_tags, sum(mismatch) as class_mismatches by _time, policy_id, user
| eval block_rate=round(100*blocks/hits,2), warn_rate=round(100*warns/hits,2)
| where blocks>0 OR warns>0 OR class_mismatches>0
| table _time, policy_id, user, hits, block_rate, warn_rate, fp_tags, class_mismatches
```
- **Implementation:** Ingest DLP or ShareFile security events with stable policy identifiers. Retain long enough for compliance reporting. Create hourly rollups and weekly anomaly review for `false_positive` spikes. For mismatches, join to label or sensitivity taxonomy in a lookup. Escalate sudden block-rate drops (possible policy bypass) and sustained warn-only surges (possible business friction).
- **Visualization:** Stacked bar: block vs warn by policy; timechart: false-positive tagged rate; table: top users and policies by hits; line: classification mismatch count.
- **CIM Models:** DLP
- **Known false positives:** Legal hold exports, e-discovery, and DLP-authorized large pulls for audits look like user policy violations in volume. Require a DLP case or legal matter ID; exclude known bulk export service accounts in the business lookup.
- **MITRE ATT&CK:** T1567, T1039
- **Last reviewed:** 2026-04-24

- **References:** [Citrix — Data loss prevention for ShareFile](https://docs.citrix.com/en-us/citrix-content-collaboration/data-loss-prevention.html)

---

### UC-2.6.72 · Citrix ShareFile Mass Download and Data Exfiltration Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Security
- **Value:** Unusual file movement through ShareFile can indicate exfiltration: large or repeated downloads, bursts of public link creation, off-hours bulk export, and access from anomalous locations. This use case focuses on high-signal mass behaviors rather than every single file open so analysts can respond quickly to theft or account abuse.
- **App/TA:** No official Splunk TA for ShareFile. Ingest audit trail via ShareFile REST API (https://api.sharefile.com) to HEC with a custom scripted input or Splunk Add-on Builder. Suggested custom sourcetype: `citrix:sharefile:audit`. Optionally correlate with Citrix Analytics Add-on for Splunk (Splunkbase 6280) for aggregated risk indicators.
- **Data Sources:** `index=sharefile` `sourcetype="citrix:sharefile:audit"` (file download, link access); optional `sourcetype="citrix:sharefile:api"` for public link creation; fields `user`, `event_type`, `bytes`, `file_count`, `link_type` (public|internal), `client_ip` Note: field names in SPL are suggested conventions for custom ingestion; actual field names depend on your parsing configuration in props.conf/transforms.conf.
- **SPL:**
```spl
index=sharefile (sourcetype="citrix:sharefile:audit" OR sourcetype="citrix:sharefile:api") earliest=-24h
| eval evt=lower(coalesce(event_type, action, "")), is_dl=if(match(evt, "(?i)download|fetch|get"),1,0), is_link=if(match(evt, "(?i)create.*link|public.*link|share.*link"),1,0), b=tonumber(bytes), hour=strftime(_time, "%H"), fc=tonumber(file_count)
| eval off_hours=if(tonumber(hour)<6 OR tonumber(hour)>20,1,0)
| eval bulk=if(is_dl=1 AND (b>200000000 OR fc>200),1,0)
| bin _time span=1h
| stats sum(b) as tot_bytes, sum(bulk) as bulk_events, sum(is_link) as link_creates, sum(eval(off_hours=1 AND is_dl=1)) as offh_dl by _time, user, client_ip
| where tot_bytes>500000000 OR bulk_events>0 OR link_creates>50 OR offh_dl>30
| table _time, user, client_ip, tot_bytes, bulk_events, link_creates, offh_dl
```
- **Implementation:** Ingest high-fidelity audit and API link events. Establish per-role baselines (sales vs finance). Tune byte and count thresholds; exclude known migration service accounts. Correlate with identity risk scores and end-point alerts. Contain with session revoke and link disable playbooks. Review privacy rules before full raw logging of filenames in regulated sectors.
- **Visualization:** Timechart: total bytes and link creates per hour; table: top users for bulk and off-hours; map or table: source IPs for flagged sessions (where available).
- **CIM Models:** DLP
- **Known false positives:** Quarterly reporting, finance consolidations, and project teams downloading large project folders in ShareFile are normal bulk downloads. Correlation with the user's business role, folder ACL, and a pre-approved DLP exception suppresses the benign exfil look.
- **MITRE ATT&CK:** T1119, T1567
- **Last reviewed:** 2026-04-24

- **References:** [Citrix — ShareFile audit logging overview](https://docs.citrix.com/en-us/citrix-content-collaboration/audit-trail-logs.html)

---

### UC-2.6.73 · Citrix ShareFile API Rate Limiting and Auth Failures
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability, Security
- **Value:** Integrations, automation, and line-of-business apps depend on ShareFile APIs. OAuth failures break sign-in, rate limiting signals abusive or mis-tuned clients, and job errors may leave folders out of sync. Monitoring these patterns protects both availability and security (stolen or misconfigured tokens).
- **App/TA:** No official Splunk TA for ShareFile. Ingest audit trail via ShareFile REST API (https://api.sharefile.com) to HEC with a custom scripted input or Splunk Add-on Builder. Suggested custom sourcetype: `citrix:sharefile:audit`. Optionally correlate with Citrix Analytics Add-on for Splunk (Splunkbase 6280) for aggregated risk indicators.
- **Data Sources:** `index=sharefile` `sourcetype="citrix:sharefile:api"` (REST responses); fields `http_status` (401, 403, 429), `error_code`, `client_id` or `app_name`, `rate_limit_key`, `integration_job` for sync worker failures Note: field names in SPL are suggested conventions for custom ingestion; actual field names depend on your parsing configuration in props.conf/transforms.conf.
- **SPL:**
```spl
index=sharefile sourcetype="citrix:sharefile:api" earliest=-4h
| eval sc=tonumber(http_status), is_auth=if(sc IN (401,403),1,0), is_rl=if(sc=429 OR match(lower(error_code),"(?i)rate|throttl|limit"),1,0), job_fail=if(match(lower(coalesce(integration_job, "")),"(?i)fail|error") OR match(lower(error_code),"(?i)job|sync|worker"),1,0), client=coalesce(client_id, app_name, "unknown")
| bin _time span=5m
| stats count as reqs, sum(is_auth) as auth_fails, sum(is_rl) as rate_hits, sum(job_fail) as job_errors by _time, client
| where auth_fails>10 OR rate_hits>0 OR job_errors>0
| table _time, client, reqs, auth_fails, rate_hits, job_errors
```
- **Implementation:** Collect API and OAuth logs with client identity. Alert on 429 from production integrations first (fix back-off and batch size). For 401/403, spike-check against key rotation and blocked accounts. Tag integration job names in events for MTTR. Compare to synthetic login tests to separate ShareFile service issues from a single app.
- **Visualization:** Timechart: 429, 401, 403 by client_id; table: top clients for rate limits; single-value: failed job count in the last hour.
- **CIM Models:** Authentication
- **Known false positives:** Scheduled RPA, sync clients, and integration workers legitimately hit API rate limits; pentest and scanner retries do too. An API client allowlist keyed to service principal and job schedule separates automation from account takeover.
- **MITRE ATT&CK:** T1110, T1190
- **Last reviewed:** 2026-04-24

- **References:** [Citrix — ShareFile API documentation](https://api.sharefile.com/)

---

### UC-2.6.74 · Citrix ShareFile User Activity Audit Trail
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Compliance, Security
- **Value:** A complete audit layer for ShareFile supports investigations and compliance: who accessed, changed, or shared which content; administrative actions in zones; and time-bounded reports for internal review or external auditors. The search summarizes daily activity mix and breadth so teams can spot gaps in logging and prove retention of evidence.
- **App/TA:** No official Splunk TA for ShareFile. Ingest audit trail via ShareFile REST API (https://api.sharefile.com) to HEC with a custom scripted input or Splunk Add-on Builder. Suggested custom sourcetype: `citrix:sharefile:audit`. Optionally correlate with Citrix Analytics Add-on for Splunk (Splunkbase 6280) for aggregated risk indicators.
- **Data Sources:** `index=sharefile` `sourcetype="citrix:sharefile:audit"` (view, download, upload, share, delete, permission change); `sourcetype="citrix:sharefile:admin"` (admin and zone actions); user, target, time, and outcome fields Note: field names in SPL are suggested conventions for custom ingestion; actual field names depend on your parsing configuration in props.conf/transforms.conf.
- **SPL:**
```spl
index=sharefile (sourcetype="citrix:sharefile:audit" OR sourcetype="citrix:sharefile:admin") earliest=-7d
| eval act=lower(coalesce(event_type, action, operation, "unknown"))
| eval actor=if(isnull(actor_type) OR actor_type="", "user", actor_type)
| bin _time span=1d
| stats count as events, dc(user) as users, values(act) as actions by _time, actor
| table _time, actor, events, users, actions
```
- **Implementation:** Enable ShareFile audit trail export to Splunk with full coverage (user and admin). Retain per policy (often 1–7 years for regulated data). Create scheduled reports for business reviews and a drill-down form with raw events for cases. Do not over-collect PII; mask where required.
- **Visualization:** Table: daily event counts; pie: user vs admin share; drill to raw event list; optional PDF/CSV scheduled report for auditors.
- **CIM Models:** Change
- **Known false positives:** End-of-quarter audit log exports, SIEM backfills, and helpdesk-driven password and MFA resets spike ShareFile read and auth events. Tag scheduled audit jobs and service desk break-glass accounts to avoid conflating operations with data theft.
- **MITRE ATT&CK:** T1074, T1039
- **Last reviewed:** 2026-04-24

- **References:** [Citrix — ShareFile audit and logging](https://docs.citrix.com/en-us/citrix-content-collaboration/audit-trail-logs.html)

---

### UC-2.6.75 · End-to-End Citrix Session Launch Time
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance
- **Value:** End-to-end session launch is the user-perceived time from initial click in Workspace through brokering, host start, logon, and HDX connect until a usable session is ready. Splunking all phases in one time series exposes whether delays sit in the broker, the hypervisor, the profile, the identity stack, or the client—so teams do not guess where to invest tuning effort.
- **App/TA:** uberAgent UXM (Splunkbase 1448) for phase insight; Template for Citrix XenDesktop 7 (TA-XD7-Broker) and Citrix Monitor Service OData; optional ITSI for service aggregation
- **Data Sources:** `index=xd` `sourcetype="citrix:broker:events"` (`event_type=SessionLogon` with `logon_duration_ms` and sub-phase fields); `sourcetype="uberAgent:Logon:LogonDetail"` for VDA phase breakdown; `sourcetype="citrix:hdx:connect"` for client-to-session handshake timing; Director OData exports if used Note: field names in SPL are suggested conventions for custom ingestion; actual field names depend on your parsing configuration in props.conf/transforms.conf.
- **SPL:**
```spl
index=xd (sourcetype="citrix:broker:events" event_type="SessionLogon" OR sourcetype="uberAgent:Logon:LogonDetail" OR sourcetype="citrix:hdx:connect") earliest=-4h
| eval total_ms=tonumber(coalesce(logon_duration_ms, total_logon_ms, 0)), phase=coalesce(phase, "e2e")
| bin _time span=15m
| stats median(total_ms) as p50, perc95(total_ms) as p95, count as n, values(phase) as phases by _time, delivery_group
| where p95>90000
| table _time, delivery_group, p50, p95, n, phases
```
- **Implementation:** Prefer uberAgent for automatic phase split on the VDA; supplement with broker events for the brokering and VM start portions. Clock-sync all tiers. Set SLOs per delivery group. Create drill-down dashboards from the same search as phase-specific panels. For cloud services, add Citrix DaaS connector latency where exposed in logs. Pair with a synthetic transaction from a test account for continuous proof.
- **Visualization:** Stacked time by phase, Sankey of phase share for p95, single value SLO, compare regions or delivery groups side by side.
- **CIM Models:** Performance
- **Known false positives:** Image rollout weeks and semester starts push session launch time for the whole user base at once. A same-day-of-week rolling median and a Studio publish window exclusion reduce Monday-morning false positives on pure latency.
- **Last reviewed:** 2026-04-24

- **References:** [uberAgent — Logon and session performance](https://splunkbase.splunk.com/app/1448), [Citrix — Session launch and logon process](https://docs.citrix.com/en-us/citrix-virtual-apps-desktops/technical-overview/logon-processes.html)

---

### UC-2.6.76 · Citrix Client Ecosystem and Platform Distribution
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Compliance
- **Value:** Supported, patched clients are a common compliance and support requirement. A live distribution of Workspace app versions, client operating systems, thin-client firmware, and device classes gives IT and security teams a single place to see drift, plan upgrades, and retire unsupported platforms before they become an audit finding or a break-fix incident.
- **App/TA:** Citrix Cloud / CVAD session metadata export, Syslog or API from supported thin clients, Template for Citrix add-ons in use at your site
- **Data Sources:** `index=xd` `sourcetype="citrix:workspace:client"` (client build, device OS, channel); `sourcetype="citrix:hdx:connect"` (endpoint type, firmware where available); `sourcetype="citrix:broker:session"` (Workspace version from session metadata) when exposed Note: field names in SPL are suggested conventions for custom ingestion; actual field names depend on your parsing configuration in props.conf/transforms.conf.
- **SPL:**
```spl
index=xd (sourcetype="citrix:workspace:client" OR sourcetype="citrix:hdx:connect" OR sourcetype="citrix:broker:session") earliest=-7d
| eval os=coalesce(client_os, device_os, platform, "unknown"), ver=coalesce(workspace_version, app_version, client_version, "unknown"), dev=coalesce(device_type, endpoint_type, "unknown")
| bin _time span=1d
| stats count as sessions by _time, os, ver, dev
| sort -sessions
| head 200
```
- **Implementation:** Pull version fields on every new session or daily heartbeat, depending on the feed. Add lookups for LTS/allowed builds. Schedule monthly compliance PDF or CSV. Partner with end-user computing to nudge or block at the gateway for builds below a floor. For BYOD, show OS mix separately from corporate-managed endpoints.
- **Visualization:** Pie: OS; bar: Workspace app version; treemap: device class; line: unsupported share over time after campaigns.
- **CIM Models:** Endpoint
- **Known false positives:** Kiosks, BYOD, contractors, and field forces skew the client OS and form-factor mix. Baseline by OU, region, and device class; a move away from a single internal gold image is often expected diversity, not client sprawl out of control.
- **Last reviewed:** 2026-04-24

- **References:** [Citrix Workspace app — Lifecycle milestones](https://docs.citrix.com/en-us/citrix-workspace-app-for-windows/technical-overview-lifecycle-milestones.html)

---

### UC-2.6.77 · Citrix Per-Application Perceived Performance (Startup vs Hang vs Network)
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance
- **Value:** Not all “Citrix is slow” tickets are a network problem. Perceived slowness may be slow application startup, long UI busy states, or real ICA network delay. Combining process startup and hang signals from the VDA with network metrics and broker-reported app ready time splits accountability between packaging, the app itself, the profile, and the path between user and host.
- **App/TA:** uberAgent UXM (Splunkbase 1448) with Citrix templates; optional Citrix Monitor / Director export for the same fields
- **Data Sources:** uberAgent: `sourcetype="uberAgent:Process:ProcessStartup"` and `sourcetype="uberAgent:Application:Error"` (if configured); `sourcetype="uberAgent:Network:Performance"` (latency, loss); `sourcetype="citrix:broker:app_usage"` (app title, `launch_to_ready_ms`); or Director OData for ICA RTT and application load time
- **SPL:**
```spl
index=xd (sourcetype="uberAgent:Process:ProcessStartup" OR sourcetype="uberAgent:Network:Performance" OR sourcetype="citrix:broker:app_usage") earliest=-4h
| eval app=coalesce(app_name, process_name, title, "unknown"), start_ms=tonumber(startup_ms), ica=tonumber(ica_rtt_ms), hang=if(match(_raw, "(?i)not.?(responding)"),1,0)
| bin _time span=15m
| stats median(start_ms) as med_start, median(ica) as med_ica, sum(hang) as hang_ev by _time, app, host
| where med_start>10000 OR med_ica>100 OR hang_ev>0
| table _time, app, host, med_start, med_ica, hang_ev
```
- **Implementation:** Standardize on one app name key (avoid publisher vs start-menu title drift). In uberAgent, enable process and network packs for gold images only first. If ICA RTT is missing in uberAgent, add broker or gateway RTT. Build three small alerts: p95 startup, p95 RTT, and not-responding process count, each routed to a different team owner.
- **Visualization:** Small multiples: one row per app with startup, hang count, and RTT; table: top hosts driving bad p95; overlay change markers on image or app version.
- **CIM Models:** Performance
- **Known false positives:** Wide-area brownouts, VPN or SD-WAN issues, and WiFi in one building can make many apps look 'network slow' or 'hung' at once. A site or path health overlay and delivery group before/after a thin-client patch differentiate network from a single bad app package.
- **Last reviewed:** 2026-04-24

- **References:** [uberAgent — Process and network metrics](https://splunkbase.splunk.com/app/1448), [Citrix — HDX and session performance](https://docs.citrix.com/en-us/citrix-virtual-apps-desktops/technical-overview/hdx-adaptive-technologies.html)

---

### UC-2.6.78 · Citrix Session Recording Pipeline and Storage Health
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability, Compliance
- **Value:** Session recording is often a compliance and insider-risk control. The recording service, search index, and long-term file storage must be healthy, searchable within agreed latency, and large enough to retain evidence. Failures in any tier create a gap where activity is not provable even though policy requires recording. Monitoring capacity and playback availability closes that gap operationally and for audits.
- **App/TA:** No official Splunk TA for Citrix Session Recording. Ingest via Windows Event Logs from the Session Recording Server (Splunk Add-on for Microsoft Windows), IIS logs from the SR web player, and optionally SR database queries via Splunk DB Connect.
- **Data Sources:** `index=xd` `sourcetype="citrix:session:recording:server"` (service up, IIS app pool, admin API), `sourcetype="citrix:session:recording:storage"` (free space, file age), `sourcetype="citrix:session:recording:search"` (indexing lag, playback requests); Windows performance or `sourcetype=WinHostMon` for disk Note: field names in SPL are suggested conventions for custom ingestion; actual field names depend on your parsing configuration in props.conf/transforms.conf.
- **SPL:**
```spl
index=xd (sourcetype="citrix:session:recording:server" OR sourcetype="citrix:session:recording:storage" OR sourcetype="citrix:session:recording:search") earliest=-24h
| eval g=tonumber(free_gb), low_disk=if((isnotnull(g) AND g<10) OR match(_raw, "(?i)low.?space|disk.?full"),1,0), lag_sec=tonumber(index_lag_sec), down=if(match(_raw, "(?i)service.?(not.?(start|run)|down|stop|fail)"),1,0)
| bin _time span=5m
| stats max(low_disk) as risk_disk, max(lag_sec) as max_lag, max(down) as down_ev by _time, host
| where risk_disk=1 OR max_lag>300 OR down_ev=1
| table _time, host, risk_disk, max_lag, down_ev
```
- **Implementation:** Separate alerts: infrastructure (service down, disk, SQL), pipeline lag (ingest to searchable), and product errors on playback. Plan retention tiering: hot, warm, and archive. Test restore and playback quarterly. If storage is object-backed, add bucket health and cost monitors outside Splunk and link the dashboard here.
- **Visualization:** Gauges: free space and index lag; timeline: down events; table: last successful backup or archive job per site if logged.
- **CIM Models:** Network_Sessions
- **Known false positives:** Replay storage maintenance, index rebuild, NFS or SMB blips, and backlog drain after a recording server patch pause ingestion. Align with storage and CIFS tickets; a growing backlog with no matching maintenance is the sustained failure case.
- **MITRE ATT&CK:** T1562
- **Last reviewed:** 2026-04-24

- **References:** [Citrix — Session Recording architecture and storage](https://docs.citrix.com/en-us/citrix-virtual-apps-desktops/technical-overview/session-recording.html)

---

### UC-2.6.79 · Citrix Secure Private Access (ZTNA) Session Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Security, Performance
- **Value:** Zero-trust access to private web and TCP apps should enforce policy, give visibility into application categories, and still feel responsive. Monitoring successful versus blocked sessions, connector path health, and round-trip time highlights misconfiguration, over-broad or over-tight rules, and performance issues on browser-based and agent-based paths alike.
- **App/TA:** Citrix Analytics Add-on for Splunk (Splunkbase 6280) imports Secure Private Access risk indicators from Citrix Analytics for Security.
- **Data Sources:** `index=ztna` or `index=cloud` with `sourcetype="citrix:ztna:session"` (user, app, policy hit, `tcp|tls` outcome), `sourcetype="citrix:ztna:access"` (web and SaaS via browser, category tags), `sourcetype="citrix:ztna:connector"` (on-prem app reachability); fields `app_category`, `result`, `rtt_ms` Note: field names in SPL are suggested conventions for custom ingestion; actual field names depend on your parsing configuration in props.conf/transforms.conf.
- **SPL:**
```spl
index=ztna (sourcetype="citrix:ztna:session" OR sourcetype="citrix:ztna:access" OR sourcetype="citrix:ztna:connector") earliest=-4h
| eval ok=if(match(lower(result),"(?i)allow|success|established|up"),1,0), rtt=tonumber(rtt_ms), cat=coalesce(app_category, category, "uncategorized"), bfail=if(match(lower(result),"(?i)block|deny|fail|down|timeout"),1,0)
| bin _time span=5m
| stats count as n, sum(ok) as okc, sum(bfail) as blks, median(rtt) as medrtt, values(cat) as cats by _time, user, app
| where blks>0 OR (isnotnull(medrtt) AND medrtt>250)
| table _time, user, app, n, okc, blks, medrtt, cats
```
- **Implementation:** Ingest the cloud service feed in near real time. Map internal app names to a category lookup for business-friendly breakdowns. Alert on block spikes, connector-down patterns, and sustained high RTT by region. Pair with traditional gateway logs during migration. Document split between legacy full tunnel and this access path for the same app families.
- **Visualization:** Sankey: user to app to outcome; timechart: block rate; map or bar: by region; table: high RTT with category.
- **CIM Models:** Network_Sessions
- **Known false positives:** Onboarding new private ZTNA apps, per-app policy cutovers, and pilot users shift SPA session baselines for days. Cohort- or OU-based baselines and a policy version tag on the alert keep expected ramp from looking like a stealth breach pattern.
- **MITRE ATT&CK:** T1078, T1021
- **Last reviewed:** 2026-04-24

- **References:** [Citrix — Secure Private Access (ZTNA) overview](https://docs.citrix.com/en-us/citrix-secure-private-access/)

---
