<!-- AUTO-GENERATED from UC-5.4.25.json — DO NOT EDIT -->

---
id: "5.4.25"
title: "Connected Client Count Trending and Capacity Planning (Meraki MR)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.4.25 · Connected Client Count Trending and Capacity Planning (Meraki MR)

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Capacity

*We watch connected client count trending and capacity planning (meraki mr) so we notice problems while they are still small, and we can fix them before Wi-Fi users get dropped calls or dead spots.*

---

## Description

Tracks client density by AP and SSID for capacity planning and performance optimization.

## Value

Facilities and security teams leverage Meraki MR built-in BLE scanning to track tagged assets, detect BLE device movement between zones, and support indoor location-based services.

## Implementation

1. Enable the Webhook Logs (HEC) input and 'client connection changed' alert profile in Meraki Dashboard. 2. Use dc(alertData.clientMac) over a sliding hour for concurrent client count per AP. 3. For coarse top-talker visibility, the polled Summary Top Clients by Usage input (meraki:summarytopclientsbyusage) returns the org's top 10. 4. AP capacity limits depend on model (typical recent Wi-Fi 6 MR45/55/56 supports 200+ clients; older MR33 ~100); set capacity_pct thresholds per model class.

## Detailed Implementation

### Prerequisites
- Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
- Ensure the following data sources are available: Splunk_TA_cisco_meraki (Splunkbase #5580): Webhook receiver (sourcetype=meraki:webhook) with 'client connection changed' alerts. The polled Dashboard API only returns the top 10 clients by usage; full client trending requires webhook ingestion..
- For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

### Step 1 — Configure data collection
1. Enable the Webhook Logs (HEC) input and 'client connection changed' alert profile in Meraki Dashboard. 2. Use dc(alertData.clientMac) over a sliding hour for concurrent client count per AP. 3. For coarse top-talker visibility, the polled Summary Top Clients by Usage input (meraki:summarytopclientsbyusage) returns the org's top 10. 4. AP capacity limits depend on model (typical recent Wi-Fi 6 MR45/55/56 supports 200+ clients; older MR33 ~100); set capacity_pct thresholds per model class.

### Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=meraki sourcetype IN ("meraki:webhook","meraki:webhooklogs:api")
    alertType="client_connectivity"
    earliest=-7d
| spath
| eval client_mac = coalesce('alertData.clientMac', 'alertData.client.mac')
| where isnotnull(client_mac)
| timechart span=1h dc(client_mac) as concurrent_clients by deviceName limit=20
```

#### Understanding this SPL

**Connected Client Count Trending and Capacity Planning (Meraki MR)** — Facilities and security teams leverage Meraki MR built-in BLE scanning to track tagged assets, detect BLE device movement between zones, and support indoor location-based services.

Documented **Data sources**: Splunk_TA_cisco_meraki (Splunkbase #5580): Webhook receiver (sourcetype=meraki:webhook) with 'client connection changed' alerts. The polled Dashboard API only returns the top 10 clients by usage; full client trending requires webhook ingestion. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: meraki.

**Pipeline walkthrough**

- Scopes the data: index=meraki, time bounds. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
- Extracts structured paths (JSON/XML) with `spath`.
- `eval` defines or adjusts **client_mac** — often to normalize units, derive a ratio, or prepare for thresholds.
- Filters the current rows with `where isnotnull(client_mac)` — typically the threshold or rule expression for this monitoring goal.
- `timechart` plots the metric over time using **span=1h** buckets with a separate series **by deviceName limit=20** — ideal for trending and alerting on this use case.


### Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

### Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Bubble chart of capacity by AP; stacked bar of clients by SSID; capacity gauge.

## SPL

```spl
index=meraki sourcetype IN ("meraki:webhook","meraki:webhooklogs:api")
    alertType="client_connectivity"
    earliest=-7d
| spath
| eval client_mac = coalesce('alertData.clientMac', 'alertData.client.mac')
| where isnotnull(client_mac)
| timechart span=1h dc(client_mac) as concurrent_clients by deviceName limit=20
```

## Visualization

Bubble chart of capacity by AP; stacked bar of clients by SSID; capacity gauge.

## Known False Positives

Wireless client counts spike during shift changes, big events, or back-to-school style rushes; compare against the calendar before calling it an incident.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
