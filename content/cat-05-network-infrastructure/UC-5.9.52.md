<!-- AUTO-GENERATED from UC-5.9.52.json — DO NOT EDIT -->

---
id: "5.9.52"
title: "ThousandEyes Trace Span Analysis"
status: "verified"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.9.52 · ThousandEyes Trace Span Analysis

> **Criticality:** Medium &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Performance &middot; **Wave:** Run &middot; **Status:** Verified

*We break down every web request into its component steps — looking up the address, connecting, encrypting, processing, and downloading — so when something is slow, we know exactly which step to fix instead of guessing.*

---

## Description

Breaks down HTTP request timing into constituent phases — DNS resolution, TCP connection, TLS handshake, server processing, and content transfer — to identify which phase contributes most to total response time. This is the equivalent of analyzing a distributed trace's span breakdown but for network-level request timing.

## Value

When an HTTP request takes 2 seconds, the instinct is to blame the server. But the 2 seconds might be 200 ms of DNS resolution, 100 ms of TCP connect, 150 ms of TLS handshake, 50 ms of server processing, and 1500 ms of content transfer. Each component points to a different team and a different fix. DNS team for slow resolution, network team for TCP/TLS, application team for processing, and CDN team for transfer. This UC provides the breakdown that eliminates finger-pointing and focuses remediation on the actual bottleneck.

## Implementation

Combines multiple ThousandEyes metrics to reconstruct the request timeline. DNS resolution time comes from associated DNS measurements, network latency from associated network measurements, and the total from HTTP metrics.

## Detailed Implementation

### Prerequisites
- All prerequisites from UC-5.9.34 apply (HTTP Server tests configured, data flowing).
- **HTTP Server tests automatically include network layer measurements.** When you configure an HTTP Server test in ThousandEyes, it automatically performs Agent-to-Server (network) and DNS measurements to the same target. This means a single HTTP Server test produces:
  - `http.client.request.duration` — total TTFB (DNS + TCP + TLS + server processing).
  - `dns.lookup.duration` — DNS resolution time.
  - `network.latency` — network round-trip time.
  These sub-metrics enable the decomposition that is the core of this UC.
- **Understand the TTFB waterfall.** Total TTFB is NOT simply the sum of components — some phases overlap or are sequential depending on the protocol:
  - Sequential: DNS → TCP Connect → TLS Handshake → Server Processing → First Byte.
  - `TTFB ≈ DNS + TCP_RTT + TLS_Handshake + Server_Processing`.
  - `Server_Processing ≈ TTFB - DNS - Network_RTT` (approximation, since TLS adds 1–2 RTTs).
  The decomposition is an approximation, not exact. But it's accurate enough to identify the dominant bottleneck.
- **Complementary data.** For deeper analysis, also configure:
  - Agent-to-Server test (UC-5.9.1) to the same target — isolates network latency.
  - DNS Server test (UC-5.9.5) for the same domain — isolates DNS resolution.
  - Path Visualization (UC-5.9.9) — identifies which network hop is the bottleneck.
- **Splunk role:** `srchIndexesAllowed` must include `thousandeyes_metrics`.

### Step 1 — Configure data collection
HTTP Server test metrics (including sub-metrics) flow through the same Tests Stream — Metrics OTel input configured in UC-5.9.1. No separate input is needed.

Verify sub-metrics are present:
```spl
index=thousandeyes_metrics sourcetype="cisco:thousandeyes:metric" thousandeyes.test.type="http-server" earliest=-1h
| head 100
| stats count values(http.client.request.duration) as ttfb values(dns.lookup.duration) as dns values(network.latency) as net_latency
```
If `dns` and `net_latency` show values, the sub-metrics are available. If they show empty/null, the OTel data model may deliver these as separate metric events rather than combined. In that case, you'll need to correlate by test name and time.

