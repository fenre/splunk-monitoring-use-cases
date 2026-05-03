<!-- AUTO-GENERATED from UC-5.6.17.json — DO NOT EDIT -->

---
id: "5.6.17"
title: "DNS Query Latency and Resolution Failure by Resolver"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.6.17 · DNS Query Latency and Resolution Failure by Resolver

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance

*We watch for unusual DNS patterns so we notice possible attacks, mistakes, or overloaded resolvers before people feel it as slow apps or failed lookups.*

---

## Description

Slow or failing DNS resolution impacts all applications. Tracking latency and NXDOMAIN/timeout rates per resolver supports capacity and upstream provider decisions.

## Value

DNS operations teams compare latency and failure rates across all DNS resolvers side-by-side, immediately identifying the weakest resolver and enabling targeted remediation before user experience degrades.

## Implementation

Run synthetic DNS probes (e.g. dig to critical domains) from multiple hosts; ingest response time and result. Optionally ingest resolver query logs. Alert when latency exceeds 200ms or failure rate exceeds 5%.

## Detailed Implementation

### Prerequisites
- DNS query/response data with per-resolver latency and failure metrics. Sources: (a) Splunk Stream (`sourcetype=stream:dns`) for passive wire-data capture with microsecond latency, (b) Synthetic DNS monitoring (ThousandEyes, Catchpoint) sending results to Splunk, (c) Infoblox NIOS query logs, (d) Windows DNS performance counters via Splunk_TA_windows perfmon.
- This UC provides a per-resolver comparative view — essential for environments with multiple DNS resolvers (primary/secondary, geographically distributed, cloud vs. on-premises). Identifying which specific resolver is degraded enables targeted remediation.
- Build a `dns_resolvers.csv` lookup: `resolver_ip,resolver_name,resolver_type,location,tier` (e.g., `10.0.0.53,dc-dns-01,active-directory,Building-A,primary`, `8.8.8.8,Google Public DNS,external-recursive,cloud,secondary`).

### Step 1 — Configure data collection
Verify per-resolver DNS data:
```spl
index=dns sourcetype="stream:dns" earliest=-15m
| stats count avg(response_time) as avg_ms by dest
| lookup dns_resolvers.csv resolver_ip as dest OUTPUT resolver_name
| eval label=if(isnotnull(resolver_name), resolver_name, dest)
| sort -count
```
Each resolver should appear with average latency. If only one resolver appears, ensure Splunk Stream (or your DNS data source) sees traffic to all resolvers.

### Step 2 — Create the search and alert

**Primary search — Per-resolver latency and failure comparison:**
```spl
index=dns sourcetype="stream:dns" earliest=-15m
| eval is_failure=if(reply_code!="NOERROR" AND reply_code!="0", 1, 0)
| stats avg(response_time) as avg_ms perc50(response_time) as p50_ms perc95(response_time) as p95_ms count as queries sum(is_failure) as failures by dest
| eval failure_rate=round(100*failures/queries, 2)
| lookup dns_resolvers.csv resolver_ip as dest OUTPUT resolver_name resolver_type location tier
| eval label=if(isnotnull(resolver_name), resolver_name, dest)
| eval latency_status=case(p95_ms > 500, "CRITICAL", p95_ms > 200, "HIGH", p95_ms > 100, "WARNING", 1==1, "OK")
| eval failure_status=case(failure_rate > 5, "CRITICAL", failure_rate > 2, "HIGH", failure_rate > 0.5, "WARNING", 1==1, "OK")
| eval worst_status=case(latency_status="CRITICAL" OR failure_status="CRITICAL", "CRITICAL", latency_status="HIGH" OR failure_status="HIGH", "HIGH", latency_status="WARNING" OR failure_status="WARNING", "WARNING", 1==1, "OK")
| sort worst_status, -p95_ms
```

#### Understanding this SPL: Provides a side-by-side comparison of all DNS resolvers on both latency and failure rate. This immediately identifies the weak link — one resolver with 500ms P95 while others have 20ms tells you exactly where to focus. The `tier` field from the lookup distinguishes primary from secondary resolvers — a degraded primary has more impact than a degraded secondary.

