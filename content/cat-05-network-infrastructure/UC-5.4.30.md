<!-- AUTO-GENERATED from UC-5.4.30.json — DO NOT EDIT -->

---
id: "5.4.30"
title: "Guest Network Access Patterns and Usage (Meraki MR)"
criticality: "low"
splunkPillar: "Observability"
---

# UC-5.4.30 · Guest Network Access Patterns and Usage (Meraki MR)

> **Criticality:** Low &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance

*We watch guest network access patterns and usage (meraki mr) so we notice problems while they are still small, and we can fix them before Wi-Fi users get dropped calls or dead spots.*

---

## Description

Tracks guest network adoption, usage patterns, and peak times for network provisioning.

## Value

Facilities teams monitor Meraki MT environmental sensor data (temperature, humidity, air quality) at wireless infrastructure locations, detecting IDF overheating and environmental conditions that degrade equipment.

## Implementation

1. Enable the Webhook Logs (HEC) input and the 'client connection changed' alert profile in Meraki Dashboard. 2. Filter on SSID names containing 'guest' (adjust to your naming convention). 3. dc(client_mac) per hour gives concurrent guest users. 4. For top-talker bandwidth on the guest SSID, use the Summary Top Clients by Usage input (meraki:summarytopclientsbyusage) and join on client.mac.

## Detailed Implementation

### Prerequisites
- Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
- Ensure the following data sources are available: Splunk_TA_cisco_meraki (Splunkbase #5580): Webhook receiver (sourcetype=meraki:webhook) with 'client connection changed' alerts. SSID name is in alertData.ssid on the webhook payload..
- For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

### Step 1 — Configure data collection
1. Enable the Webhook Logs (HEC) input and the 'client connection changed' alert profile in Meraki Dashboard. 2. Filter on SSID names containing 'guest' (adjust to your naming convention). 3. dc(client_mac) per hour gives concurrent guest users. 4. For top-talker bandwidth on the guest SSID, use the Summary Top Clients by Usage input (meraki:summarytopclientsbyusage) and join on client.mac.

### Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=meraki sourcetype IN ("meraki:webhook","meraki:webhooklogs:api")
    alertType="client_connectivity"
    earliest=-7d
| spath
| eval client_mac = coalesce('alertData.clientMac', 'alertData.client.mac')
| eval ssid = coalesce('alertData.ssid', 'alertData.ssidName')
| where isnotnull(client_mac) AND like(lower(ssid), "%guest%")
| timechart span=1h dc(client_mac) as guest_clients by ssid limit=10
```

#### Understanding this SPL

**Guest Network Access Patterns and Usage (Meraki MR)** — Facilities teams monitor Meraki MT environmental sensor data (temperature, humidity, air quality) at wireless infrastructure locations, detecting IDF overheating and environmental conditions that degrade equipment.

Documented **Data sources**: Splunk_TA_cisco_meraki (Splunkbase #5580): Webhook receiver (sourcetype=meraki:webhook) with 'client connection changed' alerts. SSID name is in alertData.ssid on the webhook payload. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: meraki.

**Pipeline walkthrough**

- Scopes the data: index=meraki, time bounds. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
- Extracts structured paths (JSON/XML) with `spath`.
- `eval` defines or adjusts **client_mac** — often to normalize units, derive a ratio, or prepare for thresholds.
- `eval` defines or adjusts **ssid** — often to normalize units, derive a ratio, or prepare for thresholds.
- Filters the current rows with `where isnotnull(client_mac) AND like(lower(ssid), "%guest%")` — typically the threshold or rule expression for this monitoring goal.
- `timechart` plots the metric over time using **span=1h** buckets with a separate series **by ssid limit=10** — ideal for trending and alerting on this use case.


### Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

### Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Time-series of guest users; daily/weekly heatmap; trend dashboard.

## SPL

```spl
index=meraki sourcetype IN ("meraki:webhook","meraki:webhooklogs:api")
    alertType="client_connectivity"
    earliest=-7d
| spath
| eval client_mac = coalesce('alertData.clientMac', 'alertData.client.mac')
| eval ssid = coalesce('alertData.ssid', 'alertData.ssidName')
| where isnotnull(client_mac) AND like(lower(ssid), "%guest%")
| timechart span=1h dc(client_mac) as guest_clients by ssid limit=10
```

## Visualization

Time-series of guest users; daily/weekly heatmap; trend dashboard.

## Known False Positives

Wireless metrics move with user behavior, maintenance, and nearby RF; we tune alerts around change windows and known busy hours so normal days do not page the team.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
