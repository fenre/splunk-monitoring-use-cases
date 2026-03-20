## 19. Compute Infrastructure (HCI & Converged)

### 19.1 Cisco UCS

**Splunk Add-on:** Cisco UCS TA, UCS Manager syslog

### UC-19.1.1 · Blade/Rack Server Health

- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** UCS blade and rack servers host critical workloads. Monitoring component health (CPU, memory, PSU, fans) enables proactive hardware replacement before failures cause VM outages and unplanned downtime.
- **App/TA:** `Splunk_TA_cisco-ucs`, UCS Manager syslog
- **Equipment Models:** Cisco UCS B200 M5/M6/M7, UCS C220 M5/M6/M7, UCS C240 M5/M6/M7, UCS C480 M5, UCS X210c M6/M7, UCS X410c M6, UCS 6324 FI, UCS 6332 FI, UCS 6454 FI, UCS 6536 FI
- **Data Sources:** UCS Manager faults, UCS Manager equipment API
- **SPL:**
```spl
index=cisco_ucs sourcetype="cisco:ucs:faults"
| search dn="sys/chassis-*/blade-*" OR dn="sys/rack-unit-*"
| eval component=case(
   like(cause, "%cpu%"), "CPU",
   like(cause, "%memory%"), "Memory",
   like(cause, "%psu%"), "PSU",
   like(cause, "%fan%"), "Fan",
   like(cause, "%disk%"), "Disk",
   1==1, "Other")
| stats count by severity, component, dn, descr
| sort -severity, -count
```
- **Implementation:** Configure UCS Manager syslog forwarding to Splunk. Poll equipment health via UCS Manager XML API every 5 minutes. Track fault creation and clearing events. Alert on critical/major faults for immediate hardware replacement. Maintain server inventory with health status overlay.
- **Visualization:** Status grid (server health map), Bar chart (faults by component), Table (active critical faults), Timechart (fault trending).
- **CIM Models:** N/A

### UC-19.1.2 · Service Profile Compliance

- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Configuration
- **Value:** UCS service profiles define the identity of compute resources. Non-compliant associations indicate configuration drift, failed hardware migrations, or policy violations that can impact workload performance and security.
- **App/TA:** `Splunk_TA_cisco-ucs`, UCS Manager events
- **Equipment Models:** Cisco UCS B200 M5/M6/M7, UCS C220 M5/M6/M7, UCS C240 M5/M6/M7, UCS C480 M5, UCS X210c M6/M7, UCS X410c M6, UCS 6324 FI, UCS 6332 FI, UCS 6454 FI, UCS 6536 FI
- **Data Sources:** UCS Manager service profile API, configuration events
- **SPL:**
```spl
index=cisco_ucs sourcetype="cisco:ucs:config"
| search object_type="service_profile"
| eval compliance=case(
    assoc_state="associated" AND config_state="applied", "Compliant",
    assoc_state="associated" AND config_state!="applied", "Non-Compliant",
    assoc_state="unassociated", "Unassociated",
    1==1, "Unknown")
| stats count by compliance, org, sp_name, server_dn
| sort compliance
```
- **Implementation:** Poll service profile status via UCS Manager API every 5 minutes. Track association state and configuration compliance. Alert on non-compliant profiles requiring reapplication. Monitor service profile migrations during maintenance windows. Report on unassociated profiles (wasted compute capacity).
- **Visualization:** Pie chart (compliance breakdown), Table (non-compliant profiles), Single value (compliance percentage), Status grid (profile status by org).
- **CIM Models:** N/A

### UC-19.1.3 · Firmware Compliance

- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Value:** Running inconsistent firmware across UCS creates compatibility issues and security vulnerabilities. Tracking firmware versions enables compliance reporting, patch planning, and ensures consistency across the compute fleet.
- **App/TA:** `Splunk_TA_cisco-ucs`, UCS Manager inventory
- **Equipment Models:** Cisco UCS B200 M5/M6/M7, UCS C220 M5/M6/M7, UCS C240 M5/M6/M7, UCS C480 M5, UCS X210c M6/M7, UCS X410c M6, UCS 6324 FI, UCS 6332 FI, UCS 6454 FI, UCS 6536 FI
- **Data Sources:** UCS Manager firmware inventory, UCS firmware policy
- **SPL:**
```spl
index=cisco_ucs sourcetype="cisco:ucs:inventory"
| search object_type="firmware"
| stats count by component_type, running_version, server_dn
| lookup ucs_approved_firmware component_type OUTPUT approved_version
| eval compliant=if(running_version==approved_version, "Yes", "No")
| stats count as server_count by component_type, running_version, approved_version, compliant
| sort compliant, component_type
```
- **Implementation:** Poll UCS firmware inventory weekly. Maintain a lookup of approved firmware versions per component type. Compare running versions against approved baselines. Generate compliance reports for audit. Prioritize non-compliant servers in maintenance windows.
- **Visualization:** Table (firmware compliance matrix), Bar chart (servers by firmware version), Pie chart (compliant vs non-compliant), Single value (fleet compliance percentage).
- **CIM Models:** N/A

### UC-19.1.4 · Fault Trending by Severity

- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity
- **Value:** UCS fault trends reveal systemic hardware issues, environmental problems, or configuration problems across the compute fleet. Rising fault counts indicate deteriorating conditions requiring proactive attention.
- **App/TA:** `Splunk_TA_cisco-ucs`, UCS Manager faults
- **Equipment Models:** Cisco UCS B200 M5/M6/M7, UCS C220 M5/M6/M7, UCS C240 M5/M6/M7, UCS C480 M5, UCS X210c M6/M7, UCS X410c M6, UCS 6324 FI, UCS 6332 FI, UCS 6454 FI, UCS 6536 FI
- **Data Sources:** UCS Manager fault log, syslog
- **SPL:**
```spl
index=cisco_ucs sourcetype="cisco:ucs:faults"
| timechart span=1h count by severity
| fields _time critical major minor warning info
```
- **Implementation:** Forward UCS Manager faults via syslog or API polling. Categorize faults by severity and type. Track fault lifecycle (create, clear, acknowledge). Alert on critical/major fault count exceeding baseline by >50%. Report weekly on fault trends and resolution times.
- **Visualization:** Timechart (fault trends by severity), Bar chart (top fault codes), Single value (open critical faults), Table (active faults detail).
- **CIM Models:** N/A

