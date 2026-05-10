<!-- AUTO-GENERATED from UC-5.4.23.json — DO NOT EDIT -->

---
id: "5.4.23"
title: "Multicast and Broadcast Storm Detection (Meraki MR)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.4.23 · Multicast and Broadcast Storm Detection (Meraki MR)

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Anomaly

*We watch multicast and broadcast storm detection (meraki mr) so we notice problems while they are still small, and we can fix them before Wi-Fi users get dropped calls or dead spots.*

---

## Description

Identifies multicast/broadcast flooding that degrades wireless performance across multiple client devices.

## Value

Facilities and wireless teams estimate location-based occupancy from Meraki MR client counts per zone, detecting near-capacity areas for facilities planning and proactive wireless capacity management.

## Implementation

1. Configure SC4S for MR syslog with the Flows category enabled. 2. Filter for broadcast / multicast destinations. 3. Per-source-MAC packet counts > 1000 in an hour usually indicate a misbehaving IoT device or a broadcast-storm-causing app. 4. Cross-reference with the wired side: if the same MAC appears on the MS switch syslog flooding messages it confirms the source is on a wired port.

## Detailed Implementation

### Prerequisites
- Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
- Ensure the following data sources are available: SC4S Meraki vendor pack (sourcetype=meraki) receiving MR L3 firewall flow logs. Broadcast / multicast traffic surfaces in flows with dst=255.255.255.255 (broadcast), dst in 224.0.0.0/4 (multicast), or mac=ff:ff:ff:ff:ff:ff (broadcast MAC)..
- For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

### Step 1 — Configure data collection
1. Configure SC4S for MR syslog with the Flows category enabled. 2. Filter for broadcast / multicast destinations. 3. Per-source-MAC packet counts > 1000 in an hour usually indicate a misbehaving IoT device or a broadcast-storm-causing app. 4. Cross-reference with the wired side: if the same MAC appears on the MS switch syslog flooding messages it confirms the source is on a wired port.

### Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=meraki sourcetype="meraki" (type=flows OR type=firewall)
    (dst="255.255.255.255" OR dst="224.*" OR dst="239.*"
     OR mac="ff:ff:ff:ff:ff:ff")
    earliest=-1h
| rex "src=(?<src_ip>[\d\.]+)"
| rex "mac=(?<src_mac>[0-9A-Fa-f:]+)"
| rex "protocol=(?<proto>\S+)"
| stats count as packet_count,
        values(src_ip) as sources,
        values(proto) as protos
         by host, src_mac
| where packet_count > 1000
| sort - packet_count
```

#### Understanding this SPL

**Multicast and Broadcast Storm Detection (Meraki MR)** — Facilities and wireless teams estimate location-based occupancy from Meraki MR client counts per zone, detecting near-capacity areas for facilities planning and proactive wireless capacity management.

Documented **Data sources**: SC4S Meraki vendor pack (sourcetype=meraki) receiving MR L3 firewall flow logs. Broadcast / multicast traffic surfaces in flows with dst=255.255.255.255 (broadcast), dst in 224.0.0.0/4 (multicast), or mac=ff:ff:ff:ff:ff:ff (broadcast MAC). **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: meraki; **sourcetype**: meraki. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

- Scopes the data: index=meraki, sourcetype="meraki", time bounds. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
- Extracts fields with `rex` (regular expression).
- Extracts fields with `rex` (regular expression).
- Extracts fields with `rex` (regular expression).
- `stats` rolls up events into metrics; results are split **by host, src_mac** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
- Filters the current rows with `where packet_count > 1000` — typically the threshold or rule expression for this monitoring goal.
- Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` sum(All_Traffic.bytes) as bytes
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.dvc span=1h
| where bytes>0
| sort -bytes
```

Understanding this CIM / accelerated SPL

**Multicast and Broadcast Storm Detection (Meraki MR)** — Facilities and wireless teams estimate location-based occupancy from Meraki MR client counts per zone, detecting near-capacity areas for facilities planning and proactive wireless capacity management.

Documented **Data sources**: SC4S Meraki vendor pack (sourcetype=meraki) receiving MR L3 firewall flow logs. Broadcast / multicast traffic surfaces in flows with dst=255.255.255.255 (broadcast), dst in 224.0.0.0/4 (multicast), or mac=ff:ff:ff:ff:ff:ff (broadcast MAC). **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

- Uses `tstats` against accelerated summaries for data model `Network_Traffic.All_Traffic` — enable acceleration for that model.
- Filters the current rows with `where bytes>0` — typically the threshold or rule expression for this monitoring goal.
- Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


### Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

### Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table of broadcast sources; time-series of broadcast packets; alert threshold dashboard.

## SPL

```spl
index=meraki sourcetype="meraki" (type=flows OR type=firewall)
    (dst="255.255.255.255" OR dst="224.*" OR dst="239.*"
     OR mac="ff:ff:ff:ff:ff:ff")
    earliest=-1h
| rex "src=(?<src_ip>[\d\.]+)"
| rex "mac=(?<src_mac>[0-9A-Fa-f:]+)"
| rex "protocol=(?<proto>\S+)"
| stats count as packet_count,
        values(src_ip) as sources,
        values(proto) as protos
         by host, src_mac
| where packet_count > 1000
| sort - packet_count
```

## CIM SPL

```spl
| tstats `summariesonly` sum(All_Traffic.bytes) as bytes
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.dvc span=1h
| where bytes>0
| sort -bytes
```

## Visualization

Table of broadcast sources; time-series of broadcast packets; alert threshold dashboard.

## Known False Positives

Backup jobs, imaging, and video can create heavy wireless flows; confirm with the app owner before assuming abuse or a misbehaving client.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
