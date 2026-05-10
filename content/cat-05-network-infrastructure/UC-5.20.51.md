<!-- AUTO-GENERATED from UC-5.20.51.json — DO NOT EDIT -->

---
id: "5.20.51"
title: "DNS AAAA Record Query Ratio and IPv6 Resolution Health"
status: "verified"
criticality: "medium"
splunkPillar: "IT Operations"
---

# UC-5.20.51 · DNS AAAA Record Query Ratio and IPv6 Resolution Health

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** IT Operations &middot; **Type:** Performance, Availability &middot; **Wave:** Walk &middot; **Status:** Verified

*When you type a website name, the computer needs to look up both the old-style address (IPv4, like a phone number) and the new-style address (IPv6, like a longer phone number). We count how often the computer asks for each type. If it stops asking for new-style addresses, something is wrong with the new phone system — even though the old phone still works fine.*

---

## Description

Measures the DNS AAAA query ratio relative to A queries as a primary indicator of IPv6 adoption and DNS resolution health. The AAAA-to-A ratio reveals how many clients and applications are actively resolving IPv6 addresses. In a properly configured dual-stack environment with Happy Eyeballs (RFC 8305), the ratio approaches 50% because every connection attempt triggers both A and AAAA queries. A declining AAAA ratio may indicate IPv6 connectivity issues causing clients to stop trying IPv6, or a DNS resolver configuration change that affects AAAA responses.

## Value

The AAAA query ratio is the most accessible and accurate measure of IPv6 adoption from the network perspective. It captures actual client behaviour rather than configuration intent. A declining AAAA ratio is an early warning signal — it may indicate that Happy Eyeballs is falling back to IPv4 due to IPv6 connectivity problems, or that a DNS resolver change has broken AAAA resolution. Tracking this ratio over time provides the adoption trend that management needs for IPv6 migration planning and the operational signal that engineers need for troubleshooting.

## Implementation

Collect DNS query logs from recursive resolvers. Parse query types (A, AAAA, PTR). Calculate the AAAA/(A+AAAA) ratio. Track over time. Alert on significant ratio changes.

## Detailed Implementation

### Prerequisites
- DNS query logging enabled on recursive resolvers (Infoblox, BIND, Unbound, Windows DNS).
- Query log forwarding to Splunk via syslog, HEC, or file monitoring.
- Sufficient retention for trend analysis (30+ days recommended).

### Step 1 — Configure data collection

**Infoblox DNS query logging:**
Queries & Responses → Logging → enable query logging. Forward via syslog to Splunk.

Sample Infoblox query log:
```
client 10.1.2.3#12345: query: www.example.com IN AAAA +ED (2001:db8::53)
```

**BIND query logging:**
```
logging {
  channel query_log {
    syslog local3;
    severity info;
    print-time yes;
  };
  category queries { query_log; };
};
```

**Windows DNS:**
Enable DNS Analytic/Audit logging via Event Tracing (ETW) or DNS Debug Logging.

**Verification:**
```spl
index=network (sourcetype="infoblox:dns" OR sourcetype="named:querylog" OR sourcetype="msad:nt6:dns") earliest=-24h
| stats count by sourcetype
```

### Step 2 — Create the search and alert

**AAAA ratio trending:**
```spl
index=network (sourcetype="infoblox:dns" OR sourcetype="named:querylog" OR sourcetype="msad:nt6:dns") earliest=-30d
| eval qtype=case(
    match(_raw, "\bAAAA\b"), "AAAA",
    match(_raw, "\bIN A\b|query_type=A\b|type A\b"), "A",
    1=1, null())
| where isnotnull(qtype)
| timechart span=1d count by qtype
| eval aaaa_ratio=round(AAAA / (AAAA + A) * 100, 1)
```

**AAAA ratio anomaly alert:**
```spl
index=network (sourcetype="infoblox:dns" OR sourcetype="named:querylog") earliest=-4h
| eval qtype=if(match(_raw, "\bAAAA\b"), "AAAA", if(match(_raw, "\bIN A\b"), "A", null()))
| where isnotnull(qtype)
| stats count(eval(qtype="AAAA")) as aaaa count(eval(qtype="A")) as a
| eval ratio=round(aaaa / (aaaa + a) * 100, 1)
| where ratio < 5
| eval alert="AAAA ratio dropped to " . ratio . "% — possible IPv6 DNS resolution issue"
```

