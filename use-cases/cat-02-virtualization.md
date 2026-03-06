# 2. Virtualization

## 2.1 VMware vSphere

**Primary App/TA:** Splunk Add-on for VMware (`TA-vmware`) — Free on Splunkbase; Splunk App for VMware (optional, provides dashboards)

---

### UC-2.1.1 · ESXi Host CPU Contention
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
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
- **Implementation:** Install TA-vmware on a heavy forwarder or search head. Configure a vCenter service account with read-only permissions. Set up the VMware data collection in the TA (vCenter IP, credentials, collection interval). The TA pulls performance data via the vSphere API. Alert when CPU ready exceeds 5% per VM.
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
- **Visualization:** Table (VM, host, balloon KB, swap KB), Line chart over time, Stacked bar chart per host.
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
- **Value:** VMs consistently using <20% of allocated CPU/memory waste resources that other VMs could use. Right-sizing saves money and improves cluster capacity.
- **App/TA:** `TA-vmware`
- **Data Sources:** `sourcetype=vmware:perf:cpu`, `sourcetype=vmware:perf:mem`, `sourcetype=vmware:inv:vm`
- **SPL:**
```spl
index=vmware sourcetype="vmware:perf:cpu" counter="cpu.usage.average"
| stats avg(Value) as avg_cpu by vm_name
| join vm_name [search index=vmware sourcetype="vmware:inv:vm" | table vm_name numCpu memoryMB]
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
- **Value:** Centralizing all vCenter alarms in Splunk enables correlation with other infrastructure data, historical trending, and unified alerting.
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

## 2.2 Microsoft Hyper-V

**Primary App/TA:** Splunk Add-on for Microsoft Hyper-V, `Splunk_TA_windows` — Free on Splunkbase

---

### UC-2.2.1 · VM Performance Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
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
- **Value:** Replication lag means your DR site is behind. If replication breaks, you lose your recovery point objective (RPO).
- **App/TA:** `Splunk_TA_windows`
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
- **Value:** CSV issues can cause VM storage access failures across the entire cluster. Redirected I/O mode significantly degrades performance.
- **App/TA:** `Splunk_TA_windows`
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
- **Value:** Audit trail for VM mobility. Excessive live migrations may indicate cluster imbalance or storage issues.
- **App/TA:** `Splunk_TA_windows`
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
- **Value:** Outdated integration services cause performance issues and prevent features like time sync, heartbeat, and data exchange from working correctly.
- **App/TA:** `Splunk_TA_windows`, custom scripted input
- **Data Sources:** PowerShell scripted input (`Get-VMIntegrationService`)
- **SPL:**
```spl
index=hyperv sourcetype=integration_services
| stats latest(version) as ic_version by vm_name, host
| where ic_version != expected_version
```
- **Implementation:** Create a PowerShell scripted input on Hyper-V hosts: `Get-VM | Get-VMIntegrationService | Select VMName, Name, Enabled, PrimaryOperationalStatus`. Run daily.
- **Visualization:** Table (VM, version, status), Pie chart (current vs. outdated).
- **CIM Models:** N/A

---

## 2.3 KVM / Proxmox / oVirt

**Primary App/TA:** Custom inputs via libvirt API, syslog

---

### UC-2.3.1 · Guest VM Resource Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
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

