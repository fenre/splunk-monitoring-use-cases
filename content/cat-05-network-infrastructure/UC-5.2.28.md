<!-- AUTO-GENERATED from UC-5.2.28.json — DO NOT EDIT -->

---
id: "5.2.28"
title: "BGP Peering Status and Route Stability (Meraki MX)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.2.28 · BGP Peering Status and Route Stability (Meraki MX)

## Description

Ensures BGP peers remain established and routing remains stable for multi-ISP designs.

## Value

Ensures BGP peers remain established and routing remains stable for multi-ISP designs.

## Implementation

Monitor BGP event syslog. Alert on neighbor state changes.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
• Ensure the following data sources are available: `sourcetype=meraki type=security_event signature="*BGP*"`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Monitor BGP event syslog. Alert on neighbor state changes.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cisco_network sourcetype="meraki" type=security_event signature="*BGP*" (signature="*neighbor*" OR signature="*route*")
| stats count as bgp_event_count by bgp_neighbor, event_type
| where bgp_event_count > 5
```

Understanding this SPL

**BGP Peering Status and Route Stability (Meraki MX)** — Ensures BGP peers remain established and routing remains stable for multi-ISP designs.

Documented **Data sources**: `sourcetype=meraki type=security_event signature="*BGP*"`. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cisco_network; **sourcetype**: meraki. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=cisco_network, sourcetype="meraki". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by bgp_neighbor, event_type** so each row reflects one combination of those dimensions.
• Filters the current rows with `where bgp_event_count > 5` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
In the Meraki cloud dashboard, use the same organization, network, and time range as the search. Confirm the same events, site or appliance names, and policy context you see in the dashboard line up with Splunk.
Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: BGP peer status table; route change timeline; peering stability gauge.

## SPL

```spl
index=cisco_network sourcetype="meraki" type=security_event signature="*BGP*" (signature="*neighbor*" OR signature="*route*")
| stats count as bgp_event_count by bgp_neighbor, event_type
| where bgp_event_count > 5
```

## Visualization

BGP peer status table; route change timeline; peering stability gauge.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
