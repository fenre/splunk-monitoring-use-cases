<!-- AUTO-GENERATED from UC-5.6.15.json — DO NOT EDIT -->

---
id: "5.6.15"
title: "DHCP Pool Exhaustion and Address Allocation Issues (Meraki)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.6.15 · DHCP Pool Exhaustion and Address Allocation Issues (Meraki)

## Description

Alerts when DHCP pools approach depletion to prevent clients from obtaining IP addresses.

## Value

Alerts when DHCP pools approach depletion to prevent clients from obtaining IP addresses.

## Implementation

Query appliance API for DHCP metrics by VLAN. Alert on >85% allocation.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
• Ensure the following data sources are available: `sourcetype=meraki:api`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Query appliance API for DHCP metrics by VLAN. Alert on >85% allocation.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cisco_network sourcetype="meraki:api" dhcp_pool=*
| stats latest(addresses_available) as available_ips, latest(pool_size) as total_pool by vlan_id
| eval allocation_pct=round((total_pool-available_ips)*100/total_pool, 2)
| where allocation_pct > 85
```

Understanding this SPL

**DHCP Pool Exhaustion and Address Allocation Issues (Meraki)** — Alerts when DHCP pools approach depletion to prevent clients from obtaining IP addresses.

Documented **Data sources**: `sourcetype=meraki:api`. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cisco_network; **sourcetype**: meraki:api. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=cisco_network, sourcetype="meraki:api". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by vlan_id** so each row reflects one combination of those dimensions.
• `eval` defines or adjusts **allocation_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where allocation_pct > 85` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Open the Cisco Meraki Dashboard (organization or network scope, under Monitor as appropriate) and compare AP, client, security, or flow totals to the search for the same window. Spot-check a few device names, SSIDs, or MAC addresses against what you see live.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: DHCP pool gauge per VLAN; timeline of pool usage; alert dashboard.

## SPL

```spl
index=cisco_network sourcetype="meraki:api" dhcp_pool=*
| stats latest(addresses_available) as available_ips, latest(pool_size) as total_pool by vlan_id
| eval allocation_pct=round((total_pool-available_ips)*100/total_pool, 2)
| where allocation_pct > 85
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Network_Sessions.DHCP
  by DHCP.mac DHCP.ip DHCP.action span=1h
| where count>0
| sort -count
```

## Visualization

DHCP pool gauge per VLAN; timeline of pool usage; alert dashboard.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
