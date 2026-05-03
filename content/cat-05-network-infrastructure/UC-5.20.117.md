<!-- AUTO-GENERATED from UC-5.20.117.json — DO NOT EDIT -->

---
id: "5.20.117"
title: "IPv6 NDP Neighbour Unreachability Detection (NUD) Failure Monitoring"
status: "verified"
criticality: "medium"
splunkPillar: "Platform"
---

# UC-5.20.117 · IPv6 NDP Neighbour Unreachability Detection (NUD) Failure Monitoring

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Platform &middot; **Type:** Availability &middot; **Wave:** Walk &middot; **Status:** Verified

*The router periodically checks if its neighbours are still there — like knocking on the door to see if they're home. If nobody answers after several tries, the router marks them as 'gone.' We monitor these 'nobody home' reports to quickly find out when devices on the network have stopped responding.*

---

## Description

Monitors NDP Neighbour Unreachability Detection (NUD) state transitions, specifically PROBE→FAILED transitions that indicate a previously reachable neighbour is now unreachable. High NUD failure rates on an interface indicate link failures, switch issues, or host outages that affect IPv6 connectivity.

## Value

NUD is the IPv6 mechanism for confirming neighbours remain reachable — equivalent to ARP keepalives in IPv4 but more sophisticated. When NUD reports a neighbour as FAILED, IPv6 traffic to that neighbour is dropped. Monitoring NUD failures provides early detection of link problems, host failures, and switch issues before they are reported by users.

## Implementation

Monitor NDP state transition logs for FAILED entries. Correlate with interface up/down events and host availability.

## Detailed Implementation

### Prerequisites
- Router/switch NDP logging enabled.
- Splunk receiving NDP syslog events.

### Step 1 — Configure data collection

NDP NUD events are logged at informational level. Ensure `logging buffered 8192 informational` is configured and NDP events are forwarded to Splunk via syslog.

### Step 2 — Create monitoring searches

**NUD failure rate by interface:**
```spl
index=network (sourcetype="cisco:ios" OR sourcetype="cisco:iosxe") earliest=-24h
  "FAILED" AND "neighbor"
| rex field=_raw "interface\s*(?<interface>\S+)"
| timechart span=15m count by interface
```

**Correlated with interface flaps:**
```spl
index=network (sourcetype="cisco:ios" OR sourcetype="cisco:iosxe") earliest=-24h
  ("FAILED" AND "neighbor") OR "%LINK" OR "%LINEPROTO"
| eval event_type=if(match(_raw, "FAILED"), "NUD_FAILURE", "LINK_EVENT")
| timechart span=5m count by event_type
```

### Step 3 — Validate
(a) Shut down a test host on a monitored VLAN. Verify NUD failure is logged within 30-60 seconds.

(b) Bring the host back up. Verify the neighbour transitions back to REACHABLE.

### Step 4 — Operationalize

**Dashboard** ("IPv6 — NDP Health"): NUD failures by interface, unreachable neighbour list, correlation with link events.

**Alert:** >20 NUD failures on a single interface in 15 minutes — possible switch/link failure.

### Step 5 — Troubleshooting

- **All neighbours on one interface failing.** The switch port, VLAN, or cable is likely down. Check physical layer.

- **Single neighbour repeatedly failing.** The host may have a bad NIC, incorrect IPv6 configuration, or firewall blocking NS/NA.

## SPL

```spl
index=network (sourcetype="cisco:ios" OR sourcetype="cisco:iosxe") earliest=-4h
  ("%IPV6_ND" OR "NUD" OR "PROBE" OR "FAILED" OR "neighbor.*unreachable")
| eval nud_event=case(
    match(_raw, "(?i)FAILED|unreachable|no.*response"), "NUD_FAILED",
    match(_raw, "(?i)STALE"), "NUD_STALE",
    match(_raw, "(?i)PROBE"), "NUD_PROBE",
    1=1, "OTHER")
| rex field=_raw "neighbor\s*(?<neighbor_ip>[0-9a-fA-F:]+)"
| rex field=_raw "interface\s*(?<interface>\S+)"
| stats count as events dc(neighbor_ip) as unique_neighbors by host, interface, nud_event
| where nud_event="NUD_FAILED" AND events > 5
| eval severity=case(
    unique_neighbors > 20, "HIGH — " . unique_neighbors . " neighbours unreachable on " . host . " " . interface . " — link or switch failure",
    unique_neighbors > 5, "MEDIUM — multiple neighbours unreachable",
    1=1, "LOW — isolated neighbour unreachability")
| sort -unique_neighbors
```

## Visualization

(1) Timechart: NUD failure rate by interface. (2) Table: unreachable neighbours. (3) Single-value: total NUD failures. (4) Correlation: NUD failures vs interface flaps.

## Known False Positives

**Mobile devices.** Phones and laptops that leave the network naturally cause NUD failures for their addresses. High mobility environments will have higher NUD failure rates.

**Sleep/hibernate.** Devices that sleep or hibernate become NUD-unreachable until they wake. This is normal for endpoint environments.

## References

- [RFC 4861 — Neighbor Discovery for IP version 6 (IPv6) (§7.3 — NUD)](https://www.rfc-editor.org/rfc/rfc4861#section-7.3)
