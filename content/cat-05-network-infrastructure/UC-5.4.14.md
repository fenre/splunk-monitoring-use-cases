<!-- AUTO-GENERATED from UC-5.4.14.json — DO NOT EDIT -->

---
id: "5.4.14"
title: "Excessive Client Roaming Activity (Meraki MR)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.4.14 · Excessive Client Roaming Activity (Meraki MR)

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance

*We watch excessive client roaming activity (meraki mr) so we notice problems while they are still small, and we can fix them before Wi-Fi users get dropped calls or dead spots.*

---

## Description

Detects unstable roaming patterns and AP handoff issues that cause latency spikes and dropped connections.

## Value

Network operations teams detect excessive wireless client roaming on Meraki MR networks, identifying ping-pong patterns between AP pairs to optimize RF design, power levels, and cell boundaries.

## Implementation

Track client handoff events between APs. Alert when a single client roams more than threshold in a 15-minute window.

## Detailed Implementation

### Prerequisites
- Meraki events showing client roaming between APs. Data in `index=meraki` with `sourcetype=meraki:events`. Key fields: `client_mac`, `type` (association/disassociation/roaming), `ap_name`/`deviceName`, `ssid`, `rssi`.
- Excessive roaming (client bouncing between APs) causes: session interruptions, increased authentication overhead, and poor user experience. Common causes: (1) overlapping AP coverage with similar signal strength — client can't decide which AP is better, (2) sticky clients — device holds onto weak AP instead of roaming, (3) AP power levels too high — creating co-channel interference.

### Step 1 — Configure data collection
Verify roaming events:
```spl
index=meraki sourcetype="meraki:events" earliest=-4h
| where match(type, "(?i)(assoc|roam)") AND isnotnull(client_mac)
| stats count by type
```

### Step 2 — Create the search and alert

**Primary search — Excessive roaming detection:**
```spl
index=meraki sourcetype="meraki:events" earliest=-4h
| where match(type, "(?i)(assoc|roam)")
| eval ap_id=coalesce(ap_name, deviceName)
| stats count as roam_events dc(ap_id) as aps_visited list(ap_id) as ap_sequence by client_mac, ssid
| where roam_events > 15 AND aps_visited > 3
| eval roam_pattern=case(roam_events > 50 AND aps_visited < 4, "PING_PONG", roam_events > 30, "EXCESSIVE", roam_events > 15, "FREQUENT", 1==1, "NORMAL")
| eval issue_hint=case(roam_pattern="PING_PONG", "Client bouncing between 2-3 APs — overlapping coverage or power issue", roam_pattern="EXCESSIVE", "Highly mobile user or client driver issue", 1==1, "Monitor — may be a mobile user")
| sort -roam_events
| head 20
```

**AP-pair roaming analysis:**
```spl
index=meraki sourcetype="meraki:events" earliest=-4h
| where match(type, "(?i)(assoc|roam)")
| sort client_mac, _time
| streamstats current=t window=1 last(ap_name) as prev_ap by client_mac
| where isnotnull(prev_ap) AND ap_name != prev_ap
| stats count as transitions by prev_ap, ap_name
| where transitions > 10
| sort -transitions
```

### Step 3 — Validate
(a) Walk between two APs repeatedly and verify the roaming events accumulate.
(b) Compare with Meraki Dashboard: Wireless > Monitor > Clients > select a specific client > Event log.
(c) Identify a known "problem client" and verify it appears in the excessive roaming list.

### Step 4 — Operationalize
Dashboard ("Meraki — Client Roaming"):
- Row 1 — Single-value tiles: "Ping-pong clients", "Excessive roamers", "Total roam events", "Average roams/client".
- Row 2 — Excessive roaming clients table with pattern classification.
- Row 3 — AP-pair roaming hotspots (which AP pairs have the most transitions).

Alerting:
- Warning (client with > 50 roams in 4 hours): ping-pong or driver issue — investigate.
- Info (AP pair with > 30 transitions): RF boundary issue — consider power adjustment.

### Step 5 — Troubleshooting

- **Ping-pong between two APs** — Both APs are at similar signal strength in the overlap area. Reduce power on one AP, or adjust the client minimum RSSI threshold (Meraki: Wireless > Radio settings > Minimum bitrate).

- **Specific client model roams excessively** — Some device drivers (especially older Windows) have aggressive roaming algorithms. Push driver updates or adjust roaming aggressiveness via MDM/GPO.

- **Roaming spikes during specific hours** — May correlate with people moving between areas (meetings, lunch). This is normal behavior.

## SPL

```spl
index=cisco_network sourcetype="meraki" type=security_event (signature="*Roaming*" OR signature="*handoff*")
| stats count as roam_count by client_mac, ap_name
| eventstats sum(roam_count) as total_roams by client_mac
| where total_roams > 20
| sort -total_roams
```

## Visualization

Table of heavy roamers; line chart of roaming frequency by client; network diagram showing roam paths.

## Known False Positives

Clients may roam often when people move between floors, during large meetings, or when access points reboot; some clients also stay 'sticky' and look noisy without a real outage.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
