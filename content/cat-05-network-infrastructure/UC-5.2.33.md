<!-- AUTO-GENERATED from UC-5.2.33.json — DO NOT EDIT -->

---
id: "5.2.33"
title: "WAN Link Quality Monitoring — Jitter, Latency, Packet Loss (Meraki MX)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.2.33 · WAN Link Quality Monitoring — Jitter, Latency, Packet Loss (Meraki MX)

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Fault

*We look at loss, delay, and jitter on internet links from the same boxes so a flaky provider is visible on a dashboard, not in angry tickets.*

---

## Description

Continuously monitors WAN quality metrics to detect link degradation before impacting users.

## Value

NOC teams monitor Meraki MX WAN uplink latency, loss, and jitter in real time to detect link degradation and trigger failover or ISP escalation before users are impacted.

## Implementation

1. Enable the Devices Uplinks Loss and Latency input. The TA emits one event per device-uplink containing serial, networkId, uplink (wan1/wan2/cellular), ip, and a timeSeries[] array of {ts, lossPercent, latencyMs} samples (default 5-minute granularity, 5-minute timespan). 2. Use mvexpand on timeSeries to flatten samples for trending. 3. Tune thresholds (>2% loss, >200ms latency) to your SLA. 4. Jitter is not directly reported by this endpoint; if you need jitter, use the Appliance VPN Stats input (meraki:appliancesdwanstatistics) which carries jitterMs for SD-WAN tunnels.

## Detailed Implementation

### Prerequisites
- Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
- Ensure the following data sources are available: Splunk_TA_cisco_meraki (Splunkbase #5580): Devices Uplinks Loss and Latency input (sourcetype=meraki:devicesuplinkslossandlatency, TA v3.3+, OAuth scope dashboard:general:telemetry:read). Polls GET /organizations/{orgId}/devices/uplinksLossAndLatency for every MX and MG..
- For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

### Step 1 — Configure data collection
1. Enable the Devices Uplinks Loss and Latency input. The TA emits one event per device-uplink containing serial, networkId, uplink (wan1/wan2/cellular), ip, and a timeSeries[] array of {ts, lossPercent, latencyMs} samples (default 5-minute granularity, 5-minute timespan). 2. Use mvexpand on timeSeries to flatten samples for trending. 3. Tune thresholds (>2% loss, >200ms latency) to your SLA. 4. Jitter is not directly reported by this endpoint; if you need jitter, use the Appliance VPN Stats inp…

### Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=meraki sourcetype="meraki:devicesuplinkslossandlatency" earliest=-1h
| spath path=timeSeries{} output=ts
| mvexpand ts
| spath input=ts
| stats avg(latencyMs) as avg_latency,
        avg(lossPercent) as avg_loss,
        max(latencyMs) as peak_latency,
        max(lossPercent) as peak_loss
         by serial, networkId, uplink, ip
| eval link_quality = case(
    avg_loss>5 OR peak_loss>20, "Critical",
    avg_loss>2 OR avg_latency>200, "Warning",
    1=1, "OK")
| where link_quality != "OK"
| sort - avg_loss
```

#### Understanding this SPL

**WAN Link Quality Monitoring — Jitter, Latency, Packet Loss (Meraki MX)** — NOC teams monitor Meraki MX WAN uplink latency, loss, and jitter in real time to detect link degradation and trigger failover or ISP escalation before users are impacted.

Documented **Data sources**: Splunk_TA_cisco_meraki (Splunkbase #5580): Devices Uplinks Loss and Latency input (sourcetype=meraki:devicesuplinkslossandlatency, TA v3.3+, OAuth scope dashboard:general:telemetry:read). Polls GET /organizations/{orgId}/devices/uplinksLossAndLatency for every MX and MG. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: meraki; **sourcetype**: meraki:devicesuplinkslossandlatency. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

- Scopes the data: index=meraki, sourcetype="meraki:devicesuplinkslossandlatency", time bounds. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
- Extracts structured paths (JSON/XML) with `spath`.
- Expands multivalue fields with `mvexpand` — use `limit=` to cap row explosion.
- Extracts structured paths (JSON/XML) with `spath`.
- `stats` rolls up events into metrics; results are split **by serial, networkId, uplink, ip** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
- `eval` defines or adjusts **link_quality** — often to normalize units, derive a ratio, or prepare for thresholds.
- Filters the current rows with `where link_quality != "OK"` — typically the threshold or rule expression for this monitoring goal.
- Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


### Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

### Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Uplink quality scorecard; latency/jitter/loss timeline; quality gauge per uplink.

## SPL

```spl
index=meraki sourcetype="meraki:devicesuplinkslossandlatency" earliest=-1h
| spath path=timeSeries{} output=ts
| mvexpand ts
| spath input=ts
| stats avg(latencyMs) as avg_latency,
        avg(lossPercent) as avg_loss,
        max(latencyMs) as peak_latency,
        max(lossPercent) as peak_loss
         by serial, networkId, uplink, ip
| eval link_quality = case(
    avg_loss>5 OR peak_loss>20, "Critical",
    avg_loss>2 OR avg_latency>200, "Warning",
    1=1, "OK")
| where link_quality != "OK"
| sort - avg_loss
```

## Visualization

Uplink quality scorecard; latency/jitter/loss timeline; quality gauge per uplink.

## Known False Positives

Carrier work, DDNS, and weather-related outages can trigger jitter and loss alerts on a clean policy.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
