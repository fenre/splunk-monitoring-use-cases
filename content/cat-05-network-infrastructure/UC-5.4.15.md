<!-- AUTO-GENERATED from UC-5.4.15.json — DO NOT EDIT -->

---
id: "5.4.15"
title: "SSID Performance Ranking and Trend Analysis (Meraki MR)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.4.15 · SSID Performance Ranking and Trend Analysis (Meraki MR)

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance

*We watch ssid performance ranking and trend analysis (meraki mr) so we notice problems while they are still small, and we can fix them before Wi-Fi users get dropped calls or dead spots.*

---

## Description

Compares performance across multiple SSIDs to identify underperforming networks and optimize deployment strategy.

## Value

Network operations teams rank Meraki SSID performance across all sites using a composite score (success rate, signal quality, latency), enabling cross-site comparison and targeted wireless optimization.

## Implementation

1. Enable the Wireless Packet Loss by Device input in Splunk_TA_cisco_meraki. The TA polls GET /organizations/{orgId}/wireless/devices/packetLoss/byDevice daily and emits one event per AP with downstream.{lossPercentage,total} and upstream.* fields. 2. Aggregate per network for a coarse 'wireless health' indicator. 3. Per-SSID metrics need either webhook ingestion (client_connection_changed) with alertData.ssid grouping, or a custom modular input that calls GET /networks/{networkId}/wireless/ssids/.../latencyStats.

## Detailed Implementation

### Prerequisites
- Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
- Ensure the following data sources are available: Splunk_TA_cisco_meraki (Splunkbase #5580): Wireless Packet Loss by Device input (sourcetype=meraki:wirelessdevicespacketlossbydevice, TA v3+, OAuth scope wireless:telemetry:read). NOTE: per-SSID throughput, retry rate, and connection time are NOT exposed by the polled API; for those, use webhooks or the per-network wireless health endpoints (not currently in the TA)..
- For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

### Step 1 — Configure data collection
1. Enable the Wireless Packet Loss by Device input in Splunk_TA_cisco_meraki. The TA polls GET /organizations/{orgId}/wireless/devices/packetLoss/byDevice daily and emits one event per AP with downstream.{lossPercentage,total} and upstream.* fields. 2. Aggregate per network for a coarse 'wireless health' indicator. 3. Per-SSID metrics need either webhook ingestion (client_connection_changed) with alertData.ssid grouping, or a custom modular input that calls GET /networks/{networkId}/wireless/ssi…

### Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=meraki sourcetype="meraki:wirelessdevicespacketlossbydevice" earliest=-24h
| stats avg(downstream.lossPercentage) as avg_dl_loss,
        avg(upstream.lossPercentage) as avg_ul_loss,
        avg(downstream.total) as avg_dl_packets,
        avg(upstream.total) as avg_ul_packets
         by serial, name, network.name
| eval health_score = round(100 - ((avg_dl_loss + avg_ul_loss) / 2), 1)
| sort health_score
```

#### Understanding this SPL

**SSID Performance Ranking and Trend Analysis (Meraki MR)** — Network operations teams rank Meraki SSID performance across all sites using a composite score (success rate, signal quality, latency), enabling cross-site comparison and targeted wireless optimization.

Documented **Data sources**: Splunk_TA_cisco_meraki (Splunkbase #5580): Wireless Packet Loss by Device input (sourcetype=meraki:wirelessdevicespacketlossbydevice, TA v3+, OAuth scope wireless:telemetry:read). NOTE: per-SSID throughput, retry rate, and connection time are NOT exposed by the polled API; for those, use webhooks or the per-network wireless health endpoints (not currently in the TA). **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: meraki; **sourcetype**: meraki:wirelessdevicespacketlossbydevice. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

- Scopes the data: index=meraki, sourcetype="meraki:wirelessdevicespacketlossbydevice", time bounds. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
- `stats` rolls up events into metrics; results are split **by serial, name, network.name** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
- `eval` defines or adjusts **health_score** — often to normalize units, derive a ratio, or prepare for thresholds.
- Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


### Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

### Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Bar chart comparing SSID performance; sparklines for trend; scorecard showing top/bottom performers.

## SPL

```spl
index=meraki sourcetype="meraki:wirelessdevicespacketlossbydevice" earliest=-24h
| stats avg(downstream.lossPercentage) as avg_dl_loss,
        avg(upstream.lossPercentage) as avg_ul_loss,
        avg(downstream.total) as avg_dl_packets,
        avg(upstream.total) as avg_ul_packets
         by serial, name, network.name
| eval health_score = round(100 - ((avg_dl_loss + avg_ul_loss) / 2), 1)
| sort health_score
```

## Visualization

Bar chart comparing SSID performance; sparklines for trend; scorecard showing top/bottom performers.

## Known False Positives

RF noise and channel changes can spike when neighbors deploy new gear, microwaves run, or the controller runs automatic channel updates; weather and outdoor clients can also move the numbers.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
