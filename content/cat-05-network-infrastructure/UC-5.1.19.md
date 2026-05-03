<!-- AUTO-GENERATED from UC-5.1.19.json — DO NOT EDIT -->

---
id: "5.1.19"
title: "PoE Power Budget Monitoring"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.1.19 · PoE Power Budget Monitoring

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Capacity, Fault

*We help you know early when something looks wrong with poe power budget monitoring so the team can act before it grows into a bigger outage.*

---

## Description

PoE budget exhaustion causes powered devices (IP phones, APs, cameras) to lose power. Proactive monitoring prevents unplanned device outages.

## Value

Operations teams monitor PoE power budget utilization across switches, preventing power denial to IP phones, wireless APs, and cameras when budget capacity is exhausted.

## Implementation

Poll POWER-ETHERNET-MIB every 300s. Track per-switch PoE budget utilization. Alert at 80% utilization. Trend over time to plan for additional PoE capacity.

## Detailed Implementation

### Prerequisites
* PoE power budget data from SNMP or syslog. Data in `index=network` with SNMP data or syslog. Key SNMP OIDs: pethMainPseConsumptionPower (.1.3.6.1.2.1.105.1.3.1.1.4), pethMainPseOperStatus. Key syslog: Cisco `%ILPOWER-5-POWER_GRANTED`, `%ILPOWER-3-CONTROLLER_ERR`.
* PoE budget: each switch has a finite power budget (total watts) shared across all PoE ports. When budget is exceeded, lower-priority devices are denied power. Monitoring budget utilization prevents IP phones, APs, and cameras from losing power.

### Step 1 — - Configure data collection
```
# SNMP polling for PoE data
[snmp_poe]
interval = 300
sourcetype = snmp:poe
index = network
# OIDs: pethMainPseConsumptionPower, pethMainPseUsageThreshold
# Cisco-specific: cpeExtPdStatsEntry

# Cisco syslog: PoE events are logged automatically
```
Verify:
```spl
index=network earliest=-24h
| where match(_raw, "(?i)ILPOWER|PoE|power.*inline|power.*granted|power.*denied|power.*budget")
| stats count by host
```

### Step 2 — - Create the search and alert

**Primary search -- PoE power budget monitoring:**
```spl
index=network earliest=-4h
| eval poe_consumed=tonumber(coalesce(pethMainPseConsumptionPower, poe_watts_used, power_consumed))
| eval poe_available=tonumber(coalesce(poe_watts_available, power_available))
| eval poe_budget=tonumber(coalesce(poe_watts_budget, power_budget))
| eval device=coalesce(host, device_name)
| where isnotnull(poe_consumed) OR match(_raw, "(?i)ILPOWER|power.*denied|power.*budget")
| eval budget_total=coalesce(poe_budget, poe_consumed + poe_available)
| eval budget_pct=if(budget_total > 0, round(100*poe_consumed/budget_total, 1), null())
| eval power_denied=if(match(_raw, "(?i)power.*denied|ILPOWER.*DENIED"), 1, 0)
| bin _time span=5m
| stats latest(poe_consumed) as watts_used latest(budget_total) as watts_budget latest(budget_pct) as budget_pct sum(power_denied) as denials by _time, device
| eval severity=case(
    denials > 0, "CRITICAL -- PoE power denied to device(s)",
    budget_pct > 90, "WARNING -- PoE budget near capacity (".budget_pct."%)",
    budget_pct > 80, "INFO -- PoE budget utilization elevated",
    1==1, "OK")
| where severity != "OK"
| table _time, device, watts_used, watts_budget, budget_pct, denials, severity
| sort severity, -budget_pct
```

### Step 3 — - Validate
(a) CLI: `show power inline` -- check per-port PoE consumption and total budget.
(b) CLI: `show power inline module <x>` -- per-module power summary.
(c) Verify priority settings: `power inline port priority high` on critical devices.

### Step 4 — - Operationalize
Dashboard ("Network -- PoE Budget"):
* Row 1 -- Single-value: "Switches > 80% PoE", "Power denied events", "Total watts consumed".
* Row 2 -- PoE budget utilization timechart.

Alert: Critical (PoE power denied): device(s) without power, investigate.

### Step 5 — - Troubleshooting

* **Power denied** -- Budget exceeded. Options: (1) set PoE priority on critical devices (phones, APs), (2) add PoE power supply module (if available), (3) move devices to switch with available budget, (4) use PoE injectors for high-power devices.

* **Unexpected high consumption** -- Check `show power inline` for devices consuming more than expected. Faulty PD (Powered Device) can draw excessive current.

* **PoE budget planning** -- Calculate: total device power requirements vs switch PoE budget. Reserve headroom for powered device peak draw. Consider 802.3bt (60W/90W) requirements.

## SPL

```spl
index=network sourcetype="snmp:poe"
| stats latest(pethMainPseOperStatus) as status, latest(pethMainPsePower) as total_watts, latest(pethMainPseConsumptionPower) as used_watts by host
| eval utilization_pct=round(used_watts/total_watts*100,1)
| where utilization_pct > 80 | sort -utilization_pct
```

## Visualization

Gauge (per switch), Line chart (utilization trending), Table (switch, budget, used, remaining).

## Known False Positives

AP reboots, phone bulk restarts, and new cameras shift PoE load. Scheduled refresh windows can look like a budget breach.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
