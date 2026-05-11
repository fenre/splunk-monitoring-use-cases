<!-- AUTO-GENERATED from UC-5.20.118.json — DO NOT EDIT -->

---
id: "5.20.118"
title: "IPv6 Bogon and Martian Address Filtering Verification"
status: "verified"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.20.118 · IPv6 Bogon and Martian Address Filtering Verification

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Security &middot; **Type:** Security, Compliance &middot; **Wave:** Walk &middot; **Status:** Verified

*There are certain address ranges that should never appear on the public internet — they're like phone numbers reserved for movies (555-0100). We check our network borders to make sure nobody is sending mail using these fake addresses, because someone using a fake address is either making a mistake or trying something sneaky.*

---

## Description

Verifies that IPv6 bogon and martian addresses (documentation, benchmarking, deprecated, loopback, unspecified, 6bone, 6to4) are properly filtered at network borders. Any bogon address appearing in permitted traffic indicates a firewall policy gap that could be exploited for spoofing or routing attacks.

## Value

Bogon filtering is the first line of defence against IPv6 spoofing and routing attacks. Documentation addresses (2001:db8::) in production traffic indicate either a misconfiguration or a test environment leaking. Deprecated addresses (6to4, site-local, 6bone) in transit indicate forgotten infrastructure. This UC verifies that border ACLs and firewall policies are correctly filtering all IPv6 bogon categories.

## Implementation

Monitor border firewall traffic for IPv6 bogon addresses. Verify bogons are denied. Alert on any permitted bogon traffic.

## Detailed Implementation

### Prerequisites
- Border firewall logging enabled for both permit and deny actions.
- IPv6 bogon ACL or address group configured on border devices.

### Step 1 — Configure bogon filtering

**Cisco IOS-XE IPv6 bogon ACL:**
```
ipv6 access-list IPV6-BOGON-FILTER
 remark Block documentation prefix
 deny ipv6 2001:db8::/32 any log
 deny ipv6 any 2001:db8::/32 log
 remark Block 6bone
 deny ipv6 3ffe::/16 any log
 deny ipv6 any 3ffe::/16 log
 remark Block 6to4
 deny ipv6 2002::/16 any log
 deny ipv6 any 2002::/16 log
 remark Block deprecated site-local
 deny ipv6 fec0::/10 any log
 remark Block loopback
 deny ipv6 host ::1 any log
 deny ipv6 any host ::1 log
 remark Block discard
 deny ipv6 100::/64 any log
 remark Permit everything else
 permit ipv6 any any
!
interface GigabitEthernet0/0/0
 description Internet-facing
 ipv6 traffic-filter IPV6-BOGON-FILTER in
```

### Step 2 — Create monitoring searches

**Bogon leak detection (permitted bogons — should be zero):**
```spl
index=network earliest=-24h action="allowed"
| eval bogon=case(
    match(src, "^2001:0?[Dd][Bb]8:") OR match(dest, "^2001:0?[Dd][Bb]8:"), 1,
    match(src, "^3[Ff][Ff][Ee]:") OR match(dest, "^3[Ff][Ff][Ee]:"), 1,
    match(src, "^2002:") OR match(dest, "^2002:"), 1,
    match(src, "^[Ff][Ee][Cc]0:") OR match(dest, "^[Ff][Ee][Cc]0:"), 1,
    1=1, 0)
| where bogon=1
| stats count by src, dest, host
```

### Step 3 — Validate
Send traffic from a source using 2001:db8::1 through the border firewall. Verify it is denied and logged.

### Step 4 — Operationalize
**Dashboard:** Bogon filtering status. Alert on any permitted bogon — critical.

### Step 5 — Troubleshooting
- Permitted bogons indicate missing or misordered ACL entries. Verify ACL is applied to the correct interface and direction.

## SPL

```spl
index=network (sourcetype="pan:traffic" OR sourcetype="cisco:asa" OR sourcetype="cisco:ftd") earliest=-24h
| eval src_bogon=case(
    match(src, "^2001:0?[Dd][Bb]8:"), "documentation (2001:db8::/32)",
    match(src, "^2001:0?0?0?2:"), "benchmarking (2001:2::/48)",
    match(src, "^2002:"), "6to4 deprecated (2002::/16)",
    match(src, "^[Ff][Ee][Cc]0:"), "site-local deprecated (fec0::/10)",
    match(src, "^0100:"), "discard prefix (100::/64)",
    match(src, "^::1$"), "loopback (::1)",
    match(src, "^::$"), "unspecified (::)",
    match(src, "^::[Ff]{4}:"), "IPv4-mapped (::ffff:0:0/96)",
    match(src, "^3[Ff][Ff][Ee]:"), "6bone decommissioned (3ffe::/16)",
    1=1, null())
| eval dst_bogon=case(
    match(dest, "^2001:0?[Dd][Bb]8:"), "documentation (2001:db8::/32)",
    match(dest, "^2002:"), "6to4 deprecated (2002::/16)",
    match(dest, "^[Ff][Ee][Cc]0:"), "site-local deprecated (fec0::/10)",
    match(dest, "^3[Ff][Ff][Ee]:"), "6bone decommissioned (3ffe::/16)",
    1=1, null())
| where isnotnull(src_bogon) OR isnotnull(dst_bogon)
| eval bogon_type=coalesce(src_bogon, dst_bogon)
| eval direction=if(isnotnull(src_bogon), "SOURCE", "DESTINATION")
| stats count as events by host, bogon_type, direction, action
| eval severity=case(
    action="allowed", "CRITICAL — bogon traffic PERMITTED through firewall",
    action="denied" OR action="blocked", "OK — bogon traffic correctly blocked",
    1=1, "REVIEW")
| sort -events
```

## Visualization

(1) Table: bogon detections by type and action. (2) Single-value: permitted bogons (should be zero). (3) Pie chart: bogon type distribution. (4) Trend: bogon detection over time.

## Known False Positives

**Lab/test environments.** Documentation addresses (2001:db8::) are intentionally used in labs. Exclude lab firewall zones from production monitoring.

**6rd deployments.** Some ISPs still use 6rd (which uses 2002:: prefix space). If 6rd is deployed, 2002:: traffic is expected. Document and exclude.

## References

- [Team Cymru — IPv6 Bogon Reference](https://team-cymru.com/community-services/bogon-reference/)
- [RFC 3849 — IPv6 Address Prefix Reserved for Documentation](https://www.rfc-editor.org/rfc/rfc3849)
- [IANA — IPv6 Special-Purpose Address Registry](https://www.iana.org/assignments/iana-ipv6-special-registry/)
