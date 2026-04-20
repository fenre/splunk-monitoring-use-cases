---
id: "5.1.37"
title: "Power over Ethernet (PoE) Consumption Tracking (Meraki MS)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.1.37 · Power over Ethernet (PoE) Consumption Tracking (Meraki MS)

## Description

Monitors PoE power allocation to prevent over-subscription and ensure sufficient power for all devices.

## Value

Monitors PoE power allocation to prevent over-subscription and ensure sufficient power for all devices.

## Implementation

Pull poe_consumption metrics from MS device API. Aggregate by switch.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
• Ensure the following data sources are available: `sourcetype=meraki:api device_type=MS`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Pull poe_consumption metrics from MS device API. Aggregate by switch.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cisco_network sourcetype="meraki:api" device_type=MS poe_consumption=*
| stats sum(poe_consumption) as total_power_watts, avg(poe_consumption) as avg_power by switch_name
| eval power_capacity_pct=round(total_power_watts*100/1000, 2)
| where power_capacity_pct > 80
```

Understanding this SPL

**Power over Ethernet (PoE) Consumption Tracking (Meraki MS)** — Monitors PoE power allocation to prevent over-subscription and ensure sufficient power for all devices.

Documented **Data sources**: `sourcetype=meraki:api device_type=MS`. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cisco_network; **sourcetype**: meraki:api. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=cisco_network, sourcetype="meraki:api". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by switch_name** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **power_capacity_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where power_capacity_pct > 80` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Gauge showing power utilization percentage; stacked bar of PoE by port; capacity dashboard.

## SPL

```spl
index=cisco_network sourcetype="meraki:api" device_type=MS poe_consumption=*
| stats sum(poe_consumption) as total_power_watts, avg(poe_consumption) as avg_power by switch_name
| eval power_capacity_pct=round(total_power_watts*100/1000, 2)
| where power_capacity_pct > 80
```

## Visualization

Gauge showing power utilization percentage; stacked bar of PoE by port; capacity dashboard.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
