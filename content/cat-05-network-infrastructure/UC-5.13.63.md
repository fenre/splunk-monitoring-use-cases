---
id: "5.13.63"
title: "Wireless Client Experience Score by SSID"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.13.63 · Wireless Client Experience Score by SSID

## Description

Calculates a per-SSID wireless client experience score combining health, signal strength, and client count to identify which wireless networks deliver the best and worst experience.

## Value

Different SSIDs serve different purposes and user populations. Per-SSID experience scoring reveals which wireless networks need optimization.

## Implementation

Use the **TA’s existing inputs** (no custom Intent poller for this UC if the fields are present): `clienthealth` from `/dna/intent/api/v1/client-health` and `client` from `/dna/intent/api/v1/client` (or the TA’s equivalent endpoints) into `cisco:dnac:clienthealth` and `cisco:dnac:client`. This Splunk search primarily uses `cisco:dnac:client` with `connectionType=WIRELESS` to segment wireless clients, then `stats` by `ssid` using `healthScore` and `rssi` (confirm field names in your data — Cisco may use `clientHealth` or similar; add `| fieldsummary` in Search if needed). Enable both inputs in the Catalyst TA to `index=catalyst`.

## Detailed Implementation

Prerequisites
• `Cisco Catalyst Add-on for Splunk` (7538) with `client` and ideally `clienthealth` inputs enabled to `index=catalyst` (see UCs in this category that use client telemetry).

Step 1 — TA data path
- `cisco:dnac:client` — from Catalyst Center client list/detail polling; should include `connectionType` (filter `WIRELESS`), `ssid` or equivalent BSSID-SSID resolution, `macAddress`, and experience fields (`healthScore` or the TA’s mapping).
- `cisco:dnac:clienthealth` — optional additional enrichment if you build a `join` on `macAddress` for richer per-client KPIs; the default SPL averages within `cisco:dnac:client` only.

Run `| fieldsummary` on a small window to confirm `healthScore`, `rssi`, and `ssid` field names; alias in `props.conf` if the TA uses different case.

Step 2 — Search

```spl
index=catalyst sourcetype="cisco:dnac:client" connectionType="WIRELESS" | stats avg(healthScore) as avg_experience avg(rssi) as avg_rssi dc(macAddress) as client_count by ssid | eval experience_rating=case(avg_experience>=8,"Excellent",avg_experience>=6,"Good",avg_experience>=4,"Fair",1==1,"Poor") | sort avg_experience
```

Step 3 — Optional join
`index=catalyst (sourcetype="cisco:dnac:client" OR sourcetype="cisco:dnac:clienthealth")` then `stats` or `join` on `macAddress` for composite scoring.

Step 4 — Validate
Compare top/bottom SSIDs to Catalyst Center Wireless → Clients / assurance insights.

Step 5 — Operationalize
Wi-Fi engineering review weekly; not a replacement for 802.11 on-site survey but a fleet-wide health signal.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:client" connectionType="WIRELESS" | stats avg(healthScore) as avg_experience avg(rssi) as avg_rssi dc(macAddress) as client_count by ssid | eval experience_rating=case(avg_experience>=8,"Excellent",avg_experience>=6,"Good",avg_experience>=4,"Fair",1==1,"Poor") | sort avg_experience
```

## Visualization

Bar chart of `avg_experience` by `ssid`, table (ssid, experience_rating, client_count, avg_rssi), single value of worst SSID by score.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
