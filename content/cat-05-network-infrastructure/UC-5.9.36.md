<!-- AUTO-GENERATED from UC-5.9.36.json — DO NOT EDIT -->

---
id: "5.9.36"
title: "HTTP Server Throughput Analysis"
status: "verified"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.9.36 · HTTP Server Throughput Analysis

> **Criticality:** Medium &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Performance, Capacity &middot; **Wave:** Walk &middot; **Status:** Verified

*We measure how fast data flows from our web servers, like checking the water pressure from a pipe — if it's too slow, large files take forever to download and applications feel sluggish.*

---

## Description

Monitors HTTP Server test download throughput — the data transfer rate from the target server. Low throughput indicates bandwidth constraints, server-side throttling, or congested network paths. Useful for large file downloads, API responses with significant payloads, or content delivery performance.

## Value

Throughput tells a different story than latency. A server may respond quickly (low TTFB) but deliver content slowly (low throughput) due to bandwidth limitations, TCP window sizing, or server-side rate limiting. For applications that transfer significant data (report downloads, file servers, media streaming, API bulk responses), throughput is the critical metric. This UC identifies servers and paths where bandwidth is the bottleneck.

## Implementation

Uses the same HTTP Server tests as UC-5.9.34. Throughput is automatically measured alongside availability and TTFB.

## Detailed Implementation

### Prerequisites
- All prerequisites from UC-5.9.34 apply — HTTP Server tests must be configured in ThousandEyes, and the Tests Stream — Metrics input must be delivering data to `thousandeyes_metrics`.
- **HTTP Server tests must be configured to download a response body.** Throughput is only measured when data is transferred. Tests configured with `HTTP Response → Headers Only` or very small response bodies produce near-zero throughput values that aren't meaningful for bandwidth analysis. For throughput monitoring, target URLs that return a substantive response (e.g., a test file, a data API endpoint returning 100+ KB, or a page with multiple resources).
- **Throughput baselines established.** Throughput depends heavily on the test target: a 1 KB health-check endpoint will always show low throughput regardless of available bandwidth, while a 10 MB test file will reveal actual bandwidth capacity. Document expected throughput per test based on the target response size and the available network bandwidth.
- **Splunk role:** `srchIndexesAllowed` must include `thousandeyes_metrics`.

### Step 1 — Configure data collection
HTTP Server test metrics (including throughput) flow through the same Tests Stream — Metrics OTel input configured in UC-5.9.1. No separate input is needed.

Verify throughput data is present:
```spl
index=thousandeyes_metrics sourcetype="cisco:thousandeyes:metric" thousandeyes.test.type="http-server" earliest=-1h
| stats avg(http.server.throughput) as avg_throughput count by thousandeyes.test.name
| where isnotnull(avg_throughput) AND avg_throughput > 0
```
Each test should show non-zero throughput. If `avg_throughput` is 0 or null, the test may be failing (check UC-5.9.34 availability first) or the response body is too small to measure meaningful throughput.

**Understanding the metric:**
- `http.server.throughput` (bytes per second) — the rate at which response data was transferred from the server to the agent. This is NOT the theoretical link speed; it's the actual achieved throughput for this specific transfer, limited by: server output rate, path bandwidth, TCP window size, and latency (TCP throughput ≈ window_size / RTT).
- Units: **bytes per second** (not bits, not kilobytes). Convert to human-readable: `bytes/sec × 8 / 1,000,000 = Mbps`. A throughput of `1,250,000` bytes/sec = **10 Mbps**.
- Throughput is affected by response size: small responses (< 10 KB) may complete within the TCP slow-start phase and never reach full throughput. For accurate bandwidth measurement, the response should be at least 100 KB.
- Throughput is only reported for successful requests (`http.server.request.availability = 100`). Failed requests produce no throughput data.

### Step 2 — Create the search and alert
**Throughput overview (sorted lowest-first):**
```spl
`stream_index` thousandeyes.test.type="http-server"
| stats avg(http.server.throughput) as avg_throughput min(http.server.throughput) as min_throughput p5(http.server.throughput) as p5_throughput by thousandeyes.test.name, server.address
| eval avg_mbps=round(avg_throughput*8/1000000,2), min_mbps=round(min_throughput*8/1000000,2), p5_mbps=round(p5_throughput*8/1000000,2)
| sort avg_mbps
```

