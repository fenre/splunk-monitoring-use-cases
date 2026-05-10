<!-- AUTO-GENERATED from UC-5.11.4.json — DO NOT EDIT -->

---
id: "5.11.4"
title: "System CPU and Memory Utilization Streaming"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.11.4 · System CPU and Memory Utilization Streaming

> **Criticality:** High &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Performance

*We help you see when a router or switch brain is getting overloaded, so we can act before it starts dropping the signals that keep the network stable.*

---

## Description

Network device control planes running hot indicate routing churn, excessive logging, or a control-plane DoS. gNMI streaming at 30-second intervals catches transient CPU spikes that 5-minute SNMP polls miss entirely. A Nexus spine hitting 90% CPU during a BGP convergence event could start dropping BFD keepalives, cascading into a fabric-wide outage.

## Value

Network operations teams monitor control plane CPU and memory utilization via gNMI streaming, enabling early detection of resource exhaustion, routing convergence bottlenecks, and memory leaks before they impact forwarding.

## Implementation

Subscribe to `/system/cpus/cpu/state` at 30s intervals. For Cisco IOS XR, use native YANG `system-monitoring/cpu-utilization/total-cpu-one-minute`. Alert at 80% sustained for 5 minutes. Correlate with BGP update storms (UC-5.11.8) and interface flaps. Track per-process CPU if platform supports `/system/processes/process/state`.

## Detailed Implementation

### Prerequisites
- Telegraf gNMI collector configured with SAMPLE subscriptions for system resource metrics. OpenConfig paths: `/system/cpus/cpu/state` for CPU utilization, `/system/memory/state` for memory. Sample interval: 30-60 seconds.
- Vendor-specific YANG paths may be needed: Cisco IOS-XR: `Cisco-IOS-XR-wdsysmon-fd-oper:system-monitoring/cpu-utilization` and `Cisco-IOS-XR-nto-misc-oper:memory-summary`; Cisco NX-OS: `openconfig-system` is well-supported; Arista EOS: OpenConfig `/system` supported; Juniper: `junos-system-state`.
- Understanding CPU on network devices: unlike servers, network devices have multiple CPUs/cores serving different functions — control plane CPU (routing protocol processing, CLI, SNMP), data plane ASIC (packet forwarding). This UC focuses on control plane CPU, which is the bottleneck for routing convergence, management responsiveness, and telemetry itself.
- Thresholds: control plane CPU > 80% sustained indicates route churn, software bug, or denial-of-service. Memory > 85% can cause process crashes and routing table truncation. These vary by platform — consult vendor documentation for recommended maximums.

### Step 1 — Configure data collection
Telegraf subscription:
```toml
[[inputs.gnmi.subscription]]
  name = "openconfig_system"
  origin = "openconfig"
  path = "/system/cpus/cpu/state"
  subscription_mode = "sample"
  sample_interval = "30s"

[[inputs.gnmi.subscription]]
  name = "openconfig_system_memory"
  origin = "openconfig"
  path = "/system/memory/state"
  subscription_mode = "sample"
  sample_interval = "30s"
```

Verify data arrival:
```spl
| mcatalog values(metric_name) WHERE index=gnmi_metrics host=spine-01
| search metric_name="openconfig_system*"
```

### Step 2 — Create the search and alert

**Primary search — CPU utilization with process-level detail:**
```spl
| mstats avg("openconfig_system.instant") AS cpu_pct WHERE index=gnmi_metrics metric_name="openconfig_system.instant" BY host span=1m
| where cpu_pct > 60
| eval status=case(cpu_pct > 90, "CRITICAL", cpu_pct > 80, "HIGH", cpu_pct > 60, "WARNING", 1==1, "OK")
| lookup device_inventory.csv host OUTPUT device_role platform
| sort -cpu_pct
```

#### Understanding this SPL: OpenConfig reports CPU utilization as `instant` (current), `avg` (1-min average), and `max` (1-min max) under `/system/cpus/cpu/state`. The `instant` metric gives the most current view. For network devices, sustained CPU > 60% on the control plane warrants investigation — unlike servers, network device control plane CPUs are sized for specific workloads and have less headroom.

**Memory utilization with exhaustion prediction:**
```spl
| mstats latest("openconfig_system_memory.used") AS mem_used latest("openconfig_system_memory.physical") AS mem_total WHERE index=gnmi_metrics BY host span=5m
| eval mem_pct=round(100*mem_used/mem_total, 1)
| eval mem_free_MB=round((mem_total-mem_used)/1048576, 0)
| where mem_pct > 75
| eval status=case(mem_pct > 95, "CRITICAL", mem_pct > 85, "HIGH", mem_pct > 75, "WARNING", 1==1, "OK")
| sort -mem_pct
```

