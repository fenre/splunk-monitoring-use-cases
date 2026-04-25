<!-- AUTO-GENERATED from UC-5.13.63.json — DO NOT EDIT -->

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
• `Cisco Catalyst Add-on for Splunk` (7538) with `client` and, if available, `clienthealth` inputs to `index=catalyst` (Intent API client listing and health).

Step 1 — TA data path (Catalyst Center)
• `cisco:dnac:client` should include `connectionType` (use `WIRELESS`), `ssid`, `macAddress`, and a numeric experience field such as `healthScore` (confirm with `| fieldsummary`).
• `cisco:dnac:clienthealth` is optional for a **join** on `macAddress` if you need richer per-client metrics than this aggregate gives.

Step 2 — Search

```spl
index=catalyst sourcetype="cisco:dnac:client" connectionType="WIRELESS" | stats avg(healthScore) as avg_experience avg(rssi) as avg_rssi dc(macAddress) as client_count by ssid | eval experience_rating=case(avg_experience>=8,"Excellent",avg_experience>=6,"Good",avg_experience>=4,"Fair",1==1,"Poor") | sort avg_experience
```

Step 3 — Optional join
`index=catalyst (sourcetype="cisco:dnac:client" OR sourcetype="cisco:dnac:clienthealth")` with `join` or `stats` on `macAddress` when the TA stores scores only on the health sourcetype.

Step 4 — Validate
• Compare a few SSIDs to **Catalyst Center > Wireless > Clients** and any Assurance “experience” view for the same time window. Watch for `ssid` that is BSSID or internal — normalize in **props** if required.

Step 5 — Operationalize and troubleshooting
• **Weekly** Wi-Fi review: focus on the bottom SSIDs, not a single outlier client. **No `ssid`:** the TA may use `wlan` or a profile name — add `coalesce` in `stats by` until fields match the UI. **RSSI in wrong units:** some builds store dBm as negative; keep comparisons consistent. **This is not a site survey** — it is a fleet hint for triage, not a replacement for on-site validation.


## SPL

```spl
index=catalyst sourcetype="cisco:dnac:client" connectionType="WIRELESS" | stats avg(healthScore) as avg_experience avg(rssi) as avg_rssi dc(macAddress) as client_count by ssid | eval experience_rating=case(avg_experience>=8,"Excellent",avg_experience>=6,"Good",avg_experience>=4,"Fair",1==1,"Poor") | sort avg_experience
```

## Visualization

Bar chart of `avg_experience` by `ssid`, table (ssid, experience_rating, client_count, avg_rssi), single value of worst SSID by score.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
