<!-- AUTO-GENERATED from UC-5.4.21.json — DO NOT EDIT -->

---
id: "5.4.21"
title: "Wireless Latency Analysis by SSID and Location (Meraki MR)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.4.21 · Wireless Latency Analysis by SSID and Location (Meraki MR)

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance

*We watch wireless latency analysis by ssid and location (meraki mr) so we notice problems while they are still small, and we can fix them before Wi-Fi users get dropped calls or dead spots.*

---

## Description

Identifies latency patterns across network to optimize AP placement, channel allocation, and client routing.

## Value

Wireless security teams leverage Meraki Air Marshal (WIDS/WIPS) events to detect rogue APs, evil twin attacks (SSID spoofing), and wired rogue devices, classifying threats by severity for rapid response.

## Implementation

1. Enable the Wireless Packet Loss by Device input. The TA polls GET /organizations/{orgId}/wireless/devices/packetLoss/byDevice daily and returns downstream.{lossPercentage,total} and upstream.* per AP. 2. High packet loss is the strongest available signal for client experience problems on Meraki MR APs. 3. For latency you have two options: (a) ingest webhook 'client connection changed' events which include alertData.latency in some payloads, or (b) deploy a synthetic probe (ICMP ping or ThousandEyes Endpoint Agent) to measure RTT.

## Detailed Implementation

### Prerequisites
- Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
- Ensure the following data sources are available: Splunk_TA_cisco_meraki (Splunkbase #5580): Wireless Packet Loss by Device input (sourcetype=meraki:wirelessdevicespacketlossbydevice). NOTE: per-client wireless latency is NOT exposed by the polled API; this UC monitors per-AP packet loss as a proxy. For round-trip latency, supplement with a synthetic ping monitor (Splunk_TA_ping or ThousandEyes Endpoint Agent)..
- For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

### Step 1 — Configure data collection
1. Enable the Wireless Packet Loss by Device input. The TA polls GET /organizations/{orgId}/wireless/devices/packetLoss/byDevice daily and returns downstream.{lossPercentage,total} and upstream.* per AP. 2. High packet loss is the strongest available signal for client experience problems on Meraki MR APs. 3. For latency you have two options: (a) ingest webhook 'client connection changed' events which include alertData.latency in some payloads, or (b) deploy a synthetic probe (ICMP ping or Thousa…

### Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=meraki sourcetype="meraki:wirelessdevicespacketlossbydevice" earliest=-24h
| stats avg(downstream.lossPercentage) as avg_dl_loss,
        avg(upstream.lossPercentage) as avg_ul_loss,
        max(downstream.lossPercentage) as peak_dl_loss
         by serial, name, network.name
| eval client_health = case(
    avg_dl_loss>5 OR avg_ul_loss>5, "Critical",
    avg_dl_loss>2 OR avg_ul_loss>2, "Warning",
    1=1, "OK")
| where client_health != "OK"
| sort - peak_dl_loss
```

#### Understanding this SPL

**Wireless Latency Analysis by SSID and Location (Meraki MR)** — Wireless security teams leverage Meraki Air Marshal (WIDS/WIPS) events to detect rogue APs, evil twin attacks (SSID spoofing), and wired rogue devices, classifying threats by severity for rapid response.

Documented **Data sources**: Splunk_TA_cisco_meraki (Splunkbase #5580): Wireless Packet Loss by Device input (sourcetype=meraki:wirelessdevicespacketlossbydevice). NOTE: per-client wireless latency is NOT exposed by the polled API; this UC monitors per-AP packet loss as a proxy. For round-trip latency, supplement with a synthetic ping monitor (Splunk_TA_ping or ThousandEyes Endpoint Agent). **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: meraki; **sourcetype**: meraki:wirelessdevicespacketlossbydevice. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

- Scopes the data: index=meraki, sourcetype="meraki:wirelessdevicespacketlossbydevice", time bounds. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
- `stats` rolls up events into metrics; results are split **by serial, name, network.name** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
- `eval` defines or adjusts **client_health** — often to normalize units, derive a ratio, or prepare for thresholds.
- Filters the current rows with `where client_health != "OK"` — typically the threshold or rule expression for this monitoring goal.
- Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


### Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

### Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Heatmap of latency by AP; line chart of latency trends; SLA compliance dashboard.

## SPL

```spl
index=meraki sourcetype="meraki:wirelessdevicespacketlossbydevice" earliest=-24h
| stats avg(downstream.lossPercentage) as avg_dl_loss,
        avg(upstream.lossPercentage) as avg_ul_loss,
        max(downstream.lossPercentage) as peak_dl_loss
         by serial, name, network.name
| eval client_health = case(
    avg_dl_loss>5 OR avg_ul_loss>5, "Critical",
    avg_dl_loss>2 OR avg_ul_loss>2, "Warning",
    1=1, "OK")
| where client_health != "OK"
| sort - peak_dl_loss
```

## Visualization

Heatmap of latency by AP; line chart of latency trends; SLA compliance dashboard.

## Known False Positives

Wireless metrics move with user behavior, maintenance, and nearby RF; we tune alerts around change windows and known busy hours so normal days do not page the team.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
