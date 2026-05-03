<!-- AUTO-GENERATED from UC-5.5.18.json — DO NOT EDIT -->

---
id: "5.5.18"
title: "vManage Cluster Health"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.5.18 · vManage Cluster Health

> **Criticality:** Critical &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Availability

*We keep an eye on how our wide-area links and SD-WAN paths are behaving so we spot a bad circuit or policy issue before branch users lose voice, video, or critical apps.*

---

## Description

vManage is the single management plane for the entire SD-WAN fabric. If the vManage cluster is unhealthy — high CPU, disk full, database replication lag, or services down — operators lose visibility and policy push capability across all sites.

## Value

Network operations teams monitor vManage cluster health including node availability, resource utilization, and quorum status, preventing the management plane blind spot where the monitoring platform itself becomes the single point of failure.

## Implementation

Poll vManage cluster health API. Monitor CPU, memory, disk usage, NMS database replication status, and running services. For clustered deployments, verify all nodes are in sync. Alert when any node exceeds 70% CPU, 80% memory, or 75% disk, or when database replication falls behind. Schedule regular config database backups independently.

## Detailed Implementation

### Prerequisites
- Cisco Catalyst Add-on for Splunk polling vManage API for cluster and system health. Data in `index=sdwan` with `sourcetype=cisco:sdwan:device` (personality=vmanage) or `sourcetype=cisco:sdwan:system`. Key fields: `personality`, `system_ip`, `reachability`, `cpu_idle`, `mem_used`, `mem_total`, `disk_used`, `disk_size`, `cluster_id`, `services_status`, `device_count`.
- vManage cluster typically runs 3 or 6 nodes for high availability. Each node runs: configuration database (Neo4j), statistics database (Elasticsearch), messaging (Kafka), application server, and NMS (network management). If any component fails, the cluster degrades.
- vManage is the single pane of glass for SD-WAN operations. If vManage goes down: operators lose visibility, can't push configuration changes, can't view alarms, and can't perform software upgrades. Existing data plane tunnels continue working, but the network is unmanaged.
- Build `sdwan_vmanage_nodes.csv` lookup: `system_ip,hostname,datacenter,role` (e.g., `10.10.1.1,vmanage-1,DC-East,primary`, `10.10.1.2,vmanage-2,DC-East,secondary`, `10.10.1.3,vmanage-3,DC-West,dr`).

### Step 1 — Configure data collection
Verify vManage cluster data:
```spl
index=sdwan sourcetype="cisco:sdwan:device" personality="vmanage" earliest=-15m
| stats count by system_ip, reachability
```

### Step 2 — Create the search and alert

**Primary search — vManage cluster health overview:**
```spl
index=sdwan sourcetype="cisco:sdwan:device" personality="vmanage" earliest=-15m
| eval cpu_pct=100 - cpu_idle
| eval mem_pct=round(100 * mem_used / mem_total, 1)
| eval disk_pct=round(100 * disk_used / disk_size, 1)
| lookup sdwan_vmanage_nodes.csv system_ip OUTPUT hostname datacenter role
| eval node_label=if(isnotnull(hostname), hostname." (".role.")", system_ip)
| eval cpu_status=case(cpu_pct > 85, "CRITICAL", cpu_pct > 70, "WARNING", 1==1, "OK")
| eval mem_status=case(mem_pct > 90, "CRITICAL", mem_pct > 80, "WARNING", 1==1, "OK")
| eval disk_status=case(disk_pct > 85, "CRITICAL", disk_pct > 75, "WARNING", 1==1, "OK")
| eval reach_status=if(reachability="reachable", "OK", "CRITICAL")
| eval worst=case(reach_status="CRITICAL", "CRITICAL", cpu_status="CRITICAL" OR mem_status="CRITICAL" OR disk_status="CRITICAL", "CRITICAL", cpu_status="WARNING" OR mem_status="WARNING" OR disk_status="WARNING", "WARNING", 1==1, "OK")
| table node_label, datacenter, reachability, cpu_pct, cpu_status, mem_pct, mem_status, disk_pct, disk_status, worst
| sort worst
```

