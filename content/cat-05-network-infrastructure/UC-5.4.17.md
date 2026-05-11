<!-- AUTO-GENERATED from UC-5.4.17.json — DO NOT EDIT -->

---
id: "5.4.17"
title: "Rogue and Unauthorized AP Detection — Air Marshal (Meraki MR)"
criticality: "critical"
splunkPillar: "Security"
---

# UC-5.4.17 · Rogue and Unauthorized AP Detection — Air Marshal (Meraki MR)

> **Criticality:** Critical &middot; **Difficulty:** Intermediate &middot; **Pillar:** Security &middot; **Type:** Security

*We watch rogue and unauthorized ap detection — air marshal (meraki mr) so we notice problems while they are still small, and we can fix them before Wi-Fi users get dropped calls or dead spots.*

---

## Description

Identifies unauthorized wireless networks and malicious APs that may represent security threats or network intrusion attempts.

## Value

Wireless security teams detect uncontained Air Marshal SSIDs and (most critically) wired rogue APs bridged into the corporate LAN, scoring each by uncontained-BSSID count and wired-link evidence so SOC can prioritize containment.

## Implementation

1. Enable the Air Marshal input in Splunk_TA_cisco_meraki (inputs.conf entry pointing at one of getOrganizationWirelessAirMarshalRules / getNetworkWirelessAirMarshal). 2. Confirm Air Marshal is enabled on every MR network in the Meraki Dashboard (Wireless → Air Marshal). 3. The SPL pivots on the API TA's nested fields: `bssids{}.contained=false` flags an active (uncontained) rogue; `wiredLastSeen` populated means the rogue is bridged onto the wired LAN — that's the immediate-paging case. 4. The TA preserves `wiredLastSeen` as a Meraki-style "null" string when no wired sighting exists, so compare with `!="null"` rather than `isnull()`. 5. Pair with Meraki Dashboard's containment policy (Air Marshal → Configure) to auto-contain matching SSIDs after triage.

## Detailed Implementation

