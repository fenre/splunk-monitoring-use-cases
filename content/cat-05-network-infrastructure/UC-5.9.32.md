<!-- AUTO-GENERATED from UC-5.9.32.json — DO NOT EDIT -->

---
id: "5.9.32"
title: "CDN Edge Network Performance"
status: "verified"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.9.32 · CDN Edge Network Performance

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance &middot; **Wave:** Run &middot; **Status:** Verified

*We check how fast our website loads from different parts of the world by testing the content delivery network (CDN) that stores copies of our pages near each user, so we can catch it when one region's copy is slow or broken.*

---

## Description

Monitors CDN edge performance from multiple geographic vantage points by running HTTP Server tests against CDN-delivered content. Measures Time to First Byte (TTFB), throughput, and availability per CDN edge node to detect CDN PoP degradation, cache misses, or origin pull delays that affect end-user experience.

## Value

CDN performance is often treated as a "set and forget" infrastructure component, but CDN edge nodes can degrade due to: capacity saturation, cache invalidation storms, origin server slowdowns, or PoP-specific issues. When a CDN edge degrades, users in that geographic region experience slow page loads — but users in other regions see normal performance, making the issue invisible to global monitoring averages. ThousandEyes' distributed Cloud Agents test from many regions simultaneously, detecting regional CDN degradation. This UC answers: "Is our CDN delivering content fast everywhere, or are specific regions underserved?"

## Implementation

Create HTTP Server tests targeting CDN-delivered URLs (static assets, API endpoints behind CDN) from multiple Cloud Agent locations. Use ThousandEyes Cloud Agents (globally distributed) for broad geographic coverage.

## Detailed Implementation

### Prerequisites
- All common prerequisites from UC-5.9.1 apply (app installed, OAuth authenticated, HEC configured, Tests Stream — Metrics input enabled).
- **HTTP Server tests configured targeting CDN-delivered URLs.** Navigate to **Cloud & Enterprise Agents → Test Settings → Add New Test → Web → HTTP Server**. Target a representative URL that is served through your CDN (e.g., a main CSS/JS bundle, a product image, or the homepage itself).
  - **Agent selection is the key differentiator for CDN monitoring.** Use Cloud Agents from as many geographic regions as possible (20+ agents across Americas, EMEA, APAC). Each agent tests from a different vantage point, so you see CDN performance as your global users experience it.
  - **Naming convention:** Use `CDN-<Provider>-<Resource>` (e.g., `CDN-Cloudflare-Homepage`, `CDN-Akamai-StaticAssets`, `CDN-AWS-CloudFront-API`). This lets SPL group by CDN provider.
  - **Test interval:** 5–10 minutes per agent. CDN providers may rate-limit or block more aggressive testing.
  - **Multiple CDN providers:** If you use different CDNs for different content (e.g., Cloudflare for web, AWS CloudFront for API, Akamai for video), create separate tests for each to compare CDN-specific performance.
- **CDN cache warmth consideration.** ThousandEyes tests keep the cache warm at CDN PoPs near each Cloud Agent. If you test every 5 minutes, the CDN PoP serving that agent will keep the resource cached. First-request cache misses will show as TTFB spikes — this is expected and useful data (it shows origin pull performance).
- **CDN vendor analytics access.** Have login access to your CDN vendor's analytics dashboard (Cloudflare Analytics, Akamai Control Center, AWS CloudFront Reports, Fastly Stats) for cross-reference during validation.
- **Splunk role:** `srchIndexesAllowed` must include `thousandeyes_metrics`.

### Step 1 — Configure data collection
CDN-targeted HTTP Server test metrics flow through the same Tests Stream — Metrics OTel input configured in UC-5.9.1. No separate input is needed.

Verify CDN test data is present:
```spl
index=thousandeyes_metrics sourcetype="cisco:thousandeyes:metric" thousandeyes.test.type="http-server" thousandeyes.test.name="*CDN*" earliest=-1h
| stats count dc(thousandeyes.source.agent.name) as agents by thousandeyes.test.name
| sort thousandeyes.test.name
```
Each CDN test should show data from many Cloud Agents (20+). Low agent count means fewer geographic vantage points.