#### Understanding this SPL: vManage is often the forgotten piece of SD-WAN monitoring — operators monitor the network through vManage but don't monitor vManage itself. CPU > 85% on a vManage node causes slow UI response, API timeouts (which means the TA stops collecting data), and delayed alarm processing. Disk > 85% causes statistics database (Elasticsearch) to stop accepting data and can trigger cluster instability.

**vManage cluster quorum check:**
```spl
index=sdwan sourcetype="cisco:sdwan:device" personality="vmanage" earliest=-15m
| stats count(eval(reachability="reachable")) as reachable_nodes count as total_nodes
| eval quorum=if(reachable_nodes > total_nodes/2, "HEALTHY", "LOST")
| eval message=case(quorum="LOST", "CRITICAL: vManage cluster has lost quorum — ".reachable_nodes." of ".total_nodes." nodes reachable", reachable_nodes < total_nodes, "WARNING: ".total_nodes - reachable_nodes." node(s) unreachable — cluster running degraded", 1==1, "OK: All ".total_nodes." nodes healthy")
```

**vManage resource trending:**
```spl
index=sdwan sourcetype="cisco:sdwan:device" personality="vmanage" earliest=-7d
| eval cpu_pct=100 - cpu_idle
| eval mem_pct=round(100 * mem_used / mem_total, 1)
| bin _time span=1h
| stats avg(cpu_pct) as cpu avg(mem_pct) as mem by _time, system_ip
| lookup sdwan_vmanage_nodes.csv system_ip OUTPUT hostname
| timechart span=1h avg(cpu) by hostname
```

### Step 3 — Validate
(a) In vManage: Administration > Cluster Management. Compare node status, CPU, memory, and disk with Splunk.
(b) SSH to a vManage node: `show system status` — compare resource utilization.
(c) Test cluster resilience: during a maintenance window, shut down one node and verify the cluster status changes in Splunk.

### Step 4 — Operationalize
Dashboard ("SD-WAN — vManage Cluster"):
- Row 1 — Single-value tiles: "Cluster quorum status", "Nodes healthy", "Nodes degraded", "Nodes unreachable".
- Row 2 — Node health table: hostname, datacenter, role, CPU, memory, disk, reachability, status.
- Row 3 — Resource trending per node over 7 days.
- Row 4 — Quorum status history.

Alerting:
- Critical (cluster quorum lost): the network is unmanageable — immediate action required.
- Critical (any node unreachable): cluster redundancy reduced.
- High (CPU > 85% or disk > 85% on any node): cluster performance degrading — API response times increase, affecting monitoring.
- Warning (memory > 80%): approaching capacity — consider adding resources.

### Step 5 — Troubleshooting

- **vManage data stops arriving in Splunk** — If vManage itself is down, the TA can't poll APIs. Check vManage accessibility. This creates a monitoring blind spot: you don't know the network is unmonitored. Consider a secondary health check (ping/HTTP check to vManage from Splunk) independent of the API.

- **Disk usage growing rapidly** — Elasticsearch (statistics DB) is the primary consumer. Check statistics retention settings in vManage: Administration > Settings > Statistics Database Config. Reduce retention days or increase disk.

- **High CPU on vManage** — Common causes: too many concurrent API sessions (including the Splunk TA), large device inventory (> 1000 devices), or statistics aggregation jobs. Consider increasing vManage VM resources or reducing TA polling frequency.

## SPL

```spl
index=sdwan sourcetype="cisco:sdwan:vmanage"
| stats latest(cpu_load) as cpu, latest(mem_util) as mem_pct, latest(disk_util) as disk_pct, latest(db_status) as db_status, latest(services_running) as services by vmanage_ip
| where cpu > 70 OR mem_pct > 80 OR disk_pct > 75 OR db_status!="healthy"
| table vmanage_ip cpu mem_pct disk_pct db_status services
```

## Visualization

Single value panels (CPU, memory, disk per node), Status indicator (cluster health), Table (services status).

## Known False Positives

Tunnels may renegotiate during ISP maintenance, BFD timer changes, planned controller upgrades, or policy pushes; short blips may look like failures when the business path is still acceptable.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
