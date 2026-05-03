<!-- AUTO-GENERATED from UC-5.6.9.json — DO NOT EDIT -->

---
id: "5.6.9"
title: "DNS Cache Hit Ratio"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.6.9 · DNS Cache Hit Ratio

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance

*We watch for unusual DNS patterns so we notice possible attacks, mistakes, or overloaded resolvers before people feel it as slow apps or failed lookups.*

---

## Description

Low cache hit ratios indicate either a surge of new queries, cache poisoning attempts, or misconfigured TTLs — all increasing latency and upstream load.

## Value

DNS operations teams monitor cache hit ratios to ensure resolver performance, identify cache sizing issues, and detect anomalies like DGA malware or cache flush events that degrade DNS resolution speed.

## Implementation

Enable query logging on DNS resolvers. Track cache hit vs. miss ratio. Alert when hit ratio drops below 70%. Investigate top domains causing misses.

## Detailed Implementation

### Prerequisites
- DNS cache statistics from resolvers. Sources: (a) SNMP polling of DNS resolver cache counters, (b) Infoblox NIOS reporting API for cache statistics, (c) BIND statistics channel (`rndc stats` output), (d) Windows DNS Server performance counters (via Splunk_TA_windows perfmon), (e) DNS wire data via Splunk Stream with response analysis.
- Cache hit ratio = cache_hits / (cache_hits + cache_misses). A healthy recursive resolver should have > 80% cache hit ratio. Lower ratios indicate: (a) cache too small, (b) low TTL records dominating, (c) cache flushed recently, (d) many unique domain lookups (DGA malware or crawlers).
- Cache hits are served in < 1ms. Cache misses require recursive resolution (10-200ms). A high miss rate directly impacts user-perceived DNS latency.

### Step 1 — Configure data collection
Verify cache statistics availability (method depends on source):
```spl
index=dns OR index=perfmon earliest=-1h
| search "cache" OR "hit" OR "miss"
| stats count by sourcetype
```

For Windows DNS perfmon:
```spl
index=perfmon sourcetype="Perfmon:DNS" earliest=-1h
| stats latest(cache_hits) as hits latest(cache_misses) as misses by host
```

### Step 2 — Create the search and alert

**Primary search — Cache hit ratio (Stream-based estimation):**
```spl
index=dns sourcetype="stream:dns" earliest=-1h
| eval is_cache_hit=if(response_time < 2, 1, 0)
| stats count as total sum(is_cache_hit) as cache_hits by dest
| eval cache_misses=total - cache_hits
| eval hit_ratio=round(100*cache_hits/total, 1)
| eval status=case(hit_ratio < 60, "CRITICAL", hit_ratio < 75, "WARNING", 1==1, "OK")
| sort hit_ratio
```

#### Understanding this SPL: Since direct cache statistics aren't always available, this uses response time as a proxy: queries answered in < 2ms are almost certainly cache hits (a recursive lookup takes 10+ ms). This approach works with Splunk Stream wire data without needing direct server-side metrics.

**Cache effectiveness trending:**
```spl
index=dns sourcetype="stream:dns" earliest=-7d
| eval is_cache_hit=if(response_time < 2, 1, 0)
| bin _time span=1h
| stats count as total sum(is_cache_hit) as hits by _time, dest
| eval hit_ratio=round(100*hits/total, 1)
| timechart span=1h avg(hit_ratio) as cache_hit_pct by dest
```

**Cache miss analysis — which domains cause the most misses:**
```spl
index=dns sourcetype="stream:dns" response_time > 5 earliest=-1h
| stats count as cache_misses avg(response_time) as avg_resolve_ms by query
| sort -cache_misses
| head 20
```

#### Understanding this SPL: Identifies domains that are never cached (every lookup is a miss). These could be: very low TTL records (some CDNs use 60-second TTLs), DGA domains (always unique), or rarely accessed domains. If a frequently accessed domain has low TTL, consider implementing a minimum TTL override on the resolver.

### Step 3 — Validate
(a) Compare with resolver statistics: Infoblox NIOS reporting, `rndc stats` for BIND, Windows DNS Server Manager statistics.
(b) Test: query the same domain twice. The second query should be a cache hit (< 2ms response time).

### Step 4 — Operationalize
Dashboard ("DNS — Cache Performance"):
- Row 1 — Single-value tiles: "Cache hit ratio (%)", "Cache misses (1h)", "Worst resolver hit ratio", "Top miss domain".
- Row 2 — Timechart: cache hit ratio per resolver over 7 days.
- Row 3 — Cache miss domains table: domain, miss count, avg resolve time.

Alerting:
- Critical (cache hit ratio < 60% for 30+ minutes): serious cache issue — investigate resolver health.
- Warning (cache hit ratio < 75%): degraded performance — review cache configuration.

Runbook:
1. **Sudden cache hit ratio drop**: Check for cache flushes (planned or unplanned). After a flush, the cache needs time to warm up. Monitor for recovery within 1-2 hours.
2. **Persistently low hit ratio**: Increase cache size if possible. Implement minimum TTL override for frequently queried domains with very low TTLs.

### Step 5 — Troubleshooting

- **Response time proxy inaccurate** — The 2ms threshold for cache hits may need adjustment based on your resolver hardware. Faster resolvers may serve cache hits in < 0.5ms; slower ones may take up to 5ms. Calibrate by querying a known cached domain.

- **No Stream data available** — Without wire data, fall back to SNMP polling of DNS cache statistics MIBs or Windows perfmon counters.

## SPL

```spl
index=network sourcetype="infoblox:dns"
| eval cache_hit=if(match(message,"cache hit"),1,0), total=1
| timechart span=1h sum(cache_hit) as hits, sum(total) as total
| eval hit_ratio=round(hits/total*100,1) | where hit_ratio < 70
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

Line chart (hit ratio over time), Single value (current ratio), Table (top miss domains).

## Known False Positives

Spikes can come from DNS cache flushes, authorized security or performance monitoring, or very talky clients; compare against change windows and known scanning tools.

## References

- [CIM: Network_Resolution](https://docs.splunk.com/Documentation/CIM/latest/User/Network_Resolution)
