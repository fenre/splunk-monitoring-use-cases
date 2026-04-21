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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)
### UC-18.1.2 · Fault Trending by Severity

- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Wave:** 🐢 crawl
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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)
### UC-18.1.3 · Endpoint Mobility Tracking

- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Wave:** 🐢 crawl
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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)
### UC-18.1.4 · Contract/Filter Hit Analysis

- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Wave:** 🐢 crawl
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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)
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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)
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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)
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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)
### UC-18.1.8 · Spine-Leaf Fabric Latency

- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance
- **Value:** Inter-switch latency within the fabric directly impacts east-west traffic between workloads. High latency causes application timeouts, database replication lag, and degraded user experience. Monitoring fabric latency identifies congestion, misrouted traffic, and capacity bottlenecks before they impact SLAs.
- **App/TA:** Custom scripted input (ping, TWAMP, fabric analytics), `TA_cisco-ACI`, `arista:eos` via SC4S
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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)
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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)
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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)
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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)
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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)
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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)
### UC-18.1.14 · L3Out Prefix Monitoring

- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance
- **Value:** Monitors advertised/ learned prefixes on L3Outs (BGP/OSPF) for flapping, withdrawal storms, and unexpected route loss.
- **App/TA:** `TA_cisco-ACI`, APIC L3ExtInstP events, `TA-cisco_ios` (external routers)
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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)
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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)
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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)
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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)
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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)
### UC-18.1.19 · ACI Fault Domain Severity Rollup

- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault, Availability
- **Value:** Fault domains group infrastructure and policy failures by functional area (for example connectivity, configuration, or capacity). Rolling up open faults by domain shows where the fabric is structurally weak, helps prioritize remediation before east-west traffic degrades, and shortens war-room triage during incidents.
- **App/TA:** `TA_cisco-ACI`, Cisco DC Networking Application (Splunkbase 7777)
- **Equipment Models:** Cisco APIC, Nexus 9300/9500 (ACI mode)
- **Data Sources:** `index=cisco_aci` `sourcetype="cisco:aci:faults"` with fields `fault_domain`, `severity`, `code`, `dn`, `lc`
- **SPL:**
```spl
index=cisco_aci sourcetype="cisco:aci:faults" earliest=-24h
| where severity IN ("critical","major") AND (isnull(lc) OR NOT match(lower(lc),"(?i)resolved|cleared"))
| stats dc(dn) as affected_objects, values(code) as codes by fault_domain, severity
| sort fault_domain, -affected_objects
| table fault_domain, severity, affected_objects, codes
```
- **Implementation:** (1) Map `fault_domain` from APIC fault MO or TA extraction; if missing, derive from `dn` prefix via `rex`. (2) Schedule hourly and alert when any domain exceeds baseline affected object count. (3) Correlate spikes with change windows and interface faults (UC-18.1.6).
- **Visualization:** Stacked bar chart (faults by domain × severity), Table (top domains), Single value (open major+critical count).
- **CIM Models:** N/A

