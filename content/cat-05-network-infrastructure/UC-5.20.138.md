<!-- AUTO-GENERATED from UC-5.20.138.json — DO NOT EDIT -->

---
id: "5.20.138"
title: "IPv6 Transition Mechanism Sunset and Deprecation Tracking"
status: "verified"
criticality: "medium"
splunkPillar: "Platform"
---

# UC-5.20.138 · IPv6 Transition Mechanism Sunset and Deprecation Tracking

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Platform &middot; **Type:** Compliance, Security &middot; **Wave:** Walk &middot; **Status:** Verified

*When we first started using IPv6, we built temporary bridges between the old and new systems. Some of those bridges are now old, rickety, and have known security holes. We check that nobody is still using the old bridges when a proper modern road (native IPv6) is available, and we track progress in tearing down the old ones.*

---

## Description

Tracks use of deprecated IPv6 transition mechanisms (6to4, Teredo, ISATAP) and active transition technologies (NAT64, 464XLAT, MAP-E). As native IPv6 deployment progresses, deprecated mechanisms should be actively removed. Continuing to use them introduces security risks and operational complexity.

## Value

Deprecated transition mechanisms (especially 6to4 and Teredo) create tunnel endpoints that bypass IPv6 security policies, inject traffic from the IPv4 internet into the IPv6 network, and are exploited for covert channels. Tracking their sunset progress ensures a clean, secure IPv6 deployment. Active mechanisms (NAT64, 464XLAT) should also be tracked for lifecycle management.

## Implementation

Detect deprecated and active transition mechanism traffic patterns. Track sunset progress over time.

## Detailed Implementation

### Prerequisites
- Firewall and router logging with IPv6 tunnel protocol visibility.

### Step 1 — Identify all transition mechanisms in use.

### Step 2 — Classify as deprecated (6to4, ISATAP) vs active (NAT64, 464XLAT).

### Step 3 — Validate: Verify deprecated mechanisms are not needed. Test native IPv6 connectivity as replacement.

### Step 4 — Operationalize
**Dashboard:** Transition mechanism lifecycle. **Report:** Monthly sunset progress.

### Step 5 — Troubleshooting
- Disable 6to4: Remove 2002::/16 routes and tunnel interfaces.
- Disable Teredo: Windows: `netsh interface teredo set state disabled`
- Disable ISATAP: Windows: `netsh interface isatap set state disabled`

## SPL

```spl
index=network (sourcetype="cisco:ios" OR sourcetype="paloalto:traffic" OR sourcetype="netflow") earliest=-7d
| eval deprecated_mechanism=case(
    match(_raw, "(?i)6to4|2002:|proto.?41.*6to4"), "6to4 (DEPRECATED per RFC 7526)",
    match(_raw, "(?i)teredo|3544|2001:0000:"), "Teredo (limited use — disable when not needed)",
    match(_raw, "(?i)isatap|fe80::5efe:"), "ISATAP (deprecated — disable)",
    match(_raw, "(?i)6rd"), "6rd (carrier-managed — verify necessity)",
    match(_raw, "(?i)nat64|464xlat|well.?known.*prefix.*64:ff9b"), "NAT64/464XLAT (active transition)",
    match(_raw, "(?i)map-e|map-t"), "MAP-E/MAP-T (carrier CGN)",
    1=1, null())
| where isnotnull(deprecated_mechanism)
| stats count as events dc(src) as unique_sources by deprecated_mechanism
| eval status=case(
    match(deprecated_mechanism, "DEPRECATED"), "ACTION REQUIRED — deprecated mechanism still in use",
    match(deprecated_mechanism, "disable"), "RECOMMEND — disable unless actively needed",
    1=1, "INFO — active transition mechanism")
| sort -events
```

## Visualization

(1) Bar chart: transition mechanisms by type. (2) Trend: deprecated mechanism use over time (should decrease). (3) Table: sources using deprecated mechanisms.

## Known False Positives

**Carrier-managed mechanisms.** ISPs may use 6rd, MAP-E, or DS-Lite legitimately. These are not deprecated but should be tracked.

**Lab environments.** Test networks may use transition mechanisms for testing. Exclude known lab ranges.

## References

- [RFC 7526 — Deprecating the Anycast Prefix for 6to4 Relay Routers](https://www.rfc-editor.org/rfc/rfc7526)
- [RFC 7059 — A Comparison of IPv6 over IPv4 Tunnel Mechanisms](https://www.rfc-editor.org/rfc/rfc7059)