**CDN-specific metrics to understand:**
- `http.client.request.duration` — Time to First Byte (TTFB) in SECONDS. For CDN monitoring, this is the most important metric. It includes DNS resolution + TCP connect + TLS handshake + server processing (which for a CDN cache hit is near-zero). A cache hit from a nearby CDN PoP should yield TTFB < 50 ms (0.050 s). A cache miss triggers an origin pull, increasing TTFB to 200–1000+ ms depending on origin distance.
- `http.server.throughput` — download throughput in BYTES/SECOND. For CDN content (large assets), this shows download speed. Convert to Mbps: `throughput * 8 / 1000000`.
- `http.server.request.availability` — percentage (0–100). Should be 100% for CDN-delivered content. Any drop indicates CDN misconfiguration, SSL issues, or WAF blocking.
- `http.response.status_code` — The HTTP status code. For CDN content, expect 200. Watch for 301/302 (redirects — adds latency), 403 (blocked), 429 (rate limited), or 5xx (CDN/origin errors).

### Step 2 — Create the search and alert
**CDN performance per region (primary view):**
```spl
`stream_index` thousandeyes.test.type="http-server" thousandeyes.test.name="*CDN*"
| stats avg(http.client.request.duration) as avg_ttfb avg(http.server.throughput) as avg_throughput avg(http.server.request.availability) as avg_avail by thousandeyes.source.agent.location, server.address, thousandeyes.test.name
| eval avg_ttfb_ms=round(avg_ttfb*1000,1), avg_throughput_mbps=round(avg_throughput*8/1000000,2), avg_avail_pct=round(avg_avail,2)
| sort -avg_ttfb_ms
```

**Understanding this SPL**

`by thousandeyes.source.agent.location` — splits by the geographic location of the testing agent. This is the core of CDN monitoring: you want to see how fast the CDN responds from each part of the world.

`avg(http.client.request.duration)` — TTFB averaged over the search window. For CDN monitoring, also track `p95(http.client.request.duration)` to catch intermittent cache misses or slow PoPs.

`avg(http.server.throughput)` — download speed. Low throughput from a specific region suggests CDN PoP congestion or underprovisioned edge capacity.

**Regional performance comparison (aggregated by continent):**
```spl
`stream_index` thousandeyes.test.type="http-server" thousandeyes.test.name="*CDN*" earliest=-24h
| eval region=case(match(thousandeyes.source.agent.location, "(?i)(new york|washington|dallas|los angeles|chicago|toronto|sao paulo|miami|seattle|denver)"), "Americas", match(thousandeyes.source.agent.location, "(?i)(london|frankfurt|amsterdam|paris|stockholm|dublin|oslo|madrid|zurich)"), "EMEA", match(thousandeyes.source.agent.location, "(?i)(tokyo|singapore|sydney|mumbai|hong kong|seoul|jakarta|bangkok)"), "APAC", 1=1, "Other")
| stats avg(http.client.request.duration) as avg_ttfb p95(http.client.request.duration) as p95_ttfb avg(http.server.request.availability) as avg_avail by region, thousandeyes.test.name
| eval avg_ttfb_ms=round(avg_ttfb*1000,1), p95_ttfb_ms=round(p95_ttfb*1000,1)
| sort region
```
This groups the 20+ Cloud Agents into three regions and shows average and p95 TTFB per region per CDN test. If EMEA shows 50 ms avg but APAC shows 400 ms avg, the CDN may not have PoPs close to your APAC users.

