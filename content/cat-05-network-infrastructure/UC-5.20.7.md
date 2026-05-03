<!-- AUTO-GENERATED from UC-5.20.7.json — DO NOT EDIT -->

---
id: "5.20.7"
title: "IPv6 Bogon and Reserved Space Detection"
status: "verified"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.20.7 · IPv6 Bogon and Reserved Space Detection

> **Criticality:** High &middot; **Difficulty:** Beginner &middot; **Pillar:** Security &middot; **Type:** Security, Compliance &middot; **Wave:** Crawl &middot; **Status:** Verified

*We watch for internet traffic using fake or discontinued addresses — like catching letters with forged return addresses. These addresses should never appear in real traffic, so if we see them, something is either broken or someone is up to no good.*

---

## Description

Detects IPv6 traffic from or to bogon and reserved address spaces at the network perimeter — deprecated prefixes (6bone 3ffe::/16, 6to4 2002::/16, site-local fec0::/10), RFC-reserved ranges (documentation 2001:db8::/32, discard 100::/64, unspecified ::), and addresses that should never appear on the wire (IPv4-Mapped ::ffff:0:0/96). Also flags ULA (fc00::/7) at the internet perimeter, which violates DISA STIG NET-IPV6-032. Any hit is a finding — these address spaces have no legitimate reason to appear in production perimeter traffic.

## Value

IPv6 bogon filtering is the first line of defence against spoofed traffic, misconfigured devices, and unauthorized transition mechanisms. Unlike IPv4 where bogon lists change as IANA allocates new blocks, IPv6 bogon space is relatively stable — the deprecated prefixes will never be re-assigned. Detection of these addresses at the perimeter means either: (1) your ingress filter has a gap (the traffic arrived from the internet and should have been blocked), (2) your egress filter has a gap (internal traffic with a bogon source is leaking to the internet), or (3) an internal device is misconfigured with a deprecated address. All three are actionable findings. DISA STIG specifically requires blocking and alerting on 6to4, Teredo, and ULA at the perimeter.

## Implementation

Apply this search against perimeter firewall logs or border router flow data. The search classifies IPv6 addresses in source and destination fields against the IANA reserved/deprecated prefix list and generates an alert for any match. Deploy the corresponding bogon ACL on all internet-facing firewalls and routers — this UC detects gaps in that ACL. Schedule as a real-time alert (any hit = investigation).

## Detailed Implementation

### Prerequisites
- Perimeter firewall or border router logs must be indexed in Splunk with IPv6 source and destination addresses extracted into searchable fields (`src_ip`, `dest_ip` or equivalent).
- Firewall deny logging must be enabled for IPv6 ACLs. On Palo Alto: ensure the security policy has "Log at session end" enabled for deny rules. On Cisco ASA: `logging enable` with appropriate level. On IOS-XE: add `log` keyword to IPv6 ACL deny entries.
- Understanding of your organisation's IPv6 address plan: which Global Unicast prefixes are legitimately yours (RIR allocation), whether ULA is intentionally used, whether NAT64 is deployed.
- DISA STIG compliance context (if applicable): NET-IPV6-032 requires blocking ULA at the perimeter, NET-IPV6-033 requires blocking deprecated transition mechanism prefixes.

### Step 1 — Configure data collection
No new data collection is needed if perimeter firewall logs are already indexed. Verify:
```spl
index=firewall sourcetype=pan:traffic OR sourcetype=cisco:asa earliest=-1h
| where match(src_ip, ":") OR match(dest_ip, ":")
| stats count
```
If count is zero but the firewall handles IPv6 traffic, check: (a) the firewall is logging IPv6 sessions (some older ASA versions require `logging permit-hostdown`), (b) the TA field extraction covers IPv6 addresses, (c) IPv6 traffic exists at the perimeter (may be legitimately absent on IPv4-only perimiter).

### Step 2 — Create the search and alert

