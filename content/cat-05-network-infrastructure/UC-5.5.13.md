<!-- AUTO-GENERATED from UC-5.5.13.json — DO NOT EDIT -->

---
id: "5.5.13"
title: "Edge Device Resource Utilization"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.5.13 · Edge Device Resource Utilization

> **Criticality:** High &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Performance, Capacity

*We keep an eye on how our wide-area links and SD-WAN paths are behaving so we spot a bad circuit or policy issue before branch users lose voice, video, or critical apps.*

---

## Description

SD-WAN edge routers running high CPU or memory can drop packets, fail to establish tunnels, or crash. Monitoring device resources prevents silent performance degradation at remote sites where physical access is limited.

## Value

Network operations teams monitor SD-WAN edge device CPU, memory, and disk utilization against model-specific capacity limits, enabling proactive hardware upgrades and identifying resource-related data plane degradation.

## Implementation

Poll vManage device statistics API for CPU, memory, and disk usage. Alert when CPU exceeds 80% or memory exceeds 85% sustained over 15 minutes. Trend over time to identify sites that need hardware upgrades. Pay special attention to devices running UTD (Unified Threat Defense) or DPI, which consume significantly more resources.

## Detailed Implementation

### Prerequisites
- Cisco Catalyst Add-on for Splunk polling vManage API for device statistics. Data in `index=sdwan` with `sourcetype=cisco:sdwan:device` or `sourcetype=cisco:sdwan:statistics`. Key fields: `system_ip`, `site_id`, `cpu_user`, `cpu_system`, `cpu_idle`, `mem_total`, `mem_used`, `mem_free`, `disk_used`, `disk_size`, `device_model`, `board_serial`.
- SD-WAN edge devices (Catalyst 8000 series, ISR, vEdge) handle: data plane encryption/decryption (IPsec), DPI classification, NAT, firewall/UTD, and control plane processing. CPU-intensive features (DPI, UTD) can push device utilization high, causing packet drops, increased latency, and tunnel instability.
- Build `sdwan_device_capacity.csv` lookup: `device_model,max_throughput_mbps,max_tunnels,max_omp_routes,cpu_threshold_warn,cpu_threshold_crit` (e.g., `C8300-1N4T,1000,500,10000,70,85`). Each device model has published capacity limits.

### Step 1 — Configure data collection
Verify device resource data:
```spl
index=sdwan (sourcetype="cisco:sdwan:device" OR sourcetype="cisco:sdwan:statistics") earliest=-15m
| stats avg(cpu_user) as cpu avg(mem_used) as mem by system_ip, device_model
```

### Step 2 — Create the search and alert

**Primary search — Edge device resource utilization:**
```spl
index=sdwan (sourcetype="cisco:sdwan:device" OR sourcetype="cisco:sdwan:statistics") earliest=-15m
| eval cpu_pct=100 - cpu_idle
| eval mem_pct=if(mem_total > 0, round(100 * mem_used / mem_total, 1), null())
| eval disk_pct=if(disk_size > 0, round(100 * disk_used / disk_size, 1), null())
| stats avg(cpu_pct) as avg_cpu max(cpu_pct) as peak_cpu avg(mem_pct) as avg_mem max(mem_pct) as peak_mem latest(disk_pct) as disk_pct by system_ip, site_id, device_model
| lookup sdwan_device_capacity.csv device_model OUTPUT max_throughput_mbps cpu_threshold_warn cpu_threshold_crit
| eval cpu_status=case(avg_cpu > cpu_threshold_crit, "CRITICAL", avg_cpu > cpu_threshold_warn, "WARNING", 1==1, "OK")
| eval mem_status=case(avg_mem > 90, "CRITICAL", avg_mem > 80, "WARNING", 1==1, "OK")
| eval disk_status=case(disk_pct > 90, "CRITICAL", disk_pct > 80, "WARNING", 1==1, "OK")
| eval worst_status=case(cpu_status="CRITICAL" OR mem_status="CRITICAL" OR disk_status="CRITICAL", "CRITICAL", cpu_status="WARNING" OR mem_status="WARNING" OR disk_status="WARNING", "WARNING", 1==1, "OK")
| where worst_status!="OK"
| lookup sdwan_sites.csv site_id OUTPUT site_name tier
| lookup sdwan_devices.csv system_ip OUTPUT hostname
| sort worst_status, tier
```

