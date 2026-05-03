<!-- AUTO-GENERATED from UC-5.20.110.json — DO NOT EDIT -->

---
id: "5.20.110"
title: "IPv6 DNS Resolution Health — AAAA Record Availability and Latency"
status: "verified"
criticality: "high"
splunkPillar: "Platform"
---

# UC-5.20.110 · IPv6 DNS Resolution Health — AAAA Record Availability and Latency

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Platform &middot; **Type:** Availability, Performance &middot; **Wave:** Walk &middot; **Status:** Verified

*Before you can visit a website, your computer needs to look up the address in a phone book (DNS). For the new address system (IPv6), it looks up a special type of entry called AAAA (quad-A). If this phone book lookup doesn't work for IPv6, your computer automatically falls back to the old address system without telling you. We monitor the phone book to make sure IPv6 lookups are working properly and not silently failing.*

---

## Description

Monitors DNS resolution health for IPv6 by tracking AAAA query success rates, response latency compared to A records, NXDOMAIN rates, and DNSSEC validation. DNS is the critical enabler of IPv6 — without working AAAA resolution, no dual-stack application can use IPv6. This UC detects DNS-layer IPv6 failures that silently degrade IPv6 preference and adoption.

## Value

DNS is the single most important service for IPv6 adoption. If AAAA records aren't returned, IPv6 doesn't work — period. If AAAA lookups are slow, Happy Eyeballs will prefer IPv4 for every connection. If AAAA records lack DNSSEC, attackers can redirect IPv6 traffic. This UC provides the essential DNS health metrics that determine whether IPv6 is actually usable in the environment.

## Implementation

Monitor AAAA query volumes, success rates, and latency. Compare with A record metrics. Alert on AAAA degradation. Track DNSSEC validation for AAAA records.

## Detailed Implementation

### Prerequisites
- DNS query logging enabled on recursive resolvers.
- Splunk Add-on for appropriate DNS platform installed.
- Zeek sensor or DNS tap for passive DNS collection.

### Step 1 — Configure DNS query logging

**BIND 9 query logging:**
```
logging {
    channel query_log {
        file "/var/log/named/query.log" versions 5 size 100m;
        severity info;
        print-time yes;
    };
    category queries { query_log; };
};
```

**Infoblox query logging:**
Enable query logging via Grid → DNS → Logging. Set to log queries and responses.

**Zeek DNS logging (passive):**
Zeek automatically logs DNS queries and responses in `dns.log`. No special configuration needed.

**Splunk UF `inputs.conf`:**
```ini
[monitor:///var/log/named/query.log]
sourcetype = named:querylog
index = dns
```

### Step 2 — Create monitoring searches

**AAAA vs A latency comparison (Happy Eyeballs signal):**
```spl
index=dns sourcetype="zeek:dns" earliest=-24h qtype IN (1, 28)
| eval query_type=if(qtype=28, "AAAA", "A")
| bin _time span=1h
| stats avg(rtt) as avg_rtt_ms p95(rtt) as p95_rtt_ms by _time, query_type
| eval avg_rtt_ms=round(avg_rtt_ms * 1000, 1)
| eval p95_rtt_ms=round(p95_rtt_ms * 1000, 1)
```

**Domains with AAAA failures (targeted investigation):**
```spl
index=dns sourcetype="zeek:dns" qtype=28 earliest=-24h
| stats count as total count(eval(rcode="NOERROR")) as success count(eval(rcode="NXDOMAIN")) as nxdomain count(eval(rcode="SERVFAIL")) as servfail by query
| eval success_pct=round(success / total * 100, 1)
| where success_pct < 50 AND total > 10
| sort success_pct
| head 50
```

**DNSSEC validation status for AAAA:**
```spl
index=dns sourcetype="named:querylog" "AAAA" earliest=-24h
| eval dnssec_validated=if(match(_raw, "(?i)AD|authenticated"), 1, 0)
| stats count as total sum(dnssec_validated) as validated by query
| eval dnssec_pct=round(validated / total * 100, 1)
| table query, total, validated, dnssec_pct
| sort -total
```

### Step 3 — Validate
(a) **AAAA resolution test.** Use `dig AAAA google.com @<resolver>` and verify the response includes AAAA records with reasonable latency.

