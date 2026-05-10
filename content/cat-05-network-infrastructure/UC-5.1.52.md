<!-- AUTO-GENERATED from UC-5.1.52.json — DO NOT EDIT -->

---
id: "5.1.52"
title: "Cellular Gateway Signal Strength Trending (Meraki MG)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.1.52 · Cellular Gateway Signal Strength Trending (Meraki MG)

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance

*We help you know early when something looks wrong with cellular gateway signal strength trending so the team can act before it grows into a bigger outage.*

---

## Description

Monitors cellular signal strength to ensure reliable backup connectivity.

## Value

Operations teams trend Meraki MG cellular gateway signal strength (RSRP, RSRQ, SINR) to detect degradation and optimize antenna placement for reliable cellular WAN connectivity.

## Implementation

1. Enable Devices Uplinks Loss and Latency input (TA v3.3+, polls GET /organizations/{orgId}/devices/uplinksLossAndLatency, OAuth scope dashboard:general:telemetry:read). The MG cellular uplink is reported alongside MX uplinks. 2. Join with the Devices input to filter to productType=cellularGateway. 3. The TA returns timeSeries[] of {ts, lossPercent, latencyMs}. 4. For raw RSSI/SINR polling use Splunk's SNMP modular input against the MG management IP and the MERAKI-CLOUD-CONTROLLER-MIB cellular OIDs.

## Detailed Implementation

### Prerequisites
- Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
- Ensure the following data sources are available: Splunk_TA_cisco_meraki (Splunkbase #5580): Devices Uplinks Loss and Latency input (sourcetype=meraki:devicesuplinkslossandlatency, TA v3.3+) and Devices input (sourcetype=meraki:devices) for MG inventory. NOTE: actual cellular RSSI/SINR/RSRP is NOT exposed by the Dashboard API; this UC monitors uplink loss/latency as a behavioural proxy. For raw radio metrics, use SNMP polling against the MG..
- For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

### Step 1 — Configure data collection
1. Enable Devices Uplinks Loss and Latency input (TA v3.3+, polls GET /organizations/{orgId}/devices/uplinksLossAndLatency, OAuth scope dashboard:general:telemetry:read). The MG cellular uplink is reported alongside MX uplinks. 2. Join with the Devices input to filter to productType=cellularGateway. 3. The TA returns timeSeries[] of {ts, lossPercent, latencyMs}. 4. For raw RSSI/SINR polling use Splunk's SNMP modular input against the MG management IP and the MERAKI-CLOUD-CONTROLLER-MIB cellular …

### Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=meraki sourcetype="meraki:devicesuplinkslossandlatency" earliest=-24h
| spath path=timeSeries{} output=ts
| mvexpand ts
| spath input=ts
| join type=left serial [
    search index=meraki sourcetype="meraki:devices" productType="cellularGateway"
    | stats latest(model) as model, latest(name) as device_name by serial
  ]
| where isnotnull(model)
| stats avg(latencyMs) as avg_latency,
        avg(lossPercent) as avg_loss,
        max(lossPercent) as peak_loss
         by serial, device_name, model, networkId, uplink
| eval link_quality = case(avg_loss>5,"Critical", avg_loss>2 OR avg_latency>250,"Warning", 1=1,"OK")
| sort - peak_loss
```

#### Understanding this SPL

**Cellular Gateway Signal Strength Trending (Meraki MG)** — Operations teams trend Meraki MG cellular gateway signal strength (RSRP, RSRQ, SINR) to detect degradation and optimize antenna placement for reliable cellular WAN connectivity.

Documented **Data sources**: Splunk_TA_cisco_meraki (Splunkbase #5580): Devices Uplinks Loss and Latency input (sourcetype=meraki:devicesuplinkslossandlatency, TA v3.3+) and Devices input (sourcetype=meraki:devices) for MG inventory. NOTE: actual cellular RSSI/SINR/RSRP is NOT exposed by the Dashboard API; this UC monitors uplink loss/latency as a behavioural proxy. For raw radio metrics, use SNMP polling against the MG. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: meraki; **sourcetype**: meraki:devicesuplinkslossandlatency. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

- Scopes the data: index=meraki, sourcetype="meraki:devicesuplinkslossandlatency", time bounds. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
- Extracts structured paths (JSON/XML) with `spath`.
- Expands multivalue fields with `mvexpand` — use `limit=` to cap row explosion.
- Extracts structured paths (JSON/XML) with `spath`.
- Joins to a subsearch with `join` — set `max=` to match cardinality and avoid silent truncation.
- Filters the current rows with `where isnotnull(model)` — typically the threshold or rule expression for this monitoring goal.
- `stats` rolls up events into metrics; results are split **by serial, device_name, model, networkId, uplink** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
- `eval` defines or adjusts **link_quality** — often to normalize units, derive a ratio, or prepare for thresholds.
- Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


### Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

### Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Signal strength gauge; trend timeline; cellular quality status.

## SPL

```spl
index=meraki sourcetype="meraki:devicesuplinkslossandlatency" earliest=-24h
| spath path=timeSeries{} output=ts
| mvexpand ts
| spath input=ts
| join type=left serial [
    search index=meraki sourcetype="meraki:devices" productType="cellularGateway"
    | stats latest(model) as model, latest(name) as device_name by serial
  ]
| where isnotnull(model)
| stats avg(latencyMs) as avg_latency,
        avg(lossPercent) as avg_loss,
        max(lossPercent) as peak_loss
         by serial, device_name, model, networkId, uplink
| eval link_quality = case(avg_loss>5,"Critical", avg_loss>2 OR avg_latency>250,"Warning", 1=1,"OK")
| sort - peak_loss
```

## Visualization

Signal strength gauge; trend timeline; cellular quality status.

## Known False Positives

Carrier testing, local SIM swaps, and planned tower work can look like a connectivity fault. Compare the Meraki event log to the same window in Splunk.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
