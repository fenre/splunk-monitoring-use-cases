<!-- AUTO-GENERATED from UC-5.9.14.json — DO NOT EDIT -->

---
id: "5.9.14"
title: "DNS Resolution Time Trending"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.9.14 · DNS Resolution Time Trending

> **Criticality:** High &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Performance &middot; **Wave:** Walk &middot; **Status:** Verified

*We measure how long it takes to look up our domain names on the internet, because even though you don't see it, a slow lookup adds delay to every single click and page load.*

---

## Description

Flags DNS Server tests where average resolution time exceeds 200 ms, indicating a DNS server or network path degradation. Every new TCP connection begins with a DNS lookup — a 200 ms DNS resolution adds 200 ms to the initial page load and every subsequent connection to a new hostname. For applications making dozens of DNS lookups per page, this compounds into seconds of visible delay.

## Value

DNS resolution time is the invisible tax on every network connection. A user loading a modern web page triggers 20–50 DNS lookups (the main domain, CDN, analytics, ads, APIs). If each lookup takes 200 ms instead of 20 ms, the page load takes an extra 3.6 seconds before a single byte of content arrives. By trending DNS resolution time in Splunk and alerting on degradation, the DNS team can identify overloaded resolvers (need more capacity), misconfigured recursive resolution chains (unnecessary hops), geo-distance issues (users being sent to a DNS server on a different continent), or cache pollution (malicious or corrupted cache entries increasing lookup chains) — all before users experience the latency as "the website is slow."

## Implementation

Uses the same DNS Server test data as UC-5.9.13. No additional test configuration needed. The `dns.lookup.duration` metric is reported alongside `dns.lookup.availability` in the same events. Schedule as a dashboard trending panel with an alert for sustained resolution times above 200 ms.

## Detailed Implementation

### Prerequisites
- All prerequisites from UC-5.9.13 apply — DNS Server tests configured, Tests Stream enabled, DNS data flowing.
- **Resolution time baselines:** Establish expected resolution times per domain × server combination over 7 days before setting thresholds. Cached lookups: 1–5 ms. Uncached lookups to local authoritative: 10–50 ms. Uncached lookups through recursive chain: 50–200 ms. Anything above 200 ms sustained is almost always a problem.

### Step 1 — Configure data collection
Same as UC-5.9.13. The `dns.lookup.duration` metric is reported in the same events as `dns.lookup.availability`.

Verify:
```spl
index=thousandeyes_metrics thousandeyes.test.type="dns-server" earliest=-30m
| stats avg(dns.lookup.duration) as avg_dur by dns.question.name, server.address
| eval avg_dur_ms = round(avg_dur * 1000, 1)
```

### Step 2 — Create the search and alert
**Trending search (dashboard):**
```spl
`stream_index` thousandeyes.test.type="dns-server"
| timechart span=5m avg(dns.lookup.duration) as avg_dns_s by dns.question.name
| foreach avg_dns_s* [eval <<FIELD>>=round(<<FIELD>>*1000,1)]
```

**Alert search:**
```spl
`stream_index` thousandeyes.test.type="dns-server"
| stats avg(dns.lookup.duration) as avg_dns_s max(dns.lookup.duration) as max_dns_s by dns.question.name, server.address
| eval avg_dns_ms=round(avg_dns_s*1000,1), max_dns_ms=round(max_dns_s*1000,1)
| where avg_dns_ms > 200
| sort -avg_dns_ms
```

**Understanding this SPL**

`dns.lookup.duration` — in OTel v2, this is in **seconds**. A value of `0.015` means 15 ms. The `eval` converts to milliseconds for human readability.

`where avg_dns_ms > 200` — 200 ms is the threshold where DNS latency becomes perceptible to users. For web-heavy workloads, tighten to 100 ms. For internal applications where DNS resolution is a small fraction of total latency, relax to 500 ms.

Why `avg` AND `max`: average tells you the sustained DNS quality; max tells you the worst single lookup. If avg is 20 ms but max is 2000 ms, you have occasional DNS timeouts (1 query timing out and being retried) that aren't visible in the average but cause individual user requests to take 2+ seconds.

**Percentile variant** (more nuanced than avg/max):
```spl
`stream_index` thousandeyes.test.type="dns-server"
| stats p50(dns.lookup.duration) as p50_s p95(dns.lookup.duration) as p95_s p99(dns.lookup.duration) as p99_s by dns.question.name, server.address
| eval p50_ms=round(p50_s*1000,1), p95_ms=round(p95_s*1000,1), p99_ms=round(p99_s*1000,1)
| where p95_ms > 200
| sort -p95_ms
```
P95 at 200 ms means 5% of lookups take longer than 200 ms — this catches intermittent DNS slowdowns that avg misses.

**Scheduling:** cron `*/15 * * * *`, time range `-1h to now`. Throttle by `dns.question.name` + `server.address` for 4 hours.