**Understanding the metric relationships for decomposition:**
- `http.client.request.duration` — Time to First Byte. This is the "total" metric. Units: SECONDS.
- `dns.lookup.duration` — DNS resolution time. The first step in any HTTP request. Units: SECONDS. Typical: 5–50 ms for cached DNS, 50–200 ms for uncached.
- `network.latency` — Round-trip time at the network layer (ICMP/TCP). Units: SECONDS. This represents the raw network distance. Multiply by ~2 for a TLS 1.2 handshake contribution (2 RTTs).
- **Server processing time** = TTFB − DNS − Network_RTT (approximately). This is the time the server spends processing your request before sending the first byte. If this dominates, the server is slow.

### Step 2 — Create the search and alert
**TTFB decomposition by test (primary diagnostic view):**
```spl
`stream_index` thousandeyes.test.type="http-server"
| stats avg(http.client.request.duration) as total_ttfb avg(dns.lookup.duration) as dns_time avg(network.latency) as network_time by thousandeyes.test.name, server.address
| eval total_ms=round(total_ttfb*1000,1), dns_ms=round(dns_time*1000,1), network_ms=round(network_time*1000,1)
| eval server_processing_ms=round(total_ms - dns_ms - network_ms, 1)
| eval server_processing_ms=if(server_processing_ms < 0, 0, server_processing_ms)
| table thousandeyes.test.name, server.address, total_ms, dns_ms, network_ms, server_processing_ms
| sort -total_ms
```

**Understanding this SPL**

`avg(http.client.request.duration) as total_ttfb` — average TTFB. This is the number users care about — how long until they see a response.

`avg(dns.lookup.duration) as dns_time` — average DNS resolution time. If this is high (> 100 ms), DNS is a bottleneck. Investigate DNS provider performance (UC-5.9.14) or DNS caching.

`avg(network.latency) as network_time` — average network RTT. If this is high, the server is far away or the network path is congested. Use path visualization (UC-5.9.9) to find the bottleneck hop.

