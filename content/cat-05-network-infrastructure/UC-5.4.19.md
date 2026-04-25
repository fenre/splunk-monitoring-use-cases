<!-- AUTO-GENERATED from UC-5.4.19.json — DO NOT EDIT -->

---
id: "5.4.19"
title: "Band Steering Effectiveness Assessment (Meraki MR)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.4.19 · Band Steering Effectiveness Assessment (Meraki MR)

## Description

Measures effectiveness of steering clients from 2.4GHz to 5GHz bands to reduce congestion and improve performance.

## Value

Measures effectiveness of steering clients from 2.4GHz to 5GHz bands to reduce congestion and improve performance.

## Implementation

Query clients API to get current band distribution. Compare against expected ratio for band steering policy.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
• Ensure the following data sources are available: `sourcetype=meraki:api`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Query clients API to get current band distribution. Compare against expected ratio for band steering policy.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cisco_network sourcetype="meraki:api"
| stats count as client_count by band
| eval band_ratio=round(client_count*100/sum(client_count), 2)
| fields band, client_count, band_ratio
```

Understanding this SPL

**Band Steering Effectiveness Assessment (Meraki MR)** — Measures effectiveness of steering clients from 2.4GHz to 5GHz bands to reduce congestion and improve performance.

Documented **Data sources**: `sourcetype=meraki:api`. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cisco_network; **sourcetype**: meraki:api. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=cisco_network, sourcetype="meraki:api". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by band** so each row reflects one combination of those dimensions.
• `eval` defines or adjusts **band_ratio** — often to normalize units, derive a ratio, or prepare for thresholds.
• Keeps or drops fields with `fields` to shape columns and size.


Step 3 — Validate
Open the Cisco Meraki Dashboard (organization or network scope, under Monitor as appropriate) and compare AP, client, security, or flow totals to the search for the same window. Spot-check a few device names, SSIDs, or MAC addresses against what you see live.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Gauge showing 5GHz percentage; pie chart of band distribution; trend line showing steering progress.

## SPL

```spl
index=cisco_network sourcetype="meraki:api"
| stats count as client_count by band
| eval band_ratio=round(client_count*100/sum(client_count), 2)
| fields band, client_count, band_ratio
```

## Visualization

Gauge showing 5GHz percentage; pie chart of band distribution; trend line showing steering progress.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
