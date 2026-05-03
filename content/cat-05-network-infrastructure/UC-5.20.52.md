<!-- AUTO-GENERATED from UC-5.20.52.json — DO NOT EDIT -->

---
id: "5.20.52"
title: "IPv6 Reverse DNS (ip6.arpa) Completeness and PTR Record Audit"
status: "verified"
criticality: "medium"
splunkPillar: "Security"
---

# UC-5.20.52 · IPv6 Reverse DNS (ip6.arpa) Completeness and PTR Record Audit

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Security &middot; **Type:** Compliance, Security &middot; **Wave:** Walk &middot; **Status:** Verified

*Every phone number should have a name in the phone book — so when you see who called, you see a name instead of just digits. IPv6 addresses are really long numbers, and many of them are missing from the phone book. We check how many IPv6 addresses have their names registered, and flag the busiest ones that are missing — like having a phone number that calls everyone but nobody knows who it belongs to.*

---

## Description

Audits IPv6 reverse DNS (ip6.arpa) completeness by tracking PTR query success rates and identifying IPv6 addresses without reverse DNS records. Missing reverse DNS for IPv6 addresses causes email delivery failures (rejected by receiving mail servers), degrades security log readability (IP addresses instead of hostnames), breaks SSH UseDNS checks, and violates RFC 6302 logging requirements. This use case identifies the gaps and tracks remediation progress.

## Value

IPv6 reverse DNS is often overlooked during deployment because it requires separate zone delegation and either dynamic DNS or wildcard PTR configuration — neither of which is required for IPv4 in many environments. The result is that IPv6 addresses appear as raw hex strings in logs, traceroutes, and email headers, making operations significantly harder. Auditing PTR completeness identifies which IPv6 subnets lack reverse DNS so they can be remediated systematically.

## Implementation

Collect DNS query logs for ip6.arpa zone. Track NXDOMAIN vs NOERROR response rates for PTR queries. Identify IPv6 subnets with high NXDOMAIN rates (missing PTR records). Monitor for SERVFAIL (misconfigured delegation).

## Detailed Implementation

### Prerequisites
- DNS query logging enabled and forwarded to Splunk.
- ip6.arpa zone delegated for the organisation's IPv6 prefix(es).
- Knowledge of which IPv6 subnets should have PTR records (servers, infrastructure) vs dynamic client subnets.

### Step 1 — Configure data collection

DNS query logs are collected using the same mechanisms as UC-5.20.51. Ensure the logging includes response codes (NOERROR, NXDOMAIN, SERVFAIL) for PTR queries.

**Create an inventory of IPv6 subnets that SHOULD have PTR records:**
```csv
prefix,zone_name,should_have_ptr,ptr_method
2001:db8:100::/48,server-infra,true,static
2001:db8:200::/48,user-desktops,true,ddns-wildcard
2001:db8:300::/48,iot-devices,false,not-required
```
Upload as `ipv6_reverse_dns_requirements.csv`.

**Verification:**
```spl
index=network (sourcetype="infoblox:dns" OR sourcetype="named:querylog") "ip6.arpa" earliest=-24h
| stats count by sourcetype
```

### Step 2 — Create the search and alert

**Reverse DNS completeness by subnet:**
```spl
index=network (sourcetype="infoblox:dns" OR sourcetype="named:querylog") "ip6.arpa" earliest=-24h
| rex field=_raw "(?<queried_arpa>[0-9a-fA-F.]+\.ip6\.arpa)"
| eval response=case(
    match(_raw, "NXDOMAIN"), "NXDOMAIN",
    match(_raw, "NOERROR"), "NOERROR",
    match(_raw, "SERVFAIL"), "SERVFAIL",
    1=1, "other")
| eval prefix_arpa=substr(queried_arpa, -40)
| stats count(eval(response="NOERROR")) as found count(eval(response="NXDOMAIN")) as missing count(eval(response="SERVFAIL")) as errors by prefix_arpa
| eval completeness_pct=round(found / (found + missing) * 100, 1)
| sort completeness_pct
```

**SERVFAIL for ip6.arpa alert (delegation broken):**
```spl
index=network (sourcetype="infoblox:dns" OR sourcetype="named:querylog") "ip6.arpa" "SERVFAIL" earliest=-1h
| stats count as servfail_count
| where servfail_count > 50
| eval alert="ip6.arpa SERVFAIL spike: " . servfail_count . " in 1 hour — reverse DNS delegation may be broken"
```
Trigger: SERVFAIL for ip6.arpa indicates the reverse DNS zone is not properly delegated or the authoritative server is unavailable.

