<!-- AUTO-GENERATED from UC-5.9.37.json — DO NOT EDIT -->

---
id: "5.9.37"
title: "Page Load Completion Rate"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.9.37 · Page Load Completion Rate

> **Criticality:** High &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Availability &middot; **Wave:** Crawl &middot; **Status:** Verified

*We open our web pages in a real browser from around the world to check that everything actually loads — all the pictures, buttons, and scripts — because a page can technically 'respond' but still be broken if one of its many pieces is missing.*

---

## Description

Monitors the completion rate of Page Load tests — full browser-based page rendering tests that load a URL with all dependent resources (CSS, JavaScript, images, fonts, API calls). Unlike HTTP Server tests (which test a single HTTP request), Page Load tests simulate a real browser, detecting issues with third-party dependencies, JavaScript errors, broken resources, and complex rendering failures.

## Value

HTTP Server tests confirm the server responds, but a modern web page loads 50–200 dependent resources from multiple domains. A single broken CDN, an expired third-party JavaScript library, or a CORS misconfiguration can break the page even though the main server responds correctly. Page Load tests catch these composite failures because they use a real browser engine. A completion rate < 100% means the page is broken for real users. This is the highest-fidelity test type for web application monitoring.

## Implementation

Page Load tests require more resources than HTTP Server tests (browser engine). They're typically run at 5–10 minute intervals from fewer agents.

## Detailed Implementation

### Prerequisites
- All common prerequisites from UC-5.9.1 apply (app installed, OAuth authenticated, HEC configured, Tests Stream — Metrics input enabled).
- **Page Load tests configured in ThousandEyes.** Navigate to **Cloud & Enterprise Agents → Test Settings → Add New Test → Web → Page Load**. Key settings:
  - **URL:** The full URL of the page to test (e.g., `https://www.example.com`, `https://portal.internal.com/dashboard`). This should be a real page that loads with all its dependencies (CSS, JS, images, fonts, APIs).
  - **Agents:** Page Load tests require **Enterprise Agents** — Cloud Agents have limited page load support (no full browser rendering). Enterprise Agents must have at least 2 GB RAM and 2 vCPU allocated for the Chromium browser engine used by Page Load tests. Insufficient resources cause timeouts and false failures.
  - **Interval:** 2 minutes (default) or 5 minutes. 1-minute intervals are possible but increase agent CPU load significantly for browser-based tests.
  - **Timeout:** Default 30 seconds. For complex single-page applications (SPAs) with heavy JavaScript, consider 45–60 seconds.
- **Page Load vs HTTP Server tests — understanding the difference:** HTTP Server tests issue a single HTTP request (like `curl`) and measure TTFB. Page Load tests open a full Chromium browser, load the URL, and render ALL resources (HTML, CSS, JavaScript, images, fonts, API calls). A page with 100 resources generates 100+ HTTP requests during a Page Load test. The `web.page_load.completion` metric measures whether ALL resources loaded successfully — a single broken image or failed JavaScript file drops completion below 100%.
- **Splunk role:** `srchIndexesAllowed` must include `thousandeyes_metrics`.

### Step 1 — Configure data collection
Page Load test metrics flow through the same Tests Stream — Metrics OTel input configured in UC-5.9.1. No separate input is needed.

Verify Page Load data is present:
```spl
index=thousandeyes_metrics sourcetype="cisco:thousandeyes:metric" thousandeyes.test.type="page-load" earliest=-30m
| stats avg(web.page_load.completion) as avg_completion count by thousandeyes.test.name
```
Each test should show data with a non-null completion value. If completion is always 0%, the Enterprise Agent's browser engine may have resource issues (see Step 5).

**Understanding the metrics:**
- `web.page_load.completion` (percentage: 0 or 100) — 100% if ALL page resources loaded without errors (HTTP errors, timeouts, JavaScript errors). 0% if ANY resource failed. Unlike `http.server.request.availability` (which tests a single HTTP request), completion tests the ENTIRE page rendering including all subresources.
- `web.page_load.duration` (seconds) — total time from navigation start to page fully loaded (all resources fetched and rendered). This is the user-perceived page load time. See UC-5.9.38 for duration monitoring.
- `web.page_load.dom_load` (seconds, if available) — time to DOM Content Loaded event (HTML parsed, DOM constructed, but images/fonts may still be loading). Faster than full `duration`.
- `web.page_load.response_time` (seconds, if available) — time for the initial HTML document to be received (similar to TTFB but measured in the browser context).

