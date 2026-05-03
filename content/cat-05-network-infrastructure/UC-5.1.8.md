<!-- AUTO-GENERATED from UC-5.1.8.json — DO NOT EDIT -->

---
id: "5.1.8"
title: "Device CPU/Memory Utilization"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.1.8 · Device CPU/Memory Utilization

> **Criticality:** High &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Performance, Capacity

*We help you know early when something looks wrong with device cpu/memory utilization so the team can act before it grows into a bigger outage.*

---

## Description

CPU exhaustion causes packet drops, routing failures, management unresponsiveness.

## Value

Operations teams monitor router and switch CPU and memory utilization, detecting resource exhaustion that degrades control-plane stability, CLI access, and packet forwarding.

## Implementation

Poll CISCO-PROCESS-MIB and CISCO-MEMORY-POOL-MIB every 300s. Alert CPU >80% or memory >85%.

## Detailed Implementation

### Prerequisites
* Device CPU and memory utilization data from SNMP or syslog. Data in `index=network` with `sourcetype=snmp:device:perf` or syslog CPU threshold alerts. Key SNMP OIDs: cpmCPUTotal5min (.1.3.6.1.4.1.9.9.109.1.1.1.1.5), ciscoMemoryPoolFree (.1.3.6.1.4.1.9.9.48.1.1.1.6), ciscoMemoryPoolUsed (.1.3.6.1.4.1.9.9.48.1.1.1.5).
* High CPU can cause control-plane instability (BGP/OSPF keepalive drops, STP delays), slow CLI response, and packet drops. High memory can cause process crashes and inability to learn routes.

### Step 1 — - Configure data collection
```
# SNMP polling for CPU/Memory
# inputs.conf
[snmp_device_perf]
interval = 300
sourcetype = snmp:device:perf
index = network
# OIDs: cpmCPUTotal5min, ciscoMemoryPoolUsed, ciscoMemoryPoolFree

# Alternative: Cisco syslog threshold alerts
process cpu threshold type total rising 80 interval 60
```
Verify:
```spl
index=network sourcetype="snmp:device:perf" earliest=-1h
| stats latest(cpmCPUTotal5min) latest(ciscoMemoryPoolUsed) by host
```

### Step 2 — - Create the search and alert

**Primary search -- CPU and memory utilization monitoring:**
```spl
index=network earliest=-4h
| eval cpu_pct=tonumber(coalesce(cpmCPUTotal5min, cpu_usage, cpu_percent))
| eval mem_used=tonumber(coalesce(ciscoMemoryPoolUsed, memory_used))
| eval mem_free=tonumber(coalesce(ciscoMemoryPoolFree, memory_free))
| eval mem_total=mem_used + mem_free
| eval mem_pct=if(mem_total > 0, round(100*mem_used/mem_total, 1), null())
| eval device=coalesce(host, device_name)
| where isnotnull(cpu_pct) OR isnotnull(mem_pct)
| bin _time span=5m
| stats avg(cpu_pct) as avg_cpu max(cpu_pct) as max_cpu avg(mem_pct) as avg_mem max(mem_pct) as max_mem by _time, device
| eval avg_cpu=round(avg_cpu, 1)
| eval avg_mem=round(avg_mem, 1)
| eval severity=case(
    max_cpu > 90 OR max_mem > 95, "CRITICAL -- device resource exhaustion",
    max_cpu > 80 OR max_mem > 85, "WARNING -- high resource utilization",
    max_cpu > 70, "INFO -- elevated CPU",
    1==1, "OK")
| where severity != "OK"
| table _time, device, avg_cpu, max_cpu, avg_mem, max_mem, severity
| sort severity, -max_cpu
```

### Step 3 — - Validate
(a) CLI: `show processes cpu sorted` -- identify top CPU consumers.
(b) CLI: `show memory statistics` -- check memory pool utilization.
(c) CLI: `show processes memory sorted` -- identify top memory consumers.

### Step 4 — - Operationalize
Dashboard ("Network -- Device Resources"):
* Row 1 -- Single-value: "Devices > 80% CPU", "Devices > 85% memory".
* Row 2 -- CPU utilization timechart.
* Row 3 -- Memory utilization timechart.

Alert: Critical (CPU >90% or Memory >95% sustained 15 min): control-plane risk.

### Step 5 — - Troubleshooting

* **High CPU** -- Identify top process: `show processes cpu sorted`. Common causes: (1) routing reconvergence, (2) ACL logging, (3) crypto operations (VPN), (4) SNMP polling overload, (5) control-plane attacks.

* **High memory** -- Check: `show processes memory sorted`. Common causes: (1) large BGP table (full internet table ~1M routes), (2) memory leak (known bug), (3) large ACL/QoS policy. Consider upgrading RAM.

* **Correlation with incidents** -- Overlay CPU/memory with interface down and routing adjacency events. High CPU often precedes protocol timeouts.

**IPv6 Coverage:** NDP storms, ICMPv6 floods, and RA flooding are IPv6-specific CPU stressors. SISF/device-tracking (Cisco Catalyst) can consume significant CPU when processing NDP at scale on access switches with many IPv6 hosts.

## SPL

```spl
index=network sourcetype="snmp:cpu"
| timechart span=5m avg(cpmCPUTotal5minRev) as cpu_pct by host | where cpu_pct > 80
```

## Visualization

Line chart, Gauge, Table of high-utilization devices.

## Known False Positives

Short CPU or memory spikes during routing convergence, code upgrade, or SNMP walks are common. Baseline by platform role and compare to a maintenance calendar.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
