<!-- AUTO-GENERATED from UC-5.9.16.json — DO NOT EDIT -->

---
id: "5.9.16"
title: "DNS Provider Comparison"
status: "verified"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.9.16 · DNS Provider Comparison

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance, Capacity &middot; **Wave:** Run &middot; **Status:** Verified

*We test the same domain name against several different DNS services side by side — like timing how fast different phone directories answer — so we always know which one is quickest and most reliable, and can switch if our usual one gets slow.*

---

## Description

Compares DNS resolution performance across multiple DNS providers (internal resolvers, Cloudflare 1.1.1.1, Google 8.8.8.8, ISP resolvers, cloud provider resolvers) querying the same domain, showing which provider delivers the lowest latency and highest availability from your agents' perspectives.

## Value

The choice of DNS resolver can make a 10–150 ms difference in every new connection — a difference that compounds across the dozens of DNS lookups in a modern web page. Many organizations default to their ISP's resolver or an internal BIND server without ever benchmarking against alternatives. This UC provides data-driven evidence for DNS architecture decisions: "Our internal resolver takes 45 ms average for external domains while Cloudflare takes 8 ms — switching saves 37 ms per lookup × 30 lookups per page = 1.1 seconds of page load time." It also provides ongoing monitoring: if your primary DNS provider degrades, you can see the secondary providers maintaining performance, and make a routing change with confidence.

## Implementation

Create multiple DNS Server tests in ThousandEyes for the same domain, each targeting a different DNS server address. Example: test #1 targets 10.0.0.53 (internal resolver), test #2 targets 1.1.1.1 (Cloudflare), test #3 targets 8.8.8.8 (Google). Use the same Cloud and/or Enterprise Agents for all tests to ensure a fair comparison from the same vantage points.

## Detailed Implementation

### Prerequisites
- All prerequisites from UC-5.9.13 apply (app installed, OAuth authenticated, HEC, Tests Stream).
- **Multiple DNS Server tests configured.** For each domain you want to compare, create one DNS Server test per DNS provider:
  - Internal corporate resolver (e.g., `10.0.0.53`)
  - Cloudflare DNS (`1.1.1.1` or `1.0.0.1`)
  - Google Public DNS (`8.8.8.8` or `8.8.4.4`)
  - ISP-provided resolver (varies)
  - Cloud provider resolver (e.g., AWS VPC resolver `169.254.169.253`, Azure DNS `168.63.129.16`)
- **Same agents for all tests.** Use identical agent selection across tests to ensure fair comparison. If one test uses 10 agents worldwide and another uses 3, the comparison is skewed.
- **Same domain for all tests.** The domain being queried must be identical across all tests (same `dns.question.name`).
- **Reasonable test intervals.** For public resolvers, use 5–15 minute intervals to avoid rate limiting. For internal resolvers, 1–5 minutes is fine.

### Step 1 — Configure data collection
Same as UC-5.9.13. All DNS Server tests flow through the same OTel stream.

Verify multiple providers are being tested for the same domain:
```spl
index=thousandeyes_metrics thousandeyes.test.type="dns-server" earliest=-1h
| stats dc(server.address) as providers values(server.address) as resolver_ips by dns.question.name
| where providers > 1
```
You should see at least 2 providers per domain you're comparing.

### Step 2 — Create the search and alert
```spl
`stream_index` thousandeyes.test.type="dns-server"
| stats avg(dns.lookup.duration) as avg_duration_s avg(dns.lookup.availability) as avg_availability p95(dns.lookup.duration) as p95_duration_s by server.address, dns.question.name
| eval avg_duration_ms=round(avg_duration_s*1000,1), p95_duration_ms=round(p95_duration_s*1000,1)
| sort dns.question.name, avg_duration_ms
```

**Understanding this SPL**

`by server.address, dns.question.name` — splits by both DNS server and domain so you get one row per provider-domain combination. Sorting by `dns.question.name` first, then `avg_duration_ms` within each domain, shows providers ranked fastest-to-slowest for each domain.

`p95(dns.lookup.duration)` — p95 is more informative than max for provider comparison because it filters out the occasional timeout outlier. A provider with avg=10ms and p95=15ms is more consistent (and better) than one with avg=8ms and p95=500ms.

**Provider labeling variant** (human-readable provider names):
```spl
`stream_index` thousandeyes.test.type="dns-server"
| eval provider = case(
    server.address="1.1.1.1" OR server.address="1.0.0.1", "Cloudflare",
    server.address="8.8.8.8" OR server.address="8.8.4.4", "Google",
    server.address="9.9.9.9", "Quad9",
    server.address="208.67.222.222" OR server.address="208.67.220.220", "OpenDNS/Cisco Umbrella",
    match(server.address, "^10\."), "Internal",
    match(server.address, "^172\.(1[6-9]|2[0-9]|3[0-1])\."), "Internal",
    match(server.address, "^192\.168\."), "Internal",
    1=1, server.address)
| stats avg(dns.lookup.duration) as avg_dur_s avg(dns.lookup.availability) as avail p95(dns.lookup.duration) as p95_dur_s by provider, dns.question.name
| eval avg_ms=round(avg_dur_s*1000,1), p95_ms=round(p95_dur_s*1000,1)
| sort dns.question.name, avg_ms
```

