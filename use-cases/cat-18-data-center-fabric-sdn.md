## 18. Data Center Fabric & SDN

### 18.1 Cisco ACI

**Splunk Add-on:** Cisco ACI TA, APIC syslog

### UC-18.1.1 · Fabric Health Score Monitoring

- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Compliance
- **Value:** ACI fabric health scores provide a single-pane view of overall data center network health. Monitoring these scores lets you catch degradation before it impacts workloads, correlate health drops with specific faults, and maintain SLA compliance across your data center fabric.
- **App/TA:** `TA_cisco-ACI`, APIC REST API via scripted input
- **Data Sources:** APIC REST API (`/api/node/mo/topology/health.json`), APIC syslog
- **SPL:**
```spl
index=cisco_aci sourcetype="cisco:aci:health"
| eval node_type=case(dn LIKE "%/node-1%", "APIC", dn LIKE "%/node-1___%", "Leaf", dn LIKE "%/node-2___%", "Spine", 1==1, "Other")
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
- **Data Sources:** APIC audit log (`/api/node/class/aaaModLR.json`)
- **SPL:**
```spl
index=cisco_aci sourcetype="cisco:aci:audit"
| search affected LIKE "uni/tn-*"
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

### 18.2 VMware NSX

**Splunk Add-on:** VMware NSX TA, syslog

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

