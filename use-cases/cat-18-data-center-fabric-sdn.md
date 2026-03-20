## 18. Data Center Fabric & SDN

### 18.1 Cisco ACI

**Splunk Add-on:** Cisco ACI Add-on for Splunk (`TA_cisco-ACI`, Splunkbase 1897 — deprecated, successor: Cisco DC Networking Application, Splunkbase 7777), APIC syslog

### UC-18.1.1 · Fabric Health Score Monitoring

- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Compliance
- **Value:** ACI fabric health scores provide a single-pane view of overall data center network health. Monitoring these scores lets you catch degradation before it impacts workloads, correlate health drops with specific faults, and maintain SLA compliance across your data center fabric.
- **App/TA:** `TA_cisco-ACI`, APIC REST API via scripted input
- **Equipment Models:** Cisco APIC, Nexus 9332C (ACI), Nexus 93180YC-FX (ACI), Nexus 9364C (ACI), Nexus 9504 (ACI), Nexus 9508 (ACI)
- **Data Sources:** APIC REST API (`/api/node/mo/topology/health.json`), APIC syslog
- **SPL:**
```spl
index=cisco_aci sourcetype="cisco:aci:health"
| eval node_type=case(like(dn, "%/node-1%"), "APIC", like(dn, "%/node-1___%"), "Leaf", like(dn, "%/node-2___%"), "Spine", 1==1, "Other")
| stats latest(healthScore) as health_score by dn, node_type
| eval status=case(health_score>=90, "Healthy", health_score>=70, "Degraded", health_score>=50, "Warning", 1==1, "Critical")
| sort health_score
```
- **Implementation:** Deploy scripted input to poll APIC health API every 60 seconds. Collect topology-wide and per-node health scores. Set threshold alerts: <90 degraded, <70 warning, <50 critical. Integrate with ITSI for service-level health correlation. Build trending to catch slow health degradation.
- **Visualization:** Single value (fabric health), Gauge (per-node health), Timechart (health trending), Status grid (node health map).
- **CIM Models:** N/A

### UC-18.1.2 · Fault Trending by Severity

- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity
- **Value:** ACI faults are the primary operational signal from the fabric. Trending faults by severity helps identify worsening conditions, recurring hardware issues, and configuration problems before they cascade into outages.
- **App/TA:** `TA_cisco-ACI`, APIC syslog
- **Equipment Models:** Cisco APIC, Nexus 9332C (ACI), Nexus 93180YC-FX (ACI), Nexus 9364C (ACI), Nexus 9504 (ACI), Nexus 9508 (ACI)
- **Data Sources:** APIC faults API (`/api/node/class/faultInst.json`), APIC syslog
- **SPL:**
```spl
index=cisco_aci sourcetype="cisco:aci:faults"
| eval severity_order=case(severity=="critical", 4, severity=="major", 3, severity=="minor", 2, severity=="warning", 1, 1==1, 0)
| timechart span=1h count by severity
| fields _time critical major minor warning
```
- **Implementation:** Poll APIC fault instance class every 5 minutes. Parse severity, fault code, affected DN, and lifecycle state. Track fault creation/clearing patterns. Alert on critical/major fault count spikes. Build fault code frequency reports for proactive maintenance.
- **Visualization:** Timechart (fault trends by severity), Bar chart (top fault codes), Table (active critical faults), Single value (open critical faults count).
- **CIM Models:** N/A

### UC-18.1.3 · Endpoint Mobility Tracking

- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Endpoint mobility in ACI tracks workload movement across leaf switches. Anomalous mobility (rapid moves, unexpected locations) can indicate misconfigurations, loops, or security issues like MAC spoofing.
- **App/TA:** `TA_cisco-ACI`, APIC endpoint tracker
- **Equipment Models:** Cisco APIC, Nexus 9332C (ACI), Nexus 93180YC-FX (ACI), Nexus 9364C (ACI), Nexus 9504 (ACI), Nexus 9508 (ACI)
- **Data Sources:** APIC endpoint tracker, ACI endpoint move events
- **SPL:**
```spl
index=cisco_aci sourcetype="cisco:aci:endpoint"
| where action="move"
| stats count as move_count, values(from_leaf) as from_leaves, values(to_leaf) as to_leaves, latest(_time) as last_move by mac, ip, tenant, epg
| where move_count > 5
| sort -move_count
| eval alert=if(move_count>20, "Anomalous", "Normal")
```
- **Implementation:** Enable endpoint tracker on APIC. Ingest endpoint move events via syslog or API polling. Baseline normal mobility rates per EPG. Alert on endpoints with excessive moves (>20/hour). Investigate rapid moves for potential loops or spoofing. Correlate with contract hits.
- **Visualization:** Table (high-mobility endpoints), Timechart (move rate trending), Sankey diagram (leaf-to-leaf moves), Single value (anomalous endpoints).
- **CIM Models:** N/A

### UC-18.1.4 · Contract/Filter Hit Analysis

- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** ACI contracts control EPG-to-EPG communication. Analyzing contract hits reveals traffic patterns, identifies overly permissive or unused contracts, and helps validate micro-segmentation policies are working as designed.
- **App/TA:** `TA_cisco-ACI`, APIC flow logs
- **Equipment Models:** Cisco APIC, Nexus 9332C (ACI), Nexus 93180YC-FX (ACI), Nexus 9364C (ACI), Nexus 9504 (ACI), Nexus 9508 (ACI)
- **Data Sources:** APIC contract hit counters, ACI flow telemetry
- **SPL:**
```spl
index=cisco_aci sourcetype="cisco:aci:contracts"
| stats sum(permit_count) as permitted, sum(deny_count) as denied by src_epg, dst_epg, contract_name, filter_name
| eval total=permitted+denied
| eval deny_pct=round((denied/total)*100, 2)
| sort -total
| table src_epg, dst_epg, contract_name, filter_name, permitted, denied, deny_pct
```
- **Implementation:** Enable contract statistics on APIC. Poll contract hit counters via API every 5 minutes. Track permit vs deny ratios per contract. Identify contracts with zero hits (candidates for cleanup). Alert on unexpected deny spikes indicating policy or application issues.
- **Visualization:** Table (contract hit summary), Bar chart (top contracts by hits), Timechart (deny trends), Sankey diagram (EPG-to-EPG flows).
- **CIM Models:** N/A

### UC-18.1.5 · Tenant Configuration Audit

- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Value:** Configuration changes in ACI tenants (BDs, EPGs, contracts) are a leading cause of outages. Auditing all changes provides accountability, supports compliance, and enables rapid rollback identification when issues occur.
- **App/TA:** `TA_cisco-ACI`, APIC audit log
- **Equipment Models:** Cisco APIC, Nexus 9332C (ACI), Nexus 93180YC-FX (ACI), Nexus 9364C (ACI), Nexus 9504 (ACI), Nexus 9508 (ACI)
- **Data Sources:** APIC audit log (`/api/node/class/aaaModLR.json`)
- **SPL:**
```spl
index=cisco_aci sourcetype="cisco:aci:audit"
| where like(affected, "uni/tn-%")
| rex field=affected "uni/tn-(?<tenant>[^/]+)"
| stats count by _time, user, action, tenant, affected, descr
| sort -_time
| table _time, user, action, tenant, affected, descr
```
- **Implementation:** Enable audit logging on APIC (enabled by default). Ingest audit records via API polling or syslog. Track all create/modify/delete operations on tenant objects. Correlate configuration changes with fault events. Require change management tickets for production tenant changes.
- **Visualization:** Table (recent changes), Timeline (change events), Bar chart (changes by user), Pie chart (changes by tenant).
- **CIM Models:** N/A

### UC-18.1.6 · Leaf/Spine Interface Utilization

- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Fabric link saturation causes packet drops and application latency. Monitoring leaf/spine interface utilization identifies hotspots, validates ECMP distribution, and supports capacity planning for fabric expansion.
- **App/TA:** `TA_cisco-ACI`, APIC interface metrics
- **Equipment Models:** Cisco APIC, Nexus 9332C (ACI), Nexus 93180YC-FX (ACI), Nexus 9364C (ACI), Nexus 9504 (ACI), Nexus 9508 (ACI)
- **Data Sources:** APIC interface statistics API, fabric port counters
- **SPL:**
```spl
index=cisco_aci sourcetype="cisco:aci:interface_stats"
| eval util_pct=round((bytesRate*8/speed)*100, 2)
| stats avg(util_pct) as avg_util, max(util_pct) as peak_util by node, interface, speed
| where peak_util > 70
| sort -peak_util
| table node, interface, speed, avg_util, peak_util
```
- **Implementation:** Poll APIC interface statistics every 60 seconds. Calculate utilization from byte rates and link speed. Set thresholds at 70% warning, 85% critical. Track ECMP balance across parallel fabric links. Alert on sustained high utilization indicating need for fabric expansion.
- **Visualization:** Heatmap (interface utilization by node), Timechart (utilization trending), Table (high-util interfaces), Gauge (fabric aggregate utilization).
- **CIM Models:** N/A

### UC-18.1.7 · APIC Cluster Health

- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Availability
- **Value:** APIC controllers manage the entire ACI fabric. Cluster health issues (split-brain, leader election, convergence problems) can cause fabric-wide configuration and policy failures. Monitoring APIC cluster state is essential for fabric reliability.
- **App/TA:** `TA_cisco-ACI`, APIC system logs
- **Equipment Models:** Cisco APIC, Nexus 9332C (ACI), Nexus 93180YC-FX (ACI), Nexus 9364C (ACI), Nexus 9504 (ACI), Nexus 9508 (ACI)
- **Data Sources:** APIC cluster health API, APIC system logs/syslog
- **SPL:**
```spl
index=cisco_aci sourcetype="cisco:aci:system"
| search (cluster_status OR leader_election OR convergence)
| eval status=case(
    searchmatch("fully-fit"), "Healthy",
    searchmatch("partially-fit"), "Degraded",
    searchmatch("not-fit"), "Critical",
    1==1, "Unknown")
| stats latest(status) as cluster_status, latest(_time) as last_update by apic_id
| table apic_id, cluster_status, last_update
```
- **Implementation:** Monitor APIC cluster health endpoint every 30 seconds. Track cluster fitness, leader election events, and database sync status. Alert immediately on any non-fully-fit state. Monitor APIC resource utilization (disk, CPU, memory). Document recovery procedures for cluster issues.
- **Visualization:** Status grid (APIC cluster state), Timeline (cluster events), Single value (cluster fitness), Table (APIC node details).
- **CIM Models:** N/A

### UC-18.1.8 · Spine-Leaf Fabric Latency

- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance
- **Value:** Inter-switch latency within the fabric directly impacts east-west traffic between workloads. High latency causes application timeouts, database replication lag, and degraded user experience. Monitoring fabric latency identifies congestion, misrouted traffic, and capacity bottlenecks before they impact SLAs.
- **App/TA:** Custom scripted input (ping, TWAMP, fabric analytics)
- **Equipment Models:** Nexus 9000, Nexus 9300/9500, Arista 7050/7280/7500
- **Data Sources:** In-band Network Telemetry (INT), fabric analytics tools, ICMP probes between switches
- **SPL:**
```spl
index=fabric sourcetype="fabric:latency"
| eval latency_ms=round(rtt_us/1000, 2)
| stats avg(latency_ms) as avg_latency, max(latency_ms) as max_latency, stdev(latency_ms) as latency_jitter by src_switch, dst_switch, path_type
| where avg_latency > 1 OR max_latency > 5
| sort -max_latency
| table src_switch, dst_switch, path_type, avg_latency, max_latency, latency_jitter
```
- **Implementation:** Deploy ICMP or TWAMP probes between leaf and spine switches on a dedicated management or out-of-band VLAN. Poll every 30–60 seconds. For INT-capable fabrics (Arista DANZ, Cisco NX-OS telemetry), enable in-band telemetry for real-time latency visibility. Parse probe results into Splunk via scripted input. Set thresholds: >1 ms average or >5 ms peak for east-west paths. Alert on sustained elevation. Correlate latency spikes with interface utilization and BGP convergence events.
- **Visualization:** Heatmap (latency by switch pair), Timechart (latency trending), Table (high-latency paths), Single value (fabric P99 latency).
- **CIM Models:** N/A

### UC-18.1.9 · ACI Contract Hit/Miss Ratio Analysis

- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance, Security
- **Value:** Complements raw contract hits (UC-18.1.4) with **permit vs deny/miss** ratios over time to catch mis-tuned filters and unexpected drops before workloads fail.
- **App/TA:** `TA_cisco-ACI`, APIC contract statistics
- **Equipment Models:** Cisco APIC, Nexus 9000 (ACI mode)
- **Data Sources:** `sourcetype=cisco:aci:contracts` or APIC API contract stats
- **SPL:**
```spl
index=cisco_aci sourcetype="cisco:aci:contracts"
| timechart span=1h sum(permit_count) as permit sum(deny_count) as deny by contract_name
| eval miss_ratio=round(100*deny/(deny+permit+0.001),2)
```
- **Implementation:** Poll contract counters on the same interval as UC-18.1.4. Alert when `miss_ratio` jumps vs 24h baseline for business-critical contracts. Map `contract_name` to owning team.
- **Visualization:** Line chart (permit vs deny), Single value (miss ratio %), Table (worst contracts).
- **CIM Models:** N/A

### UC-18.1.10 · ACI Endpoint Group (EPG) Health

- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Aggregates fault and health indicators per EPG (endpoint count, contract violations, BD binding) for application-centric status.
- **App/TA:** `TA_cisco-ACI`
- **Equipment Models:** Cisco APIC, ACI fabric
- **Data Sources:** `cisco:aci:faults`, `cisco:aci:endpoint`, EPG MO
- **SPL:**
```spl
index=cisco_aci (sourcetype="cisco:aci:faults" OR sourcetype="cisco:aci:endpoint")
| rex field=affected "epg-(?<epg>[^/]+)"
| stats count(eval(severity IN ("critical","major"))) as sev_count, dc(mac) as ep_count by tenant, epg
| eval epg_health=if(sev_count>0 OR ep_count=0,"Degraded","OK")
| where epg_health!="OK"
| table tenant, epg, sev_count, ep_count
```
- **Implementation:** Normalize `affected` DN parsing to your naming. Enrich with APIC EPG API for expected EP counts. Alert on EPG with faults or zero endpoints when baseline >0.
- **Visualization:** Status table (EPG health), Heatmap (tenant × EPG), Single value (degraded EPG count).
- **CIM Models:** N/A

### UC-18.1.11 · ACI Fault Lifecycle Tracking

- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** Tracks fault `lc` (lifecycle: raising, active, retaining, resolved) and time-to-clear — beyond raw fault counts (UC-18.1.2).
- **App/TA:** `TA_cisco-ACI`
- **Equipment Models:** Cisco APIC
- **Data Sources:** `sourcetype=cisco:aci:faults`
- **SPL:**
```spl
index=cisco_aci sourcetype="cisco:aci:faults"
| eval cleared=if(match(lower(lc),"(?i)resolved|retaining"),1,0)
| stats earliest(_time) as first_seen latest(_time) as last_seen max(cleared) as ever_cleared by code, dn
| eval duration_hrs=round((last_seen-first_seen)/3600,2)
| where duration_hrs>24 AND ever_cleared=0
| table code, dn, duration_hrs, first_seen
```
- **Implementation:** Map `lc` per APIC version. Join clear events if streamed separately. Report MTTR for critical faults.
- **Visualization:** Table (long-lived faults), Bar chart (avg clear time by code), Timeline.
- **CIM Models:** N/A

### UC-18.1.12 · Fabric Node Decommission Events

- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Configuration
- **Value:** Audits leaf/spine/APIC removal or disable operations for change control and capacity reconciliation.
- **App/TA:** `TA_cisco-ACI`, APIC audit/syslog
- **Equipment Models:** Cisco APIC, Nexus 9000
- **Data Sources:** `cisco:aci:audit`, APIC syslog
- **SPL:**
```spl
index=cisco_aci (sourcetype="cisco:aci:audit" OR sourcetype="cisco:aci:system")
| search decommission OR "node-remove" OR "unregister" OR "fabricDecommission"
| table _time, user, affected, descr
| sort -_time
```
- **Implementation:** Tune search terms to APIC messages when nodes are drained from fabric. Correlate with maintenance windows.
- **Visualization:** Table (decommission events), Timeline, Single value (events / month).
- **CIM Models:** N/A

### UC-18.1.13 · Bridge Domain Subnet Utilization

- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity
- **Value:** Tracks IP usage vs subnet size per BD to prevent exhaustion of gateway pools and VM mobility issues.
- **App/TA:** `TA_cisco-ACI`, APIC BD API
- **Equipment Models:** Cisco ACI
- **Data Sources:** `cisco:aci:bd_stats` or scripted API
- **SPL:**
```spl
index=cisco_aci sourcetype="cisco:aci:bd_stats"
| eval used_pct=round(100*ip_in_use/total_ips,1)
| where used_pct > 85
| table tenant, bd, subnet, used_pct, ip_in_use, total_ips
| sort -used_pct
```
- **Implementation:** Ingest BD statistics from periodic API poll (`fvBD` subnets vs endpoint counts). Alert at 85%/95% thresholds.
- **Visualization:** Table (full BDs), Bar chart (used % by BD), Gauge (worst BD).
- **CIM Models:** N/A

### UC-18.1.14 · L3Out Prefix Monitoring

- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance
- **Value:** Monitors advertised/ learned prefixes on L3Outs (BGP/OSPF) for flapping, withdrawal storms, and unexpected route loss.
- **App/TA:** `TA_cisco-ACI`, APIC L3ExtInstP events
- **Equipment Models:** Cisco ACI, external routers
- **Data Sources:** APIC syslog, `cisco:aci:bgp` or route telemetry
- **SPL:**
```spl
index=cisco_aci sourcetype="cisco:aci:bgp" earliest=-24h
| where match(lower(message),"(?i)withdraw|flap|prefix|l3out")
| stats count by l3out_name, peer, prefix
| where count>20
| sort -count
```
- **Implementation:** Map peer and L3Out from your TA. Correlate with northbound link monitoring. Alert on withdrawal burst.
- **Visualization:** Table (noisy prefixes), Line chart (events / hour), Timeline.
- **CIM Models:** N/A

### UC-18.1.15 · APIC Policy CAM Utilization

- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Capacity
- **Value:** Tracks TCAM/CAM-style resource use for contracts and security policies on leaf nodes — exhaustion causes policy install failures.
- **App/TA:** `TA_cisco-ACI`, leaf diagnostics
- **Equipment Models:** Nexus 9300/9500 ACI leafs
- **Data Sources:** `cisco:aci:policy_resource`, CLI snapshot via scripted input
- **SPL:**
```spl
index=cisco_aci sourcetype="cisco:aci:policy_resource"
| where resource_type="policy_cam" OR match(lower(metric_name),"(?i)tcam|cam")
| eval used_pct=round(100*used/total,1)
| where used_pct>80
| table node_id, used_pct, used, total
| sort -used_pct
```
- **Implementation:** Field names vary by NX-OS/ACI release; use vendor doc for exact OID/API. Alert before hardware policy scale limits.
- **Visualization:** Bar chart (CAM % by leaf), Table (top nodes), Line chart (trend).
- **CIM Models:** N/A

### UC-18.1.16 · ACI Tenant Configuration Compliance Audit

- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Value:** Checks tenants for required objects (vzAny restrictions, monitoring policies, SNMP/Syslog) — extends change audit (UC-18.1.5) with **policy completeness** scoring.
- **App/TA:** `TA_cisco-ACI`
- **Equipment Models:** Cisco APIC
- **Data Sources:** APIC config export or `cisco:aci:audit`
- **SPL:**
```spl
index=cisco_aci sourcetype="cisco:aci:tenant_summary"
| eval has_mon=isnotnull(mon_policy)
| eval has_snmp=isnotnull(snmp_group)
| where has_mon=0 OR has_snmp=0
| table tenant, has_mon, has_snmp
```
- **Implementation:** Build `tenant_summary` from scheduled API pulls (`fvTenant` + children). Adjust required attributes to your standards.
- **Visualization:** Table (non-compliant tenants), Pie chart (compliance %), Bar chart (missing controls).
- **CIM Models:** N/A

### UC-18.1.17 · ACI Multisite Health

- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Availability
- **Value:** Monitors inter-site control-plane sync, spine proxy, and state for Cisco ACI Multi-Site / Multi-Pod deployments.
- **App/TA:** `TA_cisco-ACI`, MSO/APIC cross-site events
- **Equipment Models:** APIC, NDO/MSO (if used)
- **Data Sources:** `cisco:aci:multisite`, APIC syslog
- **SPL:**
```spl
index=cisco_aci sourcetype="cisco:aci:multisite" earliest=-24h
| where match(lower(status),"(?i)out.of.sync|isolated|failed|degraded")
| stats count by site_name, peer_site, component
| sort -count
```
- **Implementation:** Ingest MSO/NDO or per-APIC multisite diagnostics. Alert on any site not `in-sync`. Runbook for partition scenarios.
- **Visualization:** Status grid (site × peer), Table (active issues), Single value (sites degraded).
- **CIM Models:** N/A

### UC-18.1.18 · APIC Cluster Replication Latency

- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Availability
- **Value:** Complements UC-18.1.7 with **database replication delay** and inter-APIC consensus metrics for split-brain prevention.
- **App/TA:** `TA_cisco-ACI`
- **Equipment Models:** Cisco APIC cluster
- **Data Sources:** APIC `avictrl` / cluster diagnostics API
- **SPL:**
```spl
index=cisco_aci sourcetype="cisco:aci:cluster_diag" earliest=-24h
| where repl_delay_ms>500 OR match(lower(message),"(?i)split|partition|lag")
| table _time, apic_id, repl_delay_ms, message
| sort -_time
```
- **Implementation:** Map fields from your APIC release; some metrics require Cisco DC Networking App. Alert on sustained replication lag.
- **Visualization:** Line chart (repl delay), Table (alerts), Single value (max lag ms).
- **CIM Models:** N/A

---

### 18.2 VMware NSX

**Splunk Add-on:** VMware NSX add-on (`vmware_nsx_addon`, Splunkbase 6805), syslog

### UC-18.2.1 · Distributed Firewall Rule Hits

- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** NSX Distributed Firewall (DFW) runs on every hypervisor, providing east-west traffic control. Monitoring rule hits validates security policy effectiveness, identifies unused rules for cleanup, and detects policy violations in real time.
- **App/TA:** `vmware_nsx_addon`, NSX DFW syslog
- **Data Sources:** NSX DFW firewall logs (syslog), NSX Manager API
- **SPL:**
```spl
index=vmware sourcetype="vmware:nsx:dfw"
| stats sum(eval(if(action="ALLOW", 1, 0))) as allowed, sum(eval(if(action="DROP", 1, 0))) as dropped, sum(eval(if(action="REJECT", 1, 0))) as rejected by rule_id, rule_name, src_ip, dst_ip, dst_port, protocol
| eval total=allowed+dropped+rejected
| sort -total
| table rule_id, rule_name, src_ip, dst_ip, dst_port, protocol, allowed, dropped, rejected
```
- **Implementation:** Enable DFW logging on NSX Manager for desired rule sections. Forward DFW logs via syslog to Splunk. Parse rule ID, action, source, destination, and port fields. Identify rules with zero hits (candidates for removal). Alert on unexpected DENY hits indicating misconfiguration or attack.
- **Visualization:** Bar chart (top rules by hits), Timechart (allow vs deny trending), Table (denied connections), Sankey diagram (source-to-destination flows).
- **CIM Models:** N/A

### UC-18.2.2 · Micro-Segmentation Enforcement

- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Value:** NSX micro-segmentation is a key Zero Trust control. Monitoring enforcement validates that workloads are properly isolated, detects lateral movement attempts, and proves compliance with segmentation policies during audits.
- **App/TA:** `vmware_nsx_addon`, NSX DFW logs
- **Data Sources:** NSX DFW logs, NSX security group membership
- **SPL:**
```spl
index=vmware sourcetype="vmware:nsx:dfw"
| lookup nsx_security_groups vm_name OUTPUT security_group
| stats count as hits, dc(dst_ip) as unique_destinations by security_group, action, direction
| eval compliance=if(action="DROP" AND direction="intra-group", "Violation", "Expected")
| sort -hits
```
- **Implementation:** Define security groups in NSX aligned with application tiers. Enable DFW logging for inter-group and intra-group traffic. Enrich logs with security group membership. Track allowed vs denied inter-group communication. Alert on intra-group denials or unexpected inter-group allows.
- **Visualization:** Heatmap (group-to-group traffic), Sankey diagram (flow paths), Bar chart (denials by group), Single value (policy violation count).
- **CIM Models:** N/A

### UC-18.2.3 · Logical Switch Health

- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** NSX logical switches and routers form the virtual network fabric. Monitoring their operational status ensures VM connectivity and helps identify overlay network issues before they impact applications.
- **App/TA:** `vmware_nsx_addon`, NSX Manager events
- **Data Sources:** NSX Manager API, NSX system events/syslog
- **SPL:**
```spl
index=vmware sourcetype="vmware:nsx:events"
| search object_type IN ("LogicalSwitch", "LogicalRouter", "Tier0Router", "Tier1Router")
| eval status=case(severity=="HIGH" OR severity=="CRITICAL", "Degraded", severity=="MEDIUM", "Warning", 1==1, "Healthy")
| stats latest(status) as current_status, count as event_count by object_name, object_type
| sort -event_count
```
- **Implementation:** Poll NSX Manager API for logical switch and router status every 60 seconds. Ingest NSX system events via syslog. Alert on logical switch or router down events. Track BFD session state for Tier-0/Tier-1 routers. Monitor VNI pool exhaustion.
- **Visualization:** Status grid (switch/router health), Table (degraded components), Timechart (event trends), Single value (active logical switches).
- **CIM Models:** N/A

### UC-18.2.4 · NSX Edge Performance

- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** NSX Edge nodes handle north-south traffic, load balancing, and NAT. Performance bottlenecks on Edge nodes directly impact application availability and throughput for any workload communicating outside the NSX fabric.
- **App/TA:** `vmware_nsx_addon`, NSX Edge metrics
- **Data Sources:** NSX Edge node metrics (CPU, memory, datapath), NSX Manager API
- **SPL:**
```spl
index=vmware sourcetype="vmware:nsx:edge_metrics"
| stats avg(cpu_pct) as avg_cpu, max(cpu_pct) as peak_cpu, avg(mem_pct) as avg_mem, avg(datapath_cpu_pct) as avg_dp_cpu by edge_node, cluster
| eval status=case(peak_cpu>90 OR avg_dp_cpu>80, "Critical", peak_cpu>75 OR avg_dp_cpu>60, "Warning", 1==1, "Healthy")
| table edge_node, cluster, avg_cpu, peak_cpu, avg_mem, avg_dp_cpu, status
| sort -peak_cpu
```
- **Implementation:** Collect Edge node metrics via NSX Manager API every 60 seconds. Monitor both management plane and datapath CPU separately. Track interface throughput on uplinks. Set thresholds: datapath CPU >80% critical, >60% warning. Plan Edge node scale-out when sustained utilization exceeds thresholds.
- **Visualization:** Gauge (Edge CPU/memory), Timechart (performance trending), Table (Edge node status), Single value (peak datapath CPU).
- **CIM Models:** N/A

