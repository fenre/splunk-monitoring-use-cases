---
id: "5.4.13"
title: "RSSI/Signal Strength Degradation Detection (Meraki MR)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.4.13 · RSSI/Signal Strength Degradation Detection (Meraki MR)

## Description

Proactively identifies weak WiFi coverage areas and client placement issues before users experience connectivity problems.

## Value

Proactively identifies weak WiFi coverage areas and client placement issues before users experience connectivity problems.

## Implementation

Ingest Meraki API client data periodically; analyze RSSI distribution by AP and SSID. Set thresholds for "poor" signal (< -70 dBm).

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
• Ensure the following data sources are available: `sourcetype=meraki:api`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Ingest Meraki API client data periodically; analyze RSSI distribution by AP and SSID. Set thresholds for "poor" signal (< -70 dBm).

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cisco_network sourcetype="meraki:api"
| eval rssi_level=case(rssi>=-50, "Excellent", rssi>=-60, "Good", rssi>=-70, "Fair", rssi<-70, "Poor")
| stats avg(rssi) as avg_rssi, min(rssi) as min_rssi, count by ap_name, ssid, rssi_level
| where min_rssi < -70 or avg_rssi < -65
```

Understanding this SPL

**RSSI/Signal Strength Degradation Detection (Meraki MR)** — Proactively identifies weak WiFi coverage areas and client placement issues before users experience connectivity problems.

Documented **Data sources**: `sourcetype=meraki:api`. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cisco_network; **sourcetype**: meraki:api. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=cisco_network, sourcetype="meraki:api". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **rssi_level** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by ap_name, ssid, rssi_level** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where min_rssi < -70 or avg_rssi < -65` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Heatmap of RSSI by AP location; histogram of signal strength distribution; gauge charts for coverage quality by SSID.

## SPL

```spl
index=cisco_network sourcetype="meraki:api"
| eval rssi_level=case(rssi>=-50, "Excellent", rssi>=-60, "Good", rssi>=-70, "Fair", rssi<-70, "Poor")
| stats avg(rssi) as avg_rssi, min(rssi) as min_rssi, count by ap_name, ssid, rssi_level
| where min_rssi < -70 or avg_rssi < -65
```

## Visualization

Heatmap of RSSI by AP location; histogram of signal strength distribution; gauge charts for coverage quality by SSID.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
