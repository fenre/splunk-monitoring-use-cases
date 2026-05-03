<!-- AUTO-GENERATED from UC-5.20.119.json — DO NOT EDIT -->

---
id: "5.20.119"
title: "IPv6 Multicast Scoping and Boundary Enforcement"
status: "verified"
criticality: "medium"
splunkPillar: "Platform"
---

# UC-5.20.119 · IPv6 Multicast Scoping and Boundary Enforcement

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Platform &middot; **Type:** Security &middot; **Wave:** Walk &middot; **Status:** Verified

*Some messages on our network are meant for everyone in the same room (link-local), everyone in the same building (site-local), or everyone in the whole company (organization). We make sure that room messages don't accidentally get broadcast to the whole building, and building messages don't leak out to other buildings.*

---

## Description

Monitors IPv6 multicast scope boundary enforcement. IPv6 multicast addresses encode scope explicitly — link-local (ff02::), site-local (ff05::), organization (ff08::), and global (ff0e::). Traffic with a specific scope MUST NOT be forwarded beyond that scope's boundary. Scope violations indicate router misconfiguration or attack.

## Value

Multicast scope enforcement is a security boundary. If site-local multicast (ff05::) crosses site boundaries, internal service discovery, NDP, and management protocols may leak sensitive information to other sites. If link-local multicast (ff02::) is routed, NDP messages (which are link-local multicast) would be forwarded between segments, breaking the NDP security model.

## Implementation

Monitor multicast routing for scope violations. Verify multicast boundary filters are correctly configured at scope boundaries.

## Detailed Implementation

### Prerequisites
- Multicast routing (PIMv6) deployed.
- Multicast scope boundaries configured.

### Step 1 — Configure multicast boundaries

**Cisco IOS-XE multicast scope boundary:**
```
interface GigabitEthernet0/0/0
 description Site boundary
 ipv6 multicast boundary block source
 ipv6 multicast boundary scope 5
```

### Step 2 — Create monitoring searches

**Scope boundary enforcement audit:**
```spl
index=network sourcetype="cisco:*:config" earliest=-7d
| dedup host
| eval has_mcast_boundary=if(match(_raw, "(?i)multicast boundary"), 1, 0)
| stats count as total sum(has_mcast_boundary) as with_boundary
| eval coverage=round(with_boundary / total * 100, 1) . "%"
```

### Step 3 — Validate
Send a site-local multicast packet (ff05::1) at a site boundary router. Verify it is NOT forwarded across the boundary.

### Step 4 — Operationalize
**Dashboard:** Multicast scope compliance. **Alert:** Any scope violation — high.

### Step 5 — Troubleshooting
- Missing scope boundary: Add `ipv6 multicast boundary scope 5` to site border interfaces.

## SPL

```spl
index=network (sourcetype="cisco:ios" OR sourcetype="cisco:iosxe") earliest=-24h
  ("multicast" OR "ff05" OR "ff08" OR "mcast" OR "PIM")
| eval scope_violation=case(
    match(_raw, "ff05:") AND match(_raw, "(?i)forward.*site.?boundary|cross.?site"), "SITE-LOCAL scope crossing site boundary",
    match(_raw, "ff02:") AND match(_raw, "(?i)routed|forward"), "LINK-LOCAL scope being routed (MUST NOT route)",
    match(_raw, "ff01:") AND match(_raw, "(?i)forward"), "INTERFACE-LOCAL scope forwarded (MUST NOT)",
    1=1, null())
| where isnotnull(scope_violation)
| stats count as events by host, scope_violation
| eval severity="HIGH — multicast scope violation: " . scope_violation
| sort -events
```

## Visualization

(1) Table: scope violations by type and device. (2) Single-value: violation count. (3) Map: site boundaries with scope enforcement status.

## Known False Positives

**Global multicast (ff0e::).** Global-scope multicast is intentionally forwarded across all boundaries. This is not a violation.

**Organization-scope (ff08::).** ff08:: multicast is forwarded within an organization's domain but not beyond. This is expected.

## References

- [RFC 4291 — IP Version 6 Addressing Architecture (§2.7 — multicast scoping)](https://www.rfc-editor.org/rfc/rfc4291#section-2.7)
- [RFC 7346 — IPv6 Multicast Address Scopes](https://www.rfc-editor.org/rfc/rfc7346)