**Understanding this SPL**

`avg(http.server.throughput)` — average throughput across all test rounds and agents. Represents typical download speed.

`min(http.server.throughput)` — worst single throughput measurement. A very low `min` with a normal `avg` indicates occasional bandwidth congestion or server-side throttling.

`p5(http.server.throughput)` — 5th percentile (the worst 5% of measurements). More robust than `min` for identifying sustained low-throughput patterns while ignoring one-off outliers.

`eval avg_mbps=round(avg_throughput*8/1000000,2)` — converts bytes/sec to Mbps. The `×8` converts bytes to bits; the `÷1,000,000` converts bits to megabits.

`sort avg_mbps` — lowest throughput first, so bandwidth-constrained tests appear at the top.

**Per-agent throughput comparison** (identifies regional bandwidth issues):
```spl
`stream_index` thousandeyes.test.type="http-server"
| stats avg(http.server.throughput) as avg_throughput by thousandeyes.test.name, thousandeyes.source.agent.name, thousandeyes.source.agent.location
| eval avg_mbps=round(avg_throughput*8/1000000,2)
| sort thousandeyes.test.name, avg_mbps
```
If the same test shows 50 Mbps from one agent but 2 Mbps from another, the issue is the network path from the slow agent, not the server.

**Throughput trending** (detects gradual degradation or capacity constraints):
```spl
`stream_index` thousandeyes.test.type="http-server" earliest=-7d
| eval throughput_mbps=http.server.throughput*8/1000000
| timechart span=4h avg(throughput_mbps) as avg_mbps by thousandeyes.test.name
```
A declining throughput trend over weeks suggests increasing server load, network congestion, or ISP throttling.

**Throughput vs latency correlation:**
```spl
`stream_index` thousandeyes.test.type="http-server"
| stats avg(http.server.throughput) as avg_throughput avg(http.client.request.duration) as avg_ttfb avg(network.latency) as avg_net_latency by thousandeyes.test.name
| eval avg_mbps=round(avg_throughput*8/1000000,2), avg_ttfb_ms=round(avg_ttfb*1000,1), avg_net_ms=round(avg_net_latency*1000,1)
| sort avg_mbps
```
High latency + low throughput → TCP throughput limited by RTT (bandwidth-delay product). Low latency + low throughput → server-side throttling or rate limiting.

**Scheduling:** cron `0 */4 * * *`, time range `-4h to now`. Throughput is less volatile than availability — 4-hour intervals are sufficient. Alert when `avg_mbps` drops below a per-test threshold. Throttle by `thousandeyes.test.name` for 8 hours.

### Step 3 — Validate
(a) **Manual download test.** From a machine in the same network as the ThousandEyes agent, download the same URL and measure throughput:
```bash
curl -o /dev/null -w "Speed: %{speed_download} bytes/sec\n" https://target.example.com/test-file
```
Compare with the ThousandEyes-reported throughput. They should be within 30% (network conditions vary).

(b) **Cross-reference ThousandEyes UI.** Navigate to **Cloud & Enterprise Agents → Views → HTTP Server** and check the throughput tab for the same test. The UI shows throughput in kbps or Mbps — verify the Splunk data matches after unit conversion.

(c) **Response size check.** Small responses produce misleadingly low throughput. Check the response size: in ThousandEyes, look at the HTTP response content length. If it's < 10 KB, throughput values are not representative of available bandwidth.

(d) **Verify unit conversion.** Run `| stats avg(http.server.throughput) as raw | eval mbps=round(raw*8/1000000,2)` and verify the Mbps value is reasonable for the expected network bandwidth (e.g., 10–100 Mbps for corporate WAN, 100–1000 Mbps for cloud backbone).

(e) **Throughput = 0 investigation.** If any test consistently shows 0 throughput, check UC-5.9.34 first — the test may be failing. If the test passes (100% availability) but throughput is 0, the response body may be empty (HEAD request or 204 No Content response).

### Step 4 — Operationalize
**Dashboard** ("HTTP Throughput Analysis" — or add as a row to the UC-5.9.34 availability dashboard):
- Row 1 — Single value tiles: "Lowest throughput test" (name + Mbps), "Tests below 1 Mbps" (red ≥ 1), "Average throughput across all tests".
- Row 2 — Bar chart: per-test throughput (avg and p5 Mbps), sorted lowest-first. Colour-code: red < 1 Mbps, orange 1–5 Mbps, yellow 5–20 Mbps, green > 20 Mbps.
- Row 3 — Per-agent comparison for selected test (from drill-down): bar chart of throughput per agent. Reveals which agents have slow paths.
- Row 4 — Throughput timechart over 7 days: identifies degradation trends and time-of-day patterns (business-hours congestion).

