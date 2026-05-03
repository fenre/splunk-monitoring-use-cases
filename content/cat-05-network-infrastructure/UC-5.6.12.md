<!-- AUTO-GENERATED from UC-5.6.12.json — DO NOT EDIT -->

---
id: "5.6.12"
title: "DNS Query Type Distribution"
criticality: "medium"
splunkPillar: "Security"
---

# UC-5.6.12 · DNS Query Type Distribution

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Security &middot; **Type:** Performance, Capacity

*We watch for unusual DNS patterns so we notice possible attacks, mistakes, or overloaded resolvers before people feel it as slow apps or failed lookups.*

---

## Description

Unusual query type distribution (spikes in TXT, MX, or ANY) can indicate DNS tunneling, reconnaissance, or abuse.

## Value

DNS and security teams monitor query type distribution to detect DNS tunneling (TXT/NULL spikes), amplification attacks (ANY queries), unauthorized zone transfers (AXFR), and track IPv6 adoption trends.

## Implementation

Capture DNS query types via Splunk Stream or DNS server logs. Baseline normal distribution (typically >80% A/AAAA). Alert on abnormal increases in TXT, NULL, or ANY queries.

## Detailed Implementation

### Prerequisites
- DNS query logs in `index=dns` with `query_type` field extracted. DNS query types include: A (IPv4 address), AAAA (IPv6 address), CNAME (canonical name), MX (mail exchanger), TXT (text records — used for SPF, DKIM, DMARC), PTR (reverse DNS), SRV (service location), SOA (start of authority), NS (nameserver), ANY (all record types), NULL, HINFO, and others.
- CIM field: `DNS.query_type`. Infoblox and BIND typically log the query type in each query event. Windows DNS Analytical logging includes the record type.
- Query type distribution reveals: (a) normal baseline (typically 60-80% A/AAAA, 5-15% PTR, 5-10% MX/TXT, rest misc), (b) security anomalies (sudden increase in TXT/NULL = DNS tunneling, ANY queries = potential amplification attack, AXFR = zone transfer attempt), (c) infrastructure health (high PTR volume = reverse DNS lookups from email servers or logging systems).

### Step 1 — Configure data collection
Verify query type extraction:
```spl
index=dns earliest=-15m
| stats count by query_type
| sort -count
```
You should see a distribution dominated by A and AAAA records.

### Step 2 — Create the search and alert

**Primary search — Query type distribution with anomaly detection:**
```spl
index=dns earliest=-24h
| bin _time span=1h
| stats count by _time, query_type
| eventstats sum(count) as total_queries by _time
| eval pct=round(100*count/total_queries, 2)
| eventstats avg(pct) as avg_pct stdev(pct) as std_pct by query_type
| where pct > avg_pct + (3 * std_pct) AND pct > 1
| eval shift=round(pct - avg_pct, 1)
| sort -shift
```

#### Understanding this SPL: Tracks the percentage distribution of each query type over time. Shifts in the distribution indicate anomalies: a sudden spike in TXT queries could indicate DNS tunneling, a spike in ANY queries could indicate DNS amplification attack preparation, a spike in AXFR requests indicates zone transfer attempts.

**Suspicious query type detection:**
```spl
index=dns earliest=-1h
| where query_type IN ("NULL", "ANY", "AXFR", "IXFR", "HINFO", "10", "255", "252")
| stats count dc(src) as sources dc(query) as unique_domains by query_type
| eval risk=case(query_type IN ("AXFR", "IXFR"), "HIGH - Zone transfer attempt", query_type="ANY", "MEDIUM - Possible amplification", query_type="NULL", "MEDIUM - Possible tunneling", 1==1, "LOW - Unusual but may be legitimate")
| sort risk
```

#### Understanding this SPL: Certain query types are rarely used in legitimate traffic: NULL (often used by DNS tunneling tools), ANY (deprecated, used in amplification attacks), AXFR/IXFR (zone transfers — should only come from authorized secondary DNS servers), HINFO (host info — rarely used). Any significant volume of these warrants investigation.

**IPv6 adoption tracking (A vs. AAAA ratio):**
```spl
index=dns earliest=-7d
| where query_type IN ("A", "AAAA")
| bin _time span=1d
| stats count as queries by _time, query_type
| chart sum(queries) over _time by query_type
```

### Step 3 — Validate
(a) Verify the query type field matches the actual DNS query: capture a specific query with `dig <domain> TXT` and verify it appears with query_type=TXT in Splunk.
(b) Compare distribution with DNS server statistics if available.

### Step 4 — Operationalize
Dashboard ("DNS — Query Type Distribution"):
- Row 1 — Pie chart: query type distribution (current hour).
- Row 2 — Timechart: stacked area chart of query types over 7 days.
- Row 3 — Suspicious query types table: type, count, sources, risk.
- Row 4 — A vs. AAAA trend: IPv6 adoption over time.

Alerting:
- Critical (AXFR/IXFR from unauthorized source): zone transfer attempt — alert security.
- High (ANY query volume > 100/min): possible amplification attack — alert security.
- Medium (TXT/NULL query spike > 3 sigma): possible DNS tunneling — investigate.

Runbook:
1. **Zone transfer attempt (AXFR)**: Verify the source is not an authorized secondary DNS server. If unauthorized, block the source and investigate.
2. **ANY query spike**: May indicate your DNS servers are being used as amplifiers. Implement response rate limiting (RRL) on your resolvers.

### Step 5 — Troubleshooting

- **Query type shows as numeric (1, 28, 255)** — Some DNS log formats use numeric RTYPE values instead of names. Map them: 1=A, 28=AAAA, 5=CNAME, 15=MX, 16=TXT, 12=PTR, 6=SOA, 2=NS, 252=AXFR, 255=ANY, 10=NULL, 33=SRV.

- **Very high PTR volume** — Reverse DNS lookups (PTR) are generated by services that log hostnames instead of IPs. Email servers, web servers, and SIEM systems all generate PTR queries. This is normal but high volume may indicate a misconfigured service.

## SPL

```spl
index=network sourcetype="stream:dns"
| stats count by query_type
| eventstats sum(count) as total
| eval pct=round(count/total*100,2) | sort -count
| head 20
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Network_Resolution.DNS
  by DNS.query DNS.reply_code span=5m
| where count>0
| sort -count
```

## Visualization

Pie chart (query type distribution), Timechart (by type), Table.

## Known False Positives

Spikes can come from DNS cache flushes, authorized security or performance monitoring, or very talky clients; compare against change windows and known scanning tools.

## References

- [CIM: Network_Resolution](https://docs.splunk.com/Documentation/CIM/latest/User/Network_Resolution)