#### Understanding this SPL: Edge device resource exhaustion directly causes data plane degradation. High CPU leads to packet drops (increased loss and jitter on all tunnels), high memory can cause OMP route table truncation, and disk exhaustion can prevent log storage and configuration saves. The device model capacity lookup enables model-appropriate thresholds — a C8300 has different limits than a vEdge 1000.

**CPU trending per device:**
```spl
index=sdwan (sourcetype="cisco:sdwan:device" OR sourcetype="cisco:sdwan:statistics") earliest=-24h
| eval cpu_pct=100 - cpu_idle
| bin _time span=5m
| stats avg(cpu_pct) as cpu by _time, system_ip
| lookup sdwan_devices.csv system_ip OUTPUT hostname
| eval label=if(isnotnull(hostname), hostname, system_ip)
| timechart span=5m avg(cpu) by label
```

**Device resource capacity planning:**
```spl
index=sdwan (sourcetype="cisco:sdwan:device" OR sourcetype="cisco:sdwan:statistics") earliest=-7d
| eval cpu_pct=100 - cpu_idle
| stats p95(cpu_pct) as p95_cpu avg(cpu_pct) as avg_cpu by system_ip, device_model
| lookup sdwan_device_capacity.csv device_model OUTPUT max_throughput_mbps cpu_threshold_crit
| eval headroom_pct=round(cpu_threshold_crit - p95_cpu, 1)
| where headroom_pct < 15
| lookup sdwan_devices.csv system_ip OUTPUT hostname site_id
| lookup sdwan_sites.csv site_id OUTPUT site_name
| eval recommendation=case(headroom_pct < 0, "Upgrade immediately", headroom_pct < 5, "Upgrade within 30 days", headroom_pct < 15, "Plan upgrade")
| sort headroom_pct
```

### Step 3 — Validate
(a) On an edge device: `show system status` — compare CPU, memory, and disk with Splunk values.
(b) In vManage: Monitor > Network > select device > System Status. Verify resource metrics match.
(c) Generate load (traffic throughput test) and verify CPU increase appears in Splunk trending.

### Step 4 — Operationalize
Dashboard ("SD-WAN — Edge Device Health"):
- Row 1 — Single-value tiles: "Devices CPU critical", "Devices memory critical", "Devices disk critical", "Average fleet CPU".
- Row 2 — Device resource table: hostname, model, site, CPU (avg/peak), memory, disk, status.
- Row 3 — CPU trending for selected device.
- Row 4 — Capacity planning table: devices approaching limits with upgrade recommendations.

Alerting:
- Critical (CPU > model threshold for 10+ minutes): data plane degradation — packet drops likely.
- Critical (memory > 90%): OMP route table or NAT table may be impacted.
- Warning (disk > 80%): configuration saves and log storage at risk.
- Info (weekly): capacity planning report — devices with < 15% headroom.

### Step 5 — Troubleshooting

- **High CPU on data plane** — Identify the cause: DPI processing (disable or reduce if not needed), UTD/IDS (tune signatures), high tunnel count (reduce mesh), or NAT translation table overflow.

- **Memory increasing over time** — Possible memory leak in the SD-WAN software. Check for known bugs in the running firmware version. A device reboot clears the issue temporarily; a firmware upgrade fixes permanently.

- **CPU spikes during business hours, normal at night** — Likely correlated with traffic volume. Check bandwidth utilization (UC-5.5.7). If the device is CPU-bound during peak, consider upgrading to a higher-capacity model.

## SPL

```spl
index=sdwan sourcetype="cisco:sdwan:device"
| stats latest(cpu_user) as cpu_user, latest(cpu_system) as cpu_system, latest(mem_used) as mem_used, latest(mem_total) as mem_total by hostname, system_ip, site_id
| eval cpu_pct=cpu_user+cpu_system, mem_pct=round(mem_used/mem_total*100,1)
| where cpu_pct > 80 OR mem_pct > 85
| table hostname system_ip site_id cpu_pct mem_pct
| sort -cpu_pct
```

## Visualization

Line chart (CPU/memory trending per device), Table (devices above threshold), Gauge (fleet-wide average).

## Known False Positives

Utilization and top-application charts jump during backups, patch windows, video calls, or large file transfers; compare to baselines and scheduled jobs before treating a spike as fault.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)
