<!-- AUTO-GENERATED from UC-5.4.18.json — DO NOT EDIT -->

---
id: "5.4.18"
title: "Client Device Type Distribution and Compliance (Meraki MR)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.4.18 · Client Device Type Distribution and Compliance (Meraki MR)

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Compliance

*We watch client device type distribution and compliance (meraki mr) so we notice problems while they are still small, and we can fix them before Wi-Fi users get dropped calls or dead spots.*

---

## Description

Tracks device types connecting to network for capacity planning, security policy enforcement, and support optimization.

## Value

Wireless operations teams monitor Meraki MR access point fleet health across all sites, tracking online/offline/alerting status to calculate site-level health percentages and detect outages.

## Implementation

1. Enable the Webhook Logs (HEC) input and the 'client connection changed' alert profile in Meraki Dashboard. 2. The alertData payload contains client.os, client.manufacturer, deviceTypePrediction. 3. Use dc(client_mac) to count unique devices over the period. 4. For corporate/personal segmentation, enrich with a lookup against your MDM (Meraki Systems Manager, Jamf, Intune).

## Detailed Implementation

### Prerequisites
- Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
- Ensure the following data sources are available: Splunk_TA_cisco_meraki (Splunkbase #5580): Webhook receiver (sourcetype=meraki:webhook) with 'client connection changed' alerts enabled. Per-client OS/manufacturer detection is provided by Meraki's fingerprinting in the webhook payload only; not in the polled Dashboard API..
- For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

### Step 1 — Configure data collection
1. Enable the Webhook Logs (HEC) input and the 'client connection changed' alert profile in Meraki Dashboard. 2. The alertData payload contains client.os, client.manufacturer, deviceTypePrediction. 3. Use dc(client_mac) to count unique devices over the period. 4. For corporate/personal segmentation, enrich with a lookup against your MDM (Meraki Systems Manager, Jamf, Intune).

### Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=meraki sourcetype IN ("meraki:webhook","meraki:webhooklogs:api")
    alertType="client_connectivity"
    earliest=-24h
| spath
| eval client_mac = coalesce('alertData.clientMac', 'alertData.client.mac')
| eval client_os = coalesce('alertData.os', 'alertData.client.os', 'alertData.deviceTypePrediction')
| eval client_manufacturer = 'alertData.client.manufacturer'
| where isnotnull(client_mac)
| stats dc(client_mac) as device_count
         by client_os, client_manufacturer
| eventstats sum(device_count) as total
| eval pct = round(device_count*100/total, 1)
| sort - device_count
```

#### Understanding this SPL

**Client Device Type Distribution and Compliance (Meraki MR)** — Wireless operations teams monitor Meraki MR access point fleet health across all sites, tracking online/offline/alerting status to calculate site-level health percentages and detect outages.

Documented **Data sources**: Splunk_TA_cisco_meraki (Splunkbase #5580): Webhook receiver (sourcetype=meraki:webhook) with 'client connection changed' alerts enabled. Per-client OS/manufacturer detection is provided by Meraki's fingerprinting in the webhook payload only; not in the polled Dashboard API. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: meraki.

**Pipeline walkthrough**

- Scopes the data: index=meraki, time bounds. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
- Extracts structured paths (JSON/XML) with `spath`.
- `eval` defines or adjusts **client_mac** — often to normalize units, derive a ratio, or prepare for thresholds.
- `eval` defines or adjusts **client_os** — often to normalize units, derive a ratio, or prepare for thresholds.
- `eval` defines or adjusts **client_manufacturer** — often to normalize units, derive a ratio, or prepare for thresholds.
- Filters the current rows with `where isnotnull(client_mac)` — typically the threshold or rule expression for this monitoring goal.
- `stats` rolls up events into metrics; results are split **by client_os, client_manufacturer** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
- `eventstats` aggregates the pipeline (counts, distinct values, sums, percentiles, etc.) into fewer rows.
- `eval` defines or adjusts **pct** — often to normalize units, derive a ratio, or prepare for thresholds.
- Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


### Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

### Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Pie chart of device types; bar chart by OS; treemap of device distribution; trend sparklines.

## SPL

```spl
index=meraki sourcetype IN ("meraki:webhook","meraki:webhooklogs:api")
    alertType="client_connectivity"
    earliest=-24h
| spath
| eval client_mac = coalesce('alertData.clientMac', 'alertData.client.mac')
| eval client_os = coalesce('alertData.os', 'alertData.client.os', 'alertData.deviceTypePrediction')
| eval client_manufacturer = 'alertData.client.manufacturer'
| where isnotnull(client_mac)
| stats dc(client_mac) as device_count
         by client_os, client_manufacturer
| eventstats sum(device_count) as total
| eval pct = round(device_count*100/total, 1)
| sort - device_count
```

## Visualization

Pie chart of device types; bar chart by OS; treemap of device distribution; trend sparklines.

## Known False Positives

Wireless metrics move with user behavior, maintenance, and nearby RF; we tune alerts around change windows and known busy hours so normal days do not page the team.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