### UC-19.1.5 · FI Port Channel Health

- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Fabric Interconnects are the network gateway for all UCS compute. Port-channel failures reduce bandwidth or cause complete loss of connectivity, impacting every workload in the UCS domain.
- **App/TA:** `Splunk_TA_cisco-ucs`, UCS Manager stats
- **Equipment Models:** Cisco UCS B200 M5/M6/M7, UCS C220 M5/M6/M7, UCS C240 M5/M6/M7, UCS C480 M5, UCS X210c M6/M7, UCS X410c M6, UCS 6324 FI, UCS 6332 FI, UCS 6454 FI, UCS 6536 FI
- **Data Sources:** UCS Manager FI port-channel statistics, FI syslog
- **SPL:**
```spl
index=cisco_ucs sourcetype="cisco:ucs:fi_stats"
| search object_type="port_channel"
| eval member_pct=round((active_members/configured_members)*100, 0)
| stats latest(oper_state) as status, latest(member_pct) as active_pct, latest(rx_bps) as rx_rate, latest(tx_bps) as tx_rate by fi_id, pc_id, pc_name
| eval health=case(status!="up", "Down", active_pct<100, "Degraded", 1==1, "Healthy")
| table fi_id, pc_id, pc_name, status, active_pct, rx_rate, tx_rate, health
```
- **Implementation:** Monitor FI port-channel status every 30 seconds. Track member link count vs configured count. Alert on any port-channel with less than 100% members active. Monitor FI uplink utilization for capacity planning. Correlate FI events with server connectivity issues.
- **Visualization:** Status grid (port-channel health), Gauge (member active percentage), Timechart (utilization trending), Table (degraded port-channels).
- **CIM Models:** N/A

### UC-19.1.6 · Power and Thermal Monitoring

- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** UCS power and thermal data helps optimize data center capacity planning, detect cooling failures before overheating causes server throttling, and track energy efficiency metrics for sustainability reporting.
- **App/TA:** `Splunk_TA_cisco-ucs`, UCS Manager environmental
- **Equipment Models:** Cisco UCS B200 M5/M6/M7, UCS C220 M5/M6/M7, UCS C240 M5/M6/M7, UCS C480 M5, UCS X210c M6/M7, UCS X410c M6, UCS 6324 FI, UCS 6332 FI, UCS 6454 FI, UCS 6536 FI
- **Data Sources:** UCS Manager environmental statistics, power supply metrics
- **SPL:**
```spl
index=cisco_ucs sourcetype="cisco:ucs:environmental"
| eval metric_type=case(like(stat_name, "%power%"), "Power", like(stat_name, "%temp%"), "Temperature", like(stat_name, "%fan%"), "Fan", 1==1, "Other")
| stats avg(value) as avg_val, max(value) as max_val by chassis_id, metric_type, unit
| eval status=case(
    metric_type=="Temperature" AND max_val>75, "Critical",
    metric_type=="Temperature" AND max_val>65, "Warning",
    metric_type=="Fan" AND avg_val<2000, "Warning",
    1==1, "Normal")
| table chassis_id, metric_type, avg_val, max_val, unit, status
```
- **Implementation:** Collect UCS environmental data via API every 60 seconds. Track per-chassis power draw, inlet/outlet temperatures, and fan speeds. Set thermal thresholds based on vendor specs. Alert on overheating or fan failures. Report monthly power consumption for capacity and cost planning.
- **Visualization:** Gauge (temperature/power), Timechart (power and thermal trending), Heatmap (chassis thermal map), Single value (total power draw).
- **CIM Models:** N/A

### UC-19.1.10 · Blade Firmware Compliance

- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Value:** Per-blade firmware (BIOS, adapter, storage controller) vs approved bundles — complements fleet-wide inventory (UC-19.1.3) with **per-blade** tracking for change windows.
- **App/TA:** `Splunk_TA_cisco-ucs`, UCS Manager API
- **Equipment Models:** Cisco UCS B-Series blades
- **Data Sources:** `cisco:ucs:inventory`, blade FRU
- **SPL:**
```spl
index=cisco_ucs sourcetype="cisco:ucs:inventory" object_type="blade"
| stats values(running_fw) as fw by server_dn, blade_id
| lookup ucs_blade_fw_baseline.csv blade_model OUTPUT approved_fw
| where fw!=approved_fw
| table server_dn, blade_id, fw, approved_fw
```
- **Implementation:** Normalize firmware strings per Cisco bundle naming. Report exceptions before LCM updates.
- **Visualization:** Table (non-compliant blades), Bar chart (by chassis), Single value (non-compliant count).
- **CIM Models:** N/A

### UC-19.1.11 · Service Profile Association Failures

- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Failed or stuck service profile associations block server bring-up and maintenance — complements compliance state (UC-19.1.2).
- **App/TA:** `Splunk_TA_cisco-ucs`
- **Equipment Models:** Cisco UCS
- **Data Sources:** `cisco:ucs:config`, UCS faults
- **SPL:**
```spl
index=cisco_ucs (sourcetype="cisco:ucs:config" OR sourcetype="cisco:ucs:faults")
| search assoc_state="failed" OR match(lower(descr),"(?i)association.*fail")
| stats count by sp_name, server_dn, descr
| sort -count
```
- **Implementation:** Tune search to UCS fault codes for association. Alert on any failed association in production orgs.
- **Visualization:** Table (failed associations), Timeline, Single value (open failures).
- **CIM Models:** N/A

### UC-19.1.12 · Fault Suppression Policy Audit

- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Value:** Tracks suppressed or acknowledged faults that may hide recurring hardware issues — governance for suppression rules.
- **App/TA:** `Splunk_TA_cisco-ucs`
- **Equipment Models:** Cisco UCS
- **Data Sources:** `cisco:ucs:faults`
- **SPL:**
```spl
index=cisco_ucs sourcetype="cisco:ucs:faults"
| where match(lower(lc),"(?i)suppressed") OR acked="yes"
| stats count by code, dn, user
| where count>10
| sort -count
```
- **Implementation:** Map `lc` and ack fields per UCSM version. Monthly review of chronic suppressions.
- **Visualization:** Table (top suppressed codes), Bar chart (by user), Line chart (suppression trend).
- **CIM Models:** N/A