**Alerting:**
- Average throughput < 1 Mbps for any test → low-urgency notification. May indicate server-side throttling, bandwidth saturation, or path congestion.
- Throughput drops > 50% week-over-week → high-urgency notification. Sudden throughput drop usually indicates an infrastructure change.

**Runbook** (owner: web operations / CDN team):
1. **Low throughput from all agents** → Server or hosting bandwidth issue. Check: (a) Server outbound bandwidth utilization (NIC saturation?). (b) Hosting provider bandwidth limits or throttling. (c) Web server configuration (rate limiting per client IP). (d) CDN configuration — if the CDN is not caching the test resource, every request hits the origin.
2. **Low throughput from specific agents** → Network path bandwidth constraint between that agent and the server. Check: (a) WAN link utilization at the agent's site. (b) ISP throttling or congestion on that specific path. (c) QoS policies that may be deprioritizing HTTP traffic.
3. **Throughput declining over weeks** → Capacity planning trigger. Either the server is handling more concurrent requests (reducing per-client throughput) or the network path is becoming more congested. Compare with UC-5.9.35 (TTFB) — if both TTFB and throughput degrade, the server is under load. If only throughput degrades but TTFB is stable, the issue is data transfer speed, not server processing.
4. **Throughput highly variable** → Shared infrastructure with competing traffic. The test measures the throughput achievable at the moment of the test — if other traffic is consuming bandwidth simultaneously, throughput drops. Consider testing during off-peak hours to establish maximum achievable throughput.

### Step 5 — Troubleshooting

- **Throughput = 0 or null for all tests** — Tests may be failing (check UC-5.9.34 availability first). Throughput is only reported for successful requests. If tests pass but throughput is still null, the metric may not be populated for your test configuration (e.g., HEAD requests don't transfer body data).

- **Very high throughput values (> 1 Gbps)** — If the test target is served from a CDN edge node that is very close to the agent (same data center or cloud region), throughput can be extremely high. This is expected and correct — it means the CDN is effectively serving the content.

- **Throughput doesn't match server NIC speed** — HTTP throughput is limited by many factors beyond NIC speed: TCP window size, RTT (latency), TLS overhead, server CPU for generating the response, and competing connections. Achieving NIC-speed throughput requires: large response, low latency, tuned TCP settings, and minimal competition.

- **Field name mismatch** — In OTel v1, the throughput field may be named differently. Check `| fieldsummary | search field=http*throughput*` to find the correct field name.

- **All common troubleshooting** — See UC-5.9.1 Step 5 for HEC connectivity, OAuth refresh, macro configuration, and role permissions.

## SPL

```spl
`stream_index` thousandeyes.test.type="http-server"
| stats avg(http.server.throughput) as avg_throughput min(http.server.throughput) as min_throughput by thousandeyes.test.name, server.address
| eval avg_mbps=round(avg_throughput*8/1000000,2), min_mbps=round(min_throughput*8/1000000,2)
| sort avg_mbps
```

## Visualization

(1) Bar chart: throughput per test (Mbps). (2) Timechart: throughput trending. (3) Table: tests sorted by throughput (lowest first). (4) Comparison: throughput by agent location.

## Known False Positives

**Small response bodies.** For tests targeting endpoints with tiny responses (health check endpoints, API status pages), throughput is meaningless because there's insufficient data to measure transfer rate. Focus on tests targeting pages with > 10 KB response bodies.

**Connection reuse.** Throughput for the first request on a new connection includes TCP and TLS setup. Subsequent requests on the same connection (keep-alive) will show higher throughput.

**Server-side rate limiting.** Application-level rate limiting may cap throughput by design. This is intentional, not a problem.

## References

- [Cisco ThousandEyes App for Splunk (Splunkbase 7719)](https://splunkbase.splunk.com/app/7719)
- [ThousandEyes OTel v2 — HTTP Server metrics](https://docs.thousandeyes.com/product-documentation/integration-guides/opentelemetry/data-model/data-model-v2/metrics)
