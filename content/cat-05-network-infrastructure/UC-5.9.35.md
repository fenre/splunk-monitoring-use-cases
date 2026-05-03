<!-- AUTO-GENERATED from UC-5.9.35.json — DO NOT EDIT -->

---
id: "5.9.35"
title: "HTTP Server Response Time Tracking"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.9.35 · HTTP Server Response Time Tracking

> **Criticality:** High &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Performance &middot; **Wave:** Walk &middot; **Status:** Verified

*We measure how quickly our website starts responding to requests from different parts of the world, because if it takes too long to get the first reply, users see a blank page and think our site is broken.*

---

## Description

Tracks HTTP Server response time (TTFB) across all HTTP Server tests, flagging endpoints where average response time exceeds 500 ms. TTFB includes DNS resolution, TCP connection, TLS handshake, and server processing time — providing a comprehensive measure of application responsiveness from the network perspective.

## Value

TTFB is the single best indicator of user-perceived web application speed. While full page load involves many additional steps (rendering, JavaScript, images), TTFB represents the irreducible minimum latency before the browser can start processing. A TTFB > 500 ms means the user sees a blank page for at least half a second — and modern users expect response within 200 ms. By tracking TTFB from multiple agents, this UC detects slow application responses, slow TLS handshakes, slow DNS resolution, and geographic performance disparities before users complain.

## Implementation

Same HTTP Server tests as UC-5.9.34. TTFB is automatically measured alongside availability.

## Detailed Implementation

### Prerequisites
- All common prerequisites from UC-5.9.1 apply (app installed, OAuth authenticated, HEC configured, Tests Stream — Metrics input enabled).
- **HTTP Server tests configured in ThousandEyes.** Navigate to **Cloud & Enterprise Agents → Test Settings → Add New Test → Web → HTTP Server**. Target the specific URL that users hit (e.g., `https://app.example.com/login`, not just the domain root). The root may return a 301 redirect, which adds latency that doesn't reflect application performance.
  - **HTTP version matters.** By default, ThousandEyes uses HTTP/1.1. If your application uses HTTP/2 or HTTP/3, you'll see different performance characteristics than real users. Note this when comparing.
  - **Follow redirects:** Enable this setting unless you specifically want to measure the redirect itself. A 301/302 response without following adds the redirect latency to TTFB.
  - **SSL verification:** Leave enabled for production tests. If TTFB includes certificate chain validation delays, this is what your users experience.
- **TTFB baselines per application.** TTFB = DNS lookup + TCP connect + TLS handshake + server processing time. For a well-tuned web application:
  - Static content / CDN: 20–80 ms TTFB.
  - Dynamic web application (server-rendered): 100–400 ms TTFB.
  - API endpoint with database queries: 200–800 ms TTFB.
  - Heavy server-side processing: 500+ ms TTFB (consider caching or async processing).
- **Complementary Agent-to-Server test.** Create an Agent-to-Server test to the same `server.address` (from UC-5.9.1). This isolates network latency from server processing time: `TTFB = network_RTT + server_processing + TLS_overhead`. If Agent-to-Server latency is 50 ms and TTFB is 500 ms, the server is spending ~450 ms processing.
- **Splunk role:** `srchIndexesAllowed` must include `thousandeyes_metrics`.

### Step 1 — Configure data collection
HTTP Server test metrics flow through the same Tests Stream — Metrics OTel input configured in UC-5.9.1. No separate input is needed.

Verify HTTP Server TTFB data is present:
```spl
index=thousandeyes_metrics sourcetype="cisco:thousandeyes:metric" thousandeyes.test.type="http-server" earliest=-1h
| stats count avg(http.client.request.duration) as avg_ttfb by thousandeyes.test.name
| eval avg_ttfb_ms=round(avg_ttfb*1000,1)
| sort thousandeyes.test.name
```
Each test should show data. The `avg_ttfb_ms` gives you a quick health check on TTFB.