- **References:** [Cisco DC Networking Application](https://splunkbase.splunk.com/app/7777)

---

### UC-18.1.20 · Contract Violation and Implicit Deny Bursts

- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault, Security
- **Value:** Sudden increases in implicit denies or contract violations usually mean a mis-deployed contract, a missing EPG binding, or an attack probing disallowed paths. Catching bursts early prevents application outages and avoids silent security gaps where traffic is dropped without operator visibility.
- **App/TA:** `TA_cisco-ACI`, APIC syslog
- **Equipment Models:** Cisco APIC, ACI leaf switches
- **Data Sources:** `index=cisco_aci` `sourcetype="cisco:aci:contracts"` or `sourcetype="cisco:aci:syslog"` with fields `src_epg`, `dst_epg`, `contract_name`, `deny_count`, `implicit_deny_count`
- **SPL:**
```spl
index=cisco_aci (sourcetype="cisco:aci:contracts" OR sourcetype="cisco:aci:syslog") earliest=-4h
| bin _time span=5m
| eval denies=coalesce(deny_count, implicit_deny_count, 0)
| stats sum(denies) as deny_burst by _time, src_epg, dst_epg, contract_name
| eventstats median(deny_burst) as med by src_epg, dst_epg
| where deny_burst > med*10 AND deny_burst > 100
| sort -deny_burst
| table _time, src_epg, dst_epg, contract_name, deny_burst, med
```
- **Implementation:** (1) Normalize deny counters from contract stats or syslog patterns (`implicitDeny`, `vzBrCP`). (2) Tune multiplier and floor to fabric size. (3) Page on critical EPG pairs; attach last successful change ticket from audit (UC-18.1.5).
- **Visualization:** Timechart (deny burst timeline), Table (worst EPG pairs), Heatmap (src_epg × dst_epg).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-18.1.21 · EPG Endpoint Learning and Deletion Churn

- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance, Availability
- **Value:** Rapid endpoint learn/delete cycles on an EPG strain the control plane and can precede bridging or routing instability. Monitoring learning churn protects workload mobility designs and catches misconfigured duplicate IPs or spanning-tree interactions before they impact database and storage east-west paths.
- **App/TA:** `TA_cisco-ACI`, APIC event log
- **Equipment Models:** Cisco APIC, Nexus 9000 (ACI)
- **Data Sources:** `index=cisco_aci` `sourcetype="cisco:aci:endpoint"` with fields `action`, `tenant`, `epg`, `mac`, `ip`
- **SPL:**
```spl
index=cisco_aci sourcetype="cisco:aci:endpoint" earliest=-24h
| where action IN ("learn","delete","move")
| bin _time span=15m
| stats count as ops by _time, tenant, epg, action
| stats sum(eval(if(action=="learn",ops,0))) as learn_ops sum(eval(if(action=="delete",ops,0))) as del_ops max(_time) as last_window by tenant, epg
| where learn_ops>500 OR del_ops>500
| table tenant, epg, learn_ops, del_ops, last_window
| sort -learn_ops
```
- **Implementation:** (1) Ingest endpoint tracker events at least every poll interval of APIC TA. (2) Baseline per business EPG; exclude known vMotion pools via lookup. (3) Correlate with faults on the same `dn` and with L3Out prefix churn (UC-18.1.14).
- **Visualization:** Timechart (learn vs delete), Table (noisy EPGs), Single value (EPGs over threshold).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-18.1.22 · Fabric Port-Channel and Member Link Imbalance

- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance, Capacity
- **Value:** Uneven distribution across port-channel members defeats ECMP assumptions and can saturate individual uplinks while siblings stay idle. Detecting imbalance protects spine-leaf oversubscription models and avoids tail latency for storage and replication traffic.
- **App/TA:** `TA_cisco-ACI`, APIC interface statistics
- **Equipment Models:** Cisco Nexus 9300/9500 (ACI leaf/spine)
- **Data Sources:** `index=cisco_aci` `sourcetype="cisco:aci:interface_stats"` with fields `node`, `interface`, `port_channel`, `bytesRate`, `speed`
- **SPL:**
```spl
index=cisco_aci sourcetype="cisco:aci:interface_stats" earliest=-2h
| where isnotnull(port_channel)
| stats sum(bytesRate) as br by node, port_channel, interface
| eventstats sum(br) as pc_total by node, port_channel
| eval member_pct=round(100*br/pc_total,2)
| eventstats range(member_pct) as spread by node, port_channel
| where spread > 35
| table node, port_channel, interface, member_pct, spread
| sort node, port_channel, -member_pct
```
- **Implementation:** (1) Ensure `port_channel` is extracted from interface DN or API; map orphan physical members. (2) Alert when member spread exceeds policy (for example 35%). (3) Validate hashing and down-members with operational state feed.
- **Visualization:** Bar chart (member_pct by interface), Table (imbalanced PCs), Heatmap (node × port_channel).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-18.1.23 · APIC Controller Resource Exhaustion Watch

- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Availability, Capacity
- **Value:** APIC nodes host the policy repository and cluster services; disk, memory, or inode pressure delays policy pushes and can stall fault processing. Watching controller resources prevents brownouts where the fabric stays up but automation and incremental updates fail during change windows.
- **App/TA:** `TA_cisco-ACI`, APIC SNMP or API metrics scripted input
- **Equipment Models:** Cisco APIC M3/L3 cluster nodes
- **Data Sources:** `index=cisco_aci` `sourcetype="cisco:aci:apic_capacity"` with fields `apic_id`, `disk_used_pct`, `mem_used_pct`, `inode_used_pct`
- **SPL:**
```spl
index=cisco_aci sourcetype="cisco:aci:apic_capacity" earliest=-24h
| stats latest(disk_used_pct) as disk latest(mem_used_pct) as mem latest(inode_used_pct) as inode by apic_id
| where disk>85 OR mem>90 OR inode>85
| eval risk=case(inode>85,"Inode pressure", mem>90,"Memory pressure", disk>85,"Disk pressure",1==1,"OK")
| table apic_id, disk, mem, inode, risk
| sort -mem
```
- **Implementation:** (1) Poll `/api/node/mo/sys/summary` or vendor TA capacity fields every 5 minutes. (2) Alert at staged thresholds; include log partition growth rate. (3) Correlate with cluster replication lag (UC-18.1.18).
- **Visualization:** Gauge (per-APIC disk/mem), Table (nodes at risk), Timechart (capacity trends).
- **CIM Models:** N/A

- **References:** [Splunkbase app 6805](https://splunkbase.splunk.com/app/6805)

---

### 18.2 VMware NSX

**Splunk Add-on:** VMware NSX add-on (`vmware_nsx_addon`, Splunkbase 6805), syslog

### UC-18.2.1 · Distributed Firewall Rule Hits

- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Wave:** 🐢 crawl
- **Monitoring type:** Performance
- **Value:** NSX Distributed Firewall (DFW) runs on every hypervisor, providing east-west traffic control. Monitoring rule hits validates security policy effectiveness, identifies unused rules for cleanup, and detects policy violations in real time.
- **App/TA:** `vmware_nsx_addon`, NSX DFW syslog
- **Data Sources:** NSX DFW firewall logs (syslog), NSX Manager API
- **SPL:**
```spl
index=vmware sourcetype="vmware:nsx:dfw"
| stats sum(eval(if(action="ALLOW", 1, 0))) as allowed, sum(eval(if(action="DROP", 1, 0))) as dropped, sum(eval(if(action="REJECT", 1, 0))) as rejected by rule_id, rule_name, src, dst_ip, dst_port, protocol
| eval total=allowed+dropped+rejected
| sort -total
| table rule_id, rule_name, src, dst_ip, dst_port, protocol, allowed, dropped, rejected
```
- **Implementation:** Enable DFW logging on NSX Manager for desired rule sections. Forward DFW logs via syslog to Splunk. Parse rule ID, action, source, destination, and port fields. Identify rules with zero hits (candidates for removal). Alert on unexpected DENY hits indicating misconfiguration or attack.
- **Visualization:** Bar chart (top rules by hits), Timechart (allow vs deny trending), Table (denied connections), Sankey diagram (source-to-destination flows).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)
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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)
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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)
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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)
### UC-18.2.5 · Transport Node Connectivity

- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Wave:** 🐢 crawl
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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)
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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)
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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)
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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)
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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)
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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)
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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)
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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)
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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)
### UC-18.2.14 · NSX Intelligence Top Flows and Anomalous East-West Volume

- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance, Security
- **Value:** NSX Intelligence summarizes flow metadata across the overlay. Tracking dominant flows and sudden volume shifts highlights misconfigured services, lateral movement, or noisy neighbors before micro-segmentation rules are tuned, keeping data center east-west paths predictable for latency-sensitive tiers.
- **App/TA:** `vmware_nsx_addon`, NSX Intelligence HEC/syslog export
- **Equipment Models:** NSX-T Manager, NSX Intelligence appliance
- **Data Sources:** `index=vmware` `sourcetype="vmware:nsx:intelligence_flow"` with fields `src_vm`, `dst_vm`, `service_id`, `flow_bytes`, `domain_name`
- **SPL:**
```spl
index=vmware sourcetype="vmware:nsx:intelligence_flow" earliest=-24h
| stats sum(flow_bytes) as bytes dc(dst_vm) as dst_count by src_vm, service_id, domain_name
| eventstats perc95(bytes) as p95
| where bytes > p95*3
| eval mb=round(bytes/1048576,2)
| sort -bytes
| head 50
| table domain_name, src_vm, service_id, dst_count, mb
```
- **Implementation:** (1) Enable Intelligence flow export to Splunk HEC with CIM-friendly field names. (2) Baseline per domain; exclude backup VLANs via lookup. (3) Correlate spikes with DFW deny events (UC-18.2.1).
- **Visualization:** Table (top talkers), Sankey (src to service), Timechart (bytes per domain).
- **CIM Models:** Network_Traffic
- **CIM SPL:**
```spl
| tstats summariesonly=t count from datamodel=Network_Traffic.All_Traffic by All_Traffic.action, All_Traffic.src, All_Traffic.dest, All_Traffic.dest_port | sort - count
```

