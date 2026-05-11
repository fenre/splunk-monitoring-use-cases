<!-- AUTO-GENERATED from UC-5.20.129.json — DO NOT EDIT -->

---
id: "5.20.129"
title: "IPv6 Wireless Client Roaming and Handoff Address Continuity"
status: "verified"
criticality: "medium"
splunkPillar: "Platform"
---

# UC-5.20.129 · IPv6 Wireless Client Roaming and Handoff Address Continuity

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Platform &middot; **Type:** Availability, Performance &middot; **Wave:** Walk &middot; **Status:** Verified

*When you walk from one room to another in a building, your phone switches between different WiFi antennas. We make sure that when this happens, your device doesn't lose its new-format address (IPv6) and doesn't get disconnected from whatever you were doing.*

---

## Description

Monitors IPv6 address continuity during wireless client roaming. Tracks L2 and L3 roaming events, identifies roaming failures that cause IPv6 address loss, and detects L3 roaming events that trigger IPv6 renumbering. Ensures NDP state, RA Guard policies, and SLAAC/DHCPv6 are consistent across all wireless infrastructure.

## Value

Wireless roaming is the most common scenario where IPv6 addresses change unexpectedly. L3 roaming forces clients into new /64 prefixes, breaking existing connections. L2 roaming should preserve addresses but can cause issues if NDP state isn't properly transferred. Monitoring roaming events with IPv6 context ensures wireless users maintain IPv6 connectivity during mobility.

## Implementation

Monitor WLC roaming events. Correlate with IPv6 address changes. Track DAD events post-roaming.

## Detailed Implementation

### Prerequisites
- Cisco WLC or EWC with logging enabled.
- Splunk Add-on for Cisco WLC installed.

### Step 1 — Enable roaming event logging on WLC.

### Step 2 — Create monitoring searches for L3 roaming events and failures.

### Step 3 — Validate: Force a test client to roam between APs. Verify IPv6 address continuity.

### Step 4 — Operationalize
**Dashboard:** Wireless IPv6 roaming health. **Alert:** Roaming failures >5% — medium.

### Step 5 — Troubleshooting
- L3 roaming IPv6 address change: Configure mobility anchoring or LISP to maintain client addresses across L3 boundaries.

## SPL

```spl
index=network sourcetype="cisco:wlc:syslog" earliest=-24h
  ("roam" OR "handoff" OR "mobility" OR "anchor" OR "L2-roam" OR "L3-roam")
| eval is_ipv6_relevant=if(match(_raw, "(?i)ipv6|RA|NDP|SLAAC|DHCPv6"), 1, 0)
| eval roam_type=case(
    match(_raw, "(?i)L2.?roam|intra.?vlan"), "L2_ROAM",
    match(_raw, "(?i)L3.?roam|inter.?vlan|mobility.?anchor"), "L3_ROAM",
    match(_raw, "(?i)roam.*fail|handoff.*fail"), "ROAM_FAILURE",
    1=1, "ROAM_EVENT")
| rex field=_raw "client\s*(?<client_mac>[0-9a-fA-F:.]+)"
| stats count as events by roam_type, is_ipv6_relevant
| eval concern=case(
    roam_type="ROAM_FAILURE", "HIGH — roaming failures may cause IPv6 address loss",
    roam_type="L3_ROAM" AND is_ipv6_relevant=1, "MEDIUM — L3 roam triggers IPv6 renumbering",
    1=1, null())
| where isnotnull(concern)
| sort -events
```

## Visualization

(1) Table: roaming events with IPv6 impact. (2) Timechart: roaming events by type. (3) Single-value: roaming failures.

## Known False Positives

**Normal L2 roaming.** L2 roaming events are very frequent in wireless networks. Only L3 roaming and roaming failures are IPv6-impacting.

**Client sleep/wake.** Clients going to sleep and waking appear as mobility events but don't involve actual roaming.

## References

- [RFC 4861 — Neighbor Discovery for IPv6 (§7 — NDP state management)](https://www.rfc-editor.org/rfc/rfc4861)
- [RFC 7772 — Reducing Energy Consumption of Router Advertisements (wireless context)](https://www.rfc-editor.org/rfc/rfc7772)