**Primary search — IPv6 bogon detection at perimeter:**
```spl
index=firewall sourcetype=pan:traffic OR sourcetype=cisco:asa
| where match(src_ip, ":") OR match(dest_ip, ":")
| eval bogon_src=case(
    match(src_ip, "^3ffe:"), "6bone (3ffe::/16) - deprecated RFC 3701",
    match(src_ip, "^::ffff:"), "IPv4-Mapped (::ffff:0:0/96) - should not appear on wire",
    match(src_ip, "^2002:"), "6to4 (2002::/16) - deprecated RFC 7526",
    match(src_ip, "^2001:0*db8:"), "Documentation (2001:db8::/32) - RFC 3849",
    match(src_ip, "^fec0:"), "Site-Local (fec0::/10) - deprecated RFC 3879",
    match(src_ip, "^100::"), "Discard (100::/64) - RFC 6666",
    match(src_ip, "^::$"), "Unspecified (::) - RFC 4291",
    match(src_ip, "^f[cd]") AND NOT match(dest_ip, "^f[cd]"), "ULA (fc00::/7) at perimeter - DISA STIG NET-IPV6-032",
    1==1, null())
| eval bogon_dst=case(
    match(dest_ip, "^3ffe:"), "6bone (3ffe::/16) - deprecated RFC 3701",
    match(dest_ip, "^::ffff:"), "IPv4-Mapped (::ffff:0:0/96) - should not appear on wire",
    match(dest_ip, "^2002:"), "6to4 (2002::/16) - deprecated RFC 7526",
    match(dest_ip, "^2001:0*db8:"), "Documentation (2001:db8::/32) - RFC 3849",
    match(dest_ip, "^fec0:"), "Site-Local (fec0::/10) - deprecated RFC 3879",
    match(dest_ip, "^100::"), "Discard (100::/64) - RFC 6666",
    match(dest_ip, "^f[cd]") AND NOT match(src_ip, "^f[cd]"), "ULA (fc00::/7) at perimeter - DISA STIG NET-IPV6-032",
    1==1, null())
| where isnotnull(bogon_src) OR isnotnull(bogon_dst)
| eval bogon_type=coalesce(bogon_src, bogon_dst)
| eval bogon_addr=if(isnotnull(bogon_src), src_ip, dest_ip)
| eval direction=if(isnotnull(bogon_src), "inbound (spoofed source)", "outbound (internal leak)")
| stats count as hits sum(bytes) as total_bytes values(bogon_type) as bogon_reason values(direction) as traffic_direction values(action) as firewall_action first(_time) as first_seen last(_time) as last_seen by bogon_addr, host
| eval first_seen=strftime(first_seen, "%Y-%m-%d %H:%M:%S")
| eval last_seen=strftime(last_seen, "%Y-%m-%d %H:%M:%S")
| eval severity=case(
    match(bogon_reason, "6to4|Teredo|6bone"), "HIGH - deprecated transition mechanism",
    match(bogon_reason, "ULA"), "HIGH - compliance violation (DISA STIG)",
    match(bogon_reason, "IPv4-Mapped"), "MEDIUM - protocol anomaly",
    1==1, "MEDIUM")
| sort -hits
```

