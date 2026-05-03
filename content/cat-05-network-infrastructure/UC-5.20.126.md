<!-- AUTO-GENERATED from UC-5.20.126.json — DO NOT EDIT -->

---
id: "5.20.126"
title: "IPv6 OSPFv3 Authentication and LSA Integrity Monitoring"
status: "verified"
criticality: "high"
splunkPillar: "Platform"
---

# UC-5.20.126 · IPv6 OSPFv3 Authentication and LSA Integrity Monitoring

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Platform &middot; **Type:** Security, Availability &middot; **Wave:** Walk &middot; **Status:** Verified

*Routers tell each other about the best roads to use for delivering letters (routing). If a rogue router lies about the roads, letters go to the wrong place. We watch for forged road announcements and make sure all routers prove their identity with a password (IPsec authentication) before sharing road information.*

---

## Description

Monitors OSPFv3 (the IPv6 routing protocol) for authentication failures, neighbour state changes, LSA anomalies, and routing instability. OSPFv3 uses IPsec AH or Authentication Trailer (RFC 7166) for security — without these, routing is vulnerable to injection attacks.

## Value

OSPFv3 is the primary IGP for IPv6 in many enterprise networks. Without authentication (IPsec AH or AT), an attacker on any segment with an OSPFv3-enabled interface can inject fake routes, causing traffic diversion or black holes. Monitoring authentication status and LSA integrity is essential for routing security.

## Implementation

Monitor OSPFv3 events for authentication failures, neighbour state changes, and LSA anomalies. Verify IPsec AH or Authentication Trailer is configured.

## Detailed Implementation

### Prerequisites
- OSPFv3 deployed for IPv6 routing.
- OSPFv3 logging enabled.

### Step 1 — Configure OSPFv3 authentication
**Cisco IOS-XE (IPsec AH):**
```
interface GigabitEthernet0/0/0
 ospfv3 authentication ipsec spi 256 sha1 <key>
```

**Cisco IOS-XE (Authentication Trailer — RFC 7166):**
```
router ospfv3 1
 address-family ipv6 unicast
  area 0 authentication key-chain OSPFV3-AUTH
```

### Step 2 — Create monitoring searches
```spl
index=network "OSPFv3" earliest=-24h | stats count by host, ospfv3_event
```

### Step 3 — Validate
Disable OSPFv3 auth on a test interface. Verify the neighbour drops and auth failure is logged.

### Step 4 — Operationalize
**Dashboard:** OSPFv3 health. **Alert:** Auth failure — critical. Neighbour down — high.

### Step 5 — Troubleshooting
- Auth mismatch: Verify SPI and key match on both sides. Check key-chain for correct algorithm.

## SPL

```spl
index=network (sourcetype="cisco:ios" OR sourcetype="cisco:iosxe" OR sourcetype="juniper:junos") earliest=-24h
  ("%OSPFV3" OR "%OSPFv3" OR "ospf3")
| eval ospfv3_event=case(
    match(_raw, "(?i)auth.*fail|authentication.*fail|IPsec.*fail"), "AUTH_FAILURE",
    match(_raw, "(?i)ADJCHANGE.*DOWN|neighbor.*down"), "NEIGHBOR_DOWN",
    match(_raw, "(?i)ADJCHANGE.*FULL|neighbor.*full"), "NEIGHBOR_UP",
    match(_raw, "(?i)LSA.*inject|LSA.*flood|max.?age.*LSA"), "LSA_ANOMALY",
    match(_raw, "(?i)SPF.*run|recalculat"), "SPF_RUN",
    1=1, "OTHER")
| eval is_ipv6=if(match(_raw, "(?i)ipv6|OSPFv3"), 1, 0)
| where is_ipv6=1
| stats count as events by host, ospfv3_event
| eval severity=case(
    ospfv3_event="AUTH_FAILURE", "CRITICAL — OSPFv3 authentication failure — possible route injection attack",
    ospfv3_event="NEIGHBOR_DOWN", "HIGH — OSPFv3 neighbor down — IPv6 routing impacted",
    ospfv3_event="LSA_ANOMALY", "HIGH — unusual LSA activity — verify routing integrity",
    ospfv3_event="SPF_RUN" AND events > 10, "MEDIUM — excessive SPF recalculations (" . events . ") — routing instability",
    1=1, null())
| where isnotnull(severity)
| sort -events
```

## Visualization

(1) Table: OSPFv3 events by type and device. (2) Single-value: auth failures. (3) Timeline: neighbour state changes. (4) SPF run count chart.

## Known False Positives

**Planned maintenance.** OSPFv3 neighbour flaps during maintenance are expected. Correlate with change windows.

**SPF during convergence.** After a topology change, multiple SPF runs are normal until the network converges.

## References

- [RFC 5340 — OSPF for IPv6 (OSPFv3)](https://www.rfc-editor.org/rfc/rfc5340)
- [RFC 4552 — Authentication/Confidentiality for OSPFv3 (IPsec)](https://www.rfc-editor.org/rfc/rfc4552)
- [RFC 7166 — Supporting Authentication Trailer for OSPFv3](https://www.rfc-editor.org/rfc/rfc7166)
