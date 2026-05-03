<!-- AUTO-GENERATED from UC-5.20.112.json — DO NOT EDIT -->

---
id: "5.20.112"
title: "IPv6 Address Scan and Reconnaissance Detection (RFC 7707)"
status: "verified"
criticality: "high"
splunkPillar: "ES"
---

# UC-5.20.112 · IPv6 Address Scan and Reconnaissance Detection (RFC 7707)

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** ES &middot; **Type:** Security &middot; **Wave:** Walk &middot; **Status:** Verified

*The new address system (IPv6) gives every network neighbourhood trillions of possible house numbers, so a burglar can't just try every door. Instead, they try clever patterns — like houses numbered 1, 2, 3 (low-byte), or houses with funny numbers like DEAD and BEEF (wordlist). We watch for someone methodically trying these patterns, which tells us a burglar is casing the neighbourhood before attempting a break-in.*

---

## Description

Detects IPv6 address scanning and reconnaissance using techniques described in RFC 7707: low-byte scanning (::1 through ::ff), wordlist scanning (::dead, ::beef, ::cafe), EUI-64 pattern scanning, and IPv4-derived address scanning. Because the IPv6 address space is too large for brute-force scanning, attackers must use these predictable-pattern techniques, which are highly detectable.

## Value

IPv6 scanning is the first step in most IPv6 attacks. Detecting scanning early provides an opportunity to block the attacker before they find exploitable targets. The predictable patterns used in IPv6 scanning (low-byte, wordlist, EUI-64) create reliable detection signatures. This UC turns the IPv6 address space's inherent unpredictability into a defensive advantage — any scanning pattern is visible because there is so little legitimate sequential access.

## Implementation

Monitor destination address patterns in IPv6 traffic. Flag connections to predictable address patterns (low-byte, wordlist, EUI-64). Alert when a single source targets many addresses matching scan patterns.

## Detailed Implementation

### Prerequisites
- Zeek or Suricata sensor on perimeter or key segments.
- Firewall deny logs captured in Splunk.

### Step 1 — Configure data collection

Zeek's `conn.log` captures all IPv6 connection attempts, including failed ones. Firewall deny logs from Palo Alto, Cisco FTD, or ASA capture connection attempts to non-existent hosts.

No special configuration is needed — the analysis is performed entirely in SPL on existing connection/firewall log data.

**For enhanced detection, enable Zeek's scan detection:**
```zeek
@load policy/misc/scan
redef Scan::addr_scan_interval = 5min;
redef Scan::addr_scan_threshold = 25;
```

### Step 2 — Create detection searches

**Comprehensive IPv6 scan detection:**
```spl
index=network (sourcetype="zeek:conn" OR sourcetype="paloalto:traffic") earliest=-24h
| eval is_ipv6_dest=if(match(dest, ":"), 1, 0)
| where is_ipv6_dest=1
| eval host_part=replace(dest, "^[0-9a-fA-F:]+::?", "")
| eval technique=case(
    match(host_part, "^[0-9a-fA-F]{1,2}$"), "low-byte",
    match(host_part, "(?i)(dead|beef|cafe|bad|face|babe|feed|c0de|d00d|f00d)"), "wordlist",
    match(dest, "[Ff][Ff][Ff][Ee]"), "eui64-pattern",
    match(dest, "::ffff:"), "ipv4-mapped",
    match(host_part, "^[0-9]+$") AND tonumber(host_part) < 1000, "sequential-decimal",
    1=1, "other")
| where technique != "other"
| stats dc(dest) as targets count as probes values(technique) as techniques by src
| where targets > 15
| eval risk=case(
    targets > 100, "CRITICAL",
    targets > 50, "HIGH",
    targets > 15, "MEDIUM")
| sort -targets
```

**DNS-based reconnaissance detection:**
```spl
index=dns sourcetype="zeek:dns" earliest=-24h
  qtype=12
| eval is_ipv6_ptr=if(match(query, "ip6.arpa"), 1, 0)
| where is_ipv6_ptr=1
| stats dc(query) as ptr_queries count as total by id_orig_h
| where ptr_queries > 50
| eval alert="DNS reverse scanning — " . id_orig_h . " queried " . ptr_queries . " unique IPv6 PTR records"
```

### Step 3 — Validate
(a) **Controlled scan test.** From a test host, use `nmap -6 --script targets-ipv6-wordlist <target-network>` to trigger wordlist-based scanning. Verify the detection fires.