**Understanding this SPL:**
- Each bogon prefix is checked in both source and destination. Inbound bogon source addresses indicate either spoofing or misconfigured upstream routing. Outbound bogon destination addresses indicate internal devices trying to reach invalid addresses.
- The ULA check includes `AND NOT match(dest_ip, "^f[cd]")` to avoid flagging legitimate ULA-to-ULA traffic within the enterprise that happens to traverse a device where perimeter logs are collected.
- `direction` field distinguishes inbound (spoofed) from outbound (leak) — they require different remediation.
- `firewall_action` shows whether the firewall blocked it (good — but still a finding because the traffic reached the perimeter) or allowed it (critical — there's a rule gap).

**Complete IPv6 bogon prefix list for ACL deployment:**
```
! Cisco IOS-XE IPv6 bogon ACL — apply inbound on internet-facing interface
ipv6 access-list IPV6-BOGON-FILTER
 deny ipv6 ::/128 any log              ! Unspecified
 deny ipv6 ::1/128 any log              ! Loopback
 deny ipv6 ::ffff:0:0/96 any log        ! IPv4-Mapped
 deny ipv6 100::/64 any log             ! Discard prefix (RFC 6666)
 deny ipv6 2001:db8::/32 any log        ! Documentation
 deny ipv6 2002::/16 any log            ! 6to4 (deprecated)
 deny ipv6 3ffe::/16 any log            ! 6bone (deprecated)
 deny ipv6 fec0::/10 any log            ! Site-Local (deprecated)
 deny ipv6 fc00::/7 any log             ! ULA (must not traverse perimeter)
 deny ipv6 fe80::/10 any log            ! Link-Local (must not be routed)
 deny ipv6 ff00::/8 any log             ! Multicast (should not arrive from internet)
 permit ipv6 any any
```

### Step 3 — Validate
(a) **Test with documentation prefix:** From an internal host, attempt to ping `2001:db8::1`. This should generate a bogon alert if the traffic reaches a monitored perimeter device. If no alert fires, the bogon ACL may be blocking it before logging (check ACL hit counters with `show ipv6 access-list IPV6-BOGON-FILTER`).

(b) **Verify ACL coverage:** On each perimeter device, `show ipv6 access-list` and confirm all bogon prefixes from the list above are present in deny entries with `log` keyword.

(c) **Cross-reference with UC-5.20.3:** The address type distribution UC should show 0% of the deprecated types. If UC-5.20.3 shows 6to4 traffic but this UC shows no alerts, the bogon search isn't covering all data sources.

(d) **Check for gaps:** `show ipv6 access-list IPV6-BOGON-FILTER | include deny` on all perimeter devices. Every device should have identical bogon entries.

### Step 4 — Operationalize

**Dashboard** (panel on "IPv6 Security" dashboard):
- Row 1 — Single-value: "IPv6 bogon hits (24h)" (red if > 0, green if 0).
- Row 2 — Table: bogon address, type (with RFC), direction, firewall action, hits, timestamps.
- Row 3 — Pie chart: bogon hits by type — quickly shows whether it's one type (likely one misconfiguration) or many.

**Alerting:** Real-time alert on any hit where `firewall_action=allow`. Hourly summary for `firewall_action=deny` (less urgent but still a finding).

**Runbook** (owner: Network Security):
1. Inbound bogon with `action=allow`: CRITICAL. The perimeter ACL has a gap. Immediately add the missing bogon prefix to the ingress ACL. Investigate whether the traffic is spoofed (no legitimate source uses these prefixes).
2. Outbound bogon: identify the internal source device. It's misconfigured with a deprecated address. Common cause: old tunnel configuration (6to4, ISATAP) that was never cleaned up.
3. ULA at perimeter with `action=allow`: compliance violation. Add `deny ipv6 fc00::/7 any log` to the egress ACL.
4. Any finding: open a remediation ticket and track to closure.

### Step 5 — Troubleshooting

- **Zero results despite known IPv6 perimeter traffic** — The search filters to bogon prefixes only. Zero results means no bogon traffic was detected, which is the desired state. Verify the search is running against the correct index and sourcetype by removing the bogon filter and checking total IPv6 traffic: `index=firewall | where match(src_ip, ":") | stats count`.

- **High volume of ULA alerts from one source** — A device or application is misconfigured with a ULA address and trying to reach the internet. Check: is a DNS entry pointing to a ULA address? Is a routing leak advertising ULA into the global routing table?

- **6to4 hits from many different source addresses** — Could indicate an active 6to4 relay somewhere in your network announcing 2002::/16. Check for `interface tunnel*` configurations on routers with `tunnel mode ipv6ip 6to4` or `tunnel source` using a public IPv4 address.

- **Regex doesn't match your address format** — If your firewall TA stores addresses in expanded form (e.g., `3ffe:0000:0000:...`), the `^3ffe:` regex will still match. But if addresses are stored with uppercase letters (e.g., `3FFE:`), the regex won't match because `match()` is case-sensitive by default. Add `| eval src_ip=lower(src_ip), dest_ip=lower(dest_ip)` before the case statement.

## SPL

```spl
index=firewall sourcetype=pan:traffic OR sourcetype=cisco:asa
| where match(src_ip, ":") OR match(dest_ip, ":")
| eval bogon_src=case(
    match(src_ip, "^3ffe:"), "6bone (3ffe::/16) - deprecated RFC 3701",
    match(src_ip, "^::ffff:"), "IPv4-Mapped (::ffff:0:0/96) - should not appear on wire",
    match(src_ip, "^2002:"), "6to4 (2002::/16) - deprecated RFC 7526",
    match(src_ip, "^2001:0*db8:"), "Documentation (2001:db8::/32) - RFC 3849",
    match(src_ip, "^fec0:"), "Site-Local (fec0::/10) - deprecated RFC 3879",
    match(src_ip, "^100::"), "Discard (100::/64) - RFC 6666",
    match(src_ip, "^::$"), "Unspecified (::) - RFC 4291",
    match(src_ip, "^f[cd]") AND NOT match(dest_ip, "^f[cd]"), "ULA (fc00::/7) at perimeter - DISA STIG NET-IPV6-032",
    1==1, null())
| eval bogon_dst=case(
    match(dest_ip, "^3ffe:"), "6bone (3ffe::/16) - deprecated RFC 3701",
    match(dest_ip, "^::ffff:"), "IPv4-Mapped (::ffff:0:0/96) - should not appear on wire",
    match(dest_ip, "^2002:"), "6to4 (2002::/16) - deprecated RFC 7526",
    match(dest_ip, "^2001:0*db8:"), "Documentation (2001:db8::/32) - RFC 3849",
    match(dest_ip, "^fec0:"), "Site-Local (fec0::/10) - deprecated RFC 3879",
    match(dest_ip, "^100::"), "Discard (100::/64) - RFC 6666",
    match(dest_ip, "^f[cd]") AND NOT match(src_ip, "^f[cd]"), "ULA (fc00::/7) at perimeter - DISA STIG NET-IPV6-032",
    1==1, null())
| where isnotnull(bogon_src) OR isnotnull(bogon_dst)
| eval bogon_type=coalesce(bogon_src, bogon_dst)
| eval bogon_addr=if(isnotnull(bogon_src), src_ip, dest_ip)
| stats count as hits sum(bytes) as total_bytes values(bogon_type) as bogon_reason first(_time) as first_seen last(_time) as last_seen by bogon_addr, host
| eval first_seen=strftime(first_seen, "%Y-%m-%d %H:%M:%S")
| eval last_seen=strftime(last_seen, "%Y-%m-%d %H:%M:%S")
| sort -hits
```

## Visualization

(1) Single-value tile: total bogon hits in last 24h (red if > 0). (2) Table: bogon address, bogon type (with RFC reference), hit count, first/last seen, source device — for SOC investigation. (3) Bar chart: hits by bogon type — shows whether the problem is a single misconfiguration or widespread. (4) Timechart: bogon hits over 7 days to identify patterns (scheduled tasks, recurring misconfigurations).

## Known False Positives

**Intentional ULA (fc00::/7) usage.** Some organisations deliberately use ULA for internal services that should never reach the internet. ULA at the perimeter is flagged because DISA STIG requires it, but if your firewall is correctly blocking ULA egress, you'll see deny log entries rather than permit entries. Distinguish by checking the `action` field: `action=deny` means the firewall is doing its job (informational finding); `action=allow` means there's a real gap.

**NAT64 well-known prefix (64:ff9b::/96).** This prefix is NOT in the bogon list because it's legitimately used by NAT64 gateways. If you see it at the perimeter, it should be associated with your NAT64 infrastructure, not random endpoints.

**Test/lab traffic bleeding into production logs.** Lab environments sometimes use documentation prefixes (2001:db8::/32) intentionally. If your lab traffic is logged to the same Splunk index as production, these will trigger alerts. Tag lab devices in a lookup and exclude them.

## References

- [IANA IPv6 Special-Purpose Address Registry](https://www.iana.org/assignments/iana-ipv6-special-registry/iana-ipv6-special-registry.xhtml)
- [RFC 7526 — Deprecating the Anycast Prefix for 6to4 Relay Routers (formal 6to4 deprecation)](https://www.rfc-editor.org/rfc/rfc7526)
- [RFC 9099 — Operational Security Considerations for IPv6 Networks (§2.7.2 — Transition mechanism filtering)](https://www.rfc-editor.org/rfc/rfc9099)
- [DISA STIG — Network Device IPv6 (NET-IPV6-032: ULA must not traverse perimeter)](https://www.stigviewer.com/stig/network_ipv6/)