### Prerequisites
- Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
- Ensure the following data sources are available: Splunk_TA_cisco_meraki (Splunkbase #5580): Air Marshal input (sourcetype=meraki:airmarshal). The TA polls the Meraki Dashboard `getOrganizationWirelessAirMarshalRules`/`getNetworkWirelessAirMarshal` endpoints and emits one event per detected SSID with a top-level `ssid` field, a multi-valued `bssids{}` array (each with `bssid`, `contained` boolean, and a per-detector `detectedBy{}` array of `device` (MR serial) and `rssi`), `channels{}`, `firstSeen`, `lastSeen`, plus the high-risk `wiredLastSeen` and `wiredVlans{}` fields that fire when a rogue is bridged into the wired LAN..
- For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

### Step 1 — Configure data collection
1. Enable the Air Marshal input in Splunk_TA_cisco_meraki (inputs.conf entry pointing at one of getOrganizationWirelessAirMarshalRules / getNetworkWirelessAirMarshal). 2. Confirm Air Marshal is enabled on every MR network in the Meraki Dashboard (Wireless → Air Marshal). 3. The SPL pivots on the API TA's nested fields: `bssids{}.contained=false` flags an active (uncontained) rogue; `wiredLastSeen` populated means the rogue is bridged onto the wired LAN — that's the immediate-paging case. 4. The …

### Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=meraki sourcetype="meraki:airmarshal"
| eval is_uncontained = if(mvfind('bssids{}.contained', "false") >= 0, 1, 0)
| eval wired_ts       = coalesce(tonumber(wiredLastSeen), 0)
| eval is_wired_rogue = if(wired_ts > 0, 1, 0)
| where is_uncontained=1 OR is_wired_rogue=1
| eval threat_level = case(
    is_wired_rogue=1,                                  "critical",
    is_uncontained=1 AND mvcount('bssids{}.bssid')>=3, "high",
    is_uncontained=1,                                  "medium",
    1=1,                                                "low")
| stats values(bssids{}.bssid) as bssids,
        max(mvcount('bssids{}.bssid')) as bssid_count,
        values(channels{}) as channels,
        latest(firstSeen) as first_seen,
        latest(lastSeen) as last_seen,
        latest(wiredLastSeen) as wired_last_seen,
        latest(threat_level) as threat_level
         by ssid
| where threat_level IN ("critical","high","medium")
| sort - bssid_count
```

#### Understanding this SPL

**Rogue and Unauthorized AP Detection — Air Marshal (Meraki MR)** — Wireless security teams detect uncontained Air Marshal SSIDs and (most critically) wired rogue APs bridged into the corporate LAN, scoring each by uncontained-BSSID count and wired-link evidence so SOC can prioritize containment.

Documented **Data sources**: Splunk_TA_cisco_meraki (Splunkbase #5580): Air Marshal input (sourcetype=meraki:airmarshal). The TA polls the Meraki Dashboard `getOrganizationWirelessAirMarshalRules`/`getNetworkWirelessAirMarshal` endpoints and emits one event per detected SSID with a top-level `ssid` field, a multi-valued `bssids{}` array (each with `bssid`, `contained` boolean, and a per-detector `detectedBy{}` array of `device` (MR serial) and `rssi`), `channels{}`, `firstSeen`, `lastSeen`, plus the high-risk `wiredLastSeen` and `wiredVlans{}` fields that fire when a rogue is bridged into the wired LAN. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: meraki; **sourcetype**: meraki:airmarshal. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

- Scopes the data: index=meraki, sourcetype="meraki:airmarshal". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
- `eval` defines or adjusts **is_uncontained** — often to normalize units, derive a ratio, or prepare for thresholds.
- `eval` defines or adjusts **wired_ts** — often to normalize units, derive a ratio, or prepare for thresholds.
- `eval` defines or adjusts **is_wired_rogue** — often to normalize units, derive a ratio, or prepare for thresholds.
- Filters the current rows with `where is_uncontained=1 OR is_wired_rogue=1` — typically the threshold or rule expression for this monitoring goal.
- `eval` defines or adjusts **threat_level** — often to normalize units, derive a ratio, or prepare for thresholds.
- `stats` rolls up events into metrics; results are split **by ssid** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
- Filters the current rows with `where threat_level IN ("critical","high","medium")` — typically the threshold or rule expression for this monitoring goal.
- Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


### Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

### Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table of detected rogues with threat indicators; map showing rogue AP locations; timeline of detections.

## SPL

```spl
index=meraki sourcetype="meraki:airmarshal"
| eval is_uncontained = if(mvfind('bssids{}.contained', "false") >= 0, 1, 0)
| eval wired_ts       = coalesce(tonumber(wiredLastSeen), 0)
| eval is_wired_rogue = if(wired_ts > 0, 1, 0)
| where is_uncontained=1 OR is_wired_rogue=1
| eval threat_level = case(
    is_wired_rogue=1,                                  "critical",
    is_uncontained=1 AND mvcount('bssids{}.bssid')>=3, "high",
    is_uncontained=1,                                  "medium",
    1=1,                                                "low")
| stats values(bssids{}.bssid) as bssids,
        max(mvcount('bssids{}.bssid')) as bssid_count,
        values(channels{}) as channels,
        latest(firstSeen) as first_seen,
        latest(lastSeen) as last_seen,
        latest(wiredLastSeen) as wired_last_seen,
        latest(threat_level) as threat_level
         by ssid
| where threat_level IN ("critical","high","medium")
| sort - bssid_count
```

## Visualization

Table of detected rogues with threat indicators; map showing rogue AP locations; timeline of detections.

## Known False Positives

Failed logins often come from typos, expired passwords, guest self-service, or a single misconfigured device; treat sustained rises across many users as the real signal.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
