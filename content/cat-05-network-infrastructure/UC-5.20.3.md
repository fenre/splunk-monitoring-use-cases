<!-- AUTO-GENERATED from UC-5.20.3.json — DO NOT EDIT -->

---
id: "5.20.3"
title: "IPv6 Address Type Distribution"
status: "verified"
criticality: "low"
splunkPillar: "Observability"
---

# UC-5.20.3 · IPv6 Address Type Distribution

> **Criticality:** Low &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Compliance, Security &middot; **Wave:** Crawl &middot; **Status:** Verified

*We sort all the new-style internet addresses we see into categories — like regular addresses, local-only addresses, and old discontinued types — so we can spot anything that looks wrong or outdated, the same way you'd notice a letter with a return address from a country that no longer exists.*

---

## Description

Classifies all observed IPv6 source addresses by their address type according to IANA allocations — Global Unicast (2000::/3), Link-Local (fe80::/10), ULA (fc00::/7), Multicast (ff00::/8), deprecated spaces (6to4, 6bone, Teredo), and special-purpose prefixes (NAT64 well-known, documentation, discard). This baseline reveals whether your network's IPv6 address usage is healthy: a well-configured network should be ~85-95% Global Unicast with small amounts of Link-Local and Multicast. Significant ULA, 6to4, Teredo, or deprecated-space traffic indicates misconfiguration or security risk.

## Value

Address type distribution is a hygiene metric that catches problems invisible to traffic ratio monitoring alone. ULA (fc00::/7) addresses leaking to the internet violate DISA STIG NET-IPV6-032 and can expose internal topology. Deprecated 6to4 (2002::/16) and Teredo (2001::/32) traffic indicates unauthorized transition mechanisms that bypass firewall policy (see UC-5.20.75 and UC-5.20.76). IPv4-Mapped addresses (::ffff:0:0/96) appearing on the wire suggest a misconfigured application embedding IPv4 addresses in IPv6 headers. Even the Multicast percentage is informative — more than 10% multicast is unusual and may indicate MLD misconfiguration or multicast amplification.

## Implementation

Query any data source containing IPv6 addresses (flow data, firewall logs, or syslog). The search uses regex prefix matching to classify addresses into IANA-defined categories. Run weekly for compliance dashboards or on-demand during security investigations. No additional data collection is needed — this UC reuses existing data.

## Detailed Implementation

### Prerequisites
- Any data source in Splunk containing IPv6 addresses in searchable fields. This UC does not require a dedicated input — it analyses data already collected by other UCs (NetFlow, firewall logs, syslog, NDP cache exports).
- At least one week of IPv6-bearing data for a meaningful distribution. Less than 24 hours of data will produce skewed results due to diurnal traffic patterns.
- Understanding of your organisation's IPv6 addressing plan: which Global Unicast prefixes are legitimately assigned (e.g., 2001:db8:abcd::/48 from your RIR allocation), whether ULA (fc00::/7) is intentionally used for internal services, and whether NAT64 (64:ff9b::/96) is deployed.

### Step 1 — Configure data collection
No new data collection is needed. This UC analyses IPv6 addresses already present in:
- NetFlow/IPFIX flows (`index=netflow`)
- Firewall traffic logs (`index=firewall`)
- Network device syslog (`index=network`)
- NDP cache exports (if collecting via SNMP or CLI scripts)