### Step 3 — Validate
(a) **Cross-reference ThousandEyes UI.** The ThousandEyes DNS Server view shows resolution time per agent. Compare the numbers in Splunk to the UI.

(b) **Manual query timing.** From a machine with access to the DNS server: `dig @<server> <domain> +stats` — look at the "Query time:" line at the bottom. Compare with what ThousandEyes/Splunk reports. Note: `dig` measures from the client; ThousandEyes measures from the agent. Network latency between the agent and the DNS server is included in the ThousandEyes measurement.

(c) **Cache vs uncached comparison.** Run two `dig` queries in succession. The first (uncached) will be slower; the second (cached) should be faster. ThousandEyes queries may hit cache or not depending on TTL and query timing.

### Step 4 — Operationalize
**Dashboard** (add as a row in the UC-5.9.13 "DNS Health" dashboard):
- Timechart: resolution time per domain over 24 hours. Add a reference line at 200 ms.
- Table: domain | server | avg resolution (ms) | p95 (ms) | max (ms) — sorted by p95 descending.
- Comparison bar chart: resolution time per DNS server for a selected domain (dropdown token).

**Runbook** (owner: DNS team):
1. **Resolution time increased suddenly.** Check if the DNS server was restarted (cold cache). Wait for one TTL cycle and re-check.
2. **Sustained high resolution time.** Check DNS server CPU and query rate. If CPU is high, the server needs more capacity or query rate reduction (tune TTL upward).
3. **High resolution time from specific agents only.** The problem is network latency between those agents and the DNS server, not the DNS server itself. Correlate with UC-5.9.1.
4. **Resolution time increases at specific times of day.** DNS server is overloaded during peak hours. Add more DNS capacity or use DNS load balancing.

### Step 5 — Troubleshooting

- **Resolution time seems unrealistically low (< 1 ms for all queries)** — The agent may be using a local DNS cache (systemd-resolved, dnsmasq) that intercepts queries before they reach the configured DNS server. This means you're measuring cache response time, not actual DNS server response time. Check the agent's DNS configuration.

- **Resolution time is exactly 0** — The metric may not be populated. Check field presence: `| fieldsummary | search field=dns.lookup.duration`.

- **All common troubleshooting** — See UC-5.9.13 and UC-5.9.1 Step 5.

## SPL

```spl
`stream_index` thousandeyes.test.type="dns-server"
| stats avg(dns.lookup.duration) as avg_dns_s max(dns.lookup.duration) as max_dns_s by dns.question.name, server.address
| eval avg_dns_ms=round(avg_dns_s*1000,1), max_dns_ms=round(max_dns_s*1000,1)
| where avg_dns_ms > 200
| sort -avg_dns_ms
```

## Visualization

(1) Timechart: `| timechart span=5m avg(dns.lookup.duration) as avg_dns_s by dns.question.name | eval avg_dns_ms=round(avg_dns_s*1000,1)` — shows resolution time trends per domain. Step-changes indicate DNS infrastructure events. (2) Table: domain, server, avg resolution (ms), max resolution (ms) — sorted worst-first. (3) Single value: count of domains with avg resolution > 200 ms (yellow) or > 500 ms (red). (4) Comparison bar chart: resolution time by DNS server for the same domain (compare your internal resolver vs Cloudflare vs Google — see UC-5.9.16).

## Known False Positives

**Cold cache effect.** The first query after a DNS server restarts or after a TTL expires requires full recursive resolution (root → TLD → authoritative), which takes 50–200 ms even for healthy DNS. Subsequent queries hit the cache and return in 1–5 ms. Distinguish by checking whether the slow lookups are isolated spikes (cold cache) vs sustained (real degradation). Use `avg` over 1 hour to smooth out cold-cache spikes.

**Geo-distance to DNS server.** If an agent in Asia is querying a DNS server in the US, the network round-trip alone adds 150–250 ms to the resolution time. This is not a DNS problem — it's a network latency problem. Distinguish by correlating `dns.lookup.duration` with the network latency to the same server IP (UC-5.9.1). If DNS duration ≈ network latency, the DNS server is fast but far away.

**Large DNS responses.** Queries for domains with many records (dozens of A records for load balancing, or large TXT records for SPF/DKIM) take longer to transfer over the network, even though the DNS server resolved them instantly. Distinguish by checking whether the affected domain has unusually large record sets.

**DNS server CPU under load.** During peak query hours, a DNS server's resolution time increases due to CPU contention. This is a real capacity issue (not a false positive per se), but it's a different problem than a DNS configuration issue. Check if the degradation follows daily traffic patterns.

## References

- [Cisco ThousandEyes App for Splunk (Splunkbase 7719)](https://splunkbase.splunk.com/app/7719)
- [ThousandEyes DNS Server Test — Resolution time metrics](https://docs.thousandeyes.com/product-documentation/internet-and-wan-monitoring/tests/dns-tests/dns-server-test)
- [Google Web Performance — DNS lookup impact on page load time](https://web.dev/articles/performance-http2)
