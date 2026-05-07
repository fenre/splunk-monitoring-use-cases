<!-- AUTO-GENERATED from UC-5.13.44.json — DO NOT EDIT -->

---
id: "5.13.44"
title: "Client Roaming Event Analysis"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.13.44 · Client Roaming Event Analysis

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance &middot; **Wave:** Walk &middot; **Status:** Verified

*We track when wireless devices jump from one Wi-Fi access point to another as people walk around the building. When a device keeps bouncing back and forth between two access points too quickly, it causes voice calls to drop and video to freeze. We find those trouble spots so your team can adjust the equipment and stop the bouncing.*

---

## Description

Identifies wireless clients that roam excessively between APs or experience slow roam transitions, causing VoIP drops, Webex disconnections, and application timeouts — by tracking AP association changes per client MAC address and measuring roam duration when the data is available.

## Value

A healthy roam (802.11r/k/v) completes in < 50ms — imperceptible to voice and video. A legacy roam can take 500ms–2s, causing a noticeable VoIP dropout or Webex reconnect. Clients that roam 20+ times per day between the same two APs have a coverage overlap or sticky-client problem — the client 'ping-pongs' between APs, disrupting its session each time. This UC surfaces the worst roamers and the slowest roam times so the wireless team can tune AP power, adjust band-steering, enable fast-roaming protocols (802.11r/k/v), or reposition APs to eliminate ping-pong zones.

## Implementation

Same `client` detail input as UC-5.13.40. Roaming detection uses `streamstats` to compare consecutive `apName` values per client. If your Catalyst Center/TA version includes `roamDuration`, the analysis is richer; if not, the roam event count alone is actionable. Focus on clients with > 3 roams per search window.

## Detailed Implementation

### Prerequisites
- UC-5.13.40 (Client Inventory) operational — same `client` detail input.
- This UC uses `streamstats` to detect roaming by comparing consecutive `apName` values for each client MAC. This requires:
  - `apName` field populated in the events (verify: `| stats dc(apName) as ap_count | where ap_count > 1`)
  - Sufficient poll frequency (900s) to capture roaming events. At 3600s intervals, many roams happen between polls and are invisible.
- If your Catalyst Center/TA version exposes `roamDuration`, `previousApName`, or `roamType`, the analysis is richer. Check: `| fieldsummary | search field IN ("roamDuration","previousApName","roamType")`.
- Understand 802.11 roaming protocols:
  - **802.11r (FT)**: fast BSS transition — pre-authenticates with the target AP. Roam time: 10–50ms.
  - **802.11k**: neighbor reports — client learns nearby APs without scanning. Reduces roam latency.
  - **802.11v**: BSS transition management — AP can suggest a better AP to the client. Reduces unnecessary roaming.
  - **Legacy roaming**: client does a full scan + authenticate + associate. Roam time: 500ms–2s+.
  The difference between fast and legacy roaming is the difference between a seamless VoIP call and a 2-second gap that causes the other person to say "hello? are you there?"

### Step 1 — Configure data collection
Same `client` detail input as UC-5.13.40. Confirm `apName` is populated:
```spl
index=catalyst sourcetype="cisco:dnac:client" connectionType="WIRELESS" earliest=-1h
| stats dc(apName) as aps, dc(macAddress) as clients
```
If `aps = 0`, the `apName` field is not extracted — check field name variants: `apName`, `ap_name`, `accessPoint`.

Check for roaming fields:
```spl
index=catalyst sourcetype="cisco:dnac:client" connectionType="WIRELESS" earliest=-24h
| fieldsummary
| search field IN ("roamDuration","previousApName","roamType","roamCount")
```
If these fields exist, your analysis will be richer. If not, use the `streamstats` approach to detect roams by `apName` change.

### Step 2 — Create the search and report
Option A — `streamstats` approach (works without dedicated roaming fields):
```spl
index=catalyst sourcetype="cisco:dnac:client" connectionType="WIRELESS"
| sort macAddress, _time
| streamstats current=f last(apName) as prev_ap by macAddress
| where apName != prev_ap AND isnotnull(prev_ap)
| stats count as roam_count dc(apName) as aps_visited avg(roamDuration) as avg_roam_ms by macAddress, ssid
| where roam_count > 3
| eval avg_roam_ms=round(coalesce(avg_roam_ms, -1), 0)
| sort -roam_count
| head 20
```

