<!-- AUTO-GENERATED from UC-5.10.15.json — DO NOT EDIT -->

---
id: "5.10.15"
title: "Carrier BGP Session Failover and Prefix Acceptance Tracking"
status: "verified"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.10.15 · Carrier BGP Session Failover and Prefix Acceptance Tracking

> **Criticality:** Critical &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Availability, Resilience &middot; **Wave:** Walk &middot; **Status:** Verified

*We check both whether the handshake line to our internet supplier stays up and whether we still receive the full bundle of directions we expect, so a half-working backup link cannot hide quietly.*

---

## Description

Combines SNMP BGP finite-state-machine status with accepted-prefix counters on carrier-facing peers—detecting simultaneous session impairment and silent partial reroutes when upstream filters shrink announcements without fully tearing sessions.

## Value

Architecture teams prove whether redundant uplinks actually carried expected prefixes after failover drills or carrier policy tweaks—closing blind spots where BGP stays Established yet accepted routes drop below engineered minima.

## Implementation

Poll SNMP every 60–120s; baseline `baseline_accepted_min` using steady-state observations per season; pair with syslog flap detection for root-cause narratives; throttle alerts on maintenance-flagged peers via lookup column.

## Detailed Implementation

### Prerequisites
- CISCO-BGP4-MIB enabled on PE devices with SNMP community or token scoped read-only.
- Known-good accepted-prefix counts per peer reflecting full IPv4/IPv6 families—maintain separate rows per AFI when dual-stack.
- Splunk Transform guaranteeing numeric typing (`accepted`, `denied`).
- Capacity planning for SNMP walks across hundreds of peers—consider Directed SNMP proxies.

### Step 1 — Normalize oid outputs into `snmp:cisco_bgp` sourcetype via TA props/transforms.

### Step 2 — Populate baseline CSV using thirty-day percentiles excluding maintenance spikes.

### Step 3 — Compose alerting: critical merges session_alarm + prefix_gap; informational logs gradual monotone declines >15% without crossing absolute floor.

### Step 4 — Visualization overlays transitions counter deltas versus syslog-derived flap intervals.

### Step 5 — Troubleshooting: vendor MIB omissions omit prefix counters—fallback to streaming telemetry gRPC export; vrf-aware peers require appended rd keys in lookup schema.

## SPL

```spl
index=network sourcetype="snmp:cisco_bgp" earliest=-30m
| stats latest(bgpPeerState) as peer_state latest(cbgpPeerAcceptedPrefixes) as accepted latest(cbgpPeerDeniedPrefixes) as denied latest(bgpPeerFsmEstablishedTransitions) as transitions by host, bgpPeerRemoteAddr
| lookup carrier_bgp_peers.csv peer_ip as bgpPeerRemoteAddr OUTPUT carrier site baseline_accepted_min criticality_tier max_transition_delta
| eval peer_state_num=tonumber(peer_state)
| eval established=(peer_state_num==6 OR lower(peer_state)=="established")
| eval prefix_gap=isnotnull(baseline_accepted_min) AND accepted < baseline_accepted_min
| eval session_alarm=NOT established
| eval transition_spike=isnotnull(max_transition_delta) AND transitions>max_transition_delta
| where session_alarm OR prefix_gap OR transition_spike
| eval severity=case(prefix_gap AND session_alarm,"critical", session_alarm,"high", prefix_gap,"medium", transition_spike,"medium", true(), "low")
| table host bgpPeerRemoteAddr carrier site peer_state accepted denied transitions baseline_accepted_min severity criticality_tier
| sort peer_state accepted
```

## Visualization

Dual-axis chart of accepted prefixes and peer_state code; sankey from carrier→site→peer list filtered to alarms; single-value of Established peers below quota.

## Known False Positives

Carrier-managed RR withdrawals shrink counts legitimately during congestion routing exercises; SNMPwalk restarts duplicate transitions counters—baseline deltas instead of absolutes when vendor resets counters.

## References

- [CISCO-BGP4-MIB — BGP peer metrics reference](https://www.cisco.com/c/en/us/)
- [Splunk Lantern — SNMP onboarding best practices](https://lantern.splunk.com/)