### UC-18.2.5 · Transport Node Connectivity

- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Transport nodes are the hypervisors participating in the NSX overlay. Tunnel failures between transport nodes cause VM-to-VM communication loss across hosts, directly impacting application availability.
- **App/TA:** `vmware_nsx_addon`, NSX transport node logs
- **Data Sources:** NSX transport node status API, TEP tunnel events
- **SPL:**
```spl
index=vmware sourcetype="vmware:nsx:transport_node"
| eval tunnel_status=case(status=="UP", "Healthy", status=="DEGRADED", "Degraded", status=="DOWN", "Down", 1==1, "Unknown")
| stats latest(tunnel_status) as current_status, latest(_time) as last_seen by transport_node, host_ip
| search current_status!="Healthy"
| table transport_node, host_ip, current_status, last_seen
```
- **Implementation:** Poll NSX Manager for transport node status every 30 seconds. Monitor TEP (Tunnel Endpoint) reachability between all transport nodes. Alert immediately on tunnel DOWN state. Track tunnel flapping (frequent UP/DOWN cycles). Correlate with physical network events (link failures, MTU issues).
- **Visualization:** Status grid (transport node map), Table (degraded nodes), Timechart (tunnel status changes), Single value (healthy tunnel percentage).
- **CIM Models:** N/A

### UC-18.2.6 · Distributed Firewall Rule Hit Rate Analysis

- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Baselines hits per DFW rule and flags sudden drops (unused or bypassed) or spikes (attack or misconfiguration) — complements UC-18.2.1 volume view.
- **App/TA:** `vmware_nsx_addon`
- **Equipment Models:** NSX-T Data Center
- **Data Sources:** `sourcetype=vmware:nsx:dfw`
- **SPL:**
```spl
index=vmware sourcetype="vmware:nsx:dfw" earliest=-7d
| bin _time span=1d
| stats count by _time, rule_id, rule_name
| eventstats avg(count) as baseline by rule_id
| where count < baseline*0.2 OR count > baseline*5
| table _time, rule_id, rule_name, count, baseline
```
- **Implementation:** Requires ≥7 days of data for baseline. Exclude ephemeral rules by lookup. Alert on zero-hit critical allow rules.
- **Visualization:** Line chart (hits per rule), Table (anomalies), Heatmap (rule × day).
- **CIM Models:** N/A

### UC-18.2.7 · Micro-Segmentation Policy Drift

- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Value:** Compares published DFW policy revision to approved baseline (lookup) to detect unauthorized rule changes between change windows.
- **App/TA:** `vmware_nsx_addon`, NSX policy export
- **Data Sources:** `vmware:nsx:policy_revision`, config snapshots
- **SPL:**
```spl
index=vmware sourcetype="vmware:nsx:policy_revision" earliest=-24h
| stats latest(revision_id) as rev by domain_name
| lookup nsx_policy_baseline.csv domain_name OUTPUT approved_revision
| where rev!=approved_revision
| table domain_name, rev, approved_revision
```
- **Implementation:** Populate baseline from last CAB-approved export. Run after each change window; alert on drift.
- **Visualization:** Table (drifted domains), Single value (drift count), Timeline.
- **CIM Models:** N/A

### UC-18.2.8 · NSX Edge Gateway Health

- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Service status for Tier-0/Tier-1 SR components (BGP, NAT, LB service) on Edge nodes — complements CPU metrics (UC-18.2.4).
- **App/TA:** `vmware_nsx_addon`
- **Equipment Models:** NSX Edge VM/BM
- **Data Sources:** `vmware:nsx:edge_status`
- **SPL:**
```spl
index=vmware sourcetype="vmware:nsx:edge_status" earliest=-4h
| where overall_status!="UP" OR bgp_status!="Established"
| stats latest(overall_status) as st, latest(bgp_status) as bgp by edge_node, lr_name
| table edge_node, lr_name, st, bgp
```
- **Implementation:** Map status fields from NSX Manager API. Alert on any non-UP gateway service. Correlate with northbound ISP events.
- **Visualization:** Status grid (edge × LR), Table (down services), Timeline.
- **CIM Models:** N/A

### UC-18.2.9 · NSX-T Transport Node Overlay Path Health

- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Validates GENEVE overlay between TNs (packet loss, MTU) beyond simple UP/DOWN (UC-18.2.5).
- **App/TA:** `vmware_nsx_addon`
- **Equipment Models:** ESXi KVM transport nodes
- **Data Sources:** `vmware:nsx:tn_diag`, traceflow results
- **SPL:**
```spl
index=vmware sourcetype="vmware:nsx:tn_diag" earliest=-24h
| where pkt_loss_pct>1 OR mtu_issue=1
| stats max(pkt_loss_pct) as max_loss by src_tn, dst_tn
| sort -max_loss
| head 50
```
- **Implementation:** Ingest Traceflow or TN diagnostic jobs on schedule. Alert on loss >1% between any TN pair in same pool.
- **Visualization:** Heatmap (TN × TN loss), Table (worst pairs), Line chart (loss trend).
- **CIM Models:** N/A

### UC-18.2.10 · Load Balancer Pool Health

- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Monitors NSX Advanced Load Balancer / LB pool member up/down and health check failures for published apps.
- **App/TA:** `vmware_nsx_addon`, Avi if integrated
- **Equipment Models:** NSX ALB, LB service on Edge
- **Data Sources:** `vmware:nsx:lb_pool`
- **SPL:**
```spl
index=vmware sourcetype="vmware:nsx:lb_pool" earliest=-24h
| where member_status!="UP" OR health_check_failures>0
| stats count by pool_name, member_ip, member_status
| sort -count
```
- **Implementation:** Map Avi or NSX LB API fields. Alert when active members < minimum for pool.
- **Visualization:** Table (unhealthy pools), Bar chart (failures by pool), Single value (pools in critical state).
- **CIM Models:** N/A

### UC-18.2.11 · NAT Rule Utilization

- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity
- **Value:** Tracks NAT session and port allocation per rule — prevents exhaustion on busy Edge gateways.
- **App/TA:** `vmware_nsx_addon`
- **Equipment Models:** NSX Edge NAT
- **Data Sources:** `vmware:nsx:nat_stats`
- **SPL:**
```spl
index=vmware sourcetype="vmware:nsx:nat_stats" earliest=-1h
| eval used_pct=round(100*active_sessions/session_limit,1)
| where used_pct>85
| table edge_node, rule_id, active_sessions, session_limit, used_pct
| sort -used_pct
```
- **Implementation:** Session limits depend on Edge form factor; load from capacity sheet via lookup. Alert at 85%.
- **Visualization:** Bar chart (NAT % by rule), Table (top consumers), Gauge.
- **CIM Models:** N/A