Option B — if `roamDuration` / `roamCount` fields exist:
```spl
index=catalyst sourcetype="cisco:dnac:client" connectionType="WIRELESS" roamCount > 0
| stats sum(roamCount) as total_roams avg(roamDuration) as avg_roam_ms max(roamDuration) as worst_roam_ms by macAddress, ssid
| where total_roams > 3
| sort -total_roams
| head 20
```

Why `streamstats current=f last(apName) as prev_ap by macAddress`: this looks at the *previous* event for each MAC address and compares the AP name. When `apName != prev_ap`, the client roamed between those two polls. This is a proxy for actual roaming events — some roams may happen between polls and be invisible (especially with 900s intervals).

Why `where roam_count > 3`: 1–3 roams per search window is normal for mobile users. > 3 in a few hours suggests problematic behaviour (ping-ponging, excessive scanning).

Why `dc(apName) as aps_visited`: shows how many distinct APs the client associated with. `roam_count = 20` with `aps_visited = 2` means the client is bouncing between two APs (classic ping-pong). `roam_count = 20` with `aps_visited = 10` means the client is genuinely mobile (walking across campus).

Why `avg_roam_ms = -1` when not available: `coalesce(avg_roam_ms, -1)` marks clients where `roamDuration` is not in the data, distinguishing "unknown roam time" from "0ms roam time." Display as "N/A" in the dashboard.

This is a diagnostic report, not a real-time alert. Schedule weekly for the wireless engineering team.

### Step 3 — Validate
(a) Walk across your campus with a test laptop running a continuous ping to the gateway. Count the ping drops (each drop ≈ one roam event). The `roam_count` for that MAC in the Splunk search should approximately match your ping-drop count (within the poll-interval granularity).

(b) In **Catalyst Center > Assurance > Client 360 > [a known roamer]**, check the roaming history. The number of roams and the APs visited should correspond to the Splunk results.

(c) Check for `streamstats` accuracy: the detection relies on consecutive events being ordered by `_time`. If event ordering is disrupted (clock skew, overlapping polls), false roam detections can occur. Validate by checking `| stats count(eval(apName != prev_ap AND isnotnull(prev_ap))) as roams, dc(apName) as aps by macAddress` — `roams` should never exceed `2 × (aps - 1)` for normal movement patterns.

(d) If `roamDuration` is available, validate by comparing with a packet capture (Wireshark) on the wireless interface during a test roam.

### Step 4 — Operationalize
Dashboard placement (on a "Wireless Performance" or "Roaming Analysis" dashboard):
- Table: top 20 roamers with MAC, SSID, roam_count, aps_visited, avg_roam_ms.
- Classify roaming quality: `| eval roam_quality=case(avg_roam_ms > 0 AND avg_roam_ms < 50, "Fast (good)", avg_roam_ms >= 50 AND avg_roam_ms < 200, "Moderate", avg_roam_ms >= 200, "Slow (investigate)", 1==1, "Duration unknown")`
- Campus roaming volume: `| timechart span=1h sum(roam_count) as total_roams` over 7 days.

Runbook (owner: Wireless Engineering):
1. Identify the top roaming clients. Check `aps_visited`:
   - If `aps_visited = 2` with high `roam_count`: this is an **AP ping-pong** problem. The client is equidistant between two APs. Fix: reduce power on one AP, enable sticky-client mitigation, or reposition the AP.
   - If `aps_visited > 5`: the client is genuinely mobile (nurse in a hospital, warehouse worker). Optimise roaming protocols: enable 802.11r/k/v on the WLC.
2. Check `avg_roam_ms`:
   - < 50ms: fast roaming is working. No action needed even with high roam count.
   - 50–200ms: moderate. Check whether 802.11r/k/v is enabled for the SSID.
   - > 200ms: slow legacy roaming. Likely 802.11r is not enabled or the client doesn't support it. Check client supplicant capabilities.
3. For VoIP-specific issues: correlate high-roam clients with VoIP quality metrics (jitter, packet loss) from UC-based monitoring or Webex analytics.
4. After tuning (enabling 802.11r, adjusting power, repositioning APs): monitor this UC for 1 week to confirm improvement.

### Step 5 — Troubleshooting

- **`streamstats` produces no roam detections** — all clients are associated with the same AP (very small site), or `apName` is not populated. Check `| stats dc(apName)` — if 1, there's only one AP visible to the service account.

