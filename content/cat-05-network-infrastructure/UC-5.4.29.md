<!-- AUTO-GENERATED from UC-5.4.29.json — DO NOT EDIT -->

---
id: "5.4.29"
title: "Mesh Network Link Quality and Backhaul Health (Meraki MR)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.4.29 · Mesh Network Link Quality and Backhaul Health (Meraki MR)

## Description

Monitors wireless mesh backhaul links to ensure reliability of remote AP connections.

## Value

Monitors wireless mesh backhaul links to ensure reliability of remote AP connections.

## Implementation

Query MR device API for mesh_link_quality metric. Alert on degraded quality (<70%).

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
• Ensure the following data sources are available: `sourcetype=meraki:api` (MR), `sourcetype=meraki` (events, e.g. `type=security_event`).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Query MR device API for mesh_link_quality metric. Alert on degraded quality (<70%).

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cisco_network sourcetype="meraki:api" device_type=MR mesh_link_quality=*
| stats avg(mesh_link_quality) as avg_link_quality by ap_name, upstream_ap
| where avg_link_quality < 70
| sort avg_link_quality
```

Understanding this SPL

**Mesh Network Link Quality and Backhaul Health (Meraki MR)** — Monitors wireless mesh backhaul links to ensure reliability of remote AP connections.

Documented **Data sources**: `sourcetype=meraki:api` (MR), `sourcetype=meraki` (events, e.g. `type=security_event`). **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cisco_network; **sourcetype**: meraki:api. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=cisco_network, sourcetype="meraki:api". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by ap_name, upstream_ap** so each row reflects one combination of those dimensions.
• Filters the current rows with `where avg_link_quality < 70` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Open the Cisco Meraki Dashboard (organization or network scope, under Monitor as appropriate) and compare AP, client, security, or flow totals to the search for the same window. Spot-check a few device names, SSIDs, or MAC addresses against what you see live.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Network topology showing link quality; color-coded links; detail table with metrics.

## SPL

```spl
index=cisco_network sourcetype="meraki:api" device_type=MR mesh_link_quality=*
| stats avg(mesh_link_quality) as avg_link_quality by ap_name, upstream_ap
| where avg_link_quality < 70
| sort avg_link_quality
```

## Visualization

Network topology showing link quality; color-coded links; detail table with metrics.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
