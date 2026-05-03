<!-- AUTO-GENERATED from UC-5.3.33.json — DO NOT EDIT -->

---
id: "5.3.33"
title: "Citrix SDX Platform Health (Partition Resources)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.3.33 · Citrix SDX Platform Health (Partition Resources)

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Availability

*We read partition resource use on a shared platform so a noisy neighbor on the same blade is visible before your instance starves in silence.*

---

## Description

Citrix NetScaler SDX hosts multiple isolated VPX instances. Platform health is about partition CPU and memory, hypervisor and VPX liveness, and out-of-band LOM, power, and cooling. A stressed partition throttles applications before obvious syslog noise; LOM, PSU, or fan alarms demand hardware attention before a blade fails.

## Value

Infrastructure teams monitor Citrix SDX platform resource allocation and utilization per ADC instance, detecting resource contention and instance failures on the shared hardware platform.

## Implementation

Poll SNMP with SDX/MPX and ADC-specific OIDs into `citrix:netscaler:snmp`. Forward `citrix:netscaler:syslog` for hypervisor, VPX, and platform events. Enrich with asset tags for slot, data hall, and power feed. Page on high partition utilization versus entitlement, and on any hardware or LOM down events.

## Detailed Implementation

### Prerequisites
* Splunk Add-on for Citrix NetScaler (`Splunk_TA_citrix-netscaler`, Splunkbase 2770). Citrix SDX platform syslog and SNMP/NITRO from the SDX Service VM (SVM). Key fields: `instance_name`, `cpu_allocated`, `cpu_used`, `memory_allocated`, `memory_used`, `throughput`, `instance_state`.
* Citrix SDX: hardware platform hosting multiple ADC instances (VPX/CPX) as virtual machines. The SVM manages instance lifecycle. Each instance has allocated CPU cores, memory, and throughput. Resource contention between instances degrades performance.

### Step 1 — - Configure data collection
SDX SVM syslog and NITRO stats: `GET /nitro/v1/config/ns` and `GET /nitro/v1/stat/ns`. Verify:
```spl
index=netscaler (sourcetype="citrix:netscaler:syslog" OR sourcetype="citrix:netscaler:perf") ("SDX" OR "instance" OR "partition" OR "SVM") earliest=-4h
| stats count by host
```

### Step 2 — - Create the search and alert

**Primary search -- SDX instance resource utilization:**
```spl
index=netscaler (sourcetype="citrix:netscaler:syslog" OR sourcetype="citrix:netscaler:perf") earliest=-4h
| eval instance=coalesce(instance_name, ns_instance)
| eval cpu_used=coalesce(cpu_used_pct, cpuusage)
| eval mem_used=coalesce(memory_used_pct, memusage)
| eval throughput_mbps=coalesce(throughput, throughputmbps)
| eval state=coalesce(instance_state, nsstate)
| where isnotnull(instance) AND isnotnull(cpu_used)
| bin _time span=5m
| stats avg(cpu_used) as avg_cpu avg(mem_used) as avg_mem max(throughput_mbps) as peak_throughput latest(state) as state by _time, host, instance
| eval status=case(state!="UP" AND isnotnull(state), "CRITICAL -- instance not UP", avg_cpu > 90, "HIGH -- CPU saturation", avg_mem > 90, "HIGH -- memory pressure", 1==1, "OK")
| where status != "OK"
| sort status
```

### Step 3 — - Validate
(a) On SDX SVM: check instance list and resource allocation.
(b) Compare per-instance CPU with `stat system` on each VPX instance.
(c) Verify total allocated resources don't exceed SDX physical capacity.

### Step 4 — - Operationalize
Dashboard ("Citrix SDX -- Platform Health"):
* Row 1 -- Single-value: "Total instances", "Instances UP", "Max CPU %", "Total throughput (Mbps)".
* Row 2 -- Per-instance resource table.

Alerting:
* Critical (instance not UP): ADC instance down.
* Warning (instance CPU > 90%): resource contention.

### Step 5 — - Troubleshooting

* **Instance down** -- Check SVM management console. Common causes: (1) license expired, (2) resource allocation changed, (3) SVM reboot.

* **Resource contention** -- Multiple instances competing for CPU. Review allocation: ensure no over-provisioning of CPU cores.

* **Throughput limit hit** -- Each instance has a licensed throughput cap. Check instance license.

## SPL

```spl
index=netscaler (sourcetype="citrix:netscaler:snmp" OR sourcetype="citrix:netscaler:syslog") ("SDX" OR "Xen" OR "partition" OR "VPX" OR LOM OR PSU OR FAN OR "throttle")
| eval part_cpu=coalesce(adc_partition_cpu_use_pct, sdx_cpu_use_pct, 0), part_mem=coalesce(adc_partition_mem_use_pct, sdx_mem_use_pct, 0)
| eval alarm=if(match(_raw, "(?i)(PSU|FAN|LOM|redundant|failed|critical)"),1,0)
| bin _time span=5m
| stats max(part_cpu) as max_cpu, max(part_mem) as max_mem, sum(alarm) as alarm_events, values(host) as hosts by _time, sdx_name, partition_id
| where max_cpu>85 OR max_mem>90 OR alarm_events>0
| table _time, sdx_name, partition_id, max_cpu, max_mem, alarm_events, hosts
```

## Visualization

Heatmap of partitions by CPU, horizontal bar: memory, timeline of hardware alarms, table of active VPX count per host.

## Known False Positives

Neighbor bursts and shared platform maintenance can wobble partition stats on a multi-tenant blade.

## References

- [Splunk Documentation: Splunk Add-on for Citrix NetScaler](https://docs.splunk.com/Documentation/AddOns/released/CitrixNetScaler/CitrixNetScaler)
- [Citrix ADC — SDX (multi-tenant platform)](https://docs.citrix.com/en-us/citrix-adc/)
