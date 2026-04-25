<!-- AUTO-GENERATED from UC-5.2.30.json — DO NOT EDIT -->

---
id: "5.2.30"
title: "Geo-Blocking Event Tracking and Geographic Policy Enforcement (Meraki MX)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.2.30 · Geo-Blocking Event Tracking and Geographic Policy Enforcement (Meraki MX)

## Description

Tracks geo-blocking policy enforcement to verify compliance with data residency and export controls.

## Value

Tracks geo-blocking policy enforcement to verify compliance with data residency and export controls.

## Implementation

Ingest URL logs with GeoIP enrichment. Track blocks by geography.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
• Ensure the following data sources are available: `sourcetype=meraki type=urls action="blocked" country=*`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Ingest URL logs with GeoIP enrichment. Track blocks by geography.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cisco_network sourcetype="meraki" type=urls action="blocked"
| lookup geo_ip.csv dest OUTPUTNEW country, city
| stats count as block_count by country
| sort - block_count
```

Understanding this SPL

**Geo-Blocking Event Tracking and Geographic Policy Enforcement (Meraki MX)** — Tracks geo-blocking policy enforcement to verify compliance with data residency and export controls.

Documented **Data sources**: `sourcetype=meraki type=urls action="blocked" country=*`. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cisco_network; **sourcetype**: meraki. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=cisco_network, sourcetype="meraki". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Enriches events using `lookup` (lookup definition + optional OUTPUT fields).
• `stats` rolls up events into metrics; results are split **by country** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
In the Meraki cloud dashboard, use the same organization, network, and time range as the search. Confirm the same events, site or appliance names, and policy context you see in the dashboard line up with Splunk.
Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Geo-block map; country block count chart; policy compliance dashboard.

## SPL

```spl
index=cisco_network sourcetype="meraki" type=urls action="blocked"
| lookup geo_ip.csv dest OUTPUTNEW country, city
| stats count as block_count by country
| sort - block_count
```

## Visualization

Geo-block map; country block count chart; policy compliance dashboard.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
