<!-- AUTO-GENERATED from UC-5.4.31.json — DO NOT EDIT -->

---
id: "5.4.31"
title: "WiFi Geolocation and Location Analytics (Meraki MR)"
criticality: "low"
splunkPillar: "Observability"
---

# UC-5.4.31 · WiFi Geolocation and Location Analytics (Meraki MR)

> **Criticality:** Low &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Performance

*We watch wifi geolocation and location analytics (meraki mr) so we notice problems while they are still small, and we can fix them before Wi-Fi users get dropped calls or dead spots.*

---

## Description

Uses Cisco Meraki location services to track foot traffic patterns and heat maps in physical spaces.

## Value

Network operations teams inventory wireless client device types across Meraki networks, identifying OS distribution, IoT device presence on corporate SSIDs, and BYOD policy violations for security segmentation.

## Implementation

1. In Meraki Dashboard, set the lat/lng/address fields for each MR AP under Wireless -> Access points -> AP details. 2. Enable the Devices input in Splunk_TA_cisco_meraki and confirm those fields populate. 3. Use the geom command to render APs on a Choropleth or marker map. 4. For client indoor positioning and footfall analytics deploy Cisco Spaces and ingest its Location API output via the Cisco Spaces Add-on (sourcetype=cisco:spaces:location).

## Detailed Implementation

### Prerequisites
- Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
- Ensure the following data sources are available: Splunk_TA_cisco_meraki (Splunkbase #5580): Devices input (sourcetype=meraki:devices) for AP location metadata (lat, lng, address, floorPlanId). NOTE: client-level indoor location analytics (Meraki Location API / Bluetooth scanning) is NOT exposed by this TA — for that, install Cisco Spaces and the Cisco Spaces Add-on (Splunkbase #8485)..
- For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

### Step 1 — Configure data collection
1. In Meraki Dashboard, set the lat/lng/address fields for each MR AP under Wireless -> Access points -> AP details. 2. Enable the Devices input in Splunk_TA_cisco_meraki and confirm those fields populate. 3. Use the geom command to render APs on a Choropleth or marker map. 4. For client indoor positioning and footfall analytics deploy Cisco Spaces and ingest its Location API output via the Cisco Spaces Add-on (sourcetype=cisco:spaces:location).

### Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=meraki sourcetype="meraki:devices" productType="wireless"
| stats latest(name) as ap_name,
        latest(model) as model,
        latest(lat) as latitude,
        latest(lng) as longitude,
        latest(address) as address,
        latest(network.name) as network_name,
        latest(floorPlanId) as floor_plan_id
         by serial
| where isnotnull(latitude) AND isnotnull(longitude)
| geom geo_us_states featureIdField="state"
| table serial ap_name model network_name address latitude longitude floor_plan_id
```

#### Understanding this SPL

**WiFi Geolocation and Location Analytics (Meraki MR)** — Network operations teams inventory wireless client device types across Meraki networks, identifying OS distribution, IoT device presence on corporate SSIDs, and BYOD policy violations for security segmentation.

Documented **Data sources**: Splunk_TA_cisco_meraki (Splunkbase #5580): Devices input (sourcetype=meraki:devices) for AP location metadata (lat, lng, address, floorPlanId). NOTE: client-level indoor location analytics (Meraki Location API / Bluetooth scanning) is NOT exposed by this TA — for that, install Cisco Spaces and the Cisco Spaces Add-on (Splunkbase #8485). **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: meraki; **sourcetype**: meraki:devices. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

- Scopes the data: index=meraki, sourcetype="meraki:devices". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
- `stats` rolls up events into metrics; results are split **by serial** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
- Filters the current rows with `where isnotnull(latitude) AND isnotnull(longitude)` — typically the threshold or rule expression for this monitoring goal.
- Pipeline stage (see **WiFi Geolocation and Location Analytics (Meraki MR)**): geom geo_us_states featureIdField="state"
- Pipeline stage (see **WiFi Geolocation and Location Analytics (Meraki MR)**): table serial ap_name model network_name address latitude longitude floor_plan_id


### Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

### Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Heat map by physical location; AP heat map overlay; zone traffic comparison.

## SPL

```spl
index=meraki sourcetype="meraki:devices" productType="wireless"
| stats latest(name) as ap_name,
        latest(model) as model,
        latest(lat) as latitude,
        latest(lng) as longitude,
        latest(address) as address,
        latest(network.name) as network_name,
        latest(floorPlanId) as floor_plan_id
         by serial
| where isnotnull(latitude) AND isnotnull(longitude)
| geom geo_us_states featureIdField="state"
| table serial ap_name model network_name address latitude longitude floor_plan_id
```

## Visualization

Heat map by physical location; AP heat map overlay; zone traffic comparison.

## Known False Positives

Wireless metrics move with user behavior, maintenance, and nearby RF; we tune alerts around change windows and known busy hours so normal days do not page the team.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