Verify IPv6 data exists:
```spl
index=netflow OR index=firewall OR index=network earliest=-24h
| where match(src_ip, ":")
| stats count
```
If count is zero, IPv6 data is not being collected — check UC-5.20.1 prerequisites (NetFlow v5 doesn't support IPv6; upgrade to v9/IPFIX).

### Step 2 — Create the search and alert

**Primary search — address type distribution:**
```spl
index=netflow sourcetype=netflow OR sourcetype=ipfix earliest=-7d
| where match(src_ip, ":")
| eval addr_type=case(
    match(src_ip, "^fe80:"), "Link-Local",
    match(src_ip, "^f[cd]"), "ULA (fc00::/7)",
    match(src_ip, "^ff"), "Multicast",
    match(src_ip, "^::ffff:"), "IPv4-Mapped",
    match(src_ip, "^2002:"), "6to4 (deprecated)",
    match(src_ip, "^2001:0*:"), "Teredo",
    match(src_ip, "^2001:0*db8:"), "Documentation (2001:db8::/32)",
    match(src_ip, "^3ffe:"), "6bone (deprecated)",
    match(src_ip, "^100::"), "Discard (100::/64)",
    match(src_ip, "^64:ff9b:"), "NAT64 Well-Known (64:ff9b::/96)",
    match(src_ip, "^2"), "Global Unicast",
    match(src_ip, "^::$"), "Unspecified (::)",
    match(src_ip, "^::1$"), "Loopback (::1)",
    1==1, "Other")
| stats count by addr_type
| eventstats sum(count) as total
| eval pct=round(count/total*100, 2)
| sort -count
```

**Understanding this SPL:**
- The `case()` order matters — more specific prefixes (documentation 2001:db8::, Teredo 2001::) must be checked before the broad Global Unicast match (`^2`). The regex patterns use `^` anchoring for performance and accuracy.
- `^f[cd]` matches both `fc` and `fd` prefixes, covering the entire ULA space (fc00::/7). In practice, only `fd` (locally assigned ULA) is used; `fc` (centrally assigned) was never implemented.
- `^::ffff:` matches IPv4-Mapped IPv6 addresses, which are IPv4 addresses embedded in IPv6 format. These should NOT appear on the wire — they're an application-layer construct. If they appear in flow data, an application is misconfigured.
- `^2002:` matches the 6to4 space. RFC 7526 formally deprecated 6to4 in 2015. Any 6to4 traffic in 2024+ is a security concern and should be investigated.

**Alert — deprecated or unexpected address types detected:**
```spl
index=netflow sourcetype=netflow OR sourcetype=ipfix earliest=-24h
| where match(src_ip, ":")
| where match(src_ip, "^2002:") OR match(src_ip, "^3ffe:") OR match(src_ip, "^::ffff:") OR match(src_ip, "^2001:0*db8:")
| stats count as violations values(src_ip) as sample_addresses by host
| where violations > 0
```
Trigger: any result. These address types should never appear in production flow data.

### Step 3 — Validate
(a) **Expected baseline:** A healthy enterprise network should show approximately:
  - Global Unicast: 80–95% (production traffic)
  - Link-Local: 5–15% (NDP, OSPFv3, first-hop traffic)
  - Multicast: 1–5% (NDP multicast, MLD, OSPFv3 hello)
  - Everything else: < 1% combined

(b) **Cross-reference with IPAM:** Compare observed Global Unicast prefixes against your RIR allocation and IPAM plan. Any Global Unicast prefix not in your allocation is either a customer prefix (in SP networks), a mistake, or an indicator of address hijacking.

(c) **Spot-check ULA:** If ULA appears, determine if it's intentional (some organisations use ULA for internal services that should never be internet-routable). If unintentional, it indicates misconfiguration and potential perimeter leakage (see UC-5.20.124).

(d) **Verify deprecated space is truly zero:** Run the alert search over 30 days. Even occasional 6to4 or Teredo traffic is a finding worth investigating.

### Step 4 — Operationalize

**Dashboard** ("IPv6 Address Hygiene"):
- Row 1 — Donut chart: address type distribution. Single-value tile: "Unexpected address types in last 24h" (count of deprecated/reserved, red if > 0).
- Row 2 — Table: full distribution with count, percentage, and expected/unexpected classification.
- Row 3 — Timechart: address type proportions over 30 days (stacked area) to detect shifts.
- Row 4 — Drilldown: click any unexpected type to see source hosts, timestamps, and destination addresses.

**Scheduling:** Weekly report for compliance review. Real-time alert for deprecated/reserved address types.

**Runbook** (owner: Network Security / IPv6 Operations):
1. If 6to4 (2002::/16) detected: identify the source host. On that host, check for 6to4 relay configuration (`netsh interface 6to4` on Windows, check for protocol 41 tunnels on routers). Disable 6to4 — it was deprecated by RFC 7526.
2. If Teredo (2001::/32 with port 3544) detected: identify the source host. Disable Teredo (`netsh interface teredo set state disabled` on Windows). Teredo traffic bypasses corporate firewalls.
3. If ULA at perimeter: check egress firewall rules for fc00::/7 blocking (DISA STIG NET-IPV6-032). ULA must not leak to the internet.
4. If IPv4-Mapped (::ffff:) on wire: identify the application generating these addresses. It likely has an IPv6 socket binding issue.

### Step 5 — Troubleshooting

- **All addresses classify as 'Other'** — The src_ip field may not be in standard colon-hex format. Check `index=netflow | where match(src_ip, ":") | head 10 | table src_ip` to see the actual format. Some TAs store IPv6 addresses in expanded form (2001:0db8:0000:...) vs compressed form (2001:db8::) — adjust regex patterns accordingly.

- **Global Unicast percentage is very low (< 50%)** — Your flow data may be dominated by access-layer exports where link-local NDP traffic is a large proportion. Filter to core/distribution router exports for a more application-representative distribution.

- **Unexpected high Multicast percentage** — Could indicate MLD snooping failure (all multicast flooding), a multicast amplification attack (UC-5.20.28), or misconfigured multicast sources. Investigate with `| where match(src_ip, "^ff") | stats count by dest_ip` to identify which multicast groups are generating the traffic.

- **6bone (3ffe::/16) detected** — The 6bone experimental network was decommissioned in 2006 (RFC 3701). Any traffic using this space is either an ancient misconfiguration or an attempt to use unmonitored address space. Treat as a security investigation.

## SPL

```spl
index=netflow sourcetype=netflow OR sourcetype=ipfix
| where match(src_ip, ":")
| eval addr_type=case(
    match(src_ip, "^fe80:"), "Link-Local",
    match(src_ip, "^f[cd]"), "ULA (fc00::/7)",
    match(src_ip, "^ff"), "Multicast",
    match(src_ip, "^::ffff:"), "IPv4-Mapped",
    match(src_ip, "^2002:"), "6to4 (deprecated)",
    match(src_ip, "^2001:0*:"), "Teredo",
    match(src_ip, "^2001:0*db8:"), "Documentation (2001:db8::/32)",
    match(src_ip, "^3ffe:"), "6bone (deprecated)",
    match(src_ip, "^100::"), "Discard (100::/64)",
    match(src_ip, "^64:ff9b:"), "NAT64 Well-Known (64:ff9b::/96)",
    match(src_ip, "^2"), "Global Unicast",
    match(src_ip, "^::$"), "Unspecified (::)",
    match(src_ip, "^::1$"), "Loopback (::1)",
    1==1, "Other")
| stats count by addr_type
| sort -count
```

## Visualization

(1) Pie chart or donut chart: address type distribution (expect Global Unicast to dominate). (2) Table: address type, count, percentage, with colour-coded rows — green for expected types (Global Unicast, Link-Local, Multicast), yellow for ULA, red for deprecated (6to4, 6bone, Teredo). (3) Single-value tile: count of non-Global-Unicast, non-Link-Local, non-Multicast addresses (the 'unexpected' types). (4) Timechart: address type distribution over 30 days to detect changes.

## Known False Positives

**Link-Local percentage appears high.** Link-local addresses (fe80::/10) are used for every NDP transaction, OSPFv3 neighborship, and on-link communication. On access switches with many clients, link-local traffic may represent 15-30% of all IPv6 flows. This is architecturally normal — link-local is how IPv6 works at the first hop.

**NAT64 well-known prefix (64:ff9b::/96) is legitimate.** If you operate NAT64 gateways, traffic to/from 64:ff9b::/96 is expected and correct. It should appear only at the NAT64 translator, not on other segments.

**Documentation prefix (2001:db8::/32) in production.** This prefix is reserved for documentation and examples per RFC 3849. If it appears in production traffic, it indicates a misconfiguration (someone deployed example configs verbatim) but is not malicious.

## References

- [IANA IPv6 Special-Purpose Address Registry](https://www.iana.org/assignments/iana-ipv6-special-registry/iana-ipv6-special-registry.xhtml)
- [RFC 9099 — Operational Security Considerations for IPv6 Networks (§2.6.1.1 — Address formats)](https://www.rfc-editor.org/rfc/rfc9099)
- [RFC 4193 — Unique Local IPv6 Unicast Addresses (ULA definition and filtering requirements)](https://www.rfc-editor.org/rfc/rfc4193)
