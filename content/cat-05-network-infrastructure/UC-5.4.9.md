<!-- AUTO-GENERATED from UC-5.4.9.json — DO NOT EDIT -->

---
id: "5.4.9"
title: "Client Roaming Analysis"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.4.9 · Client Roaming Analysis

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance, Anomaly

*We watch client roaming analysis so we notice problems while they are still small, and we can fix them before Wi-Fi users get dropped calls or dead spots.*

---

## Description

Poor roaming causes dropped calls, video freezes, and application timeouts. Analyzing roaming patterns identifies coverage gaps.

## Value

Network operations teams analyze wireless client roaming quality across SSIDs, measuring roam time, method effectiveness (802.11r vs. full re-auth), and failure rates to optimize RF design and ensure seamless mobility for voice and video.

## Implementation

1. Configure SC4S to receive Cisco WLC syslog. 2. The query uses transaction to group roam events per client_mac and counts roams per client. 3. If you are running Meraki MR instead: use sourcetype="meraki" type=events with type=association / type=disassociation, group by aid (Meraki association id) and look for clients seen across many APs in a short time (see UC-5.4.14 for the canonical Meraki SPL pattern). The Meraki syslog payload does not include the client MAC directly; correlation has to be done via the API-side Wireless Packet Loss by Device input or Meraki Dashboard.

## Detailed Implementation

### Prerequisites
- Wireless controller or cloud platform reporting client roaming events. Sources: (1) Cisco WLC syslog — client roaming events, 802.11r/k/v messages, (2) Meraki events — client roaming between APs, (3) Aruba controller — mobility events.
- Key fields: `client_mac`, `from_ap` (source AP), `to_ap` (destination AP), `roam_type` (802.11r fast BSS transition, OKC, full re-auth), `roam_time_ms` (transition time), `ssid`, `result` (success/failure).
- Roaming quality directly impacts user experience: voice calls drop if roaming takes > 50ms, video freezes, and applications timeout on slow roams. Fast BSS Transition (802.11r) reduces roam time to < 50ms vs. 500-2000ms for full re-authentication.

### Step 1 — Configure data collection
Verify roaming events:
```spl
index=wireless earliest=-4h
| where match(_raw, "(?i)(roam|handoff|reassoc|bss.transition|mobility)")
| stats count by sourcetype, ssid
```

### Step 2 — Create the search and alert

**Primary search — Client roaming analysis:**
```spl
index=wireless earliest=-4h
| where match(_raw, "(?i)(roam|handoff|reassoc|bss.transition)")
| eval client_id=coalesce(client_mac, src_mac)
| eval source_ap=coalesce(from_ap, ap_name)
| eval dest_ap=coalesce(to_ap, new_ap)
| eval roam_method=case(match(_raw, "(?i)11r|fast.bss|ft"), "802.11r (Fast)", match(_raw, "(?i)okc|pmkid"), "OKC/PMK Cache", match(_raw, "(?i)full.auth|re.?auth"), "Full Re-Auth", 1==1, "Standard")
| eval roam_success=case(match(_raw, "(?i)(success|complete|associated)"), "YES", match(_raw, "(?i)(fail|timeout|reject)"), "NO", 1==1, "UNKNOWN")
| stats count as roams count(eval(roam_success="NO")) as failed_roams avg(roam_time_ms) as avg_roam_ms by ssid, roam_method
| eval failure_rate=round(100*failed_roams/roams, 1)
| eval quality=case(avg_roam_ms < 50, "EXCELLENT", avg_roam_ms < 200, "GOOD", avg_roam_ms < 500, "FAIR", 1==1, "POOR")
| sort -failure_rate
```

#### Understanding this SPL: Roaming method determines quality. 802.11r (Fast BSS Transition) roams in < 50ms — seamless for voice/video. OKC/PMK caching roams in 50-200ms — acceptable for most applications. Full re-authentication takes 500-2000ms — causes voice call drops and noticeable application pauses. A high percentage of full re-auth roams on an 802.1X SSID indicates 802.11r is not properly configured.

**Frequently roaming clients (sticky or problematic):**
```spl
index=wireless earliest=-4h
| where match(_raw, "(?i)(roam|handoff|reassoc)")
| eval client_id=coalesce(client_mac, src_mac)
| stats count as roam_count dc(ap_name) as aps_visited by client_id, ssid
| where roam_count > 20
| eval roaming_pattern=case(roam_count > 100, "EXCESSIVE", roam_count > 50, "FREQUENT", 1==1, "ELEVATED")
| sort -roam_count
| head 20
```

**AP-to-AP roaming heatmap:**
```spl
index=wireless earliest=-4h
| where match(_raw, "(?i)(roam|handoff|reassoc)")
| eval from=coalesce(from_ap, ap_name)
| eval to=coalesce(to_ap, new_ap)
| where isnotnull(from) AND isnotnull(to) AND from!=to
| stats count as roams by from, to
| sort -roams
| head 30
```

### Step 3 — Validate
(a) Walk between two AP coverage areas with a voice call active and verify the roaming event appears in Splunk.
(b) Compare roaming statistics with the wireless controller's client tracking dashboard.
(c) Verify 802.11r is enabled: check the SSID configuration on the controller.

### Step 4 — Operationalize
Dashboard ("Wireless — Client Roaming"):
- Row 1 — Single-value tiles: "Total roams (4h)", "Failed roams", "Average roam time (ms)", "802.11r adoption %".
- Row 2 — Roaming quality by SSID and method.
- Row 3 — Frequently roaming clients.
- Row 4 — AP-to-AP roaming heatmap.

Alerting:
- High (roaming failure rate > 10%): RF design or configuration issue — investigate AP overlap.
- Warning (average roam time > 200ms): 802.11r may not be configured — voice quality at risk.

### Step 5 — Troubleshooting

- **All roams are "Full Re-Auth" despite 802.11r being enabled** — The client devices may not support 802.11r, or the SSID's 802.11r configuration is in mixed mode. Check client driver support for 802.11r/FT.

- **Excessive roaming for specific clients** — The client may have aggressive roaming settings or is moving in an area with overlapping AP coverage that causes "ping-pong" between APs. Adjust AP power levels to create cleaner cell boundaries.

- **Roaming failures between specific AP pairs** — These APs may not have proper mobility group configuration (Cisco) or they're on different VLANs without inter-controller mobility tunnels. Check mobility domain configuration.

## SPL

```spl
index=network sourcetype="cisco:wlc" "roam" OR "reassociation"
| transaction client_mac maxspan=1h maxpause=5m
| eval roam_count=eventcount-1
| stats avg(roam_count) as avg_roams, max(roam_count) as max_roams by client_mac, ssid
| where avg_roams > 10
```

## Visualization

Table (client, SSID, roam count), Heatmap (AP-to-AP roaming), Choropleth (floor plan).

## Known False Positives

Clients may roam often when people move between floors, during large meetings, or when access points reboot; some clients also stay 'sticky' and look noisy without a real outage.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
