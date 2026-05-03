<!-- AUTO-GENERATED from UC-5.9.38.json — DO NOT EDIT -->

---
id: "5.9.38"
title: "Page Load Duration Trending"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.9.38 · Page Load Duration Trending

> **Criticality:** High &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Performance &middot; **Wave:** Walk &middot; **Status:** Verified

*We time how long it takes our web pages to fully appear in a browser, because people leave if a page takes more than a few seconds to load.*

---

## Description

Tracks full page load duration for Page Load tests — the total time from navigation start to the page being fully rendered with all dependent resources. Flags pages where average load time exceeds 5 seconds. This metric captures the complete user experience, including DNS, network, server processing, content download, and browser rendering.

## Value

Google research shows that as page load time increases from 1 to 3 seconds, bounce probability increases 32%. From 1 to 5 seconds, it increases 90%. Page load duration directly impacts user retention, conversion rates, and SEO rankings. By trending this metric over time, teams detect performance regressions from deployments (new JavaScript library adding 2 seconds), infrastructure changes (CDN misconfiguration), and external dependency degradation (slow analytics script). The p95 percentile is especially important — it reveals the worst 5% of user experiences that averages mask.

## Implementation

Same Page Load tests as UC-5.9.37. Duration is measured alongside completion rate.

## Detailed Implementation

### Prerequisites
- All prerequisites from UC-5.9.37 apply — Page Load tests must be configured in ThousandEyes on Enterprise Agents with browser capability, and the Tests Stream — Metrics input must be delivering data.
- **Page Load tests must be completing successfully.** `web.page_load.duration` is only emitted for test rounds where the page loaded successfully (100% completion in UC-5.9.37). If tests are failing, fix completion first.
- **Performance budgets established.** Define target page load times per page type: landing pages < 3 seconds, interactive dashboards < 5 seconds, data-heavy reports < 10 seconds. Google's Core Web Vitals recommends Largest Contentful Paint (LCP) < 2.5 seconds for a good user experience. ThousandEyes `web.page_load.duration` is closest to the total load time (not exactly LCP, but a related measurement).
- **Splunk role:** `srchIndexesAllowed` must include `thousandeyes_metrics`.

### Step 1 — Configure data collection
Page Load test metrics (including duration) flow through the same Tests Stream — Metrics OTel input configured in UC-5.9.1. No separate input is needed.

Verify duration data is present:
```spl
index=thousandeyes_metrics sourcetype="cisco:thousandeyes:metric" thousandeyes.test.type="page-load" earliest=-30m
| stats avg(web.page_load.duration) as avg_dur count by thousandeyes.test.name
| where isnotnull(avg_dur)
```
Each test should show a non-null duration. If duration is null but completion is populated, the tests are failing — duration is only reported for successful completions.

