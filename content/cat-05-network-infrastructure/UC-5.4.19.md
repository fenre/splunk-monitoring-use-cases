<!-- AUTO-GENERATED from UC-5.4.19.json — DO NOT EDIT -->

---
id: "5.4.19"
title: "Band Steering Effectiveness Assessment (Meraki MR)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.4.19 · Band Steering Effectiveness Assessment (Meraki MR)

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance

*We watch band steering effectiveness assessment (meraki mr) so we notice problems while they are still small, and we can fix them before Wi-Fi users get dropped calls or dead spots.*

---

## Description

Measures effectiveness of steering clients from 2.4GHz to 5GHz bands to reduce congestion and improve performance.

## Value

Wireless operations teams monitor Meraki guest SSID splash page (captive portal) authentication success rates, detecting backend failures, timeouts, and configuration issues impacting guest WiFi access.

## Implementation

1. Enable the Webhook Logs (HEC) input and configure 'client connection changed' alerts in Meraki Dashboard. 2. Each association event includes alertData.band (2.4GHz / 5GHz / 6GHz). 3. Calculate the share of clients on each band; if 5GHz/6GHz share is below ~70% on dual-band capable APs, review band-steering configuration in Meraki Dashboard -> Wireless -> Radio settings. 4. For per-AP band steering effectiveness, group by deviceSerial in addition to band.

## Detailed Implementation

### Prerequisites
- Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
- Ensure the following data sources are available: Splunk_TA_cisco_meraki (Splunkbase #5580): Webhook receiver (sourcetype=meraki:webhook) with 'client connection changed' alerts. The polled Dashboard API does not break down clients by band; webhook payloads include alertData.band on association events..
- For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

### Step 1 — Configure data collection
1. Enable the Webhook Logs (HEC) input and configure 'client connection changed' alerts in Meraki Dashboard. 2. Each association event includes alertData.band (2.4GHz / 5GHz / 6GHz). 3. Calculate the share of clients on each band; if 5GHz/6GHz share is below ~70% on dual-band capable APs, review band-steering configuration in Meraki Dashboard -> Wireless -> Radio settings. 4. For per-AP band steering effectiveness, group by deviceSerial in addition to band.

### Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=meraki sourcetype IN ("meraki:webhook","meraki:webhooklogs:api")
    alertType="client_connectivity"
    earliest=-24h
| spath
| eval client_mac = coalesce('alertData.clientMac', 'alertData.client.mac')
| eval band = coalesce('alertData.band', 'alertData.rf.band')
| where isnotnull(client_mac) AND isnotnull(band)
| stats dc(client_mac) as client_count by band
| eventstats sum(client_count) as total
| eval band_share_pct = round(client_count*100/total, 1)
| sort - client_count
```

#### Understanding this SPL

**Band Steering Effectiveness Assessment (Meraki MR)** — Wireless operations teams monitor Meraki guest SSID splash page (captive portal) authentication success rates, detecting backend failures, timeouts, and configuration issues impacting guest WiFi access.

Documented **Data sources**: Splunk_TA_cisco_meraki (Splunkbase #5580): Webhook receiver (sourcetype=meraki:webhook) with 'client connection changed' alerts. The polled Dashboard API does not break down clients by band; webhook payloads include alertData.band on association events. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: meraki.

**Pipeline walkthrough**

- Scopes the data: index=meraki, time bounds. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
- Extracts structured paths (JSON/XML) with `spath`.
- `eval` defines or adjusts **client_mac** — often to normalize units, derive a ratio, or prepare for thresholds.
- `eval` defines or adjusts **band** — often to normalize units, derive a ratio, or prepare for thresholds.
- Filters the current rows with `where isnotnull(client_mac) AND isnotnull(band)` — typically the threshold or rule expression for this monitoring goal.
- `stats` rolls up events into metrics; results are split **by band** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
- `eventstats` aggregates the pipeline (counts, distinct values, sums, percentiles, etc.) into fewer rows.
- `eval` defines or adjusts **band_share_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
- Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


### Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

### Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Gauge showing 5GHz percentage; pie chart of band distribution; trend line showing steering progress.

## SPL

```spl
index=meraki sourcetype IN ("meraki:webhook","meraki:webhooklogs:api")
    alertType="client_connectivity"
    earliest=-24h
| spath
| eval client_mac = coalesce('alertData.clientMac', 'alertData.client.mac')
| eval band = coalesce('alertData.band', 'alertData.rf.band')
| where isnotnull(client_mac) AND isnotnull(band)
| stats dc(client_mac) as client_count by band
| eventstats sum(client_count) as total
| eval band_share_pct = round(client_count*100/total, 1)
| sort - client_count
```

## Visualization

Gauge showing 5GHz percentage; pie chart of band distribution; trend line showing steering progress.

## Known False Positives

RF noise and channel changes can spike when neighbors deploy new gear, microwaves run, or the controller runs automatic channel updates; weather and outdoor clients can also move the numbers.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
