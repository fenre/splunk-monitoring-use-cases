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

1. Enable the Summary Top Switches by Energy Usage input (TA v3+, OAuth scope switch:telemetry:read). The TA polls GET /organizations/{orgId}/summary/top/switches/byEnergyUsage daily and emits the org's top 10 switches with usage.total (kWh) and usage.percentage. 2. For per-switch hourly history enable the Switch Power History input (TA v3.2+) which polls .../summary/switch/powerHistory and emits intervals[].usage.total. 3. Per-PoE-port wattage is not exposed; if you need it use the device-level webhook 'switch port poe overcurrent' or fall back to SNMP polling.

## Detailed Implementation

### Prerequisites
- Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
- Ensure the following data sources are available: Splunk_TA_cisco_meraki (Splunkbase #5580): Summary Top Switches by Energy Usage input (sourcetype=meraki:summarytopswitchesbyenergyusage, daily) and optionally the Switch Power History input (sourcetype=meraki:summaryswitchpowerhistory) for per-switch hourly trends..
- For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

### Step 1 — Configure data collection
1. Enable the Summary Top Switches by Energy Usage input (TA v3+, OAuth scope switch:telemetry:read). The TA polls GET /organizations/{orgId}/summary/top/switches/byEnergyUsage daily and emits the org's top 10 switches with usage.total (kWh) and usage.percentage. 2. For per-switch hourly history enable the Switch Power History input (TA v3.2+) which polls .../summary/switch/powerHistory and emits intervals[].usage.total. 3. Per-PoE-port wattage is not exposed; if you need it use the device-level…

### Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=meraki sourcetype="meraki:summarytopswitchesbyenergyusage" earliest=-30d
| stats latest(usage.total) as total_kwh, latest(usage.percentage) as pct_of_org
         by serial, name, network.name, model
| eval avg_watts = round(total_kwh*1000/(30*24), 1)
| sort - total_kwh
| head 20
```

#### Understanding this SPL

**Power over Ethernet (PoE) Consumption Tracking (Meraki MS)** — Operations teams track Meraki MS per-port and total PoE power consumption, identifying switches approaching PoE budget limits and planning capacity for powered device deployments.

Documented **Data sources**: Splunk_TA_cisco_meraki (Splunkbase #5580): Summary Top Switches by Energy Usage input (sourcetype=meraki:summarytopswitchesbyenergyusage, daily) and optionally the Switch Power History input (sourcetype=meraki:summaryswitchpowerhistory) for per-switch hourly trends. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: meraki; **sourcetype**: meraki:summarytopswitchesbyenergyusage. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

- Scopes the data: index=meraki, sourcetype="meraki:summarytopswitchesbyenergyusage", time bounds. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
- `stats` rolls up events into metrics; results are split **by serial, name, network.name, model** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
- `eval` defines or adjusts **avg_watts** — often to normalize units, derive a ratio, or prepare for thresholds.
- Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
- Limits the number of rows with `head`.


### Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

### Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Gauge showing power utilization percentage; stacked bar of PoE by port; capacity dashboard.

## SPL

```spl
index=meraki sourcetype="meraki:summarytopswitchesbyenergyusage" earliest=-30d
| stats latest(usage.total) as total_kwh, latest(usage.percentage) as pct_of_org
         by serial, name, network.name, model
| eval avg_watts = round(total_kwh*1000/(30*24), 1)
| sort - total_kwh
| head 20
```

## Visualization

Gauge showing power utilization percentage; stacked bar of PoE by port; capacity dashboard.

## Known False Positives

AP reboots, phone bulk restarts, and new cameras shift PoE load. Scheduled refresh windows can look like a budget breach.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
