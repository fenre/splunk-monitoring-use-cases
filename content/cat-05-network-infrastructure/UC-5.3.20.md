<!-- AUTO-GENERATED from UC-5.3.20.json — DO NOT EDIT -->

---
id: "5.3.20"
title: "Citrix ADC System Resource Utilization (NetScaler)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.3.20 · Citrix ADC System Resource Utilization (NetScaler)

> **Criticality:** High &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Capacity, Performance

*We average cpu and memory on the same nodes so a hot vserver or a full box is a visible warning before a hard stop.*

---

## Description

Citrix ADC appliances (physical or VPX) have finite CPU, memory, and throughput capacity. Unlike general-purpose servers, ADC resource exhaustion directly impacts all applications it fronts — causing connection drops, increased latency, and SSL handshake failures. Monitoring ADC system resources enables capacity planning and prevents appliance-level bottlenecks that affect the entire application delivery infrastructure.

## Value

Infrastructure teams monitor Citrix ADC system resources distinguishing packet engine CPU from management CPU, detecting traffic processing saturation and memory pressure before throughput degradation.

## Implementation

Poll the NITRO API `ns` (system) resource for CPU utilization, memory usage, and packet engine stats. Also poll `ssl` stats for SSL transactions per second (TPS). Run every 5 minutes. Key thresholds: CPU above 70% average (capacity planning), CPU spike above 90% (performance impact imminent), memory above 80% (connection table pressure), SSL TPS approaching licensed limit (SSL offload bottleneck). Track packet engine CPU separately from management CPU — high management CPU with low packet CPU indicates control plane issues. Trend resource utilization to forecast when additional ADC capacity is needed.

## Detailed Implementation

### Prerequisites
* Splunk Add-on for Citrix NetScaler (`Splunk_TA_citrix-netscaler`, Splunkbase 2770). NITRO API performance counters or SNMP polling for system resources. Key metrics: `cpu_usage_pct`, `memory_usage_pct`, `disk_usage_pct`, `mgmt_cpu_usage_pct`, `packet_engine_cpu_pct`, `rx_mbps`, `tx_mbps`, `http_requests_rate`.
* Citrix ADC has two CPU types: (1) Management CPU -- handles config, logging, SNMP, (2) Packet Engine (PE) CPUs -- handle traffic processing. PE CPU saturation directly impacts throughput.

### Step 1 — - Configure data collection
Poll NITRO API: `GET /nitro/v1/stat/system` and `GET /nitro/v1/stat/protocolhttp` every 5 minutes. Verify:
```spl
index=netscaler sourcetype="citrix:netscaler:perf" earliest=-4h
| where isnotnull(cpu_usage_pct) OR isnotnull(packet_engine_cpu_pct) OR isnotnull(memory_usage_pct)
| stats latest(cpu_usage_pct) as cpu latest(memory_usage_pct) as mem by host
```

### Step 2 — - Create the search and alert

**Primary search -- System resource utilization:**
```spl
index=netscaler (sourcetype="citrix:netscaler:perf" OR sourcetype="citrix:netscaler:syslog") earliest=-4h
| eval cpu=coalesce(cpu_usage_pct, cpuusagepcnt)
| eval mem=coalesce(memory_usage_pct, memusagepcnt)
| eval pe_cpu=coalesce(packet_engine_cpu_pct, pktcpuusagepcnt)
| eval mgmt_cpu=coalesce(mgmt_cpu_usage_pct, mgmtcpuusagepcnt)
| eval disk=coalesce(disk_usage_pct, diskperusage)
| bin _time span=5m
| stats avg(cpu) as avg_cpu max(cpu) as max_cpu avg(mem) as avg_mem max(mem) as max_mem avg(pe_cpu) as avg_pe_cpu max(pe_cpu) as max_pe_cpu avg(disk) as avg_disk by _time, host
| eval severity=case(max_pe_cpu > 95, "CRITICAL -- packet engine saturated", max_cpu > 90, "HIGH -- CPU saturation", max_mem > 90, "HIGH -- memory pressure", avg_disk > 85, "WARNING -- disk space", max_pe_cpu > 80, "WARNING -- PE CPU elevated", 1==1, "OK")
| where severity != "OK"
| sort severity, -max_pe_cpu
```

### Step 3 — - Validate
(a) On ADC CLI: `stat system` -- compare CPU/memory with Splunk.
(b) On ADC CLI: `stat system -detail` -- get per-PE CPU breakdown.
(c) Generate load and verify CPU increases in Splunk.

### Step 4 — - Operationalize
Dashboard ("Citrix ADC -- System Resources"):
* Row 1 -- Single-value: "CPU %", "PE CPU %", "Memory %", "Disk %", "HTTP req/s".
* Row 2 -- Per-ADC resource table with severity.
* Row 3 -- Resource trending timechart (24h).

Alerting:
* Critical (PE CPU > 95% for > 5 min): traffic processing impacted.
* Warning (memory > 90%): may cause connection drops.
* Warning (disk > 85%): log storage filling up.

### Step 5 — - Troubleshooting

* **High PE CPU** -- Packet engine is processing too much traffic. Options: (1) add SSL hardware acceleration (MPX/SDX), (2) optimize SSL profiles (session reuse, ECDHE over RSA key exchange), (3) reduce iRule/responder policy complexity.

* **High management CPU** -- Too many SNMP polls, syslog messages, or NITRO API calls. Reduce polling frequency or move monitoring to SNMP traps.

* **High memory** -- Check: `show ns memory` for per-feature breakdown. Common consumers: SSL session cache, TCP connection table, content caching.

## SPL

```spl
index=network sourcetype="citrix:netscaler:perf"
| bin _time span=5m
| stats avg(cpu_use_pct) as avg_cpu, max(cpu_use_pct) as max_cpu,
  avg(mem_use_pct) as avg_mem, avg(active_connections) as avg_conns,
  avg(ssl_tps) as avg_ssl_tps, avg(rx_mbps) as avg_rx, avg(tx_mbps) as avg_tx by host, _time
| where avg_cpu > 70 OR avg_mem > 80 OR max_cpu > 90
| table _time, host, avg_cpu, max_cpu, avg_mem, avg_conns, avg_ssl_tps, avg_rx, avg_tx
```

## Visualization

Line chart (CPU and memory over time), Gauge (current utilization), Table (ADCs above threshold).

## Known False Positives

Snmp polling gaps, data drops, and short bursts can wobble averages; compare in the same minute on the node.

## References

- [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)