**CPU spike correlation with BGP events:**
```spl
| mstats avg("openconfig_system.instant") AS cpu_pct WHERE index=gnmi_metrics BY host span=1m earliest=-4h
| where cpu_pct > 70
| join type=left host _time [
    | mstats latest("openconfig_bgp.session_state") AS bgp_state WHERE index=gnmi_metrics BY host, neighbor_address span=1m earliest=-4h
    | where bgp_state != 6
    | stats count AS bgp_events by host, _time
]
| eval bgp_correlation=if(isnotnull(bgp_events), "BGP event during CPU spike", "No BGP event")
| sort -cpu_pct
```

#### Understanding this SPL: Correlates CPU spikes with BGP events. High CPU during BGP peer loss suggests route reconvergence (legitimate workload). High CPU without BGP events may indicate a software bug, denial-of-service, or runaway process.

### Step 3 — Validate
(a) On the device, check CPU: `show processes cpu` (Cisco) or `show system cpu` (Arista/Juniper). Compare the percentage with the `mstats` value.
(b) Check memory: `show system memory` or equivalent. The `mem_pct` should match within a few percent.
(c) Generate a CPU spike: if you have a test environment, inject a large number of BGP routes rapidly and verify the CPU spike appears in Splunk.

### Step 4 — Operationalize
Dashboard ("Network — Device Resource Utilization"):
- Row 1 — Single-value tiles: "Devices with CPU > 80%", "Devices with Memory > 85%", "Peak CPU (fleet)", "Lowest Free Memory (MB)".
- Row 2 — Table: host, platform, cpu_pct, mem_pct, status. Color-coded by severity.
- Row 3 — Timechart: CPU utilization for selected device over 24h with BGP event overlay.
- Row 4 — Memory trending: selected device memory utilization over 7 days for leak detection.

Alerting:
- Critical (CPU > 90% for 5+ minutes): page NOC — control plane at risk, management and routing protocol processing may be impacted.
- Critical (Memory > 95%): page NOC — imminent process crash or routing table truncation.
- High (CPU > 80% for 15+ minutes or Memory > 85%): alert for investigation.

Runbook (owner: Network Operations):
1. **CPU spike during BGP convergence**: Normal during route churn. If sustained after convergence completes, check for routing loops or excessive BGP UPDATE messages.
2. **CPU spike without network events**: Check for SNMP polling storms (too many MIB walks simultaneously), syslog flood, or software bug. `show processes cpu sorted` identifies the offending process.
3. **Memory leak**: Gradually increasing memory over days/weeks without corresponding network growth suggests a software memory leak. Document the trend and open a vendor TAC case with the memory graph as evidence.

### Step 5 — Troubleshooting

- **CPU metric names vary by platform** — OpenConfig uses `instant`/`avg`/`max`, but Cisco IOS-XR native YANG uses different paths. Check `| mcatalog values(metric_name) WHERE index=gnmi_metrics host=<device>` to discover actual metric names on each platform.

- **Memory metrics show different scales** — Some platforms report bytes, others report kilobytes. Normalize in the search: `| eval mem_used_bytes=if(mem_used < 1000000, mem_used*1024, mem_used)`.

- **CPU always shows 100% on one core** — Some platforms dedicate one CPU core to the data plane or interrupt handling. Filter to the control plane CPU: `| where cpu_index="0" OR cpu_name="RP"`.

- **Telegraf itself consuming device CPU** — gNMI subscriptions with very short intervals (< 10s) on many paths can overload the device's gRPC server. Start with 30s intervals and increase data points gradually.

## SPL

```spl
| mstats avg("openconfig_system.cpu_total_instant") AS cpu_pct WHERE index=gnmi_metrics BY host span=1m
| where cpu_pct > 80
| table _time, host, cpu_pct
| sort -cpu_pct
```

## CIM SPL

```spl
| tstats `summariesonly` max(Performance.cpu_load_percent) as cpu_load
  from datamodel=Performance.All_Performance
  by Performance.host span=5m
| where cpu_load > 80
| sort -cpu_load
```

## Visualization

Gauge (current CPU per device), Line chart (CPU trend), Table (devices above threshold).

## Known False Positives

Telemetry pauses during device reboots, cert renewals, or transport changes; subscription restarts and path renames can look like drops without a live fault.

## References

- [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)
