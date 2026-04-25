<!-- AUTO-GENERATED from UC-5.4.3.json — DO NOT EDIT -->

---
id: "5.4.3"
title: "Channel Utilization"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.4.3 · Channel Utilization

## Description

High channel utilization degrades wireless performance. Identifies congested APs needing channel changes or additional coverage.

## Value

High channel utilization degrades wireless performance. Identifies congested APs needing channel changes or additional coverage.

## Implementation

Poll Meraki RF statistics API or WLC SNMP. Track per-AP channel utilization. Alert when >60% (2.4GHz) or >50% (5GHz).

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Meraki API, WLC SNMP.
• Ensure the following data sources are available: Meraki API, SNMP (CISCO-DOT11-IF-MIB).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll Meraki RF statistics API or WLC SNMP. Track per-AP channel utilization. Alert when >60% (2.4GHz) or >50% (5GHz).

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network sourcetype="meraki:api"
| stats avg(channel_utilization) as util_pct by ap_name, channel, band
| where util_pct > 60 | sort -util_pct
```

Understanding this SPL

**Channel Utilization** — High channel utilization degrades wireless performance. Identifies congested APs needing channel changes or additional coverage.

Documented **Data sources**: Meraki API, SNMP (CISCO-DOT11-IF-MIB). **App/TA** (typical add-on context): Meraki API, WLC SNMP. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: meraki:api. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype="meraki:api". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by ap_name, channel, band** so each row reflects one combination of those dimensions.
• Filters the current rows with `where util_pct > 60` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Open the Cisco Meraki Dashboard (organization or network scope, under Monitor as appropriate) and compare AP, client, security, or flow totals to the search for the same window. Spot-check a few device names, SSIDs, or MAC addresses against what you see live.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Heatmap (APs by utilization), Table, Line chart (trending).

## SPL

```spl
index=network sourcetype="meraki:api"
| stats avg(channel_utilization) as util_pct by ap_name, channel, band
| where util_pct > 60 | sort -util_pct
```

## Visualization

Heatmap (APs by utilization), Table, Line chart (trending).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