**CDN cache performance analysis (cache hit vs miss detection):**
```spl
`stream_index` thousandeyes.test.type="http-server" thousandeyes.test.name="*CDN*" earliest=-24h
| eval cache_behavior=case(http.client.request.duration < 0.1, "cache_hit", http.client.request.duration < 0.5, "cache_miss_nearby_origin", 1=1, "cache_miss_distant_origin")
| stats count by cache_behavior, thousandeyes.test.name
| eventstats sum(count) as total by thousandeyes.test.name
| eval pct=round(count/total*100,1)
| sort thousandeyes.test.name, cache_behavior
```
This classifies each measurement as a cache hit (< 100 ms) or cache miss (> 100 ms). A healthy CDN should show > 90% cache hits from recurring tests.

**CDN TTFB trending (detect degradation over time):**
```spl
`stream_index` thousandeyes.test.type="http-server" thousandeyes.test.name="*CDN*" earliest=-7d
| timechart span=4h avg(http.client.request.duration) as avg_ttfb_s p95(http.client.request.duration) as p95_ttfb_s by thousandeyes.test.name
```

**Scheduling:** cron `*/15 * * * *`, time range `-30m to now`. Alert on: TTFB > 500 ms from any region (CDN should be fast), or availability < 100%. Throttle by `thousandeyes.test.name` for 1 hour.

### Step 3 — Validate
(a) **TTFB baseline comparison.** Expected values: cache hit from nearby PoP = 10–50 ms, cache miss with nearby origin = 100–300 ms, cache miss with distant origin = 300–1000+ ms. If all measurements show > 200 ms, the CDN may not be caching your test resource.

(b) **CDN vendor analytics cross-reference.** Login to your CDN vendor's analytics dashboard. Compare cache hit ratio, bandwidth, and error rates with ThousandEyes data. ThousandEyes shows end-user perspective (outside-in); CDN vendor analytics show server-side perspective (inside-out). Discrepancies suggest measurement methodology differences.

(c) **Cache header verification.** Use `curl -I <CDN_URL>` to inspect response headers. Look for:
  - `Cache-Control: max-age=86400` (or similar) — confirms the resource is cacheable.
  - `X-Cache: HIT` (or vendor-specific header like `cf-cache-status: HIT`) — confirms the CDN served from cache.
  - `Age: 3600` — shows how long the resource has been in cache.
  If `Cache-Control: no-cache` or `no-store`, the CDN must pull from origin every time, making TTFB equivalent to origin response time.

(d) **Agent geographic coverage.** Verify Cloud Agents are in regions where your users are. Use `| stats dc(thousandeyes.source.agent.location) as locations values(thousandeyes.source.agent.location) as location_list by thousandeyes.test.name` to see agent distribution. If all agents are in US, you have no CDN performance visibility for EMEA/APAC users.

(e) **Rate limiting check.** Run `| search http.response.status_code=429 OR http.response.status_code=403 | stats count by thousandeyes.test.name, http.response.status_code`. If rate-limited, reduce test interval to 10 minutes.

### Step 4 — Operationalize
**Dashboard** ("CDN Edge Performance" — designed for web operations / CDN engineering):
- Row 1 — World map: TTFB by agent location (Splunk choropleth map or marker map). Instantly shows which regions have fast CDN response and which are slow.
- Row 2 — Regional comparison table: region | avg TTFB (ms) | p95 TTFB (ms) | availability (%) | throughput (Mbps). One row per region per CDN provider.
- Row 3 — Cache hit rate: percentage of measurements classified as cache hits (< 100 ms TTFB) per CDN test. Target > 90%.
- Row 4 — TTFB trending: 7-day timechart with avg and p95 lines per CDN test. Shows whether CDN performance is stable, improving, or degrading.

**Alerting (tiered):**
- TTFB > 500 ms from ANY region for > 15 min → low-urgency notification to `#web-ops`. May be a cache purge or CDN PoP issue.
- TTFB > 500 ms from ALL regions → high-urgency notification. Origin server may be down or CDN configuration is broken.
- Availability < 100% from any agent → medium-urgency notification. CDN is returning errors.

