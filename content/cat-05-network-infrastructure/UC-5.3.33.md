<!-- AUTO-GENERATED from UC-5.3.33.json — DO NOT EDIT -->

---
id: "5.3.33"
title: "Citrix SDX Platform Health (Partition Resources)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.3.33 · Citrix SDX Platform Health (Partition Resources)

## Description

Citrix NetScaler SDX hosts multiple isolated VPX instances. Platform health is about partition CPU and memory, hypervisor and VPX liveness, and out-of-band LOM, power, and cooling. A stressed partition throttles applications before obvious syslog noise; LOM, PSU, or fan alarms demand hardware attention before a blade fails.

## Value

Citrix NetScaler SDX hosts multiple isolated VPX instances. Platform health is about partition CPU and memory, hypervisor and VPX liveness, and out-of-band LOM, power, and cooling. A stressed partition throttles applications before obvious syslog noise; LOM, PSU, or fan alarms demand hardware attention before a blade fails.

## Implementation

Poll SNMP with SDX/MPX and ADC-specific OIDs into `citrix:netscaler:snmp`. Forward `citrix:netscaler:syslog` for hypervisor, VPX, and platform events. Enrich with asset tags for slot, data hall, and power feed. Page on high partition utilization versus entitlement, and on any hardware or LOM down events.

## Detailed Implementation

Prerequisites: SNMP v3 credentials and OIDs; syslog to index=netscaler; map partition_id to line-of-business and VPX list. Step 1: Configure data collection — Use TA transforms to normalize adc_partition_cpu_use_pct, sdx_name, and partition_id; throttle very chatty OIDs; keep clock sync between CMC, hypervisor, and guests. Step 2: Create the search and alert — Set CPU>85% and mem>90% to match VPX entitlements; treat any LOM/PSU/FAN critical alarm as sev-1 outside maintenance; start with sustained high CPU over 30m before tuning down. Step 3: Validate — After a VPX migration or CPU share change, run `index=netscaler sourcetype="citrix:netscaler:snmp" earliest=-1h | stats max(*) by sdx_name, partition_id` and compare to SDX management UI. Step 4: Operationalize — Datacenter SOP for RMA, update CMDB, plan capacity; if partitions stay saturated, escalate to Citrix platform and data center operations; add hardware alarm routing in alerts.conf.

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

## References

- [Splunk Documentation: Splunk Add-on for Citrix NetScaler](https://docs.splunk.com/Documentation/AddOns/released/CitrixNetScaler/CitrixNetScaler)
- [Citrix ADC — SDX (multi-tenant platform)](https://docs.citrix.com/en-us/citrix-adc/)