- **References:** [CIM: Network Traffic](https://docs.splunk.com/Documentation/CIM/latest/User/Network_Traffic)

---

### UC-18.2.15 · Distributed Firewall Rule Hit Counts by Application Tier

- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance, Compliance
- **Value:** Grouping DFW hits by application tier proves which segmentation boundaries are exercised in production and identifies stale allow rules that see no traffic. This reduces attack surface during audits and prevents accidental removal of rules that still protect critical tiers.
- **App/TA:** `vmware_nsx_addon`
- **Equipment Models:** NSX-T Data Center
- **Data Sources:** `index=vmware` `sourcetype="vmware:nsx:dfw"` with fields `rule_id`, `rule_name`, `action`, `src`, `tier`
- **SPL:**
```spl
index=vmware sourcetype="vmware:nsx:dfw" earliest=-7d
| lookup nsx_vm_tier.csv vm_name AS src OUTPUT tier AS src_tier
| stats count by src_tier, rule_id, rule_name, action
| eventstats sum(count) as tier_total by src_tier, action
| eval pct=round(100*count/tier_total,2)
| sort src_tier, -count
| table src_tier, rule_id, rule_name, action, count, pct
```
- **Implementation:** (1) Maintain `nsx_vm_tier.csv` mapping VM names to tier labels. (2) Refresh weekly from CMDB. (3) Alert when production tier shows zero hits on mandatory allow rules for seven days.
- **Visualization:** Heatmap (tier × rule hits), Bar chart (hits by tier), Table (zero-hit rules).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-18.2.16 · Edge Cluster BFD and Uplink Session Health

- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Availability, Fault
- **Value:** Tier-0 edge clusters depend on BFD and stable uplinks for fast failure detection. Degraded BFD or partial uplink loss causes asymmetric north-south paths and intermittent application reachability. Proactive monitoring supports failover drills and prevents surprise brownouts during ISP maintenance.
- **App/TA:** `vmware_nsx_addon`
- **Equipment Models:** NSX Edge cluster nodes (VM or bare metal)
- **Data Sources:** `index=vmware` `sourcetype="vmware:nsx:edge_bfd"` with fields `edge_node`, `cluster`, `peer_ip`, `bfd_state`, `uplink_name`, `message`
- **SPL:**
```spl
index=vmware sourcetype="vmware:nsx:edge_bfd" earliest=-4h
| where bfd_state!="UP" OR match(lower(coalesce(message,"")),"(?i)timeout|down")
| stats latest(bfd_state) as bfd latest(_time) as t by edge_node, cluster, peer_ip, uplink_name
| sort -t
| table edge_node, cluster, uplink_name, peer_ip, bfd, t
```
- **Implementation:** (1) Ingest BFD telemetry from NSX Manager API or Edge syslog. (2) Join with `vmware:nsx:edge_status` (UC-18.2.8) for BGP state. (3) Page on any BFD not UP on production T0 uplinks.
- **Visualization:** Status grid (edge × uplink), Timeline (BFD events), Table (non-UP sessions).
- **CIM Models:** Network_Traffic
- **CIM SPL:**
```spl
| tstats summariesonly=t count from datamodel=Network_Traffic.All_Traffic by All_Traffic.action, All_Traffic.src, All_Traffic.dest, All_Traffic.dest_port | sort - count
```

- **References:** [CIM: Network Traffic](https://docs.splunk.com/Documentation/CIM/latest/User/Network_Traffic)

---

### UC-18.2.17 · Transport Node Data Plane Interface Errors and Drops

- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault, Performance
- **Value:** Overlay GENEVE depends on clean physical NICs and switch ports. Rising errors or drops on TN N-VDS or VDS uplinks manifest as intermittent VM connectivity and false-positive firewall symptoms. Isolating TN-level drops speeds root cause between server, rack, and fabric teams.
- **App/TA:** `vmware_nsx_addon`, vSphere metrics optional
- **Equipment Models:** ESXi transport nodes
- **Data Sources:** `index=vmware` `sourcetype="vmware:nsx:tn_iface"` with fields `transport_node`, `pnic`, `rx_errors`, `tx_errors`, `rx_drops`, `tx_drops`
- **SPL:**
```spl
index=vmware sourcetype="vmware:nsx:tn_iface" earliest=-24h
| eval bad=rx_errors+tx_errors+rx_drops+tx_drops
| stats sum(bad) as issues max(rx_errors) as max_rx max(tx_errors) as max_tx by transport_node, pnic
| where issues > 100 OR max_rx>0 OR max_tx>0
| sort -issues
| table transport_node, pnic, issues, max_rx, max_tx
```
- **Implementation:** (1) Collect per-pnic counters via NSX API on 60s interval. (2) Baseline known noisy lab hosts. (3) Correlate with overlay loss diagnostics (UC-18.2.9).
- **Visualization:** Bar chart (issues by TN), Table (worst pnics), Single value (TNs with errors).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-18.2.18 · NSX Intelligence Recommended Firewall Rule Publish Queue

- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Compliance, Availability
- **Value:** NSX Intelligence proposes micro-segmentation rules; a backed-up or failed publish queue delays enforcement of least-privilege changes and leaves temporary broad access in place. Monitoring queue depth ties security posture to operational SLAs for the data center network.
- **App/TA:** `vmware_nsx_addon`, NSX Intelligence API
- **Equipment Models:** NSX Intelligence Node
- **Data Sources:** `index=vmware` `sourcetype="vmware:nsx:intel_publish"` with fields `domain_name`, `queue_depth`, `last_error`, `status`
- **SPL:**
```spl
index=vmware sourcetype="vmware:nsx:intel_publish" earliest=-24h
| stats latest(queue_depth) as depth latest(status) as st latest(last_error) as err by domain_name
| where depth>25 OR match(lower(st),"(?i)fail|error") OR (isnotnull(err) AND err!="" AND err!="null")
| table domain_name, depth, st, err
| sort -depth
```
- **Implementation:** (1) Scripted input for Intelligence recommendation publish API. (2) Alert when depth exceeds agreed SLA or status non-success. (3) Link failures to NSX Manager cluster health (UC-18.2.13).
- **Visualization:** Single value (max queue depth), Table (failed domains), Timechart (depth trend).
- **CIM Models:** Change
- **CIM SPL:**
```spl
| tstats summariesonly=t latest(All_Changes.status) as agg_value from datamodel=Change.All_Changes by All_Changes.action, All_Changes.object_category, All_Changes.user | sort - agg_value
```

- **References:** [CIM: Change](https://docs.splunk.com/Documentation/CIM/latest/User/Change)

---

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)
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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)
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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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
| bin _time span=5m
| stats count by vni, host, _time
| where count > 100
| sort -count
```
- **Implementation:** Ingest EVPN route and mobility events. Alert on route storm or high mobility count in short window. Report on top movers and VNIs with most churn. Use for capacity and placement planning.
- **Visualization:** Line chart (mobility events over time), Table (top VNIs by churn), Bar chart (mobility by host).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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
| bin _time span=1h
| stats sum(packets) as denied by contract_name, src_epg, dest_epg, _time
| where denied > 1000
| sort -denied
```
- **Implementation:** Ingest ACI contract statistics. Track deny and drop by contract and EPG pair. Alert on spike in denies. Report on top denied flows for policy review. Correlate with app and security events.
- **Visualization:** Table (denied flows), Bar chart (denies by contract), Line chart (deny trend).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)
### UC-18.3.11 · EVPN/VXLAN Tunnel Health

- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Unified view of BGP EVPN tunnel state and VXLAN encapsulation errors per VNI — bridges overlay protocols (complements UC-18.3.4 and UC-18.3.9).
- **App/TA:** `TA-cisco_ios` (NX-OS), `arista:eos` via SC4S, BGP telemetry
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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)
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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)
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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)
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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)
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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)
### UC-18.3.16 · VTEP Reachability and Loss

- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Packet loss and latency between VTEP peers — augments UC-18.3.9 state-only checks.
- **App/TA:** `Splunk_TA_nix`, `TA-cisco_ios`, `arista:eos` via SC4S, ICMP probes, SNMP
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

- **References:** [Splunk_TA_nix](https://splunkbase.splunk.com/app/833)
### UC-18.3.17 · Leaf Switch Resource Utilization

- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Capacity
- **Value:** CPU, memory, and forwarding table use on leaf switches — prevents control-plane overload and FIB exhaustion.
- **App/TA:** SNMP modular input, NX-API, `TA-cisco_ios`, `arista:eos` via SC4S
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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-18.3.18 · BGP EVPN Route Withdrawal Rate and Flap Storms

- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Fault, Performance
- **Value:** Withdrawal storms shrink effective ECMP sets and extend convergence after link or node events, which shows up as application timeouts and storage path loss. Measuring withdrawal velocity per peer differentiates normal housekeeping from dangerous churn in the EVPN control plane.
- **App/TA:** Custom BGP monitor, `TA-cisco_ios`, Arista eAPI scripted input
- **Equipment Models:** BGP EVPN-capable leaf and spine switches
- **Data Sources:** `index=network` `sourcetype="bgp:evpn_events"` with fields `host`, `peer_ip`, `event_type`, `rd`, `prefix`
- **SPL:**
```spl
index=network sourcetype="bgp:evpn_events" earliest=-1h
| where match(lower(event_type),"(?i)withdraw|wdr|revoke")
| bin _time span=1m
| stats count as wdr by _time, host, peer_ip
| where wdr > 200
| sort -wdr
| table _time, host, peer_ip, wdr
```
- **Implementation:** (1) Stream BGP UPDATE syslog or BMP into `bgp:evpn_events` with normalized `event_type`. (2) Tune per-fabric scale; exclude RR-only peers if needed. (3) Correlate with spine-leaf neighbor state (UC-18.3.14).
- **Visualization:** Timechart (withdrawals per minute), Table (worst peers), Single value (peak wdr).
- **CIM Models:** Network_Traffic
- **CIM SPL:**
```spl
| tstats summariesonly=t count from datamodel=Network_Traffic.All_Traffic by All_Traffic.dest span=1m | sort - count
```

- **References:** [CIM: Network Traffic](https://docs.splunk.com/Documentation/CIM/latest/User/Network_Traffic)

---

### UC-18.3.19 · Spine-Leaf ECMP Member Utilization Balance

- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance, Capacity
- **Value:** ECMP assumes balanced hashing across parallel paths; persistent skew overloads individual spine uplinks while others remain idle. Monitoring member utilization protects oversubscribed Clos designs and avoids silent drops when one path saturates during backup or replication waves.
- **App/TA:** gNMI/Telegraf, SNMP TA
- **Equipment Models:** Cisco Nexus, Arista 7050/7280 spine-leaf
- **Data Sources:** `index=network` `sourcetype="fabric:ecmp_member"` with fields `leaf`, `spine_peer`, `member_if`, `out_bits_per_sec`
- **SPL:**
```spl
index=network sourcetype="fabric:ecmp_member" earliest=-30m
| stats avg(out_bits_per_sec) as avg_bps by leaf, spine_peer, member_if
| eventstats sum(avg_bps) as leaf_total by leaf, spine_peer
| eventstats dc(member_if) as paths by leaf, spine_peer
| eval expected_share=if(paths>0,100/paths,0)
| eval share_pct=round(100*avg_bps/leaf_total,2)
| eval skew=abs(share_pct-expected_share)
| where skew > 20 AND leaf_total > 1000000000
| table leaf, spine_peer, member_if, share_pct, expected_share, skew
| sort -skew
```
- **Implementation:** (1) Ingest per-member interface counters from telemetry at 30–60s. (2) Alert on sustained skew; verify hashing seeds and broken members. (3) Compare with interface errors on hot members.
- **Visualization:** Heatmap (member_if × leaf skew), Bar chart (skew by spine), Table (outliers).
- **CIM Models:** Network_Traffic
- **CIM SPL:**
```spl
| tstats summariesonly=t count from datamodel=Network_Traffic.All_Traffic by All_Traffic.action, All_Traffic.src, All_Traffic.dest, All_Traffic.dest_port | sort - count
```

- **References:** [CIM: Network Traffic](https://docs.splunk.com/Documentation/CIM/latest/User/Network_Traffic)

---

### UC-18.3.20 · Fabric Host Route and ARP Scale Headroom

- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Capacity, Availability
- **Value:** EVPN Type-2 host routes and ARP scale drive TCAM and forwarding table use on leafs. Running out of headroom stalls new workload placement and causes black-holed traffic during scale-out events. Trending utilization against hardware limits informs purchase timing and route summarization design.
- **App/TA:** NX-API/CLI scripted input, SNMP
- **Equipment Models:** VXLAN EVPN leaf switches
- **Data Sources:** `index=network` `sourcetype="fabric:route_scale"` with fields `host`, `host_routes`, `host_route_limit`, `arp_entries`, `arp_limit`
- **SPL:**
```spl
index=network sourcetype="fabric:route_scale" earliest=-24h
| eval host_pct=round(100*host_routes/host_route_limit,2)
| eval arp_pct=round(100*arp_entries/arp_limit,2)
| where host_pct>80 OR arp_pct>80
| stats latest(host_pct) as host_pct latest(arp_pct) as arp_pct latest(host_routes) as hr latest(arp_entries) as arp by host
| table host, host_pct, arp_pct, hr, arp
| sort -host_pct
```
- **Implementation:** (1) Poll `show system internal forwarding resource` or vendor equivalents nightly plus hourly if above 75%. (2) Map limits per platform SKU via lookup. (3) Join with EVPN route summary growth (UC-18.3.10).
- **Visualization:** Gauge (headroom %), Table (critical leafs), Timechart (host route growth).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-18.3.21 · EVPN Ethernet Segment (ESI) DF Election and BUM Stability

- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Fault, Availability
- **Value:** All-active multihoming depends on correct designated forwarder election and stable per-ESI state. DF flaps or split-brain indicators disrupt BUM handling and can isolate VLANs for dual-homed hosts. Early detection protects clustered databases and hypervisor trunks.
- **App/TA:** NX-OS/EOS syslog, custom `evpn:esi` parser
- **Equipment Models:** MLAG/EVPN multihomed leaf pairs
- **Data Sources:** `index=network` `sourcetype="evpn:esi"` with fields `leaf`, `esi`, `event`, `vlan`
- **SPL:**
```spl
index=network sourcetype="evpn:esi" earliest=-24h
| where match(lower(event),"(?i)df|designated|esi|split|conflict")
| stats count by leaf, esi, event
| where count>5
| sort -count
| table leaf, esi, event, count
```
- **Implementation:** (1) Normalize DF change syslog into `evpn:esi`. (2) Alert on rapid DF changes per ESI within one hour. (3) Correlate with port-channel member events (UC-18.3.14).
- **Visualization:** Timeline (DF changes), Table (noisy ESIs), Single value (ESIs with recent DF churn).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-18.3.22 · VXLAN Underlay Path MTU and DF Bit Fragmentation Risk

- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance, Fault
- **Value:** VXLAN adds overhead; MTU mismatches or PMTUD black holes cause silent throughput collapse and TCP retransmits on east-west paths. Tracking DF-bit probes and ICMP unreachables across the underlay separates fabric issues from guest OS misconfiguration before tickets flood application teams.
- **App/TA:** `TA-cisco_ios`, `arista:eos` via SC4S, ICMP probe scripted input
- **Equipment Models:** Spine-leaf underlay routers
- **Data Sources:** `index=network` `sourcetype="fabric:mtu_diag"` with fields `src_leaf`, `dst_leaf`, `max_mtu_ok`, `icmp_needfrag`, `test_size`
- **SPL:**
```spl
index=network sourcetype="fabric:mtu_diag" earliest=-24h
| where max_mtu_ok=0 OR icmp_needfrag>0
| stats sum(icmp_needfrag) as needfrag max(test_size) as last_size by src_leaf, dst_leaf
| sort -needfrag
| table src_leaf, dst_leaf, needfrag, last_size
```
- **Implementation:** (1) Run scheduled jumbo ping/UDP probes between loopbacks with DF set. (2) Ingest syslog `ICMP unreachable` / `MTU` messages. (3) Document expected MTU (for example 9216) per site and alert on regression.
- **Visualization:** Table (bad pairs), Diagram (site × path status), Single value (paths failing MTU).
- **CIM Models:** Network_Traffic
- **CIM SPL:**
```spl
| tstats summariesonly=t count from datamodel=Network_Traffic.All_Traffic by All_Traffic.action, All_Traffic.src, All_Traffic.dest, All_Traffic.dest_port | sort - count
```

- **References:** [Cisco DC Networking Application for Splunk](https://splunkbase.splunk.com/app/7777), [CIM: Network Traffic](https://docs.splunk.com/Documentation/CIM/latest/User/Network_Traffic)

---

### 18.4 Cisco Nexus Dashboard & NX-OS Fabric

> **Note:** Nexus Dashboard, NDFC, and NDO sourcetypes vary by add-on version and deployment method. The sourcetypes shown below (e.g. `cisco:nexusdashboard:*`, `cisco:ndfc:*`, `cisco:ndo:*`) are representative examples — verify against your installed Cisco DC Networking add-on's `props.conf`.

**Splunk Add-on:** Cisco DC Networking Application for Splunk (Splunkbase 7777), NX-OS syslog (`cisco:nexus`), gNMI/streaming telemetry via Telegraf, SNMP TA

### UC-18.4.1 · Nexus Dashboard Insights Anomaly Monitoring

- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault, Availability
- **Value:** Nexus Dashboard Insights (NDI) uses ML-driven baselining to detect anomalies across hardware, capacity, compliance, connectivity, and configuration. Forwarding these anomalies to Splunk enables correlation with application and security events that NDI cannot see, and provides long-term trending beyond NDI retention.
- **App/TA:** Cisco DC Networking Application (Splunkbase 7777), NDI webhook / syslog export
- **Equipment Models:** Nexus Dashboard, Nexus 9300, Nexus 9500, APIC (ACI mode)
- **Data Sources:** NDI anomaly exports (webhook/syslog), `cisco:ndi:anomaly`
- **SPL:**
```spl
index=cisco_dc sourcetype="cisco:ndi:anomaly" earliest=-24h
| stats count by severity, category, anomaly_type, fabric_name
| where severity IN ("critical","major")
| sort -count
```
- **Implementation:** Configure NDI to export anomalies via webhook to a Splunk HEC endpoint, or forward syslog. Map severity and category fields. Alert on critical/major anomalies. Use NDI anomaly correlation data to distinguish root causes from symptoms.
- **Visualization:** Table (anomalies by category), Bar chart (anomaly count by severity), Timeline (anomaly events), Single value (open criticals).
- **CIM Models:** Alerts
- **CIM SPL:**
```spl
| tstats summariesonly=t count from datamodel=Alerts.Alerts by Alerts.severity | sort - count
```

- **References:** [Cisco DC Networking Application](https://splunkbase.splunk.com/app/7777), [CIM: Alerts](https://docs.splunk.com/Documentation/CIM/latest/User/Alerts)

---

### UC-18.4.2 · NDFC Fabric Compliance and Configuration Drift

- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Value:** NDFC enforces intended configuration via templates. Detecting drift between running config and intended config across the fabric prevents misconfigurations that cause outages, security gaps, or inconsistent policy enforcement.
- **App/TA:** Cisco DC Networking Application (Splunkbase 7777), NDFC REST API scripted input
- **Equipment Models:** Nexus Dashboard Fabric Controller, Nexus 9300, Nexus 9500, Nexus 3000
- **Data Sources:** NDFC compliance reports (REST API), `cisco:ndfc:compliance`
- **SPL:**
```spl
index=cisco_dc sourcetype="cisco:ndfc:compliance"
| stats count by switch_name, compliance_status, drift_category
| where compliance_status!="In-Sync"
| table switch_name, compliance_status, drift_category, count
| sort -count
```
- **Implementation:** Poll NDFC compliance status via REST API daily or after change windows. Alert on Out-of-Sync devices. Track drift trends over time to identify switches that repeatedly drift. Trigger auto-remediation workflows when safe.
- **Visualization:** Table (non-compliant switches), Pie chart (compliant vs drifted), Trend chart (drift count over time).
- **CIM Models:** Change
- **CIM SPL:**
```spl
| tstats summariesonly=t count from datamodel=Change.All_Changes by All_Changes.action, All_Changes.object_category, All_Changes.user | sort - count
```

- **References:** [Cisco DC Networking Application](https://splunkbase.splunk.com/app/7777), [CIM: Change](https://docs.splunk.com/Documentation/CIM/latest/User/Change)

---

### UC-18.4.3 · Nexus Dashboard Advisory and Field Notice Alerts

- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Compliance, Risk
- **Value:** Nexus Dashboard Insights identifies field notices, PSIRTs, and hardware advisories that affect switches in the fabric by matching device serial numbers and software versions. Forwarding these to Splunk provides a centralised risk view alongside other infrastructure advisories.
- **App/TA:** Cisco DC Networking Application (Splunkbase 7777), NDI webhook
- **Equipment Models:** Nexus Dashboard, all managed Nexus switches
- **Data Sources:** NDI advisory exports, `cisco:ndi:advisory`
- **SPL:**
```spl
index=cisco_dc sourcetype="cisco:ndi:advisory"
| stats count by advisory_id, advisory_type, severity, affected_switch_count
| where severity IN ("critical","high")
| table advisory_id, advisory_type, severity, affected_switch_count
| sort -severity
```
- **Implementation:** Export NDI advisories to Splunk via webhook or scheduled API poll. Correlate with asset inventory to calculate exposure percentage. Alert on critical PSIRTs or field notices affecting production fabrics.
- **Visualization:** Table (active advisories), Single value (critical advisories), Bar chart (affected switches per advisory).
- **CIM Models:** Alerts
- **CIM SPL:**
```spl
| tstats summariesonly=t count from datamodel=Alerts.Alerts by Alerts.severity | sort - count
```

- **References:** [Cisco DC Networking Application](https://splunkbase.splunk.com/app/7777), [CIM: Alerts](https://docs.splunk.com/Documentation/CIM/latest/User/Alerts)

---

### UC-18.4.4 · Nexus 9000 NX-OS Streaming Telemetry Health

- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Availability, Performance
- **Value:** Streaming telemetry (gNMI/gRPC) from Nexus 9000 provides sub-second interface, routing, and system metrics. Monitoring the telemetry pipeline itself ensures data collection gaps are detected before they blind monitoring dashboards.
- **App/TA:** Telegraf (gNMI plugin), Splunk HEC, SNMP TA (fallback)
- **Equipment Models:** Cisco Nexus 9300, Nexus 9500, Nexus 3000 (NX-OS 9.3+)
- **Data Sources:** Telegraf internal metrics, gNMI subscription status
- **SPL:**
```spl
index=telegraf sourcetype="telegraf:internal" measurement="internal_gather"
| stats avg(gather_time_ns) as avg_gather_ns max(gather_time_ns) as max_gather_ns count as samples by host, input
| where input="cisco_telemetry_gnmi"
| eval avg_gather_ms=round(avg_gather_ns/1000000,1)
| where avg_gather_ms > 5000 OR samples < expected_samples
| table host, input, avg_gather_ms, max_gather_ns, samples
```
- **Implementation:** Deploy Telegraf with gNMI input plugin on collector hosts. Configure NX-OS sensor groups for interface, BGP, system, and environment paths. Monitor Telegraf internal metrics for collection health. Alert on stale data or excessive gather times.
- **Visualization:** Table (collector health), Line chart (gather time), Single value (active subscriptions).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-18.4.5 · NX-OS VXLAN EVPN Fabric Underlay BGP Health

- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** The VXLAN EVPN fabric relies on BGP for both underlay (iBGP/OSPF) and overlay (BGP EVPN address family) connectivity. BGP peer flaps or stuck sessions in the underlay break VTEP reachability and cause tenant network outages. Monitoring BGP state across all spines and leafs is foundational.
- **App/TA:** NX-OS syslog (`cisco:nexus`), gNMI telemetry, SNMP TA
- **Equipment Models:** Cisco Nexus 9300, Nexus 9500, Nexus 3000 (VXLAN EVPN fabrics)
- **Data Sources:** NX-OS syslog (BGP-5, BGP-3 messages), gNMI BGP sensor path, SNMP BGP4-MIB
- **SPL:**
```spl
index=network sourcetype="cisco:nexus" "BGP-5-ADJCHANGE" OR "BGP-3-NOTIFICATION"
| rex "neighbor (?<peer_ip>\S+).*(?<state>Up|Down|Established|Idle)"
| stats count latest(state) as current_state by host, peer_ip
| where current_state!="Established"
| table host, peer_ip, current_state, count
| sort -count
```
- **Implementation:** Forward NX-OS syslog to Splunk (facility BGP). Optionally stream BGP state via gNMI for sub-second detection. Alert on any peer leaving Established state. Correlate with interface flaps (UC-18.3.14) and VTEP reachability (UC-18.3.9).
- **Visualization:** Status grid (peer status matrix), Table (non-established peers), Timeline (flap events).
- **CIM Models:** Network_Traffic
- **CIM SPL:**
```spl
| tstats summariesonly=t count from datamodel=Network_Traffic.All_Traffic by All_Traffic.dest | sort - count
```

- **References:** [CIM: Network Traffic](https://docs.splunk.com/Documentation/CIM/latest/User/Network_Traffic)

---

### UC-18.4.6 · NX-OS Control Plane Policing (CoPP) Drops

- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security, Availability
- **Value:** CoPP protects the switch CPU from being overwhelmed by excessive control-plane traffic (ARP storms, BGP attacks, ICMP floods). Monitoring CoPP drop counters detects both legitimate overload and potential DoS attacks targeting the management or routing plane.
- **App/TA:** NX-OS syslog (`cisco:nexus`), SNMP TA, gNMI telemetry
- **Equipment Models:** Cisco Nexus 9300, Nexus 9500, Nexus 3000
- **Data Sources:** NX-OS CoPP counters (`show policy-map interface control-plane`), syslog, gNMI
- **SPL:**
```spl
index=network sourcetype="cisco:nexus:copp" OR (sourcetype="cisco:nexus" "COPP" "DROP")
| stats sum(dropped_packets) as drops sum(conform_packets) as conforms by host, class_name
| eval drop_pct=round(drops/(drops+conforms)*100,2)
| where drops > 1000 OR drop_pct > 5
| table host, class_name, drops, conforms, drop_pct
| sort -drops
```
- **Implementation:** Poll CoPP counters via scripted input or gNMI every 60 seconds. Baseline normal drop rates per class. Alert on sustained drops exceeding baseline, particularly for BGP, OSPF, and management classes. Investigate as potential security events.
- **Visualization:** Table (CoPP classes with drops), Bar chart (drops by class), Line chart (drop rate trending).
- **CIM Models:** Intrusion_Detection
- **CIM SPL:**
```spl
| tstats summariesonly=t count from datamodel=Intrusion_Detection.IDS_Attacks by IDS_Attacks.dest | sort - count
```

- **References:** [CIM: Intrusion Detection](https://docs.splunk.com/Documentation/CIM/latest/User/Intrusion_Detection)

---

### UC-18.4.7 · Nexus Dashboard Orchestrator Cross-Fabric Consistency

- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Compliance, Availability
- **Value:** Nexus Dashboard Orchestrator (NDO, formerly MSO) manages policies across multiple ACI fabrics or NDFC-managed NX-OS fabrics. Configuration inconsistencies between sites cause asymmetric routing, broken inter-site connectivity, and policy enforcement gaps.
- **App/TA:** Cisco DC Networking Application (Splunkbase 7777), NDO REST API scripted input
- **Equipment Models:** Nexus Dashboard Orchestrator, multi-site ACI or NDFC fabrics
- **Data Sources:** NDO audit logs, schema/template deployment status, `cisco:ndo:audit`
- **SPL:**
```spl
index=cisco_dc sourcetype="cisco:ndo:audit" earliest=-24h
| stats count by action, template_name, site_name, status, user
| where status!="deployed" OR action IN ("failed","conflict")
| table template_name, site_name, action, status, user, count
| sort -count
```
- **Implementation:** Poll NDO deployment status via REST API. Detect schema deployment failures and pending diffs between sites. Alert on any site showing stale or failed deployment. Cross-reference with ACI multisite health (UC-18.1.17).
- **Visualization:** Table (deployment status per site/template), Status grid (site consistency), Timeline (deployment events).
- **CIM Models:** Change
- **CIM SPL:**
```spl
| tstats summariesonly=t count from datamodel=Change.All_Changes by All_Changes.action, All_Changes.status, All_Changes.user | sort - count
```

- **References:** [Cisco DC Networking Application](https://splunkbase.splunk.com/app/7777), [CIM: Change](https://docs.splunk.com/Documentation/CIM/latest/User/Change)

---

### UC-18.4.8 · NDFC Switch Inventory and Lifecycle Status

- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Inventory, Compliance
- **Value:** Maintaining an accurate, up-to-date inventory of all switches managed by NDFC, including model, serial, software version, and end-of-life/end-of-support dates, supports procurement planning, compliance audits, and vulnerability management.
- **App/TA:** Cisco DC Networking Application (Splunkbase 7777), NDFC REST API scripted input
- **Equipment Models:** All NDFC-managed switches (Nexus 9300, 9500, 3000, 7000)
- **Data Sources:** NDFC switch inventory API, `cisco:ndfc:inventory`
- **SPL:**
```spl
index=cisco_dc sourcetype="cisco:ndfc:inventory"
| stats latest(software_version) as sw_ver latest(serial_number) as serial latest(model) as model by switch_name, fabric_name
| lookup cisco_eos_dates model OUTPUT eos_date, eol_date
| eval days_to_eos=round((strptime(eos_date,"%Y-%m-%d")-now())/86400)
| where days_to_eos < 365 OR isnull(days_to_eos)
| table switch_name, fabric_name, model, serial, sw_ver, eos_date, days_to_eos
| sort days_to_eos
```
- **Implementation:** Poll NDFC inventory weekly. Maintain a lookup of Cisco EoS/EoL dates. Alert at 12, 6, and 3 month thresholds. Generate quarterly lifecycle reports for procurement.
- **Visualization:** Table (switches approaching EoS), Pie chart (lifecycle status distribution), Single value (switches past EoS).
- **CIM Models:** N/A

- **References:** [Cisco DC Networking Application](https://splunkbase.splunk.com/app/7777)
### UC-18.4.9 · Nexus Dashboard Site and Fabric Assurance Health Score

- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability, Compliance
- **Value:** Site-level assurance scores roll up connectivity, best-practice violations, and capacity risk across all managed switches. Surfacing declining scores in Splunk gives data center operators a single trend line to prioritize remediation before Insights opens critical anomalies during business peaks.
- **App/TA:** Cisco DC Networking Application (Splunkbase 7777), Nexus Dashboard REST export
- **Equipment Models:** Nexus Dashboard, NDFC-managed fabrics
- **Data Sources:** `index=cisco_dc` `sourcetype="cisco:nd:site_health"` with fields `site_name`, `fabric_name`, `assurance_score`, `risk_level`, `open_findings`
- **SPL:**
```spl
index=cisco_dc sourcetype="cisco:nd:site_health" earliest=-24h
| stats latest(assurance_score) as score latest(risk_level) as risk latest(open_findings) as findings by site_name, fabric_name
| where score < 85 OR match(lower(risk),"(?i)high|critical")
| sort score
| table site_name, fabric_name, score, risk, findings
```
- **Implementation:** (1) Schedule API pull from Nexus Dashboard Assurance or ingest pre-aggregated JSON via HEC. (2) Map score scale to your SLA colors. (3) Correlate drops with NDI anomalies (UC-18.4.1) and compliance drift (UC-18.4.2).
- **Visualization:** Single value (worst site score), Bar chart (score by fabric), Table (sites below threshold).
- **CIM Models:** Alerts
- **CIM SPL:**
```spl
| tstats summariesonly=t count from datamodel=Alerts.Alerts by Alerts.severity, Alerts.signature, Alerts.app | sort - count
```

- **References:** [Cisco DC Networking Application](https://splunkbase.splunk.com/app/7777), [CIM: Alerts](https://docs.splunk.com/Documentation/CIM/latest/User/Alerts)

---

### UC-18.4.10 · Golden Firmware Image Compliance Across NDFC Fabrics

- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Compliance, Risk
- **Value:** Running multiple NX-OS trains in one fabric increases interoperability defects during upgrades. Comparing live images to the approved golden list per platform reduces unplanned reload risk and speeds security patch campaigns for the physical data center network.
- **App/TA:** Cisco DC Networking Application (Splunkbase 7777), `cisco:ndfc:inventory`
- **Equipment Models:** NDFC-managed Nexus 9000/3000
- **Data Sources:** `index=cisco_dc` `sourcetype="cisco:ndfc:inventory"` with fields `switch_name`, `fabric_name`, `model`, `software_version`
- **SPL:**
```spl
index=cisco_dc sourcetype="cisco:ndfc:inventory" earliest=-24h
| lookup ndfc_golden_image.csv model OUTPUT golden_version
| where isnotnull(golden_version) AND software_version!=golden_version
| stats values(software_version) as running_versions values(golden_version) as golden_versions count by fabric_name, model
| sort -count
| table fabric_name, model, running_versions, golden_versions, count
```
- **Implementation:** (1) Maintain `ndfc_golden_image.csv` with CAB-approved NX-OS per SKU. (2) Nightly diff from inventory API. (3) Drive remediation tickets with risk tier from PSIRT correlation (UC-18.4.3).
- **Visualization:** Pie chart (compliant vs drift), Table (non-compliant switches), Bar chart (count by fabric).
- **CIM Models:** Change
- **CIM SPL:**
```spl
| tstats summariesonly=t count from datamodel=Change.All_Changes by All_Changes.action, All_Changes.object_category, All_Changes.user | sort - count
```

- **References:** [Cisco DC Networking Application](https://splunkbase.splunk.com/app/7777), [CIM: Change](https://docs.splunk.com/Documentation/CIM/latest/User/Change)

---

### UC-18.4.11 · NDFC Flow Telemetry Drop and Export Health

- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance, Availability
- **Value:** Flow telemetry underpins capacity and security analytics for the NX-OS fabric. Collector drops or stalled exports create blind spots where congestion and microbursts go unseen until applications complain. Monitoring pipeline health preserves trust in east-west utilization dashboards.
- **App/TA:** Cisco DC Networking Application (Splunkbase 7777), NetFlow/IPFIX collector syslog
- **Equipment Models:** Nexus 9300/9500 with flow telemetry enabled
- **Data Sources:** `index=cisco_dc` `sourcetype="cisco:ndfc:flow_export"` with fields `switch_name`, `export_profile`, `dropped_flows`, `export_rate_eps`, `collector_ip`
- **SPL:**
```spl
index=cisco_dc sourcetype="cisco:ndfc:flow_export" earliest=-4h
| stats sum(dropped_flows) as drops avg(export_rate_eps) as eps by switch_name, collector_ip
| where drops>0 OR eps < 100
| sort -drops
| table switch_name, collector_ip, drops, eps
```
- **Implementation:** (1) Ingest NDFC telemetry health API or collector events with per-switch counters. (2) Baseline `eps` per site. (3) Alert on drops or sustained low export rate; verify CPU and sampler intervals on switches.
- **Visualization:** Timechart (export rate), Table (switches with drops), Single value (total dropped flows).
- **CIM Models:** Network_Traffic
- **CIM SPL:**
```spl
| tstats summariesonly=t avg(All_Traffic.bytes_in) as agg_value from datamodel=Network_Traffic.All_Traffic by All_Traffic.action, All_Traffic.src, All_Traffic.dest, All_Traffic.dest_port | sort - agg_value
```

- **References:** [Cisco DC Networking Application](https://splunkbase.splunk.com/app/7777), [CIM: Network Traffic](https://docs.splunk.com/Documentation/CIM/latest/User/Network_Traffic)

---

### UC-18.4.12 · Nexus Dashboard Insights Alert Noise and Category Mix

- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault, Compliance
- **Value:** Insights can generate bursts of correlated alerts after a single root cause. Tracking alert volume by category separates chronic noise from emerging systemic issues and helps tune NDI policies without losing visibility into real data center network regressions.
- **App/TA:** Cisco DC Networking Application (Splunkbase 7777), `cisco:ndi:anomaly`
- **Equipment Models:** Nexus Dashboard Insights
- **Data Sources:** `index=cisco_dc` `sourcetype="cisco:ndi:anomaly"` with fields `category`, `anomaly_type`, `fabric_name`, `severity`
- **SPL:**
```spl
index=cisco_dc sourcetype="cisco:ndi:anomaly" earliest=-7d
| bin _time span=1d
| stats count by _time, category, severity
| eventstats sum(count) as daily by _time
| eventstats avg(daily) as baseline
| where daily > baseline*1.5
| sort -daily
| table _time, category, severity, count, daily, baseline
```
- **Implementation:** (1) Ensure stable `category` mapping from webhook payload. (2) Tune multiplier for seasonal maintenance. (3) Feed noisy categories into NDI suppression workflow with Splunk approval ID.
- **Visualization:** Line chart (daily alert volume), Stacked bar (category mix), Table (spike days).
- **CIM Models:** Alerts
- **CIM SPL:**
```spl
| tstats summariesonly=t count from datamodel=Alerts.Alerts by Alerts.severity span=1d | sort - count
```

- **References:** [Cisco DC Networking Application](https://splunkbase.splunk.com/app/7777), [CIM: Alerts](https://docs.splunk.com/Documentation/CIM/latest/User/Alerts)

---

### UC-18.4.13 · NDFC POAP / ZTP Bootstrap and Day-0 Onboarding Failures

- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability, Fault
- **Value:** Automated provisioning brings switches into the fabric quickly; DHCP, image fetch, or certificate failures during POAP/ZTP delay expansions and leave partially configured devices in racks. Monitoring onboarding outcomes keeps brownfield growth on schedule and prevents rogue devices from sitting outside policy.
- **App/TA:** Cisco DC Networking Application (Splunkbase 7777), NDFC syslog
- **Equipment Models:** Nexus 9000 being onboarded via NDFC
- **Data Sources:** `index=cisco_dc` `sourcetype="cisco:ndfc:poap"` with fields `serial_number`, `switch_name`, `stage`, `status`, `error_code`
- **SPL:**
```spl
index=cisco_dc sourcetype="cisco:ndfc:poap" earliest=-7d
| where match(lower(status),"(?i)fail|error|timeout") OR (match(lower(stage),"(?i)image|cert|dhcp") AND status!="success")
| stats latest(_time) as last_fail latest(error_code) as err latest(stage) as stage by serial_number, switch_name
| sort -last_fail
| table last_fail, serial_number, switch_name, stage, err
```
- **Implementation:** (1) Forward NDFC POAP/ZTP logs to Splunk with parsed `stage` milestones. (2) Alert on any failure before switch reaches `In-Sync`. (3) Join serial to inventory (UC-18.4.8) for asset context.
- **Visualization:** Timeline (bootstrap attempts), Table (failed devices), Single value (open failures).
- **CIM Models:** Change
- **CIM SPL:**
```spl
| tstats summariesonly=t latest(All_Changes.status) as agg_value from datamodel=Change.All_Changes by All_Changes.action, All_Changes.object_category, All_Changes.user | sort - agg_value
```

- **References:** [Cisco DC Networking Application](https://splunkbase.splunk.com/app/7777), [CIM: Change](https://docs.splunk.com/Documentation/CIM/latest/User/Change)

---

