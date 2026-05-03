<!-- AUTO-GENERATED from UC-5.1.34.json — DO NOT EDIT -->

---
id: "5.1.34"
title: "PoE Power Budget Utilization"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.1.34 · PoE Power Budget Utilization

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Capacity

*We help you know early when something looks wrong with poe power budget utilization so the team can act before it grows into a bigger outage.*

---

## Description

Power over Ethernet budget approaching capacity per switch.

## Value

Operations teams trend PoE power budget utilization over 30 days to project capacity exhaustion and plan PoE infrastructure expansion before powered devices are denied power.

## Implementation

Poll POWER-ETHERNET-MIB (pethMainPsePower, pethMainPseConsumptionPower) every 300s. Alert when utilization exceeds 80%. Track per PSE unit on modular switches.

## Detailed Implementation

### Prerequisites
* PoE power utilization trending data from SNMP. Extends UC-5.1.19 with capacity planning focus. Key SNMP: pethMainPseConsumptionPower over time, per-port cpeExtPdStatsPower.
* PoE budget utilization trending: tracks power consumption growth over weeks/months to predict when additional PoE capacity will be needed, particularly as IoT devices and 802.3bt high-power devices proliferate.

### Step 1 — - Configure data collection
```
# Same SNMP polling as UC-5.1.19
# Ensure data retained > 30 days for capacity trending
```
Verify:
```spl
index=network earliest=-30d
| eval poe_watts=tonumber(coalesce(pethMainPseConsumptionPower, poe_watts_used))
| where isnotnull(poe_watts)
| bin _time span=1d | stats avg(poe_watts) by _time, host
```

### Step 2 — - Create the search and alert

**Primary search -- PoE budget utilization trending:**
```spl
index=network earliest=-30d
| eval poe_watts=tonumber(coalesce(pethMainPseConsumptionPower, poe_watts_used))
| eval poe_budget=tonumber(coalesce(poe_watts_budget, power_budget))
| eval device=coalesce(host, device_name)
| where isnotnull(poe_watts)
| bin _time span=1d
| stats avg(poe_watts) as avg_watts max(poe_watts) as peak_watts latest(poe_budget) as budget by _time, device
| eval util_pct=if(budget > 0, round(100*avg_watts/budget, 1), null())
| eventstats first(avg_watts) as start_watts last(avg_watts) as end_watts by device
| eval growth_rate=round((end_watts - start_watts)/30, 1)
| eval days_to_capacity=if(growth_rate > 0 AND isnotnull(budget), round((budget - end_watts)/growth_rate), null())
| eval severity=case(
    util_pct > 85, "WARNING -- PoE utilization at ".util_pct."% (near capacity)",
    days_to_capacity < 90 AND days_to_capacity > 0, "INFO -- PoE capacity exhaustion projected in ".days_to_capacity." days",
    growth_rate > 5, "INFO -- PoE consumption growing at ".growth_rate."W/day",
    1==1, "OK")
| where severity != "OK"
| dedup device sortby -_time
| table device, end_watts, budget, util_pct, growth_rate, days_to_capacity, severity
| sort severity, days_to_capacity
```

### Step 3 — - Validate
(a) CLI: `show power inline` -- current per-port and total consumption.
(b) Identify high-power devices: 802.3bt devices consuming 60-90W.
(c) Plan for new device deployments and their PoE requirements.

### Step 4 — - Operationalize
Dashboard ("Network -- PoE Capacity Planning"):
* Row 1 -- Single-value: "Switches > 85% PoE", "Fastest growing", "Days to capacity".
* Row 2 -- PoE utilization trend timechart.

Alert: Warning (PoE utilization > 85%): plan capacity expansion.

### Step 5 — - Troubleshooting

* **Approaching capacity** -- Options: (1) add external PoE power supply module, (2) deploy PoE injectors for high-power devices, (3) upgrade switch to model with higher PoE budget, (4) redistribute devices across switches.

* **Sudden capacity increase** -- New high-power devices (802.3bt cameras, APs) may consume 30-90W each. Plan PoE budget before deployment.

* **Growth projection inaccurate** -- Seasonal patterns (conference room usage, heating) may skew trends. Analyze by time-of-day and day-of-week for accurate forecasting.

## SPL

```spl
index=network sourcetype=snmp:poe
| eval util_pct=round(pethMainPseConsumptionPower/pethMainPsePower*100,1)
| where pethMainPseOperStatus="on" AND util_pct > 80
| stats latest(util_pct) as poe_util, latest(pethMainPseConsumptionPower) as used_w, latest(pethMainPsePower) as total_w by host
| table host poe_util used_w total_w
```

## Visualization

Gauge (utilization), Table (host, used, total), Line chart.

## Known False Positives

AP reboots, phone bulk restarts, and new cameras shift PoE load. Scheduled refresh windows can look like a budget breach.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
