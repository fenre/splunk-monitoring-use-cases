<!-- AUTO-GENERATED from UC-5.13.44.json — DO NOT EDIT -->

---
id: "5.13.44"
title: "Client Roaming Event Analysis"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.13.44 · Client Roaming Event Analysis

## Description

Tracks wireless client roaming events to identify devices with excessive roaming or slow roam times that degrade real-time application performance.

## Value

Excessive or slow roaming disrupts voice and video calls. Identifying problematic clients and areas enables AP placement and configuration optimization.

## Implementation

Enable the `client` input in the Cisco Catalyst TA pointing to `index=catalyst`. The TA polls client detail from the Catalyst Center Intent API on a typical 60-minute interval. Key fields: `macAddress`, `connectionType`, `ssid`, and `roamDuration` (and any dedicated roam or mobility fields your TA version extracts in the `cisco:dnac:client` payload).

## Detailed Implementation

Prerequisites
• Cisco Catalyst Add-on (7538) with `cisco:dnac:client` and a usable `roamDuration` (or your TA’s equivalent) on wireless client records.
• When Catalyst exposes a dedicated roam or mobility event stream, switch this UC to that filter; this version treats row volume as a proxy for mobility pain.
• `docs/implementation-guide.md`.

Step 1 — Configure data collection
• Confirm the `connectionType` value for Wi-Fi in your data matches the SPL (`WIRELESS` vs other spellings).

Step 2 — Heuristic for noisy and slow mobile clients
```spl
index=catalyst sourcetype="cisco:dnac:client" connectionType="WIRELESS" | stats count as roam_count avg(roamDuration) as avg_roam_ms by macAddress, ssid | where roam_count > 3 | eval avg_roam_ms=round(avg_roam_ms,0) | sort -avg_roam_ms | head 20
```

Understanding this SPL (proxy, not 802.11 sniffer data)
**Client Roaming** — Averages `roamDuration` per MAC+SSID, filters out very quiet clients, and lists the 20 **largest** average roam times. Tighten with explicit roam flags or BSSID change fields in Assurance when you have them in the event payload.

**Pipeline walkthrough**
• Wireless only → per-MAC+SSID `stats` → `where` on minimum row count → `sort` and `head` to keep the top slow averages.

Step 3 — Validate
• Pick a top MAC and compare mobility behaviour in **Client 360** in Catalyst; expect order-of-magnitude agreement, not pixel-perfect times.

Step 4 — Operationalize
• Feed RF engineering. Pair with `cisco:dnac:wireless:rf` or AP health if available. For alerts, add a **time** bucketing (for example 15m bins) so one heavy poll is not a false spike.

Step 5 — Troubleshooting
• All null `roamDuration`: the Intent payload may not carry it; adjust field names in `props` for your Catalyst version.
• Re-verify field names after controller or TA upgrade; duplicate MACs may need a `dedup` if the add-on double-emits in one poll.


## SPL

```spl
index=catalyst sourcetype="cisco:dnac:client" connectionType="WIRELESS" | stats count as roam_count avg(roamDuration) as avg_roam_ms by macAddress, ssid | where roam_count > 3 | eval avg_roam_ms=round(avg_roam_ms,0) | sort -avg_roam_ms | head 20
```

## Visualization

Table (macAddress, ssid, roam_count, avg_roam_ms), time series of roam events if timechart added in a follow-on panel, top-N list of slowest roamers.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
- [Catalyst Center Integration Guide](docs/guides/catalyst-center.md)