**Understanding `http.client.request.duration` (TTFB):**
This is the primary metric for this UC. In the OTel v2 data model, it measures the time from when the agent sends the HTTP request to when it receives the first byte of the response. Units: SECONDS. Critical details:
- This is NOT total page load time (that's `web.page_load.duration` from Page Load tests).
- This IS the server's response speed as perceived from the agent's location.
- It includes: DNS resolution + TCP connection + TLS handshake + server processing.
- It does NOT include: content download time or DOM rendering.
- The metric name `http.client.request.duration` follows OTel HTTP semantic conventions. In ThousandEyes v1 API, this was called `responseTime`.

### Step 2 — Create the search and alert
**TTFB overview — identify slow endpoints:**
```spl
`stream_index` thousandeyes.test.type="http-server"
| stats avg(http.client.request.duration) as avg_ttfb p50(http.client.request.duration) as p50_ttfb p95(http.client.request.duration) as p95_ttfb max(http.client.request.duration) as max_ttfb by thousandeyes.test.name, server.address
| eval avg_ms=round(avg_ttfb*1000,1), p50_ms=round(p50_ttfb*1000,1), p95_ms=round(p95_ttfb*1000,1), max_ms=round(max_ttfb*1000,1)
| where avg_ms > 500
| sort -avg_ms
```

**Understanding this SPL**

`avg(http.client.request.duration)` — average TTFB across all agents and time windows. This smooths out outliers but may hide tail latency.

`p50` — median TTFB. What the typical user experiences.

`p95` — 95th percentile TTFB. What the slowest 5% of users experience. If p95 >> avg, some requests are significantly slower (possibly due to cold starts, database contention, or GC pauses).

`where avg_ms > 500` — filters to endpoints with > 500 ms average TTFB. Adjust this threshold based on your SLA. Many organizations use 200 ms as a target for TTFB.

**Per-agent geographic breakdown (isolate network vs server):**
```spl
`stream_index` thousandeyes.test.type="http-server" thousandeyes.test.name="<specific-test-name>" earliest=-24h
| stats avg(http.client.request.duration) as avg_ttfb p95(http.client.request.duration) as p95_ttfb by thousandeyes.source.agent.name, thousandeyes.source.agent.location
| eval avg_ms=round(avg_ttfb*1000,1), p95_ms=round(p95_ttfb*1000,1)
| sort -avg_ms
```
If TTFB is high from ALL agents equally → server-side issue (slow application, database, or backend).
If TTFB is high from SOME agents → network path issue or geographic distance. Check Agent-to-Server latency (UC-5.9.1) to isolate.

**TTFB decomposition (separate network from server processing):**
```spl
`stream_index` thousandeyes.test.type="http-server" thousandeyes.test.name="<specific-test-name>" earliest=-24h
| stats avg(http.client.request.duration) as avg_ttfb avg(http.client.request.dns.duration) as avg_dns avg(http.client.request.connect.duration) as avg_connect avg(http.client.request.ssl.duration) as avg_ssl avg(http.client.request.wait.duration) as avg_wait by thousandeyes.source.agent.name
| eval ttfb_ms=round(avg_ttfb*1000,1), dns_ms=round(avg_dns*1000,1), connect_ms=round(avg_connect*1000,1), ssl_ms=round(avg_ssl*1000,1), wait_ms=round(avg_wait*1000,1)
| eval server_time_ms=round(ttfb_ms - dns_ms - connect_ms - ssl_ms, 1)
| table thousandeyes.source.agent.name, ttfb_ms, dns_ms, connect_ms, ssl_ms, wait_ms, server_time_ms
| sort -ttfb_ms
```
Note: Not all sub-metrics (`dns.duration`, `connect.duration`, `ssl.duration`, `wait.duration`) may be available depending on ThousandEyes configuration and data model version. If these fields are present, this decomposition shows exactly WHERE time is spent. If `server_time_ms` is the dominant component, the application is slow. If `dns_ms` is high, use UC-5.9.5/5.9.6 to investigate DNS.

**TTFB trending over time (detect regressions):**
```spl
`stream_index` thousandeyes.test.type="http-server" earliest=-7d
| timechart span=1h avg(http.client.request.duration) as avg_ttfb_s p95(http.client.request.duration) as p95_ttfb_s by thousandeyes.test.name
```
Look for step changes that correlate with deployments, infrastructure changes, or traffic pattern shifts.

**Week-over-week regression detection:**
```spl
`stream_index` thousandeyes.test.type="http-server" earliest=-14d
| eval week=if(_time > relative_time(now(), "-7d"), "this_week", "last_week")
| stats avg(http.client.request.duration) as avg_ttfb by thousandeyes.test.name, week
| eval avg_ms=round(avg_ttfb*1000,1)
| xyseries thousandeyes.test.name week avg_ms
| eval regression_ms=round(this_week - last_week, 1)
| eval regression_pct=round((this_week - last_week)/last_week*100, 1)
| where regression_pct > 20
| sort -regression_pct
```

**Scheduling:** cron `*/15 * * * *`, time range `-30m to now`. Alert on avg TTFB > SLA threshold (e.g., 500 ms). Throttle by `thousandeyes.test.name` for 1 hour.

### Step 3 — Validate
(a) **Manual `curl` comparison.** From a machine with network access to the target:
```
curl -w "DNS: %{time_namelookup}s\nConnect: %{time_connect}s\nTLS: %{time_appconnect}s\nTTFB: %{time_starttransfer}s\nTotal: %{time_total}s\n" -o /dev/null -s https://app.example.com/
```
The `time_starttransfer` value should be comparable to ThousandEyes `http.client.request.duration` from a nearby agent. Differences of 10–30 ms are normal due to measurement methodology.

(b) **TTFB vs network latency comparison.** If Agent-to-Server latency (UC-5.9.1) to the same target is 50 ms and TTFB is 500 ms, the server is spending ~450 ms processing. If TTFB ≈ network RTT + 10 ms, the server is fast and TTFB is dominated by network distance.

(c) **TLS handshake contribution.** A full TLS 1.2 handshake adds 2× RTT. TLS 1.3 adds 1× RTT. If the agent is 100 ms away, TLS adds 100–200 ms to TTFB. This is expected, not a problem.

(d) **HTTP redirect impact.** If the target URL returns 301/302 and the test follows redirects, TTFB includes the redirect round-trip. Check `http.response.status_code` — if you see 301s, test the final URL directly.

(e) **Unit verification.** Confirm units are seconds. `avg_ttfb` of `0.250` = 250 ms. If values are 250.0, you may be looking at raw milliseconds (OTel v1 legacy).

### Step 4 — Operationalize
**Dashboard** ("HTTP Response Time (TTFB)" — designed for application / SRE teams):
- Row 1 — TTFB scoreboard: one tile per HTTP test showing avg TTFB in ms, colour-coded (green < 200 ms, yellow 200–500 ms, red > 500 ms).
- Row 2 — Per-agent breakdown: for a selected test (dropdown token), show TTFB per agent location. Identifies geographic hotspots.
- Row 3 — TTFB trending: 7-day timechart with avg and p95 lines. Shows whether TTFB is stable, trending up (regression), or improving.
- Row 4 — TTFB decomposition (if sub-metrics available): stacked bar showing DNS + Connect + TLS + Server processing per agent.

**Alerting (tiered):**
- Avg TTFB > SLA threshold from any agent → low-urgency notification. Include test name, agent, TTFB value.
- Avg TTFB > 2× baseline from all agents → high-urgency notification. Server-side regression.
- p95 TTFB > 3 seconds → medium-urgency. Tail latency severely impacts user experience.

**Runbook** (owner: application / SRE team):
1. **High TTFB from ALL agents (server-side issue).** (a) Check application logs for slow queries, exceptions, or GC pauses. (b) Check server CPU and memory utilization. (c) Check database query performance — a slow query in the request path directly increases TTFB. (d) Check if a recent deployment introduced a regression — correlate TTFB increase with deployment timestamps.
2. **High TTFB from SPECIFIC agents (network/geography issue).** (a) Check Agent-to-Server latency from those agents — if network latency is high, TTFB will be high. (b) Check DNS resolution from those agents (UC-5.9.5) — DNS issues add directly to TTFB. (c) For distant agents, consider CDN or geographic load balancing.
3. **Sudden TTFB increase (step change).** (a) Correlate with deployment events, infrastructure changes, or certificate renewals. (b) A new TLS certificate with a longer chain adds handshake time. (c) A load balancer or WAF change can add processing time.
4. **Gradual TTFB increase over weeks.** (a) Application may be leaking resources (memory, connections). (b) Database growth may be slowing queries. (c) Traffic growth may be exceeding server capacity.
5. **p95 >> avg (tail latency problem).** (a) Some requests hit cold caches, uncompiled code paths (JIT), or garbage collection pauses. (b) Connection pool exhaustion causes queuing. (c) Backend service dependencies may have variable response times.

### Step 5 — Troubleshooting

- **TTFB values seem too high (> 5 seconds)** — Check if the server is returning an error page slowly, or if the test is timing out. Look at `http.response.status_code` — a 500 error that takes 5 seconds may indicate a database timeout.

- **TTFB is null or missing** — The test may be failing entirely (connection refused, DNS failure). Check `http.server.request.availability` — if it's 0%, the server is unreachable. See UC-5.9.34 for availability troubleshooting.

- **TTFB differs significantly from manual `curl`** — ThousandEyes agents are in data centers with different network paths than your local machine. Compare with an agent that is geographically close to you. Also check if your local request benefits from connection reuse (keep-alive) while ThousandEyes starts fresh connections.

- **Week-over-week regression shows increase but no deployment occurred** — Check if traffic increased (more load → slower response), if a backend dependency degraded, or if DNS resolution changed to route to a more distant server.

- **All common troubleshooting** — See UC-5.9.34 Step 5 for HTTP test issues, and UC-5.9.1 Step 5 for general app troubleshooting.

## SPL

```spl
`stream_index` thousandeyes.test.type="http-server"
| stats avg(http.client.request.duration) as avg_ttfb p95(http.client.request.duration) as p95_ttfb max(http.client.request.duration) as max_ttfb by thousandeyes.test.name, server.address
| eval avg_ttfb_ms=round(avg_ttfb*1000,1), p95_ttfb_ms=round(p95_ttfb*1000,1), max_ttfb_ms=round(max_ttfb*1000,1)
| where avg_ttfb_ms > 500
| sort -avg_ttfb_ms
```

## Visualization

(1) Table: tests sorted by TTFB (worst first). (2) Timechart: TTFB trending per test. (3) Bar chart: TTFB by agent location (geographic comparison). (4) Histogram: TTFB distribution with percentiles.

## Known False Positives

**Cold start / first request.** The first request to an application after idle may be slow due to connection pool initialization, JIT compilation, or cache warming. Subsequent requests will be faster.

**Geographic latency.** An agent in Asia testing a server in Europe will inherently have higher TTFB due to network round-trip time. Compare agents in the same region for fair application performance assessment.

**TLS handshake overhead.** HTTPS requests include TLS negotiation, adding 50–150 ms depending on cipher suite and protocol version. This is expected and not a server-side issue.

## References

- [Cisco ThousandEyes App for Splunk (Splunkbase 7719)](https://splunkbase.splunk.com/app/7719)
- [ThousandEyes OTel v2 — HTTP metrics](https://docs.thousandeyes.com/product-documentation/integration-guides/opentelemetry/data-model/data-model-v2/metrics)
