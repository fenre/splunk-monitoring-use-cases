<!-- AUTO-GENERATED from UC-5.1.47.json — DO NOT EDIT -->

---
id: "5.1.47"
title: "Trunk Link Utilization and Performance (Meraki MS)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.1.47 · Trunk Link Utilization and Performance (Meraki MS)

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance

*We help you know early when something looks wrong with trunk link utilization and performance so the team can act before it grows into a bigger outage.*

---

## Description

Monitors inter-switch and uplink trunk utilization to identify bandwidth constraints.

## Value

Network engineers monitor Meraki MS trunk link utilization, detecting inter-switch uplink saturation that impacts all downstream VLANs and devices.

## Implementation

Query MS API for trunk port utilization. Alert on sustained high utilization.

## Detailed Implementation

### Prerequisites
* Meraki MS trunk link utilization data from API. Data in `index=meraki` with `sourcetype=meraki:api:switch:portstatus`. Key fields: ports configured as trunk, traffic counters per port.
* Trunk links: inter-switch uplinks carrying multiple VLANs. Trunk saturation affects all VLANs and all devices behind the trunk. Critical for data center and distribution layer monitoring.

### Step 1 — - Configure data collection
```
# Same API polling as UC-5.1.36
# Filter for trunk ports in analysis
```
Verify:
```spl
index=meraki sourcetype="meraki:api:switch:ports" earliest=-4h
| where type="trunk"
| stats count by host, portId
```

### Step 2 — - Create the search and alert

**Primary search -- Trunk link utilization:**
```spl
index=meraki (sourcetype="meraki:api:switch:portstatus" OR sourcetype="meraki:api:switch:ports") earliest=-4h
| where type="trunk" OR match(port_type, "(?i)trunk")
| eval port=coalesce(portId, port_id)
| eval speed_mbps=case(match(speed, "(?i)10 G"), 10000, match(speed, "(?i)1 G"), 1000, 1==1, 1000)
| eval sent_kbps=tonumber(coalesce(usageInKb.sent, sent_kbps))/300
| eval recv_kbps=tonumber(coalesce(usageInKb.recv, recv_kbps))/300
| eval total_mbps=round((sent_kbps + recv_kbps)/1024, 2)
| eval util_pct=round(100*total_mbps/speed_mbps, 1)
| eval device=coalesce(serial, host)
| lookup meraki_networks.csv serial AS device OUTPUT network_name
| bin _time span=5m
| stats avg(util_pct) as avg_util max(util_pct) as max_util avg(total_mbps) as avg_mbps by _time, network_name, device, port
| eval severity=case(
    max_util > 85, "CRITICAL -- trunk port ".port." near saturation",
    max_util > 70, "WARNING -- trunk port ".port." high utilization",
    1==1, "OK")
| where severity != "OK"
| table _time, network_name, device, port, avg_mbps, avg_util, max_util, severity
| sort severity, -max_util
```

### Step 3 — - Validate
(a) Dashboard: Switch > Switch ports -- filter for trunk ports.
(b) Check LACP/link aggregation status if applicable.
(c) Verify trunk allowed VLANs are properly restricted.

### Step 4 — - Operationalize
Dashboard ("Meraki MS -- Trunk Utilization"):
* Row 1 -- Single-value: "Trunk ports > 70%", "Peak trunk utilization (%)".
* Row 2 -- Trunk utilization timechart.

Alert: Warning (trunk > 85%): capacity planning needed.

### Step 5 — - Troubleshooting

* **Trunk saturated** -- Options: (1) add link aggregation members, (2) upgrade to higher speed (1G → 10G), (3) redistribute VLANs across multiple trunks.

* **Asymmetric trunk utilization** -- Check LACP hashing algorithm. May need to adjust hash policy for better distribution.

* **Single trunk failure in LAG** -- Remaining members absorb traffic. May push utilization over threshold. Replace failed member.

## SPL

```spl
index=cisco_network sourcetype="meraki:api" device_type=MS port_type="trunk"
| stats avg(port_utilization) as avg_trunk_util, max(port_utilization) as peak_util by switch_name, port_id
| where peak_util > 70
| sort - peak_util
```

## Visualization

Trunk link utilization heatmap; timeline showing peak demand; capacity planning chart.

## Known False Positives

Short bursts during backups, patch pushes, or video calls can approach thresholds without an outage. Match alerts to business hours and known batch jobs.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