- **`roamDuration` is always null** — your Catalyst Center/TA version doesn't expose this field. Use roam count and aps_visited as the primary metrics. Roam duration can be estimated by correlating with syslog roaming events if available.

- **Excessive roam count for all clients** — the `streamstats` approach may over-count if events are out of order. Add `| sort 0 macAddress _time` before `streamstats` to ensure strict ordering.

- **A client shows 100+ roams but only 2 APs** — classic ping-pong. The client is oscillating rapidly. Check the signal strength (UC-5.13.42) from both APs at the client's location. If RSSI from both is similar (-65 to -70), reduce power on one AP to create a clear winner.

- **Search is very slow** — `streamstats` is computationally expensive because it processes events sequentially. Narrow to `earliest=-4h` for analysis. For weekly reports, use summary indexing to pre-compute roam events.

- **Roaming analysis doesn't match the Catalyst Center Client 360** — the `streamstats` approach detects roaming by poll-to-poll AP changes, which is an approximation. Catalyst Center may use real-time association events for more precise roaming tracking. Directional agreement is expected; exact match is not.

- **Mobile clients flagged as problematic** — users walking between buildings legitimately roam many times. Use `aps_visited` and `avg_roam_ms` to distinguish healthy mobile users (many APs, fast roams) from problematic ping-pong clients (2 APs, many roams).

- **802.11r enabled but roam times still slow** — the client device may not support 802.11r (older iOS, some Android devices, legacy enterprise laptops). Check the client's capabilities in Catalyst Center > Client 360 > Radio Info.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:client" connectionType="WIRELESS"
| sort macAddress, _time
| streamstats current=f last(apName) as prev_ap by macAddress
| where apName != prev_ap AND isnotnull(prev_ap)
| stats count as roam_count dc(apName) as aps_visited avg(roamDuration) as avg_roam_ms by macAddress, ssid
| where roam_count > 3
| eval avg_roam_ms=round(coalesce(avg_roam_ms, -1), 0)
| sort -roam_count
| head 20
```

## Visualization

(1) Table: macAddress, ssid, roam_count, aps_visited, avg_roam_ms — sorted by roam_count descending (worst 'ping-pongers' first). (2) Sankey or flow diagram showing client flow between APs (if Dashboard Studio supports it). (3) Timechart: `| timechart span=1h sum(roam_count) as total_roams` for campus-wide roaming volume trend. (4) Single value: clients with > 10 roams/hour (red if > 5).

## Known False Positives

**Mobile users walking between buildings.** Users physically moving between buildings legitimately roam between APs. Distinguish by checking whether the `aps_visited` value corresponds to APs in different buildings (correlate with `siteId` if available). Do not suppress — but these roams are expected and healthy. Investigate only when `avg_roam_ms` is high (> 200ms), indicating the roam is slow despite being legitimate.

**Client 'ping-ponging' between two APs with overlapping coverage.** A client positioned equidistant between two APs may oscillate rapidly between them — associating with one, then the other, then back. Distinguish by checking whether `aps_visited = 2` with high `roam_count`. Suppress by tuning AP power to reduce overlap, or enabling sticky-client mitigation on the WLC.

**VoIP/video clients showing high roam count but healthy call quality.** 802.11r/k/v fast roaming can complete in < 20ms, so even 10 roams per hour may not impact the application. Distinguish by checking `avg_roam_ms` — if < 50ms, the roaming is healthy. Suppress by only alerting when `avg_roam_ms > 200`.

**`roamDuration` not available in your Catalyst Center version.** Without `roamDuration`, you can only count roam events, not measure their impact. The event count is still useful for identifying ping-pong clients. Do not suppress — adapt the analysis to use roam count as the severity metric instead of roam duration.

## References

- [Cisco Catalyst Add-on for Splunk (Splunkbase 7538)](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center Intent API — Client Detail endpoint](https://developer.cisco.com/docs/catalyst-center/#!get-client-detail)
- [Catalyst Center Integration Guide (this repo)](../../docs/guides/catalyst-center.md)
- [Cisco 802.11r, 802.11k, 802.11v — Fast Roaming Best Practices](https://www.cisco.com/c/en/us/td/docs/wireless/controller/technotes/8-x/Fast_Secure_Roaming.html)