(b) **Low-byte scan test.** Scan ::1 through ::20 in a test /64: `for i in $(seq 1 32); do ping6 -c 1 2001:db8:test::$(printf '%x' $i); done`. Verify detection.

(c) **False positive check.** Verify that legitimate monitoring tools (SNMP poller, Nagios) targeting low-byte infrastructure addresses are excluded or documented.

### Step 4 — Operationalize

**Dashboard** ("IPv6 — Reconnaissance Detection"):
- Row 1 — Single-values: active scanners, scan events (24h).
- Row 2 — Table: scanning sources with techniques and target counts.
- Row 3 — Timechart: scan events over time.
- Row 4 — Pie chart: scanning technique distribution.

**Alert:** Any source targeting >50 unique IPv6 addresses matching scan patterns — high. Investigate and block.

**ES correlation rule:**
```spl
| tstats count dc(All_Traffic.dest) as targets from datamodel=Network_Traffic where All_Traffic.dest="*:*" by All_Traffic.src
| where targets > 50
| rename All_Traffic.src as src
```

### Step 5 — Troubleshooting

- **High false positive rate.** If legitimate monitoring generates many matches, create an exclusion lookup for known monitoring sources and subnets.

- **Scan from internal hosts.** Internal scanning may indicate a compromised host performing lateral movement. Treat internal IPv6 scanning with the same urgency as external scanning.

- **Slow scanning.** Sophisticated attackers scan slowly (one probe per minute) to avoid detection. Lower the threshold for long-duration analysis (e.g., 24-hour window with threshold of 25 unique targets instead of 15 per hour).

## SPL

```spl
index=network (sourcetype="zeek:conn" OR sourcetype="paloalto:traffic" OR sourcetype="cisco:ftd") earliest=-24h
| eval is_ipv6=if(match(dest, ":"), 1, 0)
| where is_ipv6=1
| eval scan_pattern=case(
    match(dest, "::[0-9a-fA-F]{1,2}$"), "LOW_BYTE — targeting ::1 through ::ff",
    match(dest, "::(dead|beef|cafe|bad|face|babe|feed|c0de|d00d|f00d)"), "WORDLIST — targeting memorable hex words",
    match(dest, ":[Ff][Ff][Ff][Ee]:"), "EUI64_PATTERN — targeting SLAAC addresses with known OUI",
    match(dest, "::ffff:"), "IPV4_MAPPED — targeting IPv4-mapped addresses",
    1=1, null())
| where isnotnull(scan_pattern)
| stats dc(dest) as unique_targets count as probes first(_time) as first last(_time) as last by src, scan_pattern
| where unique_targets > 10
| eval scan_rate=round(probes / ((last - first) / 60 + 1), 1)
| eval severity=case(
    unique_targets > 100, "CRITICAL — large-scale IPv6 scan (" . unique_targets . " targets) using " . scan_pattern,
    unique_targets > 50, "HIGH — significant scanning activity",
    unique_targets > 10, "MEDIUM — possible reconnaissance",
    1=1, "LOW")
| sort -unique_targets
```

## Visualization

(1) Table: scanning sources with technique classification. (2) Timechart: scan events over time. (3) Pie chart: scan technique distribution. (4) Map: geographic source of scans.

## Known False Positives

**Legitimate low-byte addresses.** Many networks use low-byte addresses (::1, ::2, ::3) for infrastructure devices. A monitoring system probing these addresses (SNMP, ping sweeps) will match the low-byte pattern. Exclude known monitoring sources.

**DNS PTR crawlers.** Some legitimate services (search engines, CDNs) query PTR records for reverse DNS. This matches the DNS reverse scanning pattern but is typically benign.

**Link-local multicast.** NDP uses solicited-node multicast (ff02::1:ffXX:XXXX) which appears as sequential address access. This is normal NDP operation, not scanning.

## References

- [RFC 7707 — Network Reconnaissance in IPv6 Networks](https://www.rfc-editor.org/rfc/rfc7707)
- [RFC 7721 — Security and Privacy Considerations for IPv6 Address Generation Mechanisms](https://www.rfc-editor.org/rfc/rfc7721)
- [RFC 9099 — Operational Security Considerations for IPv6 Networks (§3 — reconnaissance)](https://www.rfc-editor.org/rfc/rfc9099)
