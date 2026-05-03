<!-- AUTO-GENERATED from UC-5.20.127.json — DO NOT EDIT -->

---
id: "5.20.127"
title: "IS-IS for IPv6 (Multi-Topology IS-IS) Adjacency and LSP Monitoring"
status: "verified"
criticality: "high"
splunkPillar: "Platform"
---

# UC-5.20.127 · IS-IS for IPv6 (Multi-Topology IS-IS) Adjacency and LSP Monitoring

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Platform &middot; **Type:** Availability &middot; **Wave:** Walk &middot; **Status:** Verified

*IS-IS is the road map system used by the biggest postal networks. It keeps separate road maps for old (IPv4) and new (IPv6) addresses. We watch the IPv6 road map separately to make sure the routes for new-format letters are always correct, even if the old-format routes are fine.*

---

## Description

Monitors IS-IS multi-topology for IPv6 adjacency health, LSP integrity, and authentication status. IS-IS is the primary IGP for large-scale IPv6 deployments (ISPs, data centers). Multi-topology IS-IS runs separate IPv4 and IPv6 topologies, so IPv6 adjacency failures are independent of IPv4.

## Value

IS-IS is the dominant IGP for large-scale IPv6 networks. Multi-topology IS-IS means IPv6 routing can fail independently of IPv4 — a router can have full IPv4 reachability while IPv6 routes are missing. Dedicated IS-IS IPv6 monitoring catches these independent failures that would be missed by monitoring only IPv4 routing health.

## Implementation

Monitor IS-IS adjacency events filtered for IPv6 multi-topology. Track LSP integrity and authentication.

## Detailed Implementation

### Prerequisites
- IS-IS deployed with multi-topology for IPv6.
- IS-IS logging enabled.

### Step 1 — Verify multi-topology IS-IS
```
router isis CORE
 address-family ipv6 unicast
  multi-topology
```

### Step 2 — Create monitoring searches
```spl
index=network "ISIS" "ipv6" earliest=-24h | stats count by host, isis_event
```

### Step 3 — Validate: Verify IS-IS IPv6 adjacencies with `show isis neighbors` and `show isis ipv6 route`.

### Step 4 — Operationalize
**Dashboard:** IS-IS IPv6 health. **Alert:** IPv6 adjacency down — critical.

### Step 5 — Troubleshooting
- IPv6 adjacency down but IPv4 up: Check multi-topology configuration. Verify `address-family ipv6` is enabled on the interface.

## SPL

```spl
index=network (sourcetype="cisco:ios" OR sourcetype="cisco:iosxe" OR sourcetype="juniper:junos") earliest=-24h
  ("%ISIS" OR "%CLNS" OR "is-is")
| eval isis_event=case(
    match(_raw, "(?i)ADJ.*DOWN|adjacency.*down"), "ADJ_DOWN",
    match(_raw, "(?i)ADJ.*UP|adjacency.*up"), "ADJ_UP",
    match(_raw, "(?i)LSP.*corrupt|checksum.*fail|LSP.*error"), "LSP_ERROR",
    match(_raw, "(?i)authentication.*fail|auth.*mismatch"), "AUTH_FAILURE",
    match(_raw, "(?i)MT.*ipv6|topology.*2"), "MT_IPV6_EVENT",
    1=1, "OTHER")
| eval is_ipv6_related=if(match(_raw, "(?i)ipv6|MT.*2|topology.*2|multi.?topology"), 1, 0)
| stats count as events by host, isis_event, is_ipv6_related
| eval severity=case(
    isis_event="ADJ_DOWN" AND is_ipv6_related=1, "CRITICAL — IS-IS IPv6 adjacency DOWN",
    isis_event="AUTH_FAILURE", "CRITICAL — IS-IS authentication failure",
    isis_event="LSP_ERROR", "HIGH — IS-IS LSP corruption detected",
    1=1, null())
| where isnotnull(severity)
| sort -events
```

## Visualization

(1) Table: IS-IS events by type. (2) Timeline: adjacency changes. (3) Single-value: authentication failures. (4) Topology map: IS-IS adjacency status.

## Known False Positives

**Planned maintenance.** IS-IS adjacency flaps during maintenance. Correlate with change windows.

**Single-topology IS-IS.** If not using multi-topology, IPv4 and IPv6 share adjacencies. IPv6-specific events won't be distinguishable.

## References

- [RFC 5308 — Routing IPv6 with IS-IS](https://www.rfc-editor.org/rfc/rfc5308)
- [RFC 5120 — IS-IS Multi-Topology Routing](https://www.rfc-editor.org/rfc/rfc5120)