**AAAA NXDOMAIN/SERVFAIL rate:**
```spl
index=network (sourcetype="infoblox:dns" OR sourcetype="named:querylog") "AAAA" earliest=-24h
| eval response=case(
    match(_raw, "NXDOMAIN"), "NXDOMAIN",
    match(_raw, "SERVFAIL"), "SERVFAIL",
    match(_raw, "NOERROR"), "NOERROR",
    1=1, "other")
| stats count by response
| eventstats sum(count) as total
| eval pct=round(count / total * 100, 1)
```
High NXDOMAIN rate for AAAA queries is expected (many domains don't have AAAA records). High SERVFAIL rate indicates DNS resolver problems.

**DNS64 synthesis monitoring:**
```spl
index=network sourcetype="infoblox:dns" "dns64" OR "64:ff9b" earliest=-24h
| stats count as dns64_syntheses
| eval note="DNS64 synthesised " . dns64_syntheses . " AAAA responses in 24h — these hosts are using NAT64 to reach IPv4 destinations"
```

### Step 3 — Validate
(a) **Query ratio calculation.** Manually count A and AAAA queries from a 1-hour sample. Compare with the Splunk-calculated ratio.

(b) **Trend validation.** Compare the 30-day AAAA ratio trend with known IPv6 deployment activities (e.g., enabling IPv6 on a new VLAN should increase the ratio).

(c) **SERVFAIL check.** Intentionally query a broken DNS zone. Verify the SERVFAIL appears in the DNS health search.

### Step 4 — Operationalize

**Dashboard** ("IPv6 — DNS Resolution Health"):
- Row 1 — Single-value: current AAAA-to-A ratio, AAAA SERVFAIL count.
- Row 2 — Timechart: AAAA ratio over 30 days with trend line.
- Row 3 — Stacked area: A/AAAA/PTR query volumes over 24 hours.
- Row 4 — Per-subnet AAAA ratio: which networks are actively using IPv6 DNS.
- Row 5 — DNS64 synthesis count (if applicable).

**Scheduling:** Ratio trending daily. SERVFAIL alert every 15 minutes. DNS64 monitoring daily.

**Runbook:**
1. AAAA ratio drop: check if AAAA queries are being filtered at the resolver. Check if IPv6 connectivity issues are causing Happy Eyeballs to stop sending AAAA queries.
2. AAAA SERVFAIL: check DNS resolver IPv6 connectivity. Can the resolver reach authoritative servers over IPv6?
3. High DNS64 rate: indicates significant IPv6-only client population depending on NAT64. Monitor NAT64 health.

### Step 5 — Troubleshooting

- **AAAA query parsing** — Different DNS log formats use different notation for AAAA queries. Infoblox uses `IN AAAA`, BIND uses `AAAA`, Windows uses query type numbers. Ensure the regex matches all formats.

- **EDNS0 and large AAAA responses** — DNSSEC-signed AAAA responses can exceed 512 bytes (the traditional DNS UDP limit). If EDNS0 is not supported by the client or intermediate devices, AAAA queries may fail while A queries succeed. Monitor for DNS over TCP fallback rates as an indicator.

## SPL

```spl
index=network (sourcetype="infoblox:dns" OR sourcetype="named:querylog" OR sourcetype="msad:nt6:dns") earliest=-24h
| eval query_type=case(
    match(_raw, "\bAAAA\b"), "AAAA",
    match(_raw, "\b(?:type.?1\b|\bIN A\b|query_type=A\b)"), "A",
    match(_raw, "\bPTR\b"), "PTR",
    1=1, "other")
| stats count as total count(eval(query_type="AAAA")) as aaaa_queries count(eval(query_type="A")) as a_queries count(eval(query_type="PTR")) as ptr_queries
| eval aaaa_ratio=round(aaaa_queries / (aaaa_queries + a_queries) * 100, 1)
| eval aaaa_trend=case(
    aaaa_ratio > 40, "Strong IPv6 adoption — approaching dual-stack parity",
    aaaa_ratio > 20, "Moderate IPv6 adoption — Happy Eyeballs active",
    aaaa_ratio > 5, "Low IPv6 adoption — limited IPv6 clients",
    1=1, "Minimal IPv6 DNS activity")
```

## Visualization

(1) Single-value: current AAAA-to-A ratio. (2) Timechart: AAAA ratio over 30 days with trend line. (3) Stacked area: query types over 24 hours. (4) By-client breakdown: AAAA ratio per client subnet.

## Known False Positives

**IPv4-only applications.** Legacy applications that only resolve A records will lower the AAAA ratio. This is expected in environments with a significant legacy application estate.

**DNS caching.** Client-side DNS caching means not every connection attempt generates a DNS query. The ratio at the resolver level reflects unique resolutions, not connection attempts.

**AAAA filtering.** Some enterprise DNS resolvers filter AAAA responses (returning NODATA) to prevent IPv6 connectivity on networks that don't support it. This intentionally suppresses the AAAA ratio and is a valid operational choice during phased migration.

## References

- [RFC 8305 — Happy Eyeballs Version 2: Better Connectivity Using Concurrency](https://www.rfc-editor.org/rfc/rfc8305)
- [RFC 6147 — DNS64: DNS Extensions for Network Address Translation from IPv6 Clients to IPv4 Servers](https://www.rfc-editor.org/rfc/rfc6147)
- [RFC 9099 — Operational Security Considerations for IPv6 Networks (§2.6 — DNS considerations)](https://www.rfc-editor.org/rfc/rfc9099)