**Resolver performance trending (comparative):**
```spl
index=dns sourcetype="stream:dns" earliest=-24h
| bin _time span=5m
| stats avg(response_time) as avg_ms perc95(response_time) as p95_ms by _time, dest
| lookup dns_resolvers.csv resolver_ip as dest OUTPUT resolver_name
| eval label=if(isnotnull(resolver_name), resolver_name, dest)
| timechart span=5m avg(p95_ms) by label
```

**Resolver failure pattern analysis:**
```spl
index=dns sourcetype="stream:dns" earliest=-1h
| where reply_code!="NOERROR" AND reply_code!="0"
| stats count by dest, reply_code
| lookup dns_resolvers.csv resolver_ip as dest OUTPUT resolver_name
| eval label=if(isnotnull(resolver_name), resolver_name, dest)
| chart sum(count) over label by reply_code
```

#### Understanding this SPL: Shows the breakdown of failure types per resolver. A resolver with many SERVFAIL responses has upstream issues. A resolver with many REFUSED responses may have access control issues. A resolver with many NXDOMAIN is likely fine (NXDOMAIN is a valid response, not a failure).

### Step 3 — Validate
(a) From a client, test each resolver: `dig @<resolver_ip> google.com +stats`. The "Query time" should approximate the P50 latency in Splunk.
(b) Verify resolver inventory: ensure `dns_resolvers.csv` lists all resolvers clients are configured to use (check DHCP-provided DNS servers, GPO-configured DNS, VPN-assigned DNS).
(c) Compare with synthetic monitoring (ThousandEyes, Catchpoint) for external validation.

### Step 4 — Operationalize
Dashboard ("DNS — Resolver Performance"):
- Row 1 — Single-value tiles: "Active resolvers", "Resolvers with issues", "Best P95 latency (ms)", "Worst P95 latency (ms)".
- Row 2 — Resolver comparison table: label, location, tier, queries, avg_ms, p95_ms, failure_rate, status.
- Row 3 — Timechart: P95 latency per resolver over 24h (line chart, one line per resolver).
- Row 4 — Failure breakdown: stacked bar chart of failure types per resolver.

Alerting:
- Critical (primary resolver P95 > 500ms or failure rate > 5%): page DNS operations — primary DNS degraded, clients will experience slow application performance.
- High (any resolver P95 > 200ms sustained for 15+ minutes): alert for investigation.
- Warning (resolver failure rate diverges from fleet — one resolver has 3x the failure rate of others): that specific resolver needs attention.

Runbook:
1. **One resolver degraded, others OK**: Check that specific resolver's health: CPU, memory, upstream forwarder connectivity, zone file integrity. If it's a Windows DC, check AD replication health.
2. **All resolvers degraded simultaneously**: Check common upstream dependency — ISP DNS, root server reachability, or network path issue affecting all resolvers.
3. **Primary resolver down**: Verify clients can reach the secondary resolver. DNS clients retry on the secondary, but with a timeout delay (typically 1-5 seconds). Consider removing the failed primary from DHCP/GPO configuration to eliminate the timeout penalty.

### Step 5 — Troubleshooting

- **Splunk Stream not seeing queries to all resolvers** — Ensure the Stream sensor is on a network segment that sees traffic to all resolver IPs. If resolvers are on different subnets, you may need multiple Stream sensors or a centralized tap.

- **Resolver latency seems inconsistent between Splunk and `dig`** — Splunk Stream measures passive latency (actual client experience). `dig` measures from the `dig` host, which may have different network path characteristics.

- **Cannot identify which resolver is primary vs. secondary** — Check DHCP configuration (which DNS server IP is listed first) and Windows GPO DNS settings. The first listed resolver is the primary.

## SPL

```spl
index=network sourcetype=dns_query
| bin _time span=5m
| stats avg(response_time_ms) as avg_ms, count(eval(response_code="NXDOMAIN" OR response_code="SERVFAIL")) as failures, count as total by resolver_ip, _time
| eval fail_rate=round(failures/total*100, 2)
| where avg_ms > 200 OR fail_rate > 5
| table resolver_ip avg_ms fail_rate total
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

Line chart (latency by resolver), Table (resolver, avg ms, fail rate), Single value (p95 latency).

## Known False Positives

Spikes can come from DNS cache flushes, authorized security or performance monitoring, or very talky clients; compare against change windows and known scanning tools.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