(b) **Latency comparison.** Run `dig A example.com` and `dig AAAA example.com` back-to-back. Compare response times. If AAAA is consistently >100ms slower, investigate the resolver's IPv6 upstream connectivity.

(c) **DNSSEC test.** Use `dig +dnssec AAAA cloudflare.com` and verify the AD (Authenticated Data) flag is set.

### Step 4 — Operationalize

**Dashboard** ("IPv6 — DNS Resolution Health"):
- Row 1 — Gauges: AAAA success rate and A success rate.
- Row 2 — Timechart: AAAA vs A query volumes.
- Row 3 — Latency comparison: AAAA vs A response times.
- Row 4 — Table: domains with AAAA failures.

**Alert 1:** AAAA success rate drops below 80% — high. DNS infrastructure issue.
**Alert 2:** AAAA latency >200ms more than A latency — medium. IPv6 will lose Happy Eyeballs race.
**Alert 3:** AAAA SERVFAIL rate >5% — high. Resolver issue (DNSSEC validation failure?).

### Step 5 — Troubleshooting

- **AAAA queries returning SERVFAIL.** Most common cause: DNSSEC validation failure. The zone's AAAA records may have expired DNSSEC signatures. Check with `dig +cd AAAA <domain>` (bypasses validation). If this works but normal query fails, it's a DNSSEC issue.

- **AAAA latency higher than A.** Check if the resolver uses IPv6 transport to reach authoritative servers. If the resolver's IPv6 connectivity is poor, all AAAA lookups will be slow. Check resolver's IPv6 upstream path.

- **Sudden AAAA drop.** If AAAA queries suddenly show 0% success, check if a DNS policy or RPZ (Response Policy Zone) is filtering AAAA responses. Some security products block AAAA responses as a 'feature.'

## SPL

```spl
index=dns (sourcetype="zeek:dns" OR sourcetype="named:querylog" OR sourcetype="infoblox:dns") earliest=-4h
| eval query_type=case(
    match(qtype_name, "(?i)AAAA") OR qtype=28, "AAAA",
    match(qtype_name, "(?i)^A$") OR qtype=1, "A",
    1=1, qtype_name)
| where query_type IN ("A", "AAAA")
| eval success=if(rcode="NOERROR" OR rcode=0, 1, 0)
| eval nxdomain=if(rcode="NXDOMAIN" OR rcode=3, 1, 0)
| stats count as queries sum(success) as successes sum(nxdomain) as nxdomains avg(response_time) as avg_latency_ms by query_type
| eval success_pct=round(successes / queries * 100, 1)
| eval nxdomain_pct=round(nxdomains / queries * 100, 1)
| eval status=case(
    query_type="AAAA" AND success_pct < 50, "CRITICAL — AAAA success rate only " . success_pct . "% — most IPv6 DNS resolution failing",
    query_type="AAAA" AND success_pct < 80, "WARNING — AAAA success rate " . success_pct . "% — some IPv6 resolution issues",
    1=1, "OK — " . success_pct . "% success rate")
| table query_type, queries, successes, success_pct, nxdomains, nxdomain_pct, avg_latency_ms, status
```

## Visualization

(1) Gauges: AAAA success rate and A success rate side-by-side. (2) Timechart: AAAA vs A query counts. (3) Bar chart: AAAA latency vs A latency. (4) Table: domains with AAAA failures.

## Known False Positives

**Domains without AAAA records.** Many domains are still IPv4-only. NXDOMAIN or NODATA responses for AAAA queries to IPv4-only domains are expected, not an error.

**Internal domains.** Internal DNS zones may not have AAAA records if the internal network is IPv4-only. This is expected if IPv6 is only deployed on specific segments.

**CDN steering.** Some CDN providers selectively return or omit AAAA records based on the resolver's location or capabilities. This can cause variable AAAA success rates.

## References

- [RFC 3596 — DNS Extensions to Support IPv6 (AAAA record definition)](https://www.rfc-editor.org/rfc/rfc3596)
- [RFC 8305 — Happy Eyeballs Version 2 (DNS requirements for dual-stack)](https://www.rfc-editor.org/rfc/rfc8305)
- [RFC 9099 — Operational Security Considerations for IPv6 Networks (§2.6 — DNS monitoring)](https://www.rfc-editor.org/rfc/rfc9099)