### UC-19.1.13 · FI Port Channel Member Errors and CRCs

- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Per-member link errors and CRCs on FI port-channels — augments aggregate PC status (UC-19.1.5).
- **App/TA:** `Splunk_TA_cisco-ucs`
- **Equipment Models:** Cisco UCS FI
- **Data Sources:** `cisco:ucs:fi_stats` port members
- **SPL:**
```spl
index=cisco_ucs sourcetype="cisco:ucs:fi_stats" object_type="port"
| where crc_errors>0 OR link_state!="up"
| stats sum(crc_errors) as crc by fi_id, pc_id, port_id
| where crc>0
| sort -crc
```
- **Implementation:** Ingest per-member counters. Alert on CRC growth or member down inside operational PC.
- **Visualization:** Table (ports with CRCs), Heatmap (FI × port), Line chart (CRC rate).
- **CIM Models:** N/A

### UC-19.1.14 · UCS Manager Backup Validation

- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Compliance
- **Value:** Confirms scheduled all/configuration backups completed and file size is within expected bounds.
- **App/TA:** `Splunk_TA_cisco-ucs`, backup scheduler logs
- **Equipment Models:** Cisco UCSM
- **Data Sources:** `cisco:ucs:backup`, syslog backup events
- **SPL:**
```spl
index=cisco_ucs sourcetype="cisco:ucs:backup" earliest=-7d
| where status!="success" OR backup_size_bytes < 1000000
| stats latest(status) as st, latest(backup_size_bytes) as sz by ucsm_host
| table ucsm_host, st, sz
```
- **Implementation:** Ingest backup job results from syslog or automation. Alert on failed job or zero-size artifact.
- **Visualization:** Table (backup status), Single value (failed jobs), Timeline.
- **CIM Models:** N/A

### UC-19.1.15 · Chassis PSU Redundancy

- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Fault
- **Value:** Detects loss of N+1 PSU redundancy in chassis before full power loss.
- **App/TA:** `Splunk_TA_cisco-ucs`
- **Equipment Models:** UCS chassis
- **Data Sources:** `cisco:ucs:environmental`, PSU inventory
- **SPL:**
```spl
index=cisco_ucs sourcetype="cisco:ucs:environmental" metric_type="psu"
| where oper_state!="ok" OR redundancy_state!="redundant"
| stats count by chassis_id, psu_slot, oper_state, redundancy_state
```
- **Implementation:** Map PSU fields from API. Page on non-redundant state.
- **Visualization:** Status grid (chassis × PSU), Table (alerts), Single value (chassis without redundancy).
- **CIM Models:** N/A

### UC-19.1.16 · IOM Uplink Utilization

- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** IOM-to-FI uplink saturation causes east-west congestion for blade traffic.
- **App/TA:** `Splunk_TA_cisco-ucs`
- **Equipment Models:** UCS IOM modules
- **Data Sources:** `cisco:ucs:iom_stats`
- **SPL:**
```spl
index=cisco_ucs sourcetype="cisco:ucs:iom_stats" earliest=-1h
| eval util_pct=round((rx_bps+tx_bps)*8/link_speed_bps*100,1)
| where util_pct>70
| stats max(util_pct) as peak_util by chassis_id, iom_slot, port
| sort -peak_util
```
- **Implementation:** Poll IOM port counters. Alert at 70%/85%. Plan additional uplinks or rebalance servers.
- **Visualization:** Heatmap (IOM × port util), Table (hot uplinks), Line chart (trend).
- **CIM Models:** N/A

### UC-19.1.17 · BIOS Policy Compliance

- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Value:** Verifies server BIOS settings match service profile BIOS policy (VT-x, power management, boot mode).
- **App/TA:** `Splunk_TA_cisco-ucs`
- **Equipment Models:** Cisco UCS servers
- **Data Sources:** `cisco:ucs:bios`, service profile
- **SPL:**
```spl
index=cisco_ucs sourcetype="cisco:ucs:bios"
| lookup ucs_bios_policy.csv sp_name OUTPUT require_vt, require_boot_mode
| where vt_enabled!=require_vt OR boot_mode!=require_boot_mode
| table server_dn, sp_name, vt_enabled, boot_mode, require_vt, require_boot_mode
```
- **Implementation:** Extract BIOS tokens from inventory poll. Reconcile with expected policy per SP.
- **Visualization:** Table (non-compliant servers), Pie chart (compliance %), Bar chart (by org).
- **CIM Models:** N/A

### UC-19.1.18 · UCS Central Registration Health

- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Monitors UCS domain registration and heartbeat to UCS Central for multi-domain governance.
- **App/TA:** `Splunk_TA_cisco-ucs`, UCS Central syslog
- **Equipment Models:** UCS Central, UCSM domains
- **Data Sources:** `cisco:ucs_central:domain`
- **SPL:**
```spl
index=cisco_ucs sourcetype="cisco:ucs_central:domain" earliest=-24h
| where registration_state!="registered" OR last_heartbeat_age_sec>300
| stats latest(registration_state) as reg, max(last_heartbeat_age_sec) as age by domain_name
| table domain_name, reg, age
```
- **Implementation:** Ingest domain inventory from Central API. Alert when heartbeat stale or domain unregistered.
- **Visualization:** Table (domain status), Single value (stale domains), Map (site).
- **CIM Models:** N/A

#### 19.1 HCI Platforms (Nutanix)

### UC-19.1.7 · Nutanix Prism Central Alert Monitoring

- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability, Fault
- **Value:** Cluster-wide alerts from Prism Central provide early warning of infrastructure issues across managed Nutanix clusters. Monitoring unresolved critical and warning alerts enables rapid response to capacity, hardware, and service degradation before it impacts workloads.
- **App/TA:** Custom (Nutanix Prism Central REST API)
- **Data Sources:** Nutanix Prism Central `/api/nutanix/v3/alerts/list`
- **SPL:**
```spl
index=nutanix sourcetype="nutanix:prism_central:alerts"
| where resolved==false OR resolved=="false"
| eval severity_normalized=case(
    lower(severity)=="critical", "Critical",
    lower(severity)=="warning", "Warning",
    lower(severity)=="info", "Info",
    1==1, coalesce(severity, "Unknown"))
| stats count as alert_count, latest(_time) as last_occurred by cluster, severity_normalized, primary_impact_type, source_entity_type
| sort -severity_normalized, -alert_count
| table cluster, severity_normalized, primary_impact_type, source_entity_type, alert_count, last_occurred
```
- **Implementation:** Create a REST API modular input or scripted input that polls Prism Central `/api/nutanix/v3/alerts/list` every 2–5 minutes. Use POST with filter `resolved==false` to retrieve only active alerts. Authenticate with Prism Central credentials (stored in Splunk credential manager). Parse JSON response and index with sourcetype `nutanix:prism_central:alerts`. Configure field extractions for `cluster`, `severity`, `primary_impact_type`, `source_entity_type`, `resolved`, `title`. Alert on critical severity count > 0 or warning count exceeding threshold. Correlate with cluster health and CVM metrics.
- **Visualization:** Table (active alerts by cluster), Bar chart (alerts by severity and impact type), Status grid (cluster alert status), Single value (critical alert count).
- **CIM Models:** N/A

