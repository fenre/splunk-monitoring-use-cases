<!-- AUTO-GENERATED from UC-5.1.37.json — DO NOT EDIT -->

---
id: "5.1.37"
title: "Power over Ethernet (PoE) Consumption Tracking (Meraki MS)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.1.37 · Power over Ethernet (PoE) Consumption Tracking (Meraki MS)

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Fault

*We help you know early when something looks wrong with power over ethernet so the team can act before it grows into a bigger outage.*

---

## Description

Monitors PoE power allocation to prevent over-subscription and ensure sufficient power for all devices.

## Value

Operations teams track Meraki MS per-port and total PoE power consumption, identifying switches approaching PoE budget limits and planning capacity for powered device deployments.

## Implementation

Pull poe_consumption metrics from MS device API. Aggregate by switch.

## Detailed Implementation

### Prerequisites
* Meraki MS PoE data from Dashboard API. Data in `index=meraki` with `sourcetype=meraki:api:switch:portstatus`. Key fields: `powerUsageInWh`, `portId`, `poeEnabled`.
* Meraki MS PoE: dashboard provides per-port PoE consumption. API endpoint: `GET /devices/{serial}/switch/ports/statuses` includes `powerUsageInWh` per port. Switch models support 802.3af (15.4W), 802.3at (30W), or 802.3bt (60/90W).

### Step 1 — - Configure data collection
```
# Same API polling as UC-5.1.36
# PoE data is included in port status response
```
Verify:
```spl
index=meraki sourcetype="meraki:api:switch:portstatus" earliest=-4h
| where isnotnull(powerUsageInWh) AND tonumber(powerUsageInWh) > 0
| stats sum(powerUsageInWh) by host
```

### Step 2 — - Create the search and alert

**Primary search -- PoE consumption tracking:**
```spl
index=meraki sourcetype="meraki:api:switch:portstatus" earliest=-24h
| eval port=coalesce(portId, port_id)
| eval poe_wh=tonumber(coalesce(powerUsageInWh, poe_watts))
| eval device=coalesce(serial, host)
| lookup meraki_networks.csv serial AS device OUTPUT network_name, site_name
| where isnotnull(poe_wh) AND poe_wh > 0
| bin _time span=1h
| stats sum(poe_wh) as total_wh dc(port) as powered_ports by _time, network_name, device
| eval total_watts=round(total_wh, 1)
| eval severity=case(
    powered_ports > 40, "INFO -- high PoE port count (".powered_ports." ports)",
    total_watts > 500, "WARNING -- high total PoE consumption",
    1==1, "OK")
| where severity != "OK"
| table _time, network_name, device, powered_ports, total_watts, severity
| sort severity, -total_watts
```

### Step 3 — - Validate
(a) Dashboard: Switch > Switch ports -- check PoE per port.
(b) Dashboard: Network-wide > Summary -- check PoE budget.
(c) Verify switch model PoE budget capacity.

### Step 4 — - Operationalize
Dashboard ("Meraki MS -- PoE Consumption"):
* Row 1 -- Single-value: "Powered ports", "Total PoE (W)", "Highest port (W)".
* Row 2 -- PoE consumption timechart.

### Step 5 — - Troubleshooting

* **PoE budget exceeded** -- Meraki auto-prioritizes ports. Lower-priority ports may lose power. Set port priority in Dashboard.

* **Device not receiving power** -- Check: (1) PoE enabled on port, (2) device supports PoE, (3) cable quality (PoE requires all 4 pairs for 802.3at/bt).

* **Unexpected high consumption** -- Faulty PD can draw excessive power. Check per-port consumption in Dashboard.

## SPL

```spl
index=cisco_network sourcetype="meraki:api" device_type=MS poe_consumption=*
| stats sum(poe_consumption) as total_power_watts, avg(poe_consumption) as avg_power by switch_name
| eval power_capacity_pct=round(total_power_watts*100/1000, 2)
| where power_capacity_pct > 80
```

## Visualization

Gauge showing power utilization percentage; stacked bar of PoE by port; capacity dashboard.

## Known False Positives

AP reboots, phone bulk restarts, and new cameras shift PoE load. Scheduled refresh windows can look like a budget breach.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
