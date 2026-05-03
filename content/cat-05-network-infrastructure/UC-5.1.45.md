<!-- AUTO-GENERATED from UC-5.1.45.json — DO NOT EDIT -->

---
id: "5.1.45"
title: "Switch CPU and Memory Utilization (Meraki MS)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.1.45 · Switch CPU and Memory Utilization (Meraki MS)

> **Criticality:** Medium &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Fault

*We help you know early when something looks wrong with switch cpu and memory utilization so the team can act before it grows into a bigger outage.*

---

## Description

Monitors switch hardware resources to prevent performance degradation or device failure.

## Value

Operations teams monitor Meraki MS switch CPU and memory utilization, detecting resource exhaustion that affects management plane responsiveness and control plane processing.

## Implementation

Query MS device API for CPU and memory metrics. Alert on threshold breaches.

## Detailed Implementation

### Prerequisites
* Meraki MS CPU and memory utilization data. Data in `index=meraki` with `sourcetype=meraki:api:device:performance` or syslog. Key API: `GET /devices/{serial}/switch/ports/statuses` and device status endpoints.
* Meraki MS cloud-managed: CPU/memory metrics are available via Dashboard API. High CPU on a switch can cause slow management plane response, delayed STP processing, and dropped control packets.

### Step 1 — - Configure data collection
```
# API: GET /organizations/{orgId}/devices/statuses
# Returns device status including performance metrics
[meraki_device_status]
interval = 300
sourcetype = meraki:api:device:status
index = meraki
```
Verify:
```spl
index=meraki sourcetype="meraki:api:device:status" earliest=-4h
| stats count by host
```

### Step 2 — - Create the search and alert

**Primary search -- Switch CPU/memory utilization:**
```spl
index=meraki (sourcetype="meraki:api:device:status" OR sourcetype="meraki:api:device:performance") earliest=-4h
| eval device=coalesce(serial, host)
| eval cpu=tonumber(coalesce(cpu_percent, cpuUsage, cpu))
| eval mem=tonumber(coalesce(memory_percent, memoryUsage, memory))
| lookup meraki_networks.csv serial AS device OUTPUT network_name, site_name, model
| where isnotnull(cpu) OR isnotnull(mem)
| bin _time span=5m
| stats avg(cpu) as avg_cpu max(cpu) as max_cpu avg(mem) as avg_mem max(mem) as max_mem by _time, network_name, device, model
| eval avg_cpu=round(avg_cpu, 1)
| eval avg_mem=round(avg_mem, 1)
| eval severity=case(
    max_cpu > 90 OR max_mem > 95, "CRITICAL -- switch resource exhaustion",
    max_cpu > 80, "WARNING -- high CPU utilization",
    max_mem > 85, "WARNING -- high memory utilization",
    1==1, "OK")
| where severity != "OK"
| table _time, network_name, device, model, avg_cpu, max_cpu, avg_mem, max_mem, severity
| sort severity, -max_cpu
```

### Step 3 — - Validate
(a) Dashboard: Organization > Summary -- check device status.
(b) Dashboard: Switch > Overview -- per-switch performance.
(c) Check for recent firmware updates or configuration changes.

### Step 4 — - Operationalize
Dashboard ("Meraki MS -- Device Resources"):
* Row 1 -- Single-value: "High CPU switches", "High memory switches".
* Row 2 -- CPU utilization timechart.

Alert: Critical (CPU >90%): management plane impact.

### Step 5 — - Troubleshooting

* **High CPU** -- Common causes: (1) STP reconvergence, (2) large MAC table, (3) excessive broadcasts, (4) firmware bug. Check Dashboard event log for concurrent events.

* **High memory** -- May indicate large routing table or MAC table. Check connected client count and VLAN count.

* **Sustained high utilization** -- Contact Meraki support. Consider firmware upgrade or hardware model upgrade.

## SPL

```spl
index=cisco_network sourcetype="meraki:api" device_type=MS
| stats avg(cpu_usage) as avg_cpu, max(cpu_usage) as peak_cpu, avg(memory_usage) as avg_mem by switch_name
| where avg_cpu > 75 OR avg_mem > 80
```

## Visualization

Gauge charts for CPU/memory; time-series trends; capacity planning dashboard.

## Known False Positives

Short CPU or memory spikes during routing convergence, code upgrade, or SNMP walks are common. Baseline by platform role and compare to a maintenance calendar.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