`eval server_processing_ms = total_ms - dns_ms - network_ms` — estimated server processing time. This is an approximation (doesn't account for TLS handshake separately). If this dominates (> 50% of total), the server is slow — investigate application performance.

`if(server_processing_ms < 0, 0, server_processing_ms)` — safety clamp. Due to measurement timing differences, the subtraction can occasionally go negative. Clamp to 0.

**Automated bottleneck identification:**
```spl
`stream_index` thousandeyes.test.type="http-server" earliest=-24h
| stats avg(http.client.request.duration) as total avg(dns.lookup.duration) as dns avg(network.latency) as net by thousandeyes.test.name
| eval total_ms=round(total*1000,1), dns_ms=round(dns*1000,1), net_ms=round(net*1000,1)
| eval server_ms=round(total_ms - dns_ms - net_ms, 1)
| eval server_ms=if(server_ms < 0, 0, server_ms)
| eval dns_pct=round(dns_ms/total_ms*100,1), net_pct=round(net_ms/total_ms*100,1), server_pct=round(server_ms/total_ms*100,1)
| eval bottleneck=case(dns_pct > 40, "DNS", net_pct > 40, "Network", server_pct > 40, "Server", 1=1, "Balanced")
| table thousandeyes.test.name, total_ms, dns_ms, dns_pct, net_ms, net_pct, server_ms, server_pct, bottleneck
| sort -total_ms
```
This adds percentage breakdown and automatic bottleneck classification. A component contributing > 40% of total TTFB is flagged as the bottleneck.

**Per-agent decomposition (geographic breakdown):**
```spl
`stream_index` thousandeyes.test.type="http-server" thousandeyes.test.name="<specific-test>" earliest=-24h
| stats avg(http.client.request.duration) as total avg(dns.lookup.duration) as dns avg(network.latency) as net by thousandeyes.source.agent.name, thousandeyes.source.agent.location
| eval total_ms=round(total*1000,1), dns_ms=round(dns*1000,1), net_ms=round(net*1000,1)
| eval server_ms=round(total_ms - dns_ms - net_ms, 1)
| eval server_ms=if(server_ms < 0, 0, server_ms)
| eval bottleneck=case(dns_ms > net_ms AND dns_ms > server_ms, "DNS", net_ms > server_ms, "Network", 1=1, "Server")
| table thousandeyes.source.agent.name, thousandeyes.source.agent.location, total_ms, dns_ms, net_ms, server_ms, bottleneck
| sort -total_ms
```
If the bottleneck varies by agent location:
- DNS bottleneck for some agents → those agents use slower DNS resolvers.
- Network bottleneck for distant agents → expected (physics). Consider CDN/geo-LB.
- Server bottleneck for ALL agents → server issue (independent of agent location).

**Decomposition trending over time:**
```spl
`stream_index` thousandeyes.test.type="http-server" thousandeyes.test.name="<specific-test>" earliest=-7d
| timechart span=4h avg(http.client.request.duration) as total_s avg(dns.lookup.duration) as dns_s avg(network.latency) as net_s
| eval server_s=total_s - dns_s - net_s
| eval server_s=if(server_s < 0, 0, server_s)
```
Reveals which component is causing TTFB changes over time. If `server_s` suddenly increases after a deployment, the deployment introduced a server-side regression.

**Scheduling:** On-demand investigation (primary use case) or cron `0 */4 * * *` (every 4 hours) for automated bottleneck detection. Alert when any test's bottleneck shifts from "Balanced" or "Network" to "Server" (indicates application regression).

### Step 3 — Validate
(a) **ThousandEyes waterfall cross-reference.** In the ThousandEyes UI, open the HTTP Server test → Views → select a test round → look at the waterfall view. It shows DNS, Connect, TLS, Wait, and Transfer phases. Compare with your SPL decomposition values. They should be roughly consistent.

(b) **Manual `curl` decomposition.** From a machine with direct access:
```
curl -w "DNS: %{time_namelookup}s\nConnect: %{time_connect}s\nTLS: %{time_appconnect}s\nTTFB: %{time_starttransfer}s\nTotal: %{time_total}s\n" -o /dev/null -s https://app.example.com/
```
Compare: `time_namelookup` ≈ `dns.lookup.duration`, `time_connect - time_namelookup` ≈ network RTT, `time_starttransfer` ≈ TTFB.

(c) **Sub-metric availability check.** Not all OTel data model versions emit DNS and network metrics alongside HTTP metrics in the same event. If `dns_ms` or `network_ms` consistently shows null, the sub-metrics may be in separate events. Check with `| fieldsummary` on a sample of HTTP Server metric events.

(d) **Server processing time sanity check.** If `server_processing_ms` is negative, the measurement methodology creates timing inconsistencies. Use `if(server_processing_ms < 0, 0, server_processing_ms)` to handle this.

(e) **Bottleneck consistency.** Run the bottleneck identification search over 7 days. If the bottleneck for a test consistently shows "Server", it's a real application performance issue. If it alternates between "Network" and "Server", the issue may be intermittent network congestion.

### Step 4 — Operationalize
**Dashboard** ("HTTP Request Decomposition" — designed for SRE / performance engineering):
- Row 1 — Bottleneck summary: table of all HTTP tests with total TTFB, DNS %, Network %, Server %, and bottleneck classification. Color-code the bottleneck column (DNS = blue, Network = orange, Server = red).
- Row 2 — Stacked bar chart: for each test, show DNS/Network/Server as stacked bars. Immediately visualizes where time is spent.
- Row 3 — Per-agent decomposition: for a selected test (dropdown), show decomposition per agent. Reveals geographic patterns.
- Row 4 — Decomposition trending: timechart showing DNS/Network/Server components over 7 days. Reveals when the bottleneck shifted.

**Alerting:**
- Bottleneck shifts to "Server" for a previously "Network" or "Balanced" test → medium-urgency notification to application team. A deployment or configuration change may have degraded server performance.
- DNS component > 200 ms → low-urgency notification to DNS team. DNS is adding significant latency.

**Runbook** (owner: performance engineering / SRE):
1. **Bottleneck = DNS.** (a) Investigate DNS resolution time (UC-5.9.14). (b) Check DNS resolver performance — switch to a faster resolver if needed. (c) Implement DNS caching at the application or OS level. (d) Check if DNS TTL is too low (causes frequent re-resolution).
2. **Bottleneck = Network.** (a) Check network latency to the server (UC-5.9.1). (b) Use path visualization (UC-5.9.9) to identify the slow hop. (c) For distant servers, consider CDN deployment or geo-load balancing. (d) For congested paths, consider WAN optimization or alternate ISP peering.
3. **Bottleneck = Server.** (a) Check application logs for slow queries, errors, or resource exhaustion. (b) Check server CPU/memory utilization. (c) Check database query performance. (d) If the shift is recent, correlate with deployment timestamps.
4. **Bottleneck = Balanced.** No single component dominates. To improve TTFB, you need to optimize ALL components. Prioritize by absolute time: if DNS = 50 ms, Network = 50 ms, Server = 50 ms, total = 150 ms — all are reasonable, and improvement requires a holistic approach.

### Step 5 — Troubleshooting

- **DNS or network times consistently null** — The OTel data model may deliver these as separate metric events. Try correlating by test name and time window: use two separate `stats` queries and `join` by `thousandeyes.test.name` instead of relying on all metrics being in the same event.

- **Server processing time is negative** — Measurement timing differences between the HTTP, DNS, and network probes can cause this. The clamp `if(server_processing_ms < 0, 0, server_processing_ms)` handles it. For more accurate decomposition, use the ThousandEyes waterfall view.

- **Decomposition doesn't add up to total TTFB** — This is expected. The decomposition is an approximation. TLS handshake adds 1–2 RTTs that are partially captured in both TTFB and network latency. The decomposition is accurate enough to identify the DOMINANT bottleneck, not for exact accounting.

- **All tests show "Server" bottleneck** — This is normal for well-connected test agents (low DNS and network times). If agents are close to the server (same data center), network and DNS are trivial, and server processing dominates by default.

- **All common troubleshooting** — See UC-5.9.34 Step 5 for HTTP test issues, and UC-5.9.1 Step 5 for general app troubleshooting.

**IPv6 Note:** ICMPv6 is architecturally critical for IPv6 — it carries NDP (Neighbor Discovery), Path MTU Discovery, and Multicast Listener Discovery. Unlike ICMP for IPv4, blocking ICMPv6 breaks IPv6 connectivity entirely. Ensure firewall policies permit at minimum ICMPv6 types 1-4 (Destination Unreachable, Packet Too Big, Time Exceeded, Parameter Problem) and types 133-137 (RS, RA, NS, NA, Redirect). See RFC 4890 for filtering recommendations.

## SPL

```spl
`stream_index` thousandeyes.test.type="http-server"
| stats avg(http.client.request.duration) as total_ttfb avg(dns.lookup.duration) as dns_time avg(network.latency) as network_time by thousandeyes.test.name, server.address
| eval total_ms=round(total_ttfb*1000,1), dns_ms=round(dns_time*1000,1), network_ms=round(network_time*1000,1)
| eval server_processing_ms=round(total_ms - dns_ms - network_ms, 1)
| sort -total_ms
```

## Visualization

(1) Stacked bar: timing breakdown per test (DNS, network, server processing, transfer). (2) Table: per-test timing components. (3) Timechart: component timing trending.

## Known False Positives

**Component timing approximation.** The breakdown is approximate because DNS, network, and HTTP tests may run at slightly different times within a test round. The sum of components may not exactly equal the total TTFB.

**DNS caching effects.** If DNS is cached (resolved once and reused), DNS timing may appear near-zero, making it seem like DNS is not a factor. This is correct — but a cache miss during a TTL expiration event would show the true DNS cost.

## References

- [Cisco ThousandEyes App for Splunk (Splunkbase 7719)](https://splunkbase.splunk.com/app/7719)
- [ThousandEyes OTel v2 data model](https://docs.thousandeyes.com/product-documentation/integration-guides/opentelemetry/data-model/data-model-v2/metrics)
