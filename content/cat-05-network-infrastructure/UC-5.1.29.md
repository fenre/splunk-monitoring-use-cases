<!-- AUTO-GENERATED from UC-5.1.29.json — DO NOT EDIT -->

---
id: "5.1.29"
title: "ARP Table Size Trending"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.1.29 · ARP Table Size Trending

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Capacity

*We help you know early when something looks wrong with arp table size trending so the team can act before it grows into a bigger outage.*

---

## Description

ARP table approaching hardware limits; can cause connectivity failures.

## Value

Network engineers trend ARP table sizes across routers to detect abnormal growth indicating large flat networks, scanning activity, or ARP storms that risk table exhaustion.

## Implementation

Poll ipNetToMediaTable (count rows) or parse `show ip arp` / `show arp` output via scripted input. Create lookup with device→max_arp (from vendor specs). Alert when utilization exceeds 70%.

## Detailed Implementation

### Prerequisites
* ARP table size data from SNMP or CLI scripted input. SNMP OID: ipNetToMediaEntry count, or `show arp | count` via scripted input. Data in `index=network` with SNMP or `sourcetype=network:arp:stats`.
* ARP table exhaustion causes devices to drop new ARP entries, breaking connectivity. Large ARP tables indicate large flat networks (L2 broadcast domains), scanning activity, or ARP storms.

### Step 1 — - Configure data collection
```
[script:///opt/splunk/etc/apps/network_mon/bin/arp_table_size.sh]
interval = 300
sourcetype = network:arp:stats
index = network

# arp_table_size.sh
#!/bin/bash
echo "device=$(hostname)"
arp_count=$(show ip arp | wc -l 2>/dev/null || arp -an | wc -l)
echo "arp_entries=$arp_count"
```
Verify:
```spl
index=network sourcetype="network:arp:stats" earliest=-4h | stats latest(arp_entries) by device
```

### Step 2 — - Create the search and alert

**Primary search -- ARP table size trending:**
```spl
index=network earliest=-7d
| eval arp_count=tonumber(coalesce(arp_entries, arp_table_size))
| eval device=coalesce(device, host, device_name)
| where isnotnull(arp_count)
| bin _time span=1h
| stats avg(arp_count) as avg_entries max(arp_count) as max_entries by _time, device
| eventstats avg(avg_entries) as baseline_avg stdev(avg_entries) as stdev_entries by device
| eval z_score=if(stdev_entries > 0, round((avg_entries - baseline_avg)/stdev_entries, 2), 0)
| eval severity=case(
    max_entries > 4000, "CRITICAL -- ARP table very large (>4000 entries)",
    z_score > 3, "WARNING -- abnormal ARP table growth",
    max_entries > 2000, "INFO -- ARP table elevated",
    1==1, "OK")
| where severity != "OK"
| table _time, device, avg_entries, max_entries, z_score, severity
| sort severity, -max_entries
```

### Step 3 — - Validate
(a) CLI: `show ip arp | count` or `show ip arp summary` -- current ARP table size.
(b) Check ARP timeout: `show ip arp timeout` -- default 4 hours on Cisco.
(c) Verify ARP table limit: hardware-dependent.

### Step 4 — - Operationalize
Dashboard ("Network -- ARP Table"):
* Row 1 -- Single-value: "Max ARP entries", "Devices > 2000 entries".
* Row 2 -- ARP table size timechart.

Alert: Critical (>4000 ARP entries): investigate cause.

### Step 5 — - Troubleshooting

* **Large flat L2 domain** -- All hosts in the broadcast domain generate ARP entries. Consider: subnet segmentation, VRFs, or moving to routed access layer.

* **ARP storm from scanning** -- Check for new entries from same source MAC. May indicate network scanner or worm. Apply DHCP snooping and DAI.

* **ARP timeout too long** -- Default 4 hours may keep stale entries. Consider reducing: `arp timeout <seconds>` on interface.

## SPL

```spl
index=network sourcetype=snmp:arp OR sourcetype=cisco:ios:arp
| eval arp_count=coalesce(arp_entries, arp_count, 0)
| stats latest(arp_count) as current_arp by host
| lookup arp_limit host OUTPUT max_arp
| eval util_pct=round(current_arp/max_arp*100,1)
| where util_pct > 70
| table host current_arp max_arp util_pct
```

## Visualization

Line chart (ARP count over time), Gauge (utilization), Table.

## Known False Positives

VMware vMotion, imaging carts, and conference room churn move MACs often. Baseline by VLAN before calling an attack.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