### UC-18.2.12 · T0/T1 Gateway Failover Events

- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Captures active/standby transitions for Tier-0/Tier-1 logical routers for incident correlation and HA validation.
- **App/TA:** `vmware_nsx_addon`
- **Equipment Models:** NSX-T LR HA
- **Data Sources:** `vmware:nsx:lr_events`
- **SPL:**
```spl
index=vmware sourcetype="vmware:nsx:lr_events" earliest=-7d
| search failover OR "HA switch" OR "role change"
| stats latest(_time) as last_seen, count by lr_name, prev_role, new_role, edge_node
| sort -last_seen
```
- **Implementation:** Normalize syslog/API messages for HA events. Alert on any unplanned failover. Pager for T0.
- **Visualization:** Timeline (failovers), Table (events), Single value (failovers / month).
- **CIM Models:** N/A

### UC-18.2.13 · NSX Manager Cluster Health

- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Cluster quorum, Corfu/RAFT health, and API reachability for NSX Manager appliance cluster.
- **App/TA:** `vmware_nsx_addon`
- **Equipment Models:** NSX Manager cluster (3-node)
- **Data Sources:** `vmware:nsx:manager_cluster`
- **SPL:**
```spl
index=vmware sourcetype="vmware:nsx:manager_cluster" earliest=-24h
| where cluster_status!="STABLE" OR offline_nodes>0
| stats latest(cluster_status) as st latest(offline_nodes) as off by cluster_id
| table cluster_id, st, off
```
- **Implementation:** Map NSX version-specific cluster health API. Alert immediately if not STABLE or any node offline.
- **Visualization:** Status grid (manager nodes), Single value (cluster OK), Timeline.
- **CIM Models:** N/A

### 18.3 Other SDN

**Splunk Add-on:** Custom inputs, Kubernetes CNI logs

### UC-18.3.1 · Cilium/Calico Network Policy Monitoring

- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Value:** Kubernetes CNI network policies enforce pod-to-pod communication rules. Monitoring policy enforcement validates that micro-segmentation is working in containerized environments, critical for multi-tenant clusters and compliance.
- **App/TA:** Custom scripted inputs, Kubernetes logging pipeline
- **Data Sources:** Cilium/Calico policy logs, Kubernetes audit logs
- **SPL:**
```spl
index=kubernetes sourcetype="kube:cni:policy"
| stats count as hits, dc(src_pod) as src_pods, dc(dst_pod) as dst_pods by policy_name, action, namespace
| eval enforcement=if(action="deny", "Blocked", "Allowed")
| sort -hits
| table namespace, policy_name, enforcement, hits, src_pods, dst_pods
```
- **Implementation:** Enable CNI policy logging in Cilium/Calico configuration. Forward logs via Fluentd/Fluent Bit to Splunk HEC. Parse policy name, action, source/destination pod, and namespace. Track denied traffic for security visibility. Identify namespaces without network policies (compliance gap).
- **Visualization:** Bar chart (policy hits by namespace), Table (denied flows), Heatmap (namespace-to-namespace traffic), Single value (namespaces without policies).
- **CIM Models:** N/A

### UC-18.3.2 · OpenStack Neutron Events

- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Neutron manages virtual networking in OpenStack. Tracking network operations (creation, modification, deletion) provides change audit, helps troubleshoot connectivity issues, and identifies unauthorized network modifications.
- **App/TA:** Custom scripted input (OpenStack API), OpenStack syslog
- **Data Sources:** Neutron API logs, OpenStack syslog
- **SPL:**
```spl
index=openstack sourcetype="openstack:neutron"
| search action IN ("create", "update", "delete")
| stats count by action, resource_type, user, project_name
| sort -count
| table _time, user, project_name, action, resource_type, resource_name, count
```
- **Implementation:** Ingest Neutron API logs via syslog or OpenStack notification bus. Track all network, subnet, port, and router CRUD operations. Alert on mass deletions or unauthorized modifications. Correlate network changes with VM connectivity issues.
- **Visualization:** Table (recent operations), Bar chart (operations by type), Timeline (change events), Pie chart (operations by project).
- **CIM Models:** N/A

### UC-18.3.3 · SDN Controller Health

- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Availability
- **Value:** SDN controllers are the brain of software-defined networks. Controller outages or cluster consensus failures can cause network-wide disruption. Monitoring controller health ensures the control plane remains available and consistent.
- **App/TA:** Custom scripted input, SDN controller syslog
- **Data Sources:** SDN controller system logs, cluster status API
- **SPL:**
```spl
index=sdn sourcetype="sdn:controller"
| search (cluster_state OR heartbeat OR leader_election OR consensus)
| eval health=case(
    searchmatch("healthy") OR searchmatch("active"), "Healthy",
    searchmatch("degraded") OR searchmatch("standby"), "Degraded",
    searchmatch("failed") OR searchmatch("unreachable"), "Critical",
    1==1, "Unknown")
| stats latest(health) as status, latest(_time) as last_heartbeat by controller_id, role
| table controller_id, role, status, last_heartbeat
```
- **Implementation:** Monitor SDN controller cluster via heartbeat polling every 15 seconds. Track cluster membership, leader election events, and consensus state. Alert immediately on controller failure or split-brain conditions. Monitor controller resource utilization (CPU, memory, database size). Maintain runbook for controller failover.
- **Visualization:** Status grid (controller cluster), Timeline (cluster events), Single value (cluster health), Table (controller details).
- **CIM Models:** N/A

---

### UC-18.3.4 · VXLAN Tunnel and Overlay Health
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** VXLAN tunnel failures break overlay connectivity. Monitoring tunnel state and packet drops ensures fabric reliability and fast troubleshooting.
- **App/TA:** Leaf/spine device logs, fabric manager
- **Data Sources:** VXLAN tunnel status, NVE interface, encapsulation stats
- **SPL:**
```spl
index=sdn sourcetype="vxlan:tunnel"
| where state!="up" OR packet_drops > 0
| stats latest(state) as state, sum(packet_drops) as drops by tunnel_id, leaf_id, vni
| table tunnel_id, leaf_id, vni, state, drops
```
- **Implementation:** Poll VXLAN tunnel and NVE stats from fabric devices. Alert on tunnel down or non-zero drops. Report on overlay health by VNI and leaf. Correlate with BGP and underlay events.
- **Visualization:** Status grid (tunnel × state), Table (tunnels with drops), Line chart (drops over time).
- **CIM Models:** N/A

---