**Per-agent comparison** (fair comparison from same vantage point):
```spl
`stream_index` thousandeyes.test.type="dns-server"
| stats avg(dns.lookup.duration) as avg_dur_s by server.address, dns.question.name, thousandeyes.source.agent.name
| eval avg_ms=round(avg_dur_s*1000,1)
| xyseries thousandeyes.source.agent.name, server.address, avg_ms
```
This pivots the table so each row is an agent and each column is a DNS provider, making per-agent comparison easy.

**This UC is primarily a dashboard/report, not an alert.** The value is in ongoing comparison, not threshold-based alerting. However, you can add an alert for when your primary provider becomes slower than your backup: `| where <primary_provider_ms> > <backup_provider_ms> * 1.5` (primary is 50% slower than backup).

### Step 3 — Validate
(a) **Verify test parity.** All tests for the same domain should use the same agents. Check: `| stats values(thousandeyes.source.agent.name) as agents by server.address, dns.question.name`.

(b) **Sanity check results.** Public resolvers (Cloudflare, Google) should typically resolve in 1–20 ms for popular domains. Internal resolvers vary widely but should be < 50 ms for internally hosted domains. If a public resolver shows > 100 ms, the agent is geographically far from the nearest anycast PoP.

(c) **Cross-reference with DNSPerf.** Compare your ThousandEyes results with public DNS benchmarks at dnsperf.com. The rankings should be directionally consistent.

### Step 4 — Operationalize
**Dashboard** ("DNS Provider Scorecard" — used for quarterly DNS architecture reviews):
- Grouped bar chart: avg resolution time per provider per domain.
- Table: provider | domain | avg (ms) | p95 (ms) | availability % — sorted by domain then speed.
- Recommendation panel: highlight the fastest provider per domain.

**Quarterly review process:**
1. Export 30-day data as CSV.
2. Calculate per-provider cost-effectiveness: resolution_time_savings × estimated_annual_queries.
3. Present to architecture team with recommendation to switch primary DNS if significant savings are found.

### Step 5 — Troubleshooting

- **Only one provider appears for each domain** — You need to create separate DNS Server tests per provider. A single test queries only one `server.address`.

- **Internal resolver appears much slower than public** — This may be correct. Internal resolvers handle split-horizon DNS, policy enforcement, and conditional forwarding, all of which add latency. The comparison is still useful but the interpretation should account for the additional work the internal resolver is doing.

- **All common troubleshooting** — See UC-5.9.13 and UC-5.9.1 Step 5.

## SPL

```spl
`stream_index` thousandeyes.test.type="dns-server"
| stats avg(dns.lookup.duration) as avg_duration_s avg(dns.lookup.availability) as avg_availability p95(dns.lookup.duration) as p95_duration_s by server.address, dns.question.name
| eval avg_duration_ms=round(avg_duration_s*1000,1), p95_duration_ms=round(p95_duration_s*1000,1)
| sort dns.question.name, avg_duration_ms
```

## Visualization

(1) Grouped bar chart: avg resolution time per DNS provider for each domain — immediately shows which provider is fastest. (2) Table: provider (server.address) | domain | avg resolution (ms) | p95 (ms) | availability % — sorted by domain then duration. (3) Timechart: resolution time per provider over 24 hours for a selected domain (dropdown token) — shows consistency, not just average. (4) Scatter plot: resolution time (X-axis) vs availability (Y-axis), colour by provider — the ideal provider is in the top-left corner (fast and reliable).

## Known False Positives

**Anycast-induced variability.** Public DNS resolvers (1.1.1.1, 8.8.8.8) use anycast, so different agents reach different physical servers. An agent in Tokyo may get excellent performance from 1.1.1.1 (hitting the Tokyo PoP) while an agent in rural Africa gets poor performance (hitting a distant PoP). This isn't a resolver problem — it's a geographic proximity effect. Compare providers per-agent, not just fleet-wide averages.

**Cache state differences.** Public resolvers like Google and Cloudflare serve billions of queries and have warm caches for popular domains. Your internal resolver may have a cold cache for rarely-queried domains, making it appear slower. For a fair comparison, test with domains that are frequently queried across all resolvers, or account for cold-cache effects by looking at p95 rather than average.

**Internal resolver serving different records.** If your internal DNS resolver returns different records than public resolvers (e.g., split-horizon DNS for internal vs external IPs), the comparison isn't apples-to-apples. The internal resolver may be doing additional work (conditional forwarding, policy-based routing) that increases resolution time. This is the correct behavior, not a performance problem.

**Rate limiting on public resolvers.** If you send excessive test queries to public resolvers (e.g., 10 agents querying 1.1.1.1 every 60 seconds for the same domain), the resolver may rate-limit your queries, artificially degrading measured performance. Use reasonable test intervals (5–15 minutes) for public resolver tests.

## References

- [Cisco ThousandEyes App for Splunk (Splunkbase 7719)](https://splunkbase.splunk.com/app/7719)
- [ThousandEyes DNS Server Test](https://docs.thousandeyes.com/product-documentation/internet-and-wan-monitoring/tests/dns-tests/)
- [DNSPerf — Public DNS resolver performance benchmarks](https://www.dnsperf.com/)
