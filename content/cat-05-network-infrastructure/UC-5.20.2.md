<!-- AUTO-GENERATED from UC-5.20.2.json — DO NOT EDIT -->

---
id: "5.20.2"
title: "DNS AAAA Record Coverage Audit"
status: "verified"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.20.2 · DNS AAAA Record Coverage Audit

> **Criticality:** Medium &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Compliance, Capacity &middot; **Wave:** Crawl &middot; **Status:** Verified

*We check which of your websites and services are reachable using the new internet addressing system (IPv6) by looking at whether their names can be looked up in the phone book for IPv6. If a service is missing from the IPv6 phone book, people on IPv6-only networks can't reach it.*

---

## Description

Audits which DNS-resolvable services have AAAA records (IPv6-reachable) versus A-only records (IPv4-only) by analyzing production DNS query-response logs. This reveals the real dual-stack readiness of your application portfolio — not what is configured in DNS zones, but what clients are actually querying and successfully resolving. A service with an A record but no AAAA record cannot be reached over IPv6, regardless of network readiness.

## Value

Network teams often deploy IPv6 on the infrastructure and declare dual-stack readiness, but applications remain IPv4-only because nobody published AAAA records. This UC bridges the gap between 'the network supports IPv6' and 'applications use IPv6' — the distinction that matters for user experience and compliance. For OMB M-21-07 compliance, federal agencies must report the percentage of public-facing services reachable via IPv6. For enterprises, the AAAA coverage percentage is the application-layer adoption metric that complements the network-layer traffic ratio (UC-5.20.1). A drop in AAAA success rate can also detect DNS infrastructure issues affecting IPv6 resolution.

## Implementation

Enable DNS query logging on resolvers (Infoblox, BIND, Windows DNS, or deploy Splunk Stream for passive DNS capture). The search analyzes query-response pairs to classify each queried FQDN as Dual-Stack, IPv4-Only, or IPv6-Only based on whether both A and AAAA queries return NOERROR with answers. Schedule weekly for adoption tracking or daily for regression detection.

## Detailed Implementation

### Prerequisites
- DNS query logging enabled on recursive resolvers. This is a prerequisite that many organisations disable for performance reasons — you need it enabled on at least one resolver pair per site to get representative data.
  - Infoblox NIOS: Member → DNS → Logging → enable query logging, forward via syslog to Splunk.
  - BIND: `logging { channel query_log { ... }; category queries { query_log; }; };` in named.conf.
  - Windows DNS: Enable DNS Analytical logging via Event Viewer → DNS Server → enable Analytical and Debug Logs. Forward via Splunk Universal Forwarder with `Splunk_TA_microsoft_dns`.
  - Passive capture alternative: Splunk Stream (`splunk_app_stream`) with a DNS stream enabled on a SPAN/TAP port mirroring resolver traffic.
- Index: `dns` with appropriate retention (30–90 days for trending).
- Fields required: `query` (the FQDN), `query_type` (A, AAAA), `reply_code` (NOERROR, NXDOMAIN). Field names vary by sourcetype — the SPL uses common CIM-mapped names. If your DNS TA uses different field names (e.g., `record_type` instead of `query_type`), adjust the search.
- License: DNS query logs can be very high volume (1–10 GB/day per resolver). Consider using Splunk Edge Processor or props.conf routing to filter to only A/AAAA queries before indexing if volume is a concern.

### Step 1 — Configure data collection

For Infoblox (most common enterprise DNS):
1. In NIOS Grid Manager: Grid → Grid Properties → Monitoring → enable syslog forwarding to the Splunk Heavy Forwarder IP, UDP 514.
2. Per DNS member: Member → DNS → Logging → enable "Log queries" and "Log responses" checkboxes.
3. On the Splunk HF, inputs.conf:
```
[udp://514]
sourcetype = infoblox:dns
index = dns
```
4. Install `Splunk_TA_infoblox` on the HF and Search Heads.

For BIND:
1. Configure query logging in named.conf (see Prerequisites).
2. Forward via syslog (rsyslog/syslog-ng) to Splunk HF.
3. Sourcetype: `named` or `bind:querylog`.

