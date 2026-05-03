<!-- AUTO-GENERATED from UC-5.6.8.json — DO NOT EDIT -->

---
id: "5.6.8"
title: "DNS Latency Monitoring"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.6.8 · DNS Latency Monitoring

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance

*We watch for unusual DNS patterns so we notice possible attacks, mistakes, or overloaded resolvers before people feel it as slow apps or failed lookups.*

---

## Description

DNS latency directly adds to every network connection. Slow DNS = slow everything.

## Value

DNS operations teams monitor DNS query latency per resolver in real time, detecting performance degradation before users experience slow application load times caused by DNS resolution delays.

## Implementation

Use scripted input running `dig` queries against DNS servers measuring response time. Or enable DNS analytical logging with timing. Alert when average latency >50ms.

## Detailed Implementation

### Prerequisites
- DNS response time data. Sources: (a) Splunk Stream (`sourcetype=stream:dns`) — passive capture of DNS query/response pairs with microsecond-precision latency, (b) Infoblox NIOS query logs with response time (if enabled), (c) Synthetic monitoring (ThousandEyes, Catchpoint) sending DNS probe results to Splunk. Passive wire data via Stream is the most accurate source for real DNS latency.
- Understanding DNS latency: (a) cache hit: < 1 ms (response from local cache), (b) recursive resolution: 10-100 ms (resolver queries authoritative servers), (c) degraded: 200-500 ms (upstream timeout or congestion), (d) timeout: > 2000 ms (usually results in retry or failure). Client-perceived latency includes: DNS lookup + TCP handshake + TLS handshake + HTTP request.
- CIM: Network_Resolution data model includes `DNS.response_time` for normalized latency.

### Step 1 — Configure data collection
Verify DNS latency data:
```spl
index=dns sourcetype="stream:dns" earliest=-15m
| stats count avg(response_time) as avg_latency_ms perc95(response_time) as p95_latency_ms by dest
```
If `response_time` is null, the data source may not include latency. Splunk Stream provides this natively; syslog-based DNS logs typically do not.

### Step 2 — Create the search and alert

**Primary search — DNS latency by resolver:**
```spl
index=dns sourcetype="stream:dns" earliest=-15m
| stats avg(response_time) as avg_ms perc50(response_time) as p50_ms perc95(response_time) as p95_ms perc99(response_time) as p99_ms max(response_time) as max_ms count as queries by dest
| eval status=case(p95_ms > 500, "CRITICAL", p95_ms > 200, "HIGH", p95_ms > 100, "WARNING", 1==1, "OK")
| where p95_ms > 50
| sort -p95_ms
```

#### Understanding this SPL: P95 latency (95th percentile) is the key metric — it shows the worst latency experienced by 1 in 20 queries. If P95 > 200ms, 5% of DNS lookups are slow enough to noticeably impact user experience. P50 (median) shows typical performance. The gap between P50 and P95 indicates consistency — a large gap means occasional spikes.

**Latency trending with anomaly detection:**
```spl
index=dns sourcetype="stream:dns" earliest=-24h
| bin _time span=5m
| stats avg(response_time) as avg_ms perc95(response_time) as p95_ms by _time, dest
| eventstats avg(avg_ms) as baseline_avg stdev(avg_ms) as std_avg by dest
| where avg_ms > baseline_avg + (3 * std_avg)
| eval deviation=round((avg_ms - baseline_avg) / std_avg, 1)
| sort -deviation
```

**Slow query analysis — which domains are slow:**
```spl
index=dns sourcetype="stream:dns" response_time > 200 earliest=-1h
| stats count avg(response_time) as avg_ms dc(src) as affected_clients by query
| sort -avg_ms
| head 20
```

### Step 3 — Validate
(a) Compare Splunk DNS latency with `dig` measurements: `dig @<resolver> <domain> | grep "Query time"`. Splunk Stream captures real client latency; `dig` measures from the measurement host.
(b) Verify during a known outage: if an upstream DNS provider has issues, latency should spike in Splunk.

### Step 4 — Operationalize
Dashboard ("DNS — Latency Monitoring"):
- Row 1 — Single-value tiles: "Average DNS latency (ms)", "P95 latency (ms)", "Resolvers > 200ms P95", "Slow queries (1h)".
- Row 2 — Timechart: P50 and P95 latency per resolver over 24h.
- Row 3 — Slow domain table: query, avg_ms, affected_clients.

Alerting:
- Critical (P95 > 500ms on any resolver for 10+ minutes): DNS resolution severely impacted — page DNS operations.
- Warning (P95 > 200ms sustained): investigate upstream resolver health.

Runbook:
1. **All resolvers slow**: Check upstream forwarder connectivity. If using cloud DNS (8.8.8.8, 1.1.1.1), check provider status pages. If self-hosted, check resolver CPU/memory.
2. **One resolver slow, others OK**: Check that specific resolver's health — CPU, memory, network connectivity to authoritative servers.
3. **Specific domains slow**: The authoritative server for that domain may be overloaded or geographically distant. Consider prefetching or adding a local stub zone.

### Step 5 — Troubleshooting

- **No `response_time` field available** — Syslog-based DNS logs (Infoblox, BIND) typically don't include latency. Deploy Splunk Stream for passive DNS latency measurement, or use synthetic monitoring probes.

- **Latency values seem too low (< 1ms for everything)** — This likely means all queries are cache hits. To measure recursive latency, filter to first-time queries: `| where response_time > 1`.

- **Splunk Stream not capturing DNS** — Ensure the Stream forwarder is on a network segment that sees DNS traffic (span/mirror port or inline). Verify the DNS protocol stream is enabled in Stream configuration.

## SPL

```spl
index=dns sourcetype="dns:latency"
| timechart span=5m avg(response_time_ms) as avg_latency by dns_server
| where avg_latency > 50
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

Line chart per server, Gauge, Table.

## Known False Positives

Spikes can come from DNS cache flushes, authorized security or performance monitoring, or very talky clients; compare against change windows and known scanning tools.

## References

- [CIM: Network_Resolution](https://docs.splunk.com/Documentation/CIM/latest/User/Network_Resolution)