**Top IPv6 addresses without PTR (remediation priority):**
```spl
index=network (sourcetype="infoblox:dns" OR sourcetype="named:querylog") "ip6.arpa" "NXDOMAIN" earliest=-7d
| rex field=_raw "(?<queried_arpa>[0-9a-fA-F.]+\.ip6\.arpa)"
| stats count as query_count by queried_arpa
| sort -query_count
| head 50
| eval priority="Create PTR record — this address was queried " . query_count . " times without a reverse DNS entry"
```
The most-queried NXDOMAIN addresses should be prioritised for PTR record creation.

### Step 3 — Validate
(a) **Known PTR record.** Query a PTR record for an IPv6 address that has one. Verify it shows as NOERROR in the audit.

(b) **Known missing PTR.** Query a PTR record for an IPv6 address without one. Verify it shows as NXDOMAIN.

(c) **SERVFAIL test.** If available in a lab, misconfigure ip6.arpa delegation. Verify SERVFAIL responses appear and the alert fires.

### Step 4 — Operationalize

**Dashboard** ("IPv6 — Reverse DNS Completeness"):
- Row 1 — Single-value: overall ip6.arpa completeness %, SERVFAIL count.
- Row 2 — Pie chart: response code distribution for ip6.arpa queries.
- Row 3 — Table: per-subnet reverse DNS completeness.
- Row 4 — Top 50 addresses needing PTR records (highest query volume without PTR).

**Scheduling:** Completeness report daily. SERVFAIL alert every 15 minutes.

**Runbook:**
1. Low completeness on server subnets: create static PTR records for all server IPv6 addresses.
2. Low completeness on client subnets: implement wildcard PTR records or Dynamic DNS updates from DHCPv6.
3. SERVFAIL: check ip6.arpa zone delegation in the parent zone. Verify authoritative server is responding.

### Step 5 — Troubleshooting

- **ip6.arpa nibble format** — The ip6.arpa name is built by reversing each nibble (4-bit hex digit) of the IPv6 address. Tools like `host -t PTR <ipv6_addr>` automatically construct the correct ip6.arpa name.

- **Delegation at nibble boundaries** — ip6.arpa delegation must follow nibble boundaries (/4, /8, /12, /16, /20, /24, /28, /32, /36, /40, /44, /48). A /48 prefix like 2001:db8:cafe::/48 delegates `e.f.a.c.8.b.d.0.1.0.0.2.ip6.arpa` (12 nibbles for 48 bits).

- **Wildcard PTR records** — For client subnets where individual PTR records are impractical, a wildcard PTR provides a generic name for all addresses in the zone: `* IN PTR dynamic-client.subnet-100.example.com`. This satisfies FCrDNS checks without per-host configuration.

## SPL

```spl
index=network (sourcetype="infoblox:dns" OR sourcetype="named:querylog") "ip6.arpa" earliest=-24h
| eval response_type=case(
    match(_raw, "NXDOMAIN"), "NXDOMAIN — no PTR record",
    match(_raw, "NOERROR"), "NOERROR — PTR found",
    match(_raw, "SERVFAIL"), "SERVFAIL — resolver error",
    match(_raw, "REFUSED"), "REFUSED — not authoritative",
    1=1, "query")
| stats count by response_type
| eventstats sum(count) as total
| eval pct=round(count / total * 100, 1)
```

## Visualization

(1) Pie chart: ip6.arpa response distribution (NOERROR/NXDOMAIN/SERVFAIL). (2) Table: top queried IPv6 addresses with NXDOMAIN — highest-priority PTR records to create. (3) Timechart: reverse DNS completeness over 30 days. (4) By-subnet analysis: which /48s have the worst reverse DNS coverage.

## Known False Positives

**Privacy extension addresses.** Hosts using RFC 8981 privacy extensions generate new temporary IPv6 addresses daily. Creating PTR records for every temporary address is impractical. Use wildcard PTR records for client subnets (e.g., `*.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.1.0.0.8.b.d.0.1.0.0.2.ip6.arpa IN PTR dynamic-client.example.com`).

**SLAAC addresses without DDNS.** Hosts using SLAAC (Stateless Address Autoconfiguration) do not register in DNS unless dynamic DNS updates are configured. NXDOMAIN for SLAAC addresses is expected without DDNS.

**External addresses.** PTR queries for external IPv6 addresses (not controlled by the organisation) will return NXDOMAIN if the external organisation hasn't configured reverse DNS. This is outside the organisation's control.

## References

- [RFC 3596 — DNS Extensions to Support IP Version 6 (AAAA and ip6.arpa)](https://www.rfc-editor.org/rfc/rfc3596)
- [RFC 6302 — Logging Recommendations for Internet-Facing Servers (requires FCrDNS)](https://www.rfc-editor.org/rfc/rfc6302)
- [RFC 8501 — Reverse DNS in IPv6 for Internet Service Providers (operational guidance)](https://www.rfc-editor.org/rfc/rfc8501)