---

### UC-19.1.8 · Nutanix AOS Version Compliance

- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Compliance
- **Value:** Clusters running non-current AOS versions face compatibility risks, support limitations, and security gaps. Tracking version compliance enables upgrade planning, audit reporting, and ensures consistency across the Nutanix fleet.
- **App/TA:** Custom (Nutanix Prism Central REST API)
- **Data Sources:** Nutanix `/api/nutanix/v3/clusters/list` (cluster_version)
- **SPL:**
```spl
index=nutanix sourcetype="nutanix:prism_central:clusters"
| stats latest(cluster_version) as aos_version, latest(cluster_name) as cluster_name, latest(uuid) as cluster_uuid by cluster_name
| lookup nutanix_aos_baseline.csv cluster_name OUTPUT target_version
| eval compliant=if(aos_version==target_version OR isnull(target_version), "Yes", "No")
| where compliant=="No"
| table cluster_name, aos_version, target_version, compliant
| sort cluster_name
```
- **Implementation:** Poll Prism Central `/api/nutanix/v3/clusters/list` (or equivalent cluster inventory endpoint) every 6–24 hours. Extract `cluster_version` (AOS version) and `name` from each cluster entity. Create lookup `nutanix_aos_baseline.csv` with columns `cluster_name` and `target_version` defining the approved AOS version per cluster or environment. Compare running version to baseline. Alert on clusters with version drift. Generate weekly compliance report. Use for maintenance window planning and support eligibility checks.
- **Visualization:** Table (non-compliant clusters), Pie chart (version distribution), Single value (compliance percentage), Bar chart (clusters by AOS version).
- **CIM Models:** N/A

---

### UC-19.1.9 · Nutanix Snapshot Retention Compliance

- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance, Capacity
- **Value:** Protection domain snapshots that exceed retention policy consume storage and increase backup window duration. Monitoring snapshot age and count identifies stale snapshots for cleanup, reduces storage waste, and ensures alignment with data protection policies.
- **App/TA:** Custom (Nutanix Prism Element REST API)
- **Data Sources:** Nutanix `/api/nutanix/v2/protection_domains`, `/api/nutanix/v2/protection_domains/:name/dr_snapshots`
- **SPL:**
```spl
index=nutanix sourcetype="nutanix:protection_domains:snapshots"
| eval snapshot_age_days=round((now()-_time)/86400, 0)
| lookup nutanix_snapshot_retention_policy.csv protection_domain OUTPUT max_age_days, max_count
| stats count as snapshot_count, max(snapshot_age_days) as oldest_days, latest(max_age_days) as max_age_days, latest(max_count) as max_count by cluster, protection_domain
| eval over_retention=if(oldest_days>max_age_days OR snapshot_count>max_count, "Non-Compliant", "Compliant")
| where over_retention=="Non-Compliant"
| table cluster, protection_domain, snapshot_count, oldest_days, max_age_days, max_count, over_retention
| sort -oldest_days
```
- **Implementation:** Poll each Prism Element (per-cluster) for `/api/nutanix/v2/protection_domains` to list protection domains, then call `/api/nutanix/v2/protection_domains/{name}/dr_snapshots` for each domain to retrieve snapshot metadata (creation time, count). Run every 6–12 hours. Index with sourcetype `nutanix:protection_domains:snapshots`. Create lookup `nutanix_snapshot_retention_policy.csv` with `protection_domain`, `max_age_days`, `max_count` per policy. Calculate snapshot age from creation timestamp. Alert when snapshot count or oldest snapshot age exceeds policy. Report on storage consumed by over-retention snapshots. Integrate with capacity dashboards.
- **Visualization:** Table (non-compliant protection domains), Bar chart (snapshot count by domain), Gauge (oldest snapshot age), Single value (domains over retention).
- **CIM Models:** N/A

---

### 19.2 Hyper-Converged Infrastructure (HCI)

**Splunk Add-on:** Nutanix TA, VMware vSAN (via vCenter TA), vendor APIs

### UC-19.2.1 · Cluster Health Monitoring

- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** HCI cluster health directly determines workload availability. Monitoring overall cluster state, node availability, and service health enables rapid response to degradation before it impacts VMs and applications running on the cluster.
- **App/TA:** `TA-nutanix` or vendor-specific TA, HCI management API
- **Data Sources:** HCI management API (Prism, vSAN Health), cluster status events
- **SPL:**
```spl
index=hci sourcetype="hci:cluster_health"
| stats latest(cluster_status) as status, latest(num_nodes) as total_nodes, latest(healthy_nodes) as healthy_nodes, latest(storage_usage_pct) as storage_pct by cluster_name
| eval node_health=round((healthy_nodes/total_nodes)*100, 0)
| eval overall=case(status=="HEALTHY" AND node_health==100, "Healthy", status=="WARNING" OR node_health<100, "Degraded", 1==1, "Critical")
| table cluster_name, overall, total_nodes, healthy_nodes, node_health, storage_pct
```
- **Implementation:** Poll HCI management API every 60 seconds for cluster health. Track node online/offline state, storage health, and service availability. Alert on any cluster degradation (non-healthy state). Monitor rebuild operations and their impact on performance. Integrate with ITSI for service-level visibility.
- **Visualization:** Status grid (cluster health map), Single value (cluster status), Gauge (storage capacity), Table (cluster details).
- **CIM Models:** N/A

### UC-19.2.2 · Storage Pool Capacity

- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity
- **Value:** HCI storage pools are shared across all workloads. Running out of storage capacity causes VM provisioning failures, snapshot failures, and ultimately VM crashes. Proactive monitoring and forecasting prevents capacity emergencies.
- **App/TA:** `TA-nutanix` or vendor-specific TA
- **Data Sources:** HCI storage metrics, capacity API
- **SPL:**
```spl
index=hci sourcetype="hci:storage_metrics"
| stats latest(total_capacity_tb) as total_tb, latest(used_capacity_tb) as used_tb by cluster_name, storage_pool
| eval free_tb=round(total_tb-used_tb, 2)
| eval used_pct=round((used_tb/total_tb)*100, 1)
| sort -used_pct
| table cluster_name, storage_pool, total_tb, used_tb, free_tb, used_pct
```
- **Implementation:** Collect storage capacity metrics every 5 minutes. Track daily growth rates for forecasting. Alert at 75% warning and 85% critical thresholds. Use Splunk predict command for capacity forecasting. Plan procurement cycles based on projected exhaustion dates.
- **Visualization:** Gauge (capacity utilization), Timechart (capacity trending with forecast), Table (pool details), Single value (days to capacity).
- **CIM Models:** N/A

### UC-19.2.3 · Storage I/O Latency

- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Storage latency directly impacts application performance on HCI. Elevated latency affects all VMs on the cluster. Early detection of latency spikes enables workload rebalancing or troubleshooting before user impact escalates.
- **App/TA:** `TA-nutanix` or vendor-specific TA
- **Data Sources:** HCI performance metrics, per-VM I/O statistics
- **SPL:**
```spl
index=hci sourcetype="hci:io_metrics"
| stats avg(read_latency_ms) as avg_read_lat, avg(write_latency_ms) as avg_write_lat, max(read_latency_ms) as peak_read_lat, max(write_latency_ms) as peak_write_lat, sum(iops) as total_iops by cluster_name, node
| eval status=case(peak_read_lat>20 OR peak_write_lat>20, "Critical", peak_read_lat>10 OR peak_write_lat>10, "Warning", 1==1, "Healthy")
| sort -peak_write_lat
| table cluster_name, node, avg_read_lat, peak_read_lat, avg_write_lat, peak_write_lat, total_iops, status
```
- **Implementation:** Collect HCI I/O metrics every 30 seconds. Track read/write latency at cluster, node, and VM level. Set thresholds: >10ms warning, >20ms critical (adjust per workload SLA). Correlate latency spikes with rebuild operations, snapshot activity, or capacity constraints. Alert on sustained latency above threshold.
- **Visualization:** Timechart (latency trending), Gauge (current latency), Table (high-latency nodes), Heatmap (latency by node over time).
- **CIM Models:** N/A

### UC-19.2.4 · Node Performance Balance

- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** HCI relies on balanced workload distribution across nodes. Imbalanced nodes lead to hotspots where some nodes are overloaded while others are underutilized, reducing overall cluster efficiency and increasing failure risk.
- **App/TA:** `TA-nutanix` or vendor-specific TA
- **Data Sources:** HCI node-level performance metrics
- **SPL:**
```spl
index=hci sourcetype="hci:node_metrics"
| stats avg(cpu_pct) as avg_cpu, avg(mem_pct) as avg_mem, avg(iops) as avg_iops by cluster_name, node
| eventstats avg(avg_cpu) as cluster_avg_cpu, stdev(avg_cpu) as cluster_stdev_cpu by cluster_name
| eval cpu_deviation=round(abs(avg_cpu-cluster_avg_cpu)/cluster_stdev_cpu, 2)
| eval balance=case(cpu_deviation>2, "Imbalanced", cpu_deviation>1, "Slightly Imbalanced", 1==1, "Balanced")
| table cluster_name, node, avg_cpu, avg_mem, avg_iops, cpu_deviation, balance
| sort -cpu_deviation
```
- **Implementation:** Collect per-node CPU, memory, and I/O metrics every 60 seconds. Calculate standard deviation across nodes to detect imbalance. Alert when any node deviates >2 standard deviations from cluster average. Recommend DRS or workload migration to rebalance. Track balance improvement after actions.
- **Visualization:** Bar chart (node utilization comparison), Heatmap (node balance over time), Table (imbalanced nodes), Single value (cluster balance score).
- **CIM Models:** N/A

### UC-19.2.5 · Disk Failure Tracking

- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** Disk failures in HCI trigger data rebuild operations that consume cluster resources and temporarily reduce resilience. Tracking failures enables rapid replacement, monitoring rebuild progress, and assessing the cluster's ability to tolerate additional failures.
- **App/TA:** `TA-nutanix` or vendor-specific TA
- **Data Sources:** HCI disk events, SMART data, rebuild status
- **SPL:**
```spl
index=hci sourcetype="hci:disk_events"
| search event_type IN ("disk_failure", "disk_offline", "disk_rebuild_start", "disk_rebuild_complete", "smart_warning")
| stats count as events, latest(event_type) as latest_event, latest(_time) as last_event_time by cluster_name, node, disk_id, disk_serial
| eval status=case(
    latest_event=="disk_failure" OR latest_event=="disk_offline", "Failed",
    latest_event=="disk_rebuild_start", "Rebuilding",
    latest_event=="smart_warning", "Warning",
    1==1, "OK")
| search status!="OK"
| table cluster_name, node, disk_id, disk_serial, status, last_event_time
```
- **Implementation:** Ingest HCI disk events and SMART health data. Alert immediately on disk failures. Track rebuild start/complete times to measure rebuild duration. Monitor cluster resiliency during rebuilds (can it tolerate another failure?). Maintain spare disk inventory based on failure rate trends.
- **Visualization:** Status grid (disk health by node), Timeline (failure and rebuild events), Single value (disks in rebuild), Table (failed/warning disks).
- **CIM Models:** N/A

### UC-19.2.6 · Replication Factor Compliance

- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Value:** HCI data resilience depends on maintaining the configured replication factor (RF2/RF3). Non-compliant replication means data loss risk if additional failures occur. Monitoring RF compliance is essential for data protection assurance.
- **App/TA:** `TA-nutanix` or vendor-specific TA
- **Data Sources:** HCI replication status, data protection metrics
- **SPL:**
```spl
index=hci sourcetype="hci:replication"
| stats latest(configured_rf) as target_rf, latest(actual_rf) as current_rf, latest(rebuild_pct) as rebuild_progress by cluster_name, container
| eval compliant=if(current_rf>=target_rf, "Yes", "No")
| eval risk=case(current_rf<target_rf-1, "Data Loss Risk", current_rf<target_rf, "Reduced Resilience", 1==1, "Protected")
| table cluster_name, container, target_rf, current_rf, compliant, risk, rebuild_progress
| sort risk
```
- **Implementation:** Monitor replication factor status continuously. Alert immediately when actual RF drops below configured RF. Track rebuild progress to estimate time to full compliance. Monitor cluster capacity to ensure sufficient space for re-replication. Alert critically if RF drops to 1 (single copy—data loss imminent on next failure).
- **Visualization:** Single value (RF compliance status), Gauge (rebuild progress), Table (non-compliant containers), Status grid (cluster RF map).
- **CIM Models:** N/A

### UC-19.2.7 · CVM (Controller VM) Health

- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Nutanix Controller VMs manage all storage I/O on each node. CVM failures cause I/O to redirect to other nodes, impacting performance. Monitoring CVM health ensures the HCI control plane remains operational across all nodes.
- **App/TA:** `TA-nutanix`, Nutanix CVM logs
- **Data Sources:** Nutanix CVM resource metrics, CVM service status logs
- **SPL:**
```spl
index=hci sourcetype="nutanix:cvm"
| stats latest(cpu_pct) as cpu, latest(mem_pct) as mem, latest(stargate_status) as stargate, latest(cassandra_status) as cassandra, latest(zookeeper_status) as zk by node, cvm_ip
| eval all_services_up=if(stargate=="UP" AND cassandra=="UP" AND zk=="UP", "Yes", "No")
| eval health=case(all_services_up=="No", "Critical", cpu>80 OR mem>85, "Warning", 1==1, "Healthy")
| table node, cvm_ip, cpu, mem, stargate, cassandra, zk, health
| sort health
```
- **Implementation:** Monitor CVM service status (Stargate, Cassandra, Zookeeper, Prism) every 30 seconds. Track CVM CPU and memory utilization. Alert immediately on any CVM service failure. Monitor CVM-to-CVM communication for cluster stability. Track CVM restart events and correlate with I/O disruptions.
- **Visualization:** Status grid (CVM health by node), Table (CVM service status), Gauge (CVM resource utilization), Timechart (CVM metrics trending).
- **CIM Models:** N/A

---

### UC-19.2.8 · HCI Cluster Balance and Skew
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Imbalanced storage or compute across nodes causes hot spots and reduced resilience. Monitoring skew supports rebalance and capacity planning.
- **App/TA:** Nutanix/vSphere HCI APIs, Prism metrics
- **Data Sources:** Storage used per node, IOPS per node, VM count per node
- **SPL:**
```spl
index=hci sourcetype="nutanix:capacity"
| stats latest(storage_used_gb) as used_gb, latest(iops) as iops, latest(vm_count) as vms by node
| eventstats avg(used_gb) as avg_gb, avg(iops) as avg_iops by cluster
| eval storage_skew_pct=abs(used_gb-avg_gb)/avg_gb*100
| where storage_skew_pct > 25
| table node, used_gb, avg_gb, storage_skew_pct, iops, vms
```
- **Implementation:** Ingest per-node capacity and load. Compute skew vs cluster average. Alert when storage or IOPS skew exceeds threshold. Trigger rebalance or migration. Report on balance trend.
- **Visualization:** Table (nodes with skew), Bar chart (used by node), Gauge (cluster balance score).
- **CIM Models:** N/A

---

### UC-19.2.9 · HCI Data Resiliency and Rebuild Progress
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** After node or disk failure, rebuild must complete before another failure. Monitoring rebuild progress and ETA ensures data remains protected.
- **App/TA:** Nutanix/vSAN resiliency APIs
- **Data Sources:** Rebuild progress %, ETA, affected containers/vSAN components
- **SPL:**
```spl
index=hci sourcetype="nutanix:resiliency"
| where status="rebuilding" OR status="rebalancing"
| stats latest(progress_pct) as progress, latest(eta_sec) as eta, latest(affected_gb) as gb by cluster, task_type
| table cluster, task_type, progress, eta, gb
```
- **Implementation:** Poll resiliency and rebuild status. Alert when rebuild is slow or ETA exceeds threshold. Report on rebuild history and time-to-full resilience. Correlate with disk and node events.
- **Visualization:** Gauge (rebuild progress), Table (active rebuilds), Line chart (rebuild rate).
- **CIM Models:** N/A

---

### UC-19.2.10 · HCI Hypervisor and AOS Version Compliance
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Compliance
- **Value:** Mixed hypervisor or AOS versions can cause compatibility and support issues. Tracking version compliance supports upgrade planning and support eligibility.
- **App/TA:** Nutanix Prism, vSphere/vCenter API
- **Data Sources:** Node AOS version, hypervisor version, compliance baseline
- **SPL:**
```spl
index=hci sourcetype="nutanix:cluster"
| stats latest(aos_version) as aos, latest(hypervisor_version) as hv by node
| lookup hci_compliance_baseline.csv env OUTPUT target_aos, target_hv
| where aos!=target_aos OR hv!=target_hv
| table node, aos, target_aos, hv, target_hv
```
- **Implementation:** Ingest cluster and node version data. Maintain baseline by environment. Alert on version drift. Report on compliance percentage and nodes due for upgrade.
- **Visualization:** Table (non-compliant nodes), Pie chart (version distribution), Single value (compliance %).
- **CIM Models:** N/A

---

### UC-19.2.11 · HCI Network and Storage Controller Saturation
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Saturated storage or network controllers cause latency and timeouts. Monitoring utilization supports capacity and design decisions.
- **App/TA:** HCI platform metrics, Prism/vCenter
- **Data Sources:** Controller queue depth, network throughput per node, latency percentiles
- **SPL:**
```spl
index=hci sourcetype="nutanix:io"
| stats latest(queue_depth) as queue, latest(latency_p99_ms) as p99, latest(throughput_mbps) as mbps by node, controller
| where queue > 50 OR p99 > 100 OR mbps > 9000
| table node, controller, queue, p99, mbps
```
- **Implementation:** Ingest I/O and network metrics per node and controller. Alert when queue depth or latency exceeds threshold. Report on saturation events and trend. Plan node or network upgrade when sustained.
- **Visualization:** Table (saturated controllers), Line chart (latency and queue), Gauge (throughput utilization).
- **CIM Models:** N/A

