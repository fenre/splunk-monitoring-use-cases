<!-- AUTO-GENERATED from UC-5.4.29.json — DO NOT EDIT -->

---
id: "5.4.29"
title: "Mesh Network Link Quality and Backhaul Health (Meraki MR)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.4.29 · Mesh Network Link Quality and Backhaul Health (Meraki MR)

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Availability

*We watch mesh network link quality and backhaul health (meraki mr) so we notice problems while they are still small, and we can fix them before Wi-Fi users get dropped calls or dead spots.*

---

## Description

Monitors wireless mesh backhaul links to ensure reliability of remote AP connections.

## Value

Wireless security teams detect and classify active wireless attacks (deauthentication floods, MAC spoofing, EAPOL capture attempts) from Meraki security events, enabling rapid incident response.

## Implementation

1. Enable the Assurance Alerts input. Mesh / repeater / backhaul issues surface as wireless device alerts in the assurance feed. 2. Optionally enable the Wireless Devices Ethernet Statuses input (sourcetype=meraki:wirelessdevicesethernetstatuses) which reports per-AP Ethernet link speed, duplex, aggregation, and PoE status — useful for distinguishing wired vs mesh-uplinked APs. 3. For deeper visibility (per-mesh-link RSSI/bandwidth) use the Meraki Dashboard Wireless -> Mesh page or scrape its API endpoint with a custom modular input.

## Detailed Implementation

### Prerequisites
- Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
- Ensure the following data sources are available: Splunk_TA_cisco_meraki (Splunkbase #5580): Assurance Alerts input (sourcetype=meraki:assurancealerts). NOTE: per-mesh-link RSSI and bandwidth metrics are NOT exposed by the polled Dashboard API; mesh health is inferred from wireless connectivity alerts and (where available) the Wireless Devices Ethernet Statuses input which reports backhaul Ethernet status..
- For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

### Step 1 — Configure data collection
1. Enable the Assurance Alerts input. Mesh / repeater / backhaul issues surface as wireless device alerts in the assurance feed. 2. Optionally enable the Wireless Devices Ethernet Statuses input (sourcetype=meraki:wirelessdevicesethernetstatuses) which reports per-AP Ethernet link speed, duplex, aggregation, and PoE status — useful for distinguishing wired vs mesh-uplinked APs. 3. For deeper visibility (per-mesh-link RSSI/bandwidth) use the Meraki Dashboard Wireless -> Mesh page or scrape its AP…

### Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=meraki sourcetype="meraki:assurancealerts"
    deviceType="wireless"
    (title="*mesh*" OR title="*backhaul*" OR title="*repeater*"
     OR categoryType="connectivity")
    earliest=-24h
| stats count as alert_count,
        values(title) as mesh_alerts,
        latest(severity) as severity
         by deviceSerial, deviceName, networkName
| sort - alert_count
```

#### Understanding this SPL

**Mesh Network Link Quality and Backhaul Health (Meraki MR)** — Wireless security teams detect and classify active wireless attacks (deauthentication floods, MAC spoofing, EAPOL capture attempts) from Meraki security events, enabling rapid incident response.

Documented **Data sources**: Splunk_TA_cisco_meraki (Splunkbase #5580): Assurance Alerts input (sourcetype=meraki:assurancealerts). NOTE: per-mesh-link RSSI and bandwidth metrics are NOT exposed by the polled Dashboard API; mesh health is inferred from wireless connectivity alerts and (where available) the Wireless Devices Ethernet Statuses input which reports backhaul Ethernet status. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: meraki; **sourcetype**: meraki:assurancealerts. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

- Scopes the data: index=meraki, sourcetype="meraki:assurancealerts", time bounds. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
- `stats` rolls up events into metrics; results are split **by deviceSerial, deviceName, networkName** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
- Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


### Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

### Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Network topology showing link quality; color-coded links; detail table with metrics.

## SPL

```spl
index=meraki sourcetype="meraki:assurancealerts"
    deviceType="wireless"
    (title="*mesh*" OR title="*backhaul*" OR title="*repeater*"
     OR categoryType="connectivity")
    earliest=-24h
| stats count as alert_count,
        values(title) as mesh_alerts,
        latest(severity) as severity
         by deviceSerial, deviceName, networkName
| sort - alert_count
```

## Visualization

Network topology showing link quality; color-coded links; detail table with metrics.

## Known False Positives

Wireless metrics move with user behavior, maintenance, and nearby RF; we tune alerts around change windows and known busy hours so normal days do not page the team.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