### UC-18.3.5 · EVPN Route and MAC Mobility Events
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** EVPN route churn or MAC mobility storms can impact convergence and stability. Tracking route and mobility events supports fabric tuning and VM mobility analysis.
- **App/TA:** BGP/EVPN route monitor, spine/leaf logs
- **Data Sources:** EVPN route advertisements, MAC mobility sequence numbers
- **SPL:**
```spl
index=sdn sourcetype="evpn:route"
| search (type=mac_ip OR type=mac_mobility)
| stats count by vni, host, _time span=5m
| where count > 100
| sort -count
```
- **Implementation:** Ingest EVPN route and mobility events. Alert on route storm or high mobility count in short window. Report on top movers and VNIs with most churn. Use for capacity and placement planning.
- **Visualization:** Line chart (mobility events over time), Table (top VNIs by churn), Bar chart (mobility by host).
- **CIM Models:** N/A

---

### UC-18.3.6 · ACI Contract Deny and Drop Statistics
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** High contract deny or drop counts may indicate overly restrictive policy or attack traffic. Monitoring supports policy tuning and security analysis.
- **App/TA:** ACI policy stats, fabric stats
- **Data Sources:** Contract hit counters, deny/drop by contract and EPG
- **SPL:**
```spl
index=aci sourcetype="aci:contract_stats"
| where action="deny" OR action="drop"
| stats sum(packets) as denied by contract_name, src_epg, dest_epg, _time span=1h
| where denied > 1000
| sort -denied
```
- **Implementation:** Ingest ACI contract statistics. Track deny and drop by contract and EPG pair. Alert on spike in denies. Report on top denied flows for policy review. Correlate with app and security events.
- **Visualization:** Table (denied flows), Bar chart (denies by contract), Line chart (deny trend).
- **CIM Models:** N/A

---

### UC-18.3.7 · NSX-T Segment and Gateway Capacity
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Segment or gateway overload affects tenant connectivity and performance. Monitoring capacity and utilization supports scale planning and troubleshooting.
- **App/TA:** NSX-T API, vSphere/NSX metrics
- **Data Sources:** Segment port count, gateway session count, throughput per segment
- **SPL:**
```spl
index=nsx sourcetype="nsx:segment"
| stats latest(port_count) as ports, latest(port_limit) as limit, latest(throughput_mbps) as mbps by segment_id, gateway_id
| eval port_pct=round((ports/limit)*100, 1)
| where port_pct > 80 OR mbps > 9000
| table segment_id, gateway_id, ports, limit, port_pct, mbps
```
- **Implementation:** Poll NSX-T segment and gateway metrics. Alert when port usage or throughput approaches limit. Report on capacity trend and top-loaded segments. Plan gateway scale-out when needed.
- **Visualization:** Table (segments near limit), Gauge (port utilization), Line chart (throughput trend).
- **CIM Models:** N/A

---

### UC-18.3.8 · SDN Configuration Change and Rollback Audit
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Value:** Unauthorized fabric or policy changes can cause outages or security gaps. Auditing changes and rollbacks supports change control and incident analysis.
- **App/TA:** APIC/NSX/controller audit logs
- **Data Sources:** Configuration change events, user, object, before/after
- **SPL:**
```spl
index=sdn sourcetype="sdn:audit"
| search (action="modified" OR action="deleted" OR action="rollback")
| table _time, user, object_type, object_name, action, change_summary
| sort -_time
```
- **Implementation:** Ingest controller and fabric audit logs. Alert on change to critical objects (e.g., tenant, contract, segment) without change ticket. Report on change frequency and rollback rate. Integrate with change management.
- **Visualization:** Table (recent changes), Timeline (change events), Bar chart (changes by user).
- **CIM Models:** N/A

---

### UC-18.3.9 · VXLAN VTEP Reachability
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Availability, Fault
- **Value:** VTEP (VXLAN Tunnel Endpoint) peers form the overlay mesh in VXLAN fabrics. When a VTEP goes down, tenant segments lose connectivity and workloads become isolated. Monitoring VTEP reachability ensures overlay health and enables rapid detection of NVE failures before tenant impact.
- **App/TA:** SNMP modular input, NX-OS/EOS syslog
- **Data Sources:** `show nve peers` (NX-OS), `show vxlan vtep` (EOS), syslog VTEP events
- **SPL:**
```spl
index=network (sourcetype="cisco:nxos:nve_peers" OR sourcetype="arista:eos:vxlan_vtep" OR sourcetype="syslog")
| search (nve OR vtep OR "NVE peer" OR "VTEP")
| eval peer_status=case(
    like(_raw, "%Up%") OR like(_raw, "%up%") OR like(_raw, "%established%"), "Up",
    like(_raw, "%Down%") OR like(_raw, "%down%") OR like(_raw, "%failed%"), "Down",
    like(_raw, "%Init%") OR like(_raw, "%init%"), "Init",
    1==1, "Unknown")
| rex field=_raw "peer\s+(?<peer_ip>\d+\.\d+\.\d+\.\d+)|(?<peer_ip>\d+\.\d+\.\d+\.\d+)\s+.*?(?<state>\w+)"
| where peer_status!="Up" OR isnull(peer_ip)
| stats latest(peer_status) as status, latest(_time) as last_seen by host, peer_ip, vni
| table host, peer_ip, vni, status, last_seen
```
- **Implementation:** Run scripted input every 60 seconds to execute `show nve peers` (Cisco NX-OS) or `show vxlan vtep` (Arista EOS) via SSH/API. Parse peer IP, state, and VNI. Ingest syslog for VTEP state-change events (e.g., NVE peer down, BGP session lost). Create sourcetype with field extractions for peer_ip, state, vni, host. Alert immediately when any VTEP peer transitions to Down. Track peer flapping (rapid Up/Down cycles) for underlay stability issues. Correlate VTEP failures with BGP and physical link events.
- **Visualization:** Status grid (VTEP peer matrix by host), Table (down peers), Timechart (peer state changes), Single value (healthy VTEP peer count).
- **CIM Models:** N/A

---

### UC-18.3.10 · EVPN Route Type Distribution
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance, Capacity
- **Value:** EVPN route table growth (Type-2 MAC/IP and Type-5 IP prefix routes) impacts control-plane memory and convergence time. Trending route counts by type supports capacity planning, identifies runaway growth (e.g., VM sprawl, IP prefix leakage), and helps size fabric hardware for future scale.
- **App/TA:** Custom scripted input (`show bgp l2vpn evpn summary`)
- **Data Sources:** BGP EVPN route table counts per type
- **SPL:**
```spl
index=network sourcetype="evpn:route_summary"
| eval route_type=case(
    type=="2" OR type=="mac_ip", "Type2_MAC_IP",
    type=="3" OR type=="imcast", "Type3_IMET",
    type=="5" OR type=="ip_prefix", "Type5_IP_Prefix",
    1==1, "Other")
| timechart span=1h latest(count) as count by route_type
```
- **Implementation:** Deploy scripted input to run `show bgp l2vpn evpn summary` or equivalent (e.g., `show bgp evpn summary` on Arista) on each leaf every 5–15 minutes via SSH or eAPI. Parse route counts by type: Type-2 (MAC/IP), Type-3 (IMET), Type-5 (IP prefix). Ingest into Splunk with host, route_type, count, and timestamp. Baseline normal growth rates per VNI/tenant. Alert on sudden spikes (>20% in 1 hour) or sustained growth exceeding hardware limits. Report on top VNIs by route count for cleanup and capacity planning.
- **Visualization:** Timechart (route count by type over time), Table (current counts by host and type), Single value (total EVPN routes), Bar chart (route growth rate by type).
- **CIM Models:** N/A

