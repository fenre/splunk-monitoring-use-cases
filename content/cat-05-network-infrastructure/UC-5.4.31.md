---
id: "5.4.31"
title: "WiFi Geolocation and Location Analytics (Meraki MR)"
criticality: "low"
splunkPillar: "Observability"
---

# UC-5.4.31 · WiFi Geolocation and Location Analytics (Meraki MR)

## Description

Uses Cisco Meraki location services to track foot traffic patterns and heat maps in physical spaces.

## Value

Uses Cisco Meraki location services to track foot traffic patterns and heat maps in physical spaces.

## Implementation

Use Meraki location API to get AP-based location estimates. Map to floor/zone.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
• Ensure the following data sources are available: `sourcetype=meraki:api location_data=*`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Use Meraki location API to get AP-based location estimates. Map to floor/zone.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cisco_network sourcetype="meraki:api" ap_name=*
| stats count as foot_traffic by ap_name, floor
| geom geo_from_metric lat, lon
```

Understanding this SPL

**WiFi Geolocation and Location Analytics (Meraki MR)** — Uses Cisco Meraki location services to track foot traffic patterns and heat maps in physical spaces.

Documented **Data sources**: `sourcetype=meraki:api location_data=*`. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cisco_network; **sourcetype**: meraki:api. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=cisco_network, sourcetype="meraki:api". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by ap_name, floor** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Pipeline stage (see **WiFi Geolocation and Location Analytics (Meraki MR)**): geom geo_from_metric lat, lon


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Heat map by physical location; AP heat map overlay; zone traffic comparison.

## SPL

```spl
index=cisco_network sourcetype="meraki:api" ap_name=*
| stats count as foot_traffic by ap_name, floor
| geom geo_from_metric lat, lon
```

## Visualization

Heat map by physical location; AP heat map overlay; zone traffic comparison.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