**Understanding the metric:**
- `web.page_load.duration` (seconds) — total time from navigation start to page fully rendered (the browser's `load` event fires). This includes: DNS resolution, TCP/TLS connection, HTML download, parsing, CSS download/parsing, JavaScript download/execution, image download/rendering, and any asynchronous API calls that complete before the `load` event. It is the user-perceived "time until the page is done loading."
- Units: **seconds**. A value of `3.5` means 3.5 seconds total page load time. Unlike `http.client.request.duration` (which measures TTFB for a single request), this measures the entire browser rendering pipeline.
- Duration is typically much larger than TTFB because modern pages make dozens to hundreds of subresource requests after the initial HTML is received. A page with 200 ms TTFB might have a 5-second total page load if it loads 100+ resources.

### Step 2 — Create the search and alert
**Page load duration overview (flags slow pages):**
```spl
`stream_index` thousandeyes.test.type="page-load"
| stats avg(web.page_load.duration) as avg_load p50(web.page_load.duration) as p50_load p95(web.page_load.duration) as p95_load max(web.page_load.duration) as max_load by thousandeyes.test.name, server.address
| eval avg_s=round(avg_load,2), p50_s=round(p50_load,2), p95_s=round(p95_load,2), max_s=round(max_load,2)
| where avg_s > 5
| sort -avg_s
```

**Understanding this SPL**

`avg(web.page_load.duration)` — average page load time across all agents and test rounds. Represents typical user experience.

`p50` vs `p95` — the median (p50) and 95th percentile. If `p50` is 3 seconds but `p95` is 12 seconds, most users have a fast experience but 5% of users wait 12+ seconds. This long tail may be caused by slow CDN edges, cold caches, or agents hitting a slow backend instance.

`where avg_s > 5` — 5 seconds is a conservative threshold. Google research shows 53% of mobile users abandon pages taking > 3 seconds. For critical pages, set threshold to 3 seconds. For internal tools, 8 seconds may be acceptable.

**Per-agent comparison (identifies regional performance differences):**
```spl
`stream_index` thousandeyes.test.type="page-load"
| stats avg(web.page_load.duration) as avg_load_s by thousandeyes.test.name, thousandeyes.source.agent.name, thousandeyes.source.agent.location
| eval avg_load_s=round(avg_load_s,2)
| sort thousandeyes.test.name, -avg_load_s
```
If the same page loads in 2 seconds from US agents but 8 seconds from EU agents, the CDN isn't serving cached content from the EU edge, or there's no EU edge node at all.

**Regression detection (week-over-week comparison):**
```spl
`stream_index` thousandeyes.test.type="page-load" earliest=-14d
| eval week=if(_time > relative_time(now(), "-7d"), "This Week", "Last Week")
| stats avg(web.page_load.duration) as avg_load by thousandeyes.test.name, week
| xyseries thousandeyes.test.name week avg_load
| fillnull value=0 "Last Week" "This Week"
| where 'Last Week' > 0
| eval regression_pct=round(('This Week' - 'Last Week') / 'Last Week' * 100, 1)
| where regression_pct > 20
| sort -regression_pct
```
A >20% increase week-over-week strongly suggests a performance regression — typically from a code deployment adding JavaScript, larger images, or additional API calls.

**Duration trending over time:**
```spl
`stream_index` thousandeyes.test.type="page-load" earliest=-30d
| timechart span=1d avg(web.page_load.duration) as avg_load by thousandeyes.test.name
```
A gradually increasing trend over weeks indicates page bloat — more resources being added over time.

**Scheduling:** cron `*/15 * * * *`, time range `-30m to now`. Alert when `avg_s` exceeds the per-page performance budget. Throttle by `thousandeyes.test.name` for 2 hours.

### Step 3 — Validate
(a) **Browser DevTools comparison.** Open the test URL in Chrome. Press F12 → Performance tab → Record → Reload. Note the total load time in the Performance summary. Compare with the ThousandEyes-reported duration. They should be within 30% (different network location, different browser configuration).

(b) **Cross-reference ThousandEyes UI.** Navigate to **Cloud & Enterprise Agents → Views → Page Load** and check the waterfall for the test. The UI shows total page load time and per-resource timing. The total should match what Splunk reports.

(c) **Duration vs TTFB comparison.** Run both UC-5.9.35 (TTFB) and this UC for the same page. If TTFB is 200 ms but total load is 8 seconds, the page is spending 7.8 seconds loading subresources. The bottleneck is page complexity (too many resources, large JavaScript bundles, unoptimized images), not server response time.

(d) **Duration vs completion correlation.** Duration should only be reported for rounds with 100% completion. Verify: `| stats avg(web.page_load.duration) as dur avg(web.page_load.completion) as comp`. Duration should correlate with completion = 100.

(e) **Redirect chain check.** If duration seems too high, check for redirect chains. A URL that redirects through 3 intermediate URLs adds 3× the connection setup time. Check in ThousandEyes waterfall for 301/302 responses.

### Step 4 — Operationalize
**Dashboard** ("Page Load Performance" — designed for web platform team):
- Row 1 — Single value tiles: "Pages exceeding 5s budget" (red ≥ 1), "Slowest page" (name + duration), "Average page load across all pages" (green < 3s, yellow 3–5s, red > 5s).
- Row 2 — Bar chart: per-page load time (avg and p95), sorted slowest-first. Reference line at 5-second threshold. Colour-code: green < 3s, yellow 3–5s, red > 5s.
- Row 3 — Per-agent comparison for selected page: bar chart showing load time per agent/location. Reveals CDN and regional performance differences.
- Row 4 — Duration trend over 30 days: line chart with per-day average. Add deployment marker annotations. This reveals gradual page bloat and deployment-related regressions.

**Alerting:**
- Average page load > performance budget → low-urgency notification to `#web-performance` (Slack/Teams). Include page name, current load time, and budget.
- WoW regression > 25% → high-urgency email to engineering lead. Likely deployment regression.
- Average page load > 10 seconds → high-urgency page. Effectively broken for users.

**Runbook** (owner: web platform / frontend engineering team):
1. **Load time increased after deployment.** Review deployment changes: (a) New JavaScript bundles (check bundle sizes). (b) Larger images (check image optimization). (c) Additional API calls (check API response times). (d) New third-party scripts (analytics, chat widgets, ad trackers).
2. **Load time high from specific regions.** CDN issue: (a) Check CDN cache hit rates for those regions. (b) Verify CDN PoP exists in that region. (c) Check DNS Anycast routing — agents may be routed to a distant CDN edge.
3. **p95 >> avg (long tail).** Inconsistent performance: (a) Some agents hitting cold CDN cache. (b) Load balancer routing to a slow backend instance. (c) Time-of-day effect (business hours congestion). (d) Intermittent third-party resource slowness.
4. **Duration gradually increasing over weeks.** Page bloat: (a) Audit page resources (Lighthouse audit). (b) Implement lazy loading for below-the-fold images. (c) Code-split JavaScript bundles. (d) Remove unused CSS. (e) Evaluate and remove low-value third-party scripts.
5. **Duration stable but TTFB increasing (UC-5.9.35).** Server-side issue — backend is getting slower. Investigate database queries, API response times, and server-side rendering performance.

### Step 5 — Troubleshooting

- **Duration values seem unrealistically high (> 60 seconds)** — Check for redirect chains. If the URL redirects through multiple intermediate URLs, each redirect adds connection setup time. Also check the test timeout setting — if set to 180 seconds, a very slow page may take the full timeout before completing.

- **Duration = null for all tests** — Tests are failing (0% completion). Fix UC-5.9.37 first. Duration is only reported for successful page loads.

- **Duration very different from manual browser test** — The Enterprise Agent's browser configuration may differ from yours: different screen resolution (affects responsive layouts), different network location, different DNS resolver, or resource constraints on the agent VM causing slower rendering.

- **Regression detection shows spurious results** — If tests were added or removed between weeks, the comparison is invalid. Filter to tests that existed in both weeks: `| where isnotnull('Last Week') AND isnotnull('This Week')`.

- **All common troubleshooting** — See UC-5.9.1 Step 5 for HEC connectivity, OAuth refresh, macro configuration, v1/v2 field name differences, and role permissions.

## SPL

```spl
`stream_index` thousandeyes.test.type="page-load"
| stats avg(web.page_load.duration) as avg_load p95(web.page_load.duration) as p95_load by thousandeyes.test.name, server.address
| eval avg_load_s=round(avg_load,2), p95_load_s=round(p95_load,2)
| where avg_load_s > 5
| sort -avg_load_s
```

## Visualization

(1) Table: pages sorted by load time. (2) Timechart: load duration trending per page. (3) Percentile chart: p50, p95, p99 distribution. (4) Bar chart: load time by agent location.

## Known False Positives

**Heavy pages by design.** Some pages (dashboards, data-heavy reports) are inherently slow to load. Establish page-specific baselines rather than using a universal threshold.

**Page load duration not reported on failure.** If `web.page_load.completion` = 0%, `web.page_load.duration` may not be reported (the page didn't finish loading). Check completion first.

**Browser caching disabled in tests.** ThousandEyes Page Load tests typically clear cache between rounds, meaning every test is a cold-cache load. Real users with browser cache enabled will see faster load times.

## References

- [Cisco ThousandEyes App for Splunk (Splunkbase 7719)](https://splunkbase.splunk.com/app/7719)
- [ThousandEyes OTel v2 — Page Load metrics](https://docs.thousandeyes.com/product-documentation/integration-guides/opentelemetry/data-model/data-model-v2/metrics)