---

### UC-19.2.12 · HCI Prism Central and Management Plane Health
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Prism Central (PC) failure affects visibility and automation. Monitoring PC and management plane ensures operations and alerting remain functional.
- **App/TA:** Prism Central API, management node metrics
- **Data Sources:** PC service status, API latency, task queue depth
- **SPL:**
```spl
index=hci sourcetype="nutanix:prism_central"
| stats latest(status) as status, latest(api_latency_ms) as latency, latest(task_queue) as queue by pc_instance
| where status!="healthy" OR latency > 5000 OR queue > 100
| table pc_instance, status, latency, queue
```
- **Implementation:** Poll Prism Central health and API metrics. Alert on unhealthy status, high API latency, or backed-up task queue. Report on PC availability and performance trend. Maintain HA for PC where available.
- **Visualization:** Status grid (PC health), Table (PC metrics), Line chart (API latency).
- **CIM Models:** N/A

---

### UC-19.2.13 · Dell VxRail Cluster Health

- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability, Fault
- **Value:** VxRail Manager health checks and LCM (Lifecycle Manager) update status directly impact cluster availability and supportability. Monitoring cluster and host health enables rapid response to hardware or software issues before they cause VM outages or failed upgrades.
- **App/TA:** Custom (VxRail Manager REST API)
- **Data Sources:** VxRail Manager `/rest/vxm/v1/cluster`, `/rest/vxm/v1/system/cluster-hosts`
- **SPL:**
```spl
index=vxrail sourcetype="vxrail:cluster"
| stats latest(health) as cluster_health, latest(vcenter_name) as vcenter, latest(version) as vxrail_version by cluster_id
| eval overall=case(cluster_health!="Healthy" AND cluster_health!="", "Degraded", 1==1, "Healthy")
| table cluster_id, overall, cluster_health, vxrail_version, vcenter
```
- **Implementation:** Create a REST API modular input or scripted input that polls VxRail Manager at `https://<vxrail_manager>/rest/vxm/v1/cluster` and `https://<vxrail_manager>/rest/vxm/v1/system/cluster-hosts` every 2–5 minutes. Authenticate with VxRail Manager credentials. Parse JSON responses and index with sourcetypes `vxrail:cluster` and `vxrail:cluster_hosts`. Extract fields: `health`, `version`, `vcenter_name`, `host_state`, `cluster_id`. Optionally poll LCM status endpoints for update state. Alert on cluster health != "Healthy" or any host not in CONNECTED/Healthy state. Correlate with vCenter and ESXi events for root cause analysis.
- **Visualization:** Status grid (cluster and host health from cluster_hosts), Table (cluster details with LCM status), Single value (unhealthy cluster count), Gauge (host connectivity percentage from cluster_hosts data).
- **CIM Models:** N/A

### UC-19.2.14 · Nutanix CVM Resource and Service Health

- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Deep-dive CVM CPU/memory pressure and Stargate latency vs UC-19.2.7 — for capacity and noisy-neighbor triage.
- **App/TA:** `TA-nutanix`, Prism metrics
- **Equipment Models:** Nutanix AOS nodes
- **Data Sources:** `nutanix:cvm:metrics`
- **SPL:**
```spl
index=hci sourcetype="nutanix:cvm:metrics" earliest=-4h
| where cpu_pct>85 OR mem_pct>90 OR stargate_latency_ms>5
| stats max(cpu_pct) as max_cpu, max(mem_pct) as max_mem, max(stargate_latency_ms) as max_lat by node
| sort -max_lat
```
- **Implementation:** Poll Prism per-CVM metrics API. Alert on sustained high latency with high CPU (investigate disk/network). Correlate with storage rebuilds.
- **Visualization:** Table (hot CVMs), Line chart (latency vs CPU), Heatmap (node × time).
- **CIM Models:** N/A

### UC-19.2.15 · Storage Pool Rebalance Monitoring

- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Tracks Curator/Planned Outage rebalance and disk usage skew during rebalance operations on Nutanix/vSAN.
- **App/TA:** Nutanix Prism, vSAN health
- **Data Sources:** `nutanix:curator`, `vsan:rebalance`
- **SPL:**
```spl
index=hci sourcetype="nutanix:curator" earliest=-24h
| where status="running" OR rebalance_pct>0
| stats latest(rebalance_pct) as pct, latest(eta_min) as eta by cluster, task_id
| table cluster, task_id, pct, eta
```
- **Implementation:** Map Curator task fields. Alert when rebalance stalls or ETA exceeds policy. Report impact on I/O (UC-19.2.3).
- **Visualization:** Gauge (rebalance %), Table (active tasks), Line chart (skew index).
- **CIM Models:** N/A

### UC-19.2.16 · HCI Node Failure Domain Risk

- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Validates RF/FTM rules so critical VM replicas don’t share the same fault domain (rack/block) — risk scoring when domains are imbalanced.
- **App/TA:** Nutanix Prism, vSAN stretched cluster APIs
- **Data Sources:** `hci:fd`, host-to-disk mapping
- **SPL:**
```spl
index=hci sourcetype="hci:fault_domain" earliest=-7d
| stats dc(node) as nodes_in_fd by cluster, fault_domain_name
| where nodes_in_fd>3
| lookup hci_fd_risk.csv cluster fault_domain_name OUTPUT risk_score
| where risk_score>70
| table cluster, fault_domain_name, nodes_in_fd, risk_score
```
- **Implementation:** Build fault domain from rack metadata. Flag Tier-0 VMs without FD separation. Use for BCP testing.
- **Visualization:** Table (risky placements), Sankey (VM → FD), Single value (violations).
- **CIM Models:** N/A

### UC-19.2.17 · vSAN Disk Group Health

- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** Disk group mount state, component health, and checksum errors for VMware vSAN.
- **App/TA:** vSAN health API, vCenter TA
- **Equipment Models:** vSAN ReadyNodes
- **Data Sources:** `vsan:diskgroup`
- **SPL:**
```spl
index=hci sourcetype="vsan:diskgroup" earliest=-4h
| where state!="healthy" OR checksum_errors>0 OR component_state!="active"
| stats latest(state) as st, sum(checksum_errors) as checksums by cluster, host, dg_name
| sort -checksums
```
- **Implementation:** Ingest vSAN health JSON. Page on unhealthy disk group or rising checksums. Correlate with physical disk (UC-19.2.5).
- **Visualization:** Status grid (DG × host), Table (issues), Timeline (events).
- **CIM Models:** N/A

### UC-19.2.18 · Cluster Expansion Events

- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Configuration
- **Value:** Audits node add/remove, disk group expand, and maintenance mode during cluster scale events.
- **App/TA:** `TA-nutanix`, vCenter events
- **Data Sources:** `hci:cluster_events`
- **SPL:**
```spl
index=hci sourcetype="hci:cluster_events" earliest=-30d
| search "node added" OR "add node" OR "remove node" OR "expand"
| table _time, cluster, user, action, details
| sort -_time
```
- **Implementation:** Normalize messages from Prism and vCenter. Correlate with change tickets. Alert on unplanned expansion.
- **Visualization:** Timeline (expansion events), Table (recent changes), Bar chart (events by cluster).
- **CIM Models:** N/A

### UC-19.2.19 · Nutanix AHV Host Capacity

- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Capacity
- **Value:** vCPU, memory, and VM density headroom on AHV hosts — for right-sizing and new workload placement.
- **App/TA:** Prism Element API
- **Equipment Models:** Nutanix AHV
- **Data Sources:** `nutanix:ahv:host`
- **SPL:**
```spl
index=hci sourcetype="nutanix:ahv:host" earliest=-1h
| eval used_pct=round(100*vcpu_used/vcpu_total,1)
| where used_pct>80
| stats max(used_pct) as peak by host, cluster
| sort -peak
```
- **Implementation:** Poll host capacity. Alert at 80% vCPU or memory. Integrate with provisioning automation.
- **Visualization:** Bar chart (used % by host), Table (headroom), Gauge (cluster average).
- **CIM Models:** N/A

### UC-19.2.20 · SimpliVity Backup Efficiency

- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Value:** Backup job success, dedupe ratio, and store utilization for HPE SimpliVity.
- **App/TA:** HPE SimpliVity REST API
- **Equipment Models:** HPE SimpliVity
- **Data Sources:** `simplivity:backup`
- **SPL:**
```spl
index=hci sourcetype="simplivity:backup" earliest=-7d
| where status!="success" OR dedupe_ratio<3
| stats latest(status) as st, latest(dedupe_ratio) as dr by cluster, policy_name
| table cluster, policy_name, st, dr
```
- **Implementation:** Map OmniStack API fields. Alert on failed backup or low dedupe vs baseline.
- **Visualization:** Table (backup status), Line chart (dedupe trend), Single value (failed jobs).
- **CIM Models:** N/A

### UC-19.2.21 · Azure Stack HCI Cluster Health

- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Cluster validation, storage pool health, and Azure Arc connection state for Azure Stack HCI.
- **App/TA:** Windows Admin Center, Azure Monitor connector
- **Equipment Models:** Azure Stack HCI validated nodes
- **Data Sources:** `azurestackhci:health`
- **SPL:**
```spl
index=hci sourcetype="azurestackhci:health" earliest=-4h
| where overall_status!="healthy" OR storage_pool_status!="ok" OR arc_connected=0
| stats latest(overall_status) as st, latest(storage_pool_status) as pool by cluster_name
| table cluster_name, st, pool
```
- **Implementation:** Ingest WAC/OMS JSON. Alert on any non-healthy or Arc disconnect. Correlate with Windows Update pauses.
- **Visualization:** Status grid (HCI clusters), Table (issues), Timeline.
- **CIM Models:** N/A

### UC-19.2.22 · HPE dHCI Tier Health

- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** HPE disaggregated HCI storage tier latency, capacity, and replication lag between compute and storage.
- **App/TA:** HPE OneView, dHCI metrics
- **Equipment Models:** HPE dHCI
- **Data Sources:** `hpe:dhci:tier`
- **SPL:**
```spl
index=hci sourcetype="hpe:dhci:tier" earliest=-4h
| where tier_latency_ms>5 OR capacity_pct>85 OR repl_lag_sec>30
| stats max(tier_latency_ms) as lat, max(repl_lag_sec) as lag by cluster, tier_name
| sort -lat
```
- **Implementation:** Map vendor tier IDs. Alert on latency or replication lag SLO breach.
- **Visualization:** Table (tier health), Line chart (latency), Gauge (capacity).
- **CIM Models:** N/A

### UC-19.2.23 · vSAN Witness Appliance Health

- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Stretched vSAN witness availability and quorum for split-brain prevention.
- **App/TA:** vCenter, witness VM metrics
- **Equipment Models:** vSAN witness
- **Data Sources:** `vsan:witness`
- **SPL:**
```spl
index=hci sourcetype="vsan:witness" earliest=-24h
| where witness_state!="connected" OR quorum!="met"
| stats latest(witness_state) as ws, latest(quorum) as q by cluster
| table cluster, ws, q
```
- **Implementation:** Poll witness health API. Page immediately if witness disconnected or quorum lost.
- **Visualization:** Single value (witness OK), Table (clusters at risk), Timeline.
- **CIM Models:** N/A

### UC-19.2.24 · HCI Deduplication Efficiency Ratio

- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Capacity
- **Value:** Cluster-wide dedupe/compression ratio (Nutanix vs vSAN) vs baseline — efficiency regression indicates new noisy workloads or mis-tuned containers.
- **App/TA:** `TA-nutanix`, vSAN capacity
- **Data Sources:** `hci:storage_efficiency`
- **SPL:**
```spl
index=hci sourcetype="hci:storage_efficiency" earliest=-24h
| eval ratio=logical_tb/physical_tb
| lookup hci_efficiency_baseline.csv cluster OUTPUT baseline_ratio
| where ratio < baseline_ratio*0.85
| stats latest(ratio) as r, latest(baseline_ratio) as baseline by cluster
| table cluster, r, baseline
```
- **Implementation:** Define `baseline_ratio` from lookup or 30-day rolling mean. Alert on >15% drop week-over-week.
- **Visualization:** Line chart (dedupe ratio trend), Single value (fleet average), Table (regressions).
- **CIM Models:** N/A

---

