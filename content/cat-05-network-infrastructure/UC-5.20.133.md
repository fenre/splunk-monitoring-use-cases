<!-- AUTO-GENERATED from UC-5.20.133.json — DO NOT EDIT -->

---
id: "5.20.133"
title: "IPv6 Anycast Service Health and Routing Consistency"
status: "verified"
criticality: "medium"
splunkPillar: "Platform"
---

# UC-5.20.133 · IPv6 Anycast Service Health and Routing Consistency

> **Criticality:** Medium &middot; **Difficulty:** Advanced &middot; **Pillar:** Platform &middot; **Type:** Availability, Performance &middot; **Wave:** Run &middot; **Status:** Verified

*Some important services (like the phone book for the internet) have copies in many cities. Your computer automatically goes to the nearest copy. We make sure your computer consistently reaches the same copy and doesn't keep switching between cities, which would slow things down.*

---

## Description

Monitors IPv6 anycast service health and routing consistency. Tracks which anycast instances clients are reaching, detects routing instability causing flapping between instances, and verifies consistent service behavior. Essential for DNS resolvers, CDN endpoints, and other anycast-dependent services.

## Value

Anycast is fundamental to IPv6 service delivery (DNS root servers, CDN, DDoS mitigation). Routing instability can cause clients to rapidly switch between anycast instances, potentially causing cache misses (DNS), session resets (TCP), and inconsistent responses. Monitoring anycast routing stability ensures optimal service delivery.

## Implementation

Track next-hop diversity for known anycast destinations. Monitor for rapid anycast instance changes.

## Detailed Implementation

### Prerequisites
- NetFlow/IPFIX with next-hop information.
- List of known anycast IPv6 addresses.

### Step 1 — Create anycast address lookup.
### Step 2 — Monitor next-hop diversity for anycast destinations.
### Step 3 — Validate: Verify DNS queries to anycast resolvers return consistent results.
### Step 4 — Operationalize: Dashboard and alerting for anycast routing instability.
### Step 5 — Troubleshooting: Excessive instance changes indicate BGP instability on the anycast prefix path.

## SPL

```spl
index=network sourcetype="netflow" earliest=-4h
| eval is_anycast=if(match(dest, "^2001:4860:4860::(8888|8844)$") OR match(dest, "^2606:4700:4700::(1111|1001)$") OR match(dest, "^2620:119:35::35$"), 1, 0)
| where is_anycast=1
| stats dc(next_hop) as anycast_instances count as flows by dest
| eval status=case(
    anycast_instances > 3, "WARNING — " . anycast_instances . " different anycast instances seen — possible routing instability",
    anycast_instances > 1, "OK — " . anycast_instances . " anycast instances (normal for multi-homed)",
    1=1, "OK — stable single instance")
| table dest, anycast_instances, flows, status
```

## Visualization

(1) Table: anycast destinations with instance count. (2) Timeline: instance changes. (3) Latency to anycast services.

## Known False Positives

**Multi-path routing.** ECMP may distribute flows across different anycast instances. This is normal for load-balanced anycast.

**BGP convergence.** During BGP convergence after a topology change, temporary anycast instance changes are expected.

## References

- [RFC 4786 — Operation of Anycast Services](https://www.rfc-editor.org/rfc/rfc4786)
- [RFC 7094 — Architectural Considerations of IP Anycast](https://www.rfc-editor.org/rfc/rfc7094)