### UC-18.3.11 · EVPN/VXLAN Tunnel Health

- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Unified view of BGP EVPN tunnel state and VXLAN encapsulation errors per VNI — bridges overlay protocols (complements UC-18.3.4 and UC-18.3.9).
- **App/TA:** NX-OS/EOS syslog, BGP telemetry
- **Equipment Models:** Cisco Nexus, Arista
- **Data Sources:** `evpn:bgp`, `vxlan:tunnel`
- **SPL:**
```spl
index=network (sourcetype="evpn:bgp" OR sourcetype="vxlan:tunnel") earliest=-24h
| eval bad=if(match(lower(state),"(?i)down|idle") OR error_count>0,1,0)
| where bad=1
| stats latest(state) as st, sum(error_count) as err by vni, peer_ip, leaf
| table leaf, peer_ip, vni, st, err
```
- **Implementation:** Normalize peer and VNI from vendor logs. Alert on any down EVPN session carrying VXLAN for production VNIs.
- **Visualization:** Table (unhealthy tunnels), Geo/leaf map, Line chart (error count).
- **CIM Models:** N/A

### UC-18.3.12 · SDN Controller High Availability

- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Availability
- **Value:** Quorum, leader election, and data-store sync for controller clusters — extends generic health (UC-18.3.3) with **HA-specific** failover signals.
- **App/TA:** `sdn:controller`, OpenDaylight, ONOS (custom)
- **Equipment Models:** SDN controller cluster
- **Data Sources:** `sdn:controller_ha`
- **SPL:**
```spl
index=sdn sourcetype="sdn:controller_ha" earliest=-24h
| where quorum_ok=0 OR leader_id!=expected_leader
| stats latest(quorum_ok) as q, latest(leader_id) as leader by cluster_name
| table cluster_name, q, leader
```
- **Implementation:** Map `expected_leader` from static config lookup. Alert on quorum loss or rogue leader.
- **Visualization:** Status grid (cluster), Timeline (failover events), Single value (cluster up).
- **CIM Models:** N/A

### UC-18.3.13 · Fabric Upgrade Compliance

- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Compliance
- **Value:** Tracks switch OS / ACI firmware versions against approved upgrade wave — identifies stragglers and unsupported trains.
- **App/TA:** Inventory scripted input, SNMP
- **Equipment Models:** Leaf/spine switches
- **Data Sources:** `network:inventory`
- **SPL:**
```spl
index=inventory sourcetype="network:inventory" role IN ("leaf","spine")
| lookup fabric_target_version.csv platform OUTPUT target_version
| where os_version!=target_version
| stats count by site, os_version, target_version
| sort -count
```
- **Implementation:** Refresh inventory daily. Drive remediation campaigns for nodes not on target.
- **Visualization:** Table (non-compliant nodes), Pie chart (compliance %), Bar chart (by site).
- **CIM Models:** N/A

### UC-18.3.14 · Spine-Leaf Topology Anomalies

- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** Detects unexpected BGP neighbor loss, missing spine links, or asymmetric ECMP paths in Clos topology.
- **App/TA:** BGP syslog, LLDP
- **Data Sources:** `bgp:neighbor`, `lldp:topology`
- **SPL:**
```spl
index=network sourcetype="bgp:neighbor" earliest=-4h
| where state!="Established"
| lookup expected_bgp_peers.csv local_host peer_ip OUTPUT 1 as expected
| where isnotnull(expected)
| stats count by local_host, peer_ip, state, reason
| sort -count
```
- **Implementation:** Maintain `expected_peers.csv` from design. Alert on any spine-leaf session not Established.
- **Visualization:** Graph (topology violations), Table (bad neighbors), Timeline.
- **CIM Models:** N/A

### UC-18.3.15 · BGP EVPN Route Table Convergence

- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance
- **Value:** Measures time-to-stable route count after churn events (link bounce, leaf reboot) — complements route count trending (UC-18.3.10).
- **App/TA:** BGP monitor, `evpn:route_summary`
- **Equipment Models:** EVPN/VXLAN leafs
- **Data Sources:** `evpn:route_summary`
- **SPL:**
```spl
index=network sourcetype="evpn:route_summary" earliest=-24h
| sort 0 host _time
| streamstats global=f last(total_routes) as prev_routes by host
| eval churn=abs(total_routes-prev_routes)
| where churn>500
| table _time, host, total_routes, prev_routes, churn
```
- **Implementation:** Simplify: alert on `total_routes` delta spikes; use scripted convergence test after maintenance. Tune thresholds to fabric size.
- **Visualization:** Line chart (total routes), Table (churn events), Bar chart (max churn by leaf).
- **CIM Models:** N/A

### UC-18.3.16 · VTEP Reachability and Loss

- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Packet loss and latency between VTEP peers — augments UC-18.3.9 state-only checks.
- **App/TA:** `Splunk_TA_nix`, ICMP probes, SNMP
- **Equipment Models:** VXLAN-capable switches
- **Data Sources:** `vtep:probe` or synthetic tests
- **SPL:**
```spl
index=network sourcetype="vtep:probe" earliest=-24h
| where loss_pct>2 OR latency_ms>10
| stats avg(loss_pct) as avg_loss, avg(latency_ms) as avg_lat by src_vtep, dst_vtep
| sort -avg_loss
| head 20
```
- **Implementation:** Run periodic probes between TEP IPs from automation. Correlate with underlay QoS drops.
- **Visualization:** Heatmap (VTEP × VTEP loss), Table (worst pairs), Line chart (loss trend).
- **CIM Models:** N/A

### UC-18.3.17 · Leaf Switch Resource Utilization

- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Capacity
- **Value:** CPU, memory, and forwarding table use on leaf switches — prevents control-plane overload and FIB exhaustion.
- **App/TA:** SNMP modular input, NX-API
- **Equipment Models:** Cisco/Arista leafs
- **Data Sources:** `snmp:cpu`, `snmp:mem`, `hw:forwarding`
- **SPL:**
```spl
index=snmp sourcetype="snmp:cpu" role="leaf" earliest=-1h
| eval use=cpu_pct
| append [ search index=snmp sourcetype="snmp:mem" role="leaf" earliest=-1h | eval use=mem_pct ]
| stats avg(use) as avg_use max(use) as peak by host
| where peak>85
| table host, avg_use, peak
```
- **Implementation:** Add FIB/ARP scale via `show forwarding` scripted input. Alert on sustained high CPU with EVPN churn.
- **Visualization:** Heatmap (leaf × metric), Table (top peaks), Line chart (utilization).
- **CIM Models:** N/A

---