**Runbook** (owner: web / CDN team):
1. **High TTFB from a specific region.** (a) Check if the CDN has a PoP in that region. If not, requests route to the nearest PoP which may be far. (b) Check CDN PoP health in vendor dashboard. (c) Check if the resource was recently purged or cache TTL expired — look for a spike in origin pulls.
2. **TTFB high from everywhere.** (a) Check origin server health — if the CDN can't reach the origin, all edge PoPs will have cache misses. (b) Check if someone purged the CDN cache globally. (c) Check if the `Cache-Control` header was changed (e.g., set to `no-cache` in a recent deployment).
3. **Availability < 100%.** (a) Check `error.type` and `http.response.status_code`. (b) 403 responses often mean CDN WAF is blocking ThousandEyes agents. Whitelist agent IP ranges. (c) 5xx responses mean CDN or origin is failing. (d) SSL errors mean the CDN certificate expired or is misconfigured.
4. **One CDN provider consistently slower than another.** If you use multiple CDNs, compare them. Prepare data for CDN vendor renegotiation or migration.

### Step 5 — Troubleshooting

- **TTFB > 1 second from all agents** — CDN is not caching the tested URL. Check cache headers with `curl -I`. If `Cache-Control: no-store` or `Pragma: no-cache`, the resource is not cacheable. Choose a different URL to test, or fix the origin's cache headers.

- **HTTP 403/429 responses** — CDN's WAF or rate limiter is blocking ThousandEyes agents. Each CDN vendor has a different process: Cloudflare → Firewall Rules → allow ThousandEyes IPs. Akamai → Security Config → whitelist. CloudFront → WAF → IP set.

- **TTFB varies wildly between measurements from the same agent** — The CDN is alternating between cache hits and misses. Check `max-age` TTL on the resource. If TTL < test interval, the cache expires between tests. Also check if origin uses `Vary` header which can cause cache fragmentation.

- **Throughput shows 0 or very low values** — The tested resource may be very small (< 1 KB). Throughput measurement requires a response body of meaningful size. Test a larger resource (image, JS bundle) for accurate throughput.

- **All common troubleshooting** — See UC-5.9.34 Step 5 for HTTP test issues, and UC-5.9.1 Step 5 for general app troubleshooting.

## SPL

```spl
`stream_index` thousandeyes.test.type="http-server" thousandeyes.test.name="*CDN*"
| stats avg(http.client.request.duration) as avg_ttfb avg(http.server.throughput) as avg_throughput avg(http.server.request.availability) as avg_avail by thousandeyes.source.agent.location, server.address
| eval avg_ttfb_ms=round(avg_ttfb*1000,1), avg_throughput_mbps=round(avg_throughput*8/1000000,2)
| sort -avg_ttfb_ms
```

## Visualization

(1) Map: Cloud Agent locations colour-coded by CDN TTFB. (2) Table: per-agent CDN performance (TTFB, throughput, availability). (3) Bar chart: TTFB by region. (4) Timechart: TTFB trending over 24 hours.

## Known False Positives

**Cache misses on first request.** If the CDN edge hasn't cached the tested resource, the first request causes an origin pull — dramatically increasing TTFB. Subsequent requests will be fast. Use recurring tests (every 2–5 minutes) so the cache stays warm.

**CDN Anycast routing changes.** CDN providers dynamically route users to different PoPs. The `server.address` resolved for the test may change between rounds, making per-PoP trending difficult. Group by `thousandeyes.source.agent.location` (the agent's location is stable) rather than `server.address`.

**Rate limiting by CDN.** Aggressive test frequencies may trigger CDN rate limiting or bot protection, causing artificial availability drops or slow responses. Use moderate test intervals (5–10 minutes per agent).

## References

- [Cisco ThousandEyes App for Splunk (Splunkbase 7719)](https://splunkbase.splunk.com/app/7719)
- [ThousandEyes OTel v2 — HTTP Server metrics](https://docs.thousandeyes.com/product-documentation/integration-guides/opentelemetry/data-model/data-model-v2/metrics)
