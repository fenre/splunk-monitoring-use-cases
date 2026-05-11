<!-- AUTO-GENERATED from UC-5.20.63.json — DO NOT EDIT -->

---
id: "5.20.63"
title: "IPv6 Bogon and Martian Prefix Filtering Verification"
status: "verified"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.20.63 · IPv6 Bogon and Martian Prefix Filtering Verification

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Security &middot; **Type:** Security, Compliance &middot; **Wave:** Walk &middot; **Status:** Verified

*There are certain addresses in IPv6 that should never appear on the public internet — like test addresses, internal-only addresses, and addresses from systems that were shut down years ago. They're like fake IDs.*

---

## Description

Detects IPv6 traffic with bogon or martian source/destination addresses at the network perimeter. Bogon addresses are addresses that should never appear in transit traffic — they indicate source address spoofing, misconfiguration, or deprecated tunnel leakage. IPv6 has a significantly larger bogon list than IPv4 because many prefixes have been allocated for special purposes, deprecated, or reserved. Filtering bogon traffic is a fundamental security hygiene practice required by RFC 9099, NIST SP 800-119, and BCP 38/84.

## Value

Bogon traffic at the perimeter is always suspicious. Documentation addresses (2001:db8::/32) in production traffic indicate test configuration leaked to production. Link-local addresses (fe80::/10) in routed traffic indicate a routing misconfiguration. Deprecated 6to4 addresses (2002::/16) indicate legacy tunnel leakage (UC-5.20.57). ULA addresses (fc00::/7) crossing the perimeter indicate internal address leakage. Detecting any of these provides immediate actionable intelligence for remediation.

## Implementation

Apply bogon prefix-lists at all perimeter interfaces. Log denied bogon traffic. Monitor the deny log for bogon detections. Alert on any detection. Maintain the bogon list by updating from Team Cymru or equivalent sources.

## Detailed Implementation

### Prerequisites
- Bogon prefix-lists deployed on all perimeter routers and firewalls.
- Logging enabled for bogon prefix-list denials.
- Team Cymru or equivalent bogon reference for list updates.

### Step 1 — Configure data collection

**Cisco IOS-XE — IPv6 bogon prefix-list:**
```
ipv6 prefix-list BOGON_V6 seq 5 deny ::/128
ipv6 prefix-list BOGON_V6 seq 10 deny ::1/128
ipv6 prefix-list BOGON_V6 seq 15 deny ::ffff:0:0/96 le 128
ipv6 prefix-list BOGON_V6 seq 20 deny 64:ff9b::/96 le 128
ipv6 prefix-list BOGON_V6 seq 25 deny 100::/64 le 128
ipv6 prefix-list BOGON_V6 seq 30 deny 2001:db8::/32 le 128
ipv6 prefix-list BOGON_V6 seq 35 deny 2001::/32 le 128
ipv6 prefix-list BOGON_V6 seq 40 deny 2002::/16 le 128
ipv6 prefix-list BOGON_V6 seq 45 deny 3ffe::/16 le 128
ipv6 prefix-list BOGON_V6 seq 50 deny fc00::/7 le 128
ipv6 prefix-list BOGON_V6 seq 55 deny fe80::/10 le 128
ipv6 prefix-list BOGON_V6 seq 60 deny fec0::/10 le 128
ipv6 prefix-list BOGON_V6 seq 65 deny ff00::/8 le 128
ipv6 prefix-list BOGON_V6 seq 100 permit ::/0 le 128
```

Apply to BGP peers:
```
router bgp 65001
 address-family ipv6 unicast
  neighbor 2001:db8:ff::1 prefix-list BOGON_V6 in
```

Apply to interface ACL:
```
ipv6 access-list PERIMETER_IN
 remark === Deny bogon sources ===
 deny ipv6 ::/128 any log
 deny ipv6 ::1/128 any log
 deny ipv6 ::ffff:0:0/96 any log
 deny ipv6 2001:db8::/32 any log
 deny ipv6 2002::/16 any log
 deny ipv6 fc00::/7 any log
 deny ipv6 fe80::/10 any log
 deny ipv6 fec0::/10 any log
 remark === Permit everything else ===
 permit ipv6 any any
```

**Verification:**
```spl
index=network sourcetype="cisco:ios" "BOGON" OR "access-list" "deny" ("fe80" OR "2001:db8" OR "fc00" OR "2002:" OR "fec0") earliest=-7d
| stats count by host
```

### Step 2 — Create the search and alert

**Bogon source detection at perimeter:**
```spl
index=network (sourcetype="pan:traffic" OR sourcetype="cisco:ios" OR sourcetype="netflow") earliest=-1h
| rex field=_raw "(?:src|source)\s*=?\s*(?<src>[0-9a-fA-F:.]+)"
| eval bogon_type=case(
    match(src, "^2001:0?[Dd][Bb]8:"), "Documentation (RFC 3849)",
    match(src, "^2002:"), "6to4 (deprecated)",
    match(src, "^[Ff][CcDd]"), "ULA leaked",
    match(src, "^[Ff][Ee][89AaBb]"), "Link-local routed",
    match(src, "^[Ff][Ee][CcDdEeFf]"), "Site-local (deprecated)",
    match(src, "^3[Ff]{3}[Ee]:"), "6bone (decommissioned)",
    match(src, "^::$"), "Unspecified",
    1=1, null())
| where isnotnull(bogon_type)
| stats count as hits first(_time) as first_seen last(_time) as last_seen by host, src, bogon_type
| sort -hits
```

