<!-- AUTO-GENERATED from UC-5.13.42.json — DO NOT EDIT -->

---
id: "5.13.42"
title: "Client RSSI/SNR Quality Monitoring (Wireless)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.13.42 · Client RSSI/SNR Quality Monitoring (Wireless)

## Description

Monitors wireless client signal quality (RSSI and SNR) by SSID and location to identify areas with poor wireless coverage.

## Value

Poor RSSI and SNR directly cause slow connections, dropped sessions, and user complaints. Monitoring these metrics proactively finds coverage gaps.

## Implementation

Enable the `client` input in the Cisco Catalyst TA pointing to `index=catalyst`. The TA polls client detail data from the Catalyst Center Intent API every 60 minutes. Key fields: `macAddress`, `hostType`, `connectionType`, `ssid`, `vlanId`, `location`, `healthScore`, `rssi`, `snr`.

## Detailed Implementation

Prerequisites
• Cisco Catalyst Add-on (7538) with **client** data including **wireless** fields `rssi` and `snr` in `cisco:dnac:client` events.
• Confirm the literal value for `connectionType` for Wi-Fi in your data (`WIRELESS` vs `Wireless` or similar) before relying on the filter; adjust the `where` to match if needed.
• `docs/implementation-guide.md` and `docs/guides/catalyst-center.md`.

Step 1 — Configure data collection
• If `location` is blank, aggregate by `ssid` only or join site/building from device or topology data outside this UC.

Step 2 — RSSI / SNR by SSID and location
```spl
index=catalyst sourcetype="cisco:dnac:client" connectionType="WIRELESS" | stats avg(rssi) as avg_rssi avg(snr) as avg_snr count as client_count by ssid, location | eval signal_quality=case(avg_rssi>=-65,"Good",avg_rssi>=-75,"Fair",1==1,"Poor") | sort avg_rssi
```

Understanding this SPL (RF health from client perspective)
**RSSI and SNR** — Surfaces the weakest **average** experience per `ssid` and `location` bucket. Tighten the `case` cutoffs for voice or 6 GHz–only designs as your RF team specifies.

**Pipeline walkthrough**
• Wireless events only, then `stats` of average `rssi`/`snr` and a simple label from RSSI, sorted ascending (worst average RSSI at the top after sort).

Step 3 — Validate
• Pick one `ssid`+`location` marked Poor and open Catalyst **Client 360** or Assurance wireless views for a sample MAC on that segment; confirm poor RF is plausible.
• Check for `rssi` nulls—`avg()` may hide missing samples; consider `count` of null in a support panel.

Step 4 — Operationalize
• Alert when `avg_rssi` stays below -75 for multiple poll cycles for the same `ssid`+`location` (use a trend or summary index; single polls can be noisy). Pair with `cisco:dnac:wireless:rf` or AP health UCs if available.

Step 5 — Troubleshooting
• Empty results: `connectionType` mismatch, or all wireless in another sourcetype—`fieldsummary connectionType` on the index.
• `location` changing labels between polls: normalise in `eval` to building code or `siteName` if present.
• SNR or RSSI from wired mis-tagged: verify raw JSON for a few WIRELESS rows.


## SPL

```spl
index=catalyst sourcetype="cisco:dnac:client" connectionType="WIRELESS" | stats avg(rssi) as avg_rssi avg(snr) as avg_snr count as client_count by ssid, location | eval signal_quality=case(avg_rssi>=-65,"Good",avg_rssi>=-75,"Fair",1==1,"Poor") | sort avg_rssi
```

## Visualization

Table (ssid, location, avg_rssi, avg_snr, signal_quality), heat map or geospatial chart if `location` is normalized, threshold-based alerts on Poor signal_quality.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
- [Catalyst Center Integration Guide](docs/guides/catalyst-center.md)