Verification:
```spl
index=dns query_type=AAAA earliest=-1h | stats count by reply_code
```
You should see `NOERROR` (AAAA exists), `NXDOMAIN` (name doesn't exist), and possibly `SERVFAIL` (resolver error). If zero events, check syslog forwarding and sourcetype assignment.

### Step 2 — Create the search and alert

**Primary search — AAAA coverage audit:**
```spl
index=dns (query_type=A OR query_type=AAAA) reply_code=NOERROR earliest=-7d
| stats dc(query_type) as record_types values(query_type) as types values(answer) as addresses count as query_count by query
| eval has_A=if(match(types, "A"), 1, 0)
| eval has_AAAA=if(match(types, "AAAA"), 1, 0)
| eval dual_stack_status=case(
    has_A=1 AND has_AAAA=1, "Dual-Stack",
    has_A=1 AND has_AAAA=0, "IPv4-Only",
    has_A=0 AND has_AAAA=1, "IPv6-Only",
    1==1, "Unknown")
| stats count by dual_stack_status
| eventstats sum(count) as total
| eval pct=round(count/total*100, 1)
```

**Understanding this SPL:**
- `reply_code=NOERROR` — only counts successful resolutions. NXDOMAIN means the name doesn't exist at all; SERVFAIL means the resolver failed. Neither indicates AAAA availability.
- `values(query_type) as types` — collects all record types seen for each FQDN over the 7-day window. If a client queries both A and AAAA for the same FQDN and both return NOERROR, the FQDN is Dual-Stack.
- The `case()` classification is exhaustive: a service is Dual-Stack (both), IPv4-Only (A but no AAAA), IPv6-Only (AAAA but no A — rare, but exists for IPv6-native services), or Unknown.

**Variant — top IPv4-Only services by query volume (prioritization for AAAA publication):**
```spl
index=dns (query_type=A OR query_type=AAAA) reply_code=NOERROR earliest=-7d
| stats dc(query_type) as record_types values(query_type) as types count as total_queries by query
| where NOT match(types, "AAAA")
| sort -total_queries
| head 50
| table query, total_queries
```
This identifies the 50 most-queried FQDNs that lack AAAA records — these are the highest-impact candidates for IPv6 enablement.

**Alert — AAAA coverage regression:**
```spl
index=dns (query_type=A OR query_type=AAAA) reply_code=NOERROR earliest=-1d
| stats dc(query_type) as record_types values(query_type) as types by query
| eval has_AAAA=if(match(types, "AAAA"), 1, 0)
| stats sum(has_AAAA) as aaaa_count count as total
| eval aaaa_pct=round(aaaa_count/total*100, 1)
| where aaaa_pct < 20
```
Trigger: AAAA coverage drops below 20% (adjust threshold to your baseline). This catches DNS zone misconfigurations, accidental AAAA record deletions, or resolver failures specific to IPv6.

### Step 3 — Validate
(a) **Manual dig verification:** Pick 3 FQDNs from the Dual-Stack list and 3 from IPv4-Only. Run `dig AAAA <fqdn>` and `dig A <fqdn>` from a client. The Splunk classification should match the dig results.

(b) **Zone file cross-reference:** If you have access to authoritative zone files (or Infoblox IPAM exports), compare the FQDN list against zone records. Services may have AAAA records published but never queried — that's valid but different from the query-based audit.

(c) **Spot-check volume leaders:** The top-10 most-queried FQDNs should be well-known internal services (Active Directory, email, intranet). Verify their classification matches reality.

(d) **Check for resolver bias:** If some resolvers are configured with `dns64` synthesis, AAAA queries to those resolvers will always return NOERROR (synthesized AAAA). Filter to non-DNS64 resolvers for an accurate audit: `| where NOT match(resolver, "dns64")`.

### Step 4 — Operationalize

**Dashboard** ("IPv6 Adoption — DNS AAAA Coverage"):
- Row 1 — Pie chart: Dual-Stack / IPv4-Only / IPv6-Only distribution. Single-value tile: AAAA coverage % with trend.
- Row 2 — Top 50 IPv4-Only services by query volume (table with drilldown to per-service detail).
- Row 3 — Weekly AAAA coverage trend (timechart over 90 days).
- Row 4 — Services that lost AAAA records (present last week, absent this week) — regression detector.

**Scheduling:** Weekly report (Monday 06:00, over `-7d`). For active migration projects, run daily.

**Runbook** (owner: DNS/IPAM Team):
1. Review the IPv4-Only list weekly during dual-stack rollout. For each high-traffic FQDN, determine if the underlying server has an IPv6 address. If yes, publish the AAAA record. If no, add to the IPv6 enablement backlog.
2. If AAAA coverage drops week-over-week, check for: accidental zone changes, DNS zone transfer failures, DNSSEC key rollover issues affecting AAAA records.
3. For OMB M-21-07 reporting: export the AAAA coverage percentage for public-facing services (filter by external domain names) to the quarterly FISMA metrics report.

### Step 5 — Troubleshooting

- **All services show as IPv4-Only** — DNS query logging may not capture AAAA queries. On some resolvers, AAAA queries are not logged separately from A queries. Verify with `index=dns query_type=AAAA | stats count` — if zero, the resolver or TA is not extracting `query_type` correctly. Check field extractions in the TA.

- **Very high IPv6-Only count** — Unusual in enterprise networks. Check if `dns64` synthesis is creating false AAAA-only records, or if the search is counting reverse DNS (PTR) queries to ip6.arpa zones as AAAA.

- **Same FQDN appears in both Dual-Stack and IPv4-Only across different time windows** — Likely a transient DNS issue (zone propagation delay, AAAA record TTL expiry). Extend the search window to 7d+ for a stable classification.

- **DNS log volume too high for this search to complete** — DNS query logs can reach millions of events per day. Accelerate by pre-filtering to only A and AAAA query types in props.conf/transforms.conf, or use `tstats` against an accelerated data model.

- **Field names don't match** — Different DNS TAs use different field names. Infoblox uses `query_type`; Microsoft DNS uses `QTYPE`; Splunk Stream uses `query_type`. Use `| fieldsummary` on a sample of events to identify the correct field names for your environment.

## SPL

```spl
index=dns (query_type=A OR query_type=AAAA) reply_code=NOERROR
| stats dc(query_type) as record_types values(query_type) as types values(answer) as addresses by query
| eval has_A=if(match(types, "A"), 1, 0)
| eval has_AAAA=if(match(types, "AAAA"), 1, 0)
| eval dual_stack_status=case(
    has_A=1 AND has_AAAA=1, "Dual-Stack",
    has_A=1 AND has_AAAA=0, "IPv4-Only",
    has_A=0 AND has_AAAA=1, "IPv6-Only",
    1==1, "Unknown")
| stats count by dual_stack_status
| eventstats sum(count) as total
| eval pct=round(count/total*100, 1)
```

## Visualization

(1) Pie chart: Dual-Stack vs IPv4-Only vs IPv6-Only service distribution. (2) Single-value tile: AAAA coverage percentage (count of Dual-Stack / total services × 100). (3) Table: top 50 most-queried IPv4-Only FQDNs — these are your highest-impact candidates for AAAA record publication. (4) Timechart: AAAA coverage percentage trended weekly over 90 days to show adoption progress.

## Known False Positives

**CDN and cloud services with dynamic AAAA records.** Services behind CDNs (Cloudflare, Akamai, AWS CloudFront) may return AAAA records for some resolvers but not others, depending on the CDN's IPv6 support per PoP. The same FQDN may appear as Dual-Stack from one resolver and IPv4-Only from another. This isn't a false positive per se — it accurately reflects the client experience from that resolver.

**Internal services behind split-horizon DNS.** Internal-only FQDNs resolved by internal resolvers may not have AAAA records published even though the underlying hosts have IPv6 addresses. This is a configuration gap, not a false positive — the UC correctly identifies these as IPv4-Only from the DNS perspective.

**DNS-SD and mDNS entries.** Service discovery protocols (Bonjour, mDNS) may generate A/AAAA query patterns that skew the service inventory. Filter with `| where NOT match(query, "\.local$")` to exclude mDNS.

**NXDOMAIN for AAAA but NOERROR for A.** A client querying for AAAA gets NXDOMAIN (the name doesn't exist in the IPv6 namespace) but A returns normally. This is the standard case for IPv4-Only services. The search handles this correctly by requiring `reply_code=NOERROR` — NXDOMAIN responses don't produce false Dual-Stack classifications.

## References

- [RFC 9099 — Operational Security Considerations for IPv6 Networks (§2.1.7 — DNS considerations)](https://www.rfc-editor.org/rfc/rfc9099)
- [NIST SP 800-119 — Guidelines for the Secure Deployment of IPv6 (§4.1 — DNS infrastructure)](https://csrc.nist.gov/publications/detail/sp/800-119/final)
- [Splunk Add-on for Infoblox (Splunkbase 2934)](https://splunkbase.splunk.com/app/2934)