**Bogon in BGP announcements (route hijack indicator):**
```spl
index=network sourcetype="cisco:ios" "%BGP" ("2001:db8" OR "2002:" OR "3ffe:" OR "fc00:" OR "fe80:") earliest=-1h
| rex field=_raw "(?:prefix|network)\s+(?<prefix>[0-9a-fA-F:/]+)"
| eval bogon_in_bgp="CRITICAL — bogon prefix " . prefix . " received via BGP on " . host
| table _time, host, prefix, bogon_in_bgp
```
Trigger: any bogon prefix received via BGP is a definitive misconfiguration or route hijack.

### Step 3 — Validate
(a) **Known bogon test.** Send a packet with source 2001:db8::1 toward the perimeter. Verify it is logged as a bogon detection.

(b) **BGP bogon test.** Announce 2001:db8::/32 from a test BGP peer. Verify the prefix-list denies it and the alert fires.

(c) **Legitimate traffic.** Verify that traffic with legitimate global unicast addresses (2000::/3 excluding bogons) passes without detection.

### Step 4 — Operationalize

**Dashboard** ("IPv6 — Bogon Detection"):
- Row 1 — Single-value: total bogon detections (should be 0 at a clean perimeter).
- Row 2 — Table: all bogon detections with source, type, and volume.
- Row 3 — Pie chart: bogon type distribution.
- Row 4 — Timechart: bogon detections over 30 days.

**Scheduling:** Bogon detection continuous (every 5 minutes). BGP bogon alert real-time.

**Runbook:**
1. Documentation address (2001:db8): find the source device. Likely a test configuration that leaked to production. Fix the source.
2. 6to4 (2002:): legacy tunnel leakage. Block at perimeter. Investigate source for deprecated tunnel (UC-5.20.57).
3. ULA (fc00:/fc00): internal address leaking externally. Check routing — ULA should not be redistributed to external BGP.
4. Link-local (fe80:): routing misconfiguration. Link-local should never be routed. Check for incorrect route redistribution.

### Step 5 — Troubleshooting

- **Bogon list maintenance** — The IPv6 bogon list changes when IANA allocates new /12 blocks. Subscribe to Team Cymru bogon updates and refresh the prefix-list quarterly.

- **ULA policy decision** — Some organisations intentionally use ULA across site boundaries via VPN. If so, create an exception for known ULA prefixes used inter-site, but maintain the bogon filter for ULA on public-facing interfaces.

- **Multicast (ff00::/8) filtering** — Multicast is technically bogon at the internet perimeter (should not cross autonomous system boundaries for most applications). However, some multicast applications (SSM, inter-domain multicast) may cross boundaries. Filter ff00::/8 at the perimeter unless specific inter-domain multicast is required.

## SPL

```spl
index=network (sourcetype="pan:traffic" OR sourcetype="cisco:ios" OR sourcetype="netflow") earliest=-24h
| rex field=_raw "(?:src|source)\s*=?\s*(?<src_ipv6>[0-9a-fA-F:.]+)"
| rex field=_raw "(?:dst|dest)\s*=?\s*(?<dst_ipv6>[0-9a-fA-F:.]+)"
| eval src_bogon=case(
    match(src_ipv6, "^::$|^::1$"), "loopback/unspecified",
    match(src_ipv6, "^::ffff:"), "IPv4-mapped",
    match(src_ipv6, "^64:ff9b:"), "NAT64 well-known prefix",
    match(src_ipv6, "^100::"), "discard prefix (RFC 6666)",
    match(src_ipv6, "^2001:db8:"), "documentation (RFC 3849)",
    match(src_ipv6, "^2001:0?0?0?0?:"), "Teredo",
    match(src_ipv6, "^2002:"), "6to4 (deprecated)",
    match(src_ipv6, "^3ffe:"), "6bone (decommissioned)",
    match(src_ipv6, "^[Ff][CcDd]"), "ULA (should not cross perimeter)",
    match(src_ipv6, "^[Ff][Ee][89AaBb]"), "link-local (should never be routed)",
    match(src_ipv6, "^[Ff][Ee][CcDdEeFf]"), "site-local (deprecated RFC 3879)",
    1=1, null())
| where isnotnull(src_bogon)
| stats count as events by host, src_bogon, src_ipv6
| sort -events
```

## Visualization

(1) Table: detected bogon traffic by type, source, and volume. (2) Single-value: total bogon detections (target: 0 at perimeter). (3) Pie chart: bogon type distribution. (4) Timechart: bogon detections over 30 days.

## Known False Positives

**ULA in multi-site VPN.** Organisations using ULA (fc00::/7) for inter-site communication over VPN may see ULA traffic at WAN interfaces. This is legitimate if the VPN is encrypted and the ULA is intentional. ULA should not appear on public internet-facing interfaces.

**NAT64 well-known prefix at provider boundary.** In deployments using NAT64, the 64:ff9b::/96 prefix appears in traffic between the DNS64 resolver and the NAT64 gateway. This is legitimate within the NAT64 infrastructure but should not cross the site perimeter to the internet.

**IANA new allocations.** When IANA allocates a new IPv6 /12 block, previously-bogon addresses become legitimate. The bogon list must be updated after IANA allocations to prevent false positives.

## References

- [RFC 9099 — Operational Security Considerations for IPv6 Networks (§2.4.2 — bogon filtering)](https://www.rfc-editor.org/rfc/rfc9099)
- [RFC 6890 — Special-Purpose IP Address Registries (comprehensive list of special addresses)](https://www.rfc-editor.org/rfc/rfc6890)
- [Team Cymru Bogon Reference — IPv6 bogon list](https://www.team-cymru.com/)
- [NIST SP 800-119 — Guidelines for the Secure Deployment of IPv6 (§4.3.1 — bogon filtering)](https://csrc.nist.gov/publications/detail/sp/800-119/final)
