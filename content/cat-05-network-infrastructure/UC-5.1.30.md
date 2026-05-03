<!-- AUTO-GENERATED from UC-5.1.30.json — DO NOT EDIT -->

---
id: "5.1.30"
title: "MAC Address Table Capacity"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.1.30 · MAC Address Table Capacity

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Capacity

*We help you know early when something looks wrong with mac address table capacity so the team can act before it grows into a bigger outage.*

---

## Description

CAM table utilization on switches approaching hardware limits.

## Value

Operations teams monitor MAC address table capacity across switches, detecting CAM table exhaustion that causes unicast flooding, performance degradation, and security exposure.

## Implementation

Poll dot1qTpFdbTable (count) or parse `show mac address-table count`. Create lookup with switch model→max_mac. Alert when CAM utilization exceeds 75%.

## Detailed Implementation

### Prerequisites
* MAC address table capacity data from SNMP or CLI. SNMP OID: dot1dTpFdbEntry count. CLI: `show mac address-table count`. Data in `index=network`.
* MAC table exhaustion: when the CAM table fills, the switch begins flooding unicast frames to all ports (like a hub), causing performance degradation and security risks (traffic visible to unintended recipients).

### Step 1 — - Configure data collection
```
[script:///opt/splunk/etc/apps/network_mon/bin/mac_table_stats.sh]
interval = 300
sourcetype = network:mac:stats
index = network
```
Verify:
```spl
index=network sourcetype="network:mac:stats" earliest=-4h | stats latest(mac_count) latest(mac_limit) by device
```

### Step 2 — - Create the search and alert

**Primary search -- MAC table capacity monitoring:**
```spl
index=network earliest=-4h
| eval mac_count=tonumber(coalesce(mac_count, mac_entries, dot1dTpFdbTableSize))
| eval mac_limit=tonumber(coalesce(mac_limit, mac_table_size, cam_table_size))
| eval device=coalesce(device, host, device_name)
| where isnotnull(mac_count)
| eval mac_pct=if(isnotnull(mac_limit) AND mac_limit > 0, round(100*mac_count/mac_limit, 1), null())
| bin _time span=5m
| stats latest(mac_count) as count latest(mac_limit) as limit latest(mac_pct) as util_pct by _time, device
| eval severity=case(
    util_pct > 90, "CRITICAL -- MAC table near capacity (".util_pct."%)",
    util_pct > 75, "WARNING -- MAC table at ".util_pct."%",
    count > 8000, "INFO -- large MAC table",
    1==1, "OK")
| where severity != "OK"
| table _time, device, count, limit, util_pct, severity
| sort severity, -util_pct
```

### Step 3 — - Validate
(a) CLI: `show mac address-table count` -- current count and limit per VLAN.
(b) CLI: `show platform resource utilization` (Cisco) -- check TCAM usage.
(c) Identify top VLANs: `show mac address-table count vlan <id>`.

### Step 4 — - Operationalize
Dashboard ("Network -- MAC Table Capacity"):
* Row 1 -- Single-value: "Switches > 75% MAC", "Maximum utilization (%)".
* Row 2 -- MAC table utilization timechart.

Alert: Critical (>90% MAC table utilization): flooding risk.

### Step 5 — - Troubleshooting

* **MAC table filling up** -- Check for MAC flooding attack. Enable port security: `switchport port-security maximum <n>`. Investigate unknown MAC addresses.

* **Large VLAN spanning many switches** -- Reduce broadcast domain size. Consider VLAN segmentation or routed access design.

* **MAC flapping consuming table** -- Same MAC on multiple ports uses multiple entries. Fix the root cause (UC-5.1.12).

## SPL

```spl
index=network sourcetype=snmp:bridge OR sourcetype=cisco:ios:mac
| eval mac_count=coalesce(fdb_entries, mac_count, 0)
| stats latest(mac_count) as current_mac by host
| lookup mac_limit host OUTPUT max_mac
| eval util_pct=round(current_mac/max_mac*100,1)
| where util_pct > 75
| table host current_mac max_mac util_pct
```

## Visualization

Line chart (MAC count over time), Gauge, Table.

## Known False Positives

VMware vMotion, imaging carts, and conference room churn move MACs often. Baseline by VLAN before calling an attack.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