### Step 2 — Create the search and alert
**Page load completion overview (flags any page with rendering failures):**
```spl
`stream_index` thousandeyes.test.type="page-load"
| stats avg(web.page_load.completion) as avg_completion min(web.page_load.completion) as min_completion by thousandeyes.test.name, server.address, thousandeyes.source.agent.name
| where avg_completion < 100
| sort avg_completion
```

**Understanding this SPL**

`thousandeyes.test.type="page-load"` — filters to Page Load tests only. HTTP Server tests (`http-server`) test a single request; Page Load tests test the full browser rendering.

`avg(web.page_load.completion)` — average completion over the search window. 100% means every test round rendered the page completely. Values < 100% indicate rendering failures (broken resources, JavaScript errors, timeouts).

`min(web.page_load.completion)` — worst single reading. If `min_completion` is 0% but `avg_completion` is 90%, the page fails intermittently (perhaps a third-party resource that's flaky).

`where avg_completion < 100` — ANY page rendering failure is significant. A page that fails to load completely is broken for users, even if the HTTP Server test (UC-5.9.34) shows 100% availability. This is because the HTTP Server test only checks the initial HTML response, not the 100+ subresources the page needs.

**Aggregate completion per page (fleet view):**
```spl
`stream_index` thousandeyes.test.type="page-load" earliest=-24h
| stats avg(web.page_load.completion) as avg_completion dc(thousandeyes.source.agent.name) as agents by thousandeyes.test.name
| sort avg_completion
```

**Completion timeline:**
```spl
`stream_index` thousandeyes.test.type="page-load" earliest=-24h
| timechart span=15m avg(web.page_load.completion) by thousandeyes.test.name
```

**Scheduling:** cron `*/10 * * * *`, time range `-15m to now`. Alert when `avg_completion < 100`. Throttle by `thousandeyes.test.name` for 2 hours.

### Step 3 — Validate
(a) **Manual browser test with DevTools.** Open the test URL in Chrome/Edge. Press F12 to open DevTools. Check: (i) Console tab for JavaScript errors (red errors cause completion failures). (ii) Network tab for failed resource requests (red entries). (iii) Performance tab → record a page load and check the waterfall. Compare with ThousandEyes completion status.

(b) **Cross-reference ThousandEyes UI.** Navigate to **Cloud & Enterprise Agents → Views → Page Load** and select the test. The UI shows a waterfall diagram of all page resources with status codes and timing. A red resource in the waterfall caused the completion failure.

(c) **Compare Page Load vs HTTP Server.** Run both UC-5.9.34 (HTTP availability) and this UC for the same URL. If HTTP Server shows 100% availability but Page Load shows < 100% completion, the HTML response is fine but a subresource is broken. The ThousandEyes waterfall identifies which resource.

(d) **Agent resource check.** If completion is 0% from specific agents, check the agent's resource allocation. Page Load tests require significantly more CPU and RAM than network tests. An agent running 10+ Page Load tests simultaneously may exhaust resources.

(e) **Third-party resource check.** Modern web pages load resources from multiple domains (CDNs, analytics, ad networks, fonts). If completion fails because a third-party resource is unavailable, the page completion drops even though YOUR infrastructure is fine. Identify the failing domain in the ThousandEyes waterfall.

### Step 4 — Operationalize
**Dashboard** ("Page Load Health" — designed for web platform team):
- Row 1 — Single value tiles: "Pages 100% complete" (green), "Pages with failures" (red ≥ 1), "Overall page completion %" (green ≥ 99%, yellow ≥ 95%, red < 95%).
- Row 2 — Completion timechart over 24 hours at 15-minute granularity. Each line is a page. Dips below 100% indicate periods when the page was partially broken.
- Row 3 — Detail table: page name | server | agent | avg completion | min completion — sorted worst-first. Drilldown to ThousandEyes permalink for waterfall analysis.
- Row 4 — Agent comparison: for a selected page, show completion per agent. Reveals if the issue is regional (CDN edge problem) or global (origin server problem).

**Alerting:**
- Completion < 100% from ANY agent for a production page → low-urgency Slack notification. Page may have a broken subresource.
- Completion < 100% from ALL agents → high-urgency page (PagerDuty). The page is universally broken.
- Completion 0% from ALL agents → critical incident. Full page failure.

**Runbook** (owner: web platform / frontend team):
1. **Completion < 100% from all agents.** A resource the page depends on is broken or unreachable. Open the ThousandEyes waterfall (via permalink) to identify the failing resource. Common causes: (a) CDN misconfiguration (asset moved or deleted). (b) API endpoint returning 500 errors. (c) Third-party script blocked or down. (d) JavaScript runtime error preventing subsequent resource loading.
2. **Completion < 100% from specific agents.** Regional issue. Common causes: (a) CDN edge node for that region serving stale or broken content. (b) Regional DNS resolving to a different backend. (c) Geo-specific content rules serving different assets to different regions.
3. **Intermittent failures (avg 80–99%).** A flaky resource that fails sometimes. Common causes: (a) Third-party analytics or ad scripts with availability issues. (b) Race condition in JavaScript loading order. (c) Resource served with aggressive caching that intermittently expires.
4. **Completion was 100% yesterday, now 0%.** Likely a deployment broke something. Check: (a) Recent code deployments. (b) CDN configuration changes. (c) DNS changes. (d) Certificate renewals that may have broken a subdomain.

### Step 5 — Troubleshooting

- **All Page Load tests show 0% completion** — Enterprise Agent browser engine issue. Check: (a) Agent has at least 2 GB RAM and 2 vCPU allocated. (b) The BrowserBot component is running on the agent (`te-browserbot` process). (c) The agent can reach the test URL (check for proxy or DNS issues on the agent host).

- **Completion is always 100% even when the page is visually broken** — The `web.page_load.completion` metric measures HTTP-level resource loading success, not visual correctness. A page can load all resources successfully but display incorrectly due to CSS bugs or JavaScript rendering issues. For visual validation, use Transaction tests with screenshot assertions (UC-5.9.41).

- **Completion drops only during maintenance windows** — The test is detecting real failures during deployments. Either exclude maintenance windows (add a time filter) or implement zero-downtime deployments.

- **One specific agent always fails** — The agent may have connectivity issues to a specific CDN or third-party domain. Check DNS resolution from the agent host for the failing resource domain. If the agent is behind a proxy, the proxy may be blocking certain resources.

- **`web.page_load.completion` field missing** — Check `thousandeyes.data.version`. In OTel v1, the field name may differ. Run `| fieldsummary | search field=web*` to identify available field names.

- **All common troubleshooting** — See UC-5.9.1 Step 5 for HEC connectivity, OAuth refresh, macro configuration, and role permissions.

## SPL

```spl
`stream_index` thousandeyes.test.type="page-load"
| stats avg(web.page_load.completion) as avg_completion min(web.page_load.completion) as min_completion by thousandeyes.test.name, server.address, thousandeyes.source.agent.name
| where avg_completion < 100
| sort avg_completion
```

## Visualization

(1) Single value: average page load completion. (2) Table: pages with < 100% completion, showing agent and error. (3) Timechart: completion rate trending. (4) Drilldown: link to ThousandEyes waterfall view for failed tests.

## Known False Positives

**Third-party resource failures.** Analytics scripts, ad networks, or social media widgets failing cause page load completion to drop even though the application itself works. Check the ThousandEyes waterfall view to identify which resource failed.

**Content gating (CAPTCHA, login).** If the page requires authentication or presents a CAPTCHA, the browser-based test may not be able to proceed, showing 0% completion. Configure the test with appropriate credentials or exclude gated pages.

**Browser rendering timeouts.** Complex pages with heavy JavaScript may exceed the test timeout (default 30 seconds). Increase the timeout in the test configuration if needed.

## References

- [Cisco ThousandEyes App for Splunk (Splunkbase 7719)](https://splunkbase.splunk.com/app/7719)
- [ThousandEyes OTel v2 — Page Load metrics](https://docs.thousandeyes.com/product-documentation/integration-guides/opentelemetry/data-model/data-model-v2/metrics)
