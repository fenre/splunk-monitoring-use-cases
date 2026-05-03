<!-- AUTO-GENERATED from UC-5.9.42.json — DO NOT EDIT -->

---
id: "5.9.42"
title: "Transaction Duration Analysis"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.9.42 · Transaction Duration Analysis

> **Criticality:** High &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Performance &middot; **Wave:** Walk &middot; **Status:** Verified

*We time how long the whole process takes — from clicking 'log in' to finishing a task — because each extra second of waiting means frustrated employees and customers.*

---

## Description

Tracks the total duration of Transaction test workflows — the end-to-end time for a complete user journey (login through task completion). Flags transactions exceeding 10 seconds. Duration is only reported for successful transactions, so this UC focuses on performance of working workflows.

## Value

Transaction duration measures the user's total wait time for a complete workflow. A login workflow taking 15 seconds means users wait 15 seconds before they can start working. For e-commerce, a checkout workflow taking 30 seconds means lost sales. Trending transaction duration over time detects gradual degradation (database growing, more JavaScript, heavier pages) that users notice but individual test metrics might not flag because each component is within threshold.

## Implementation

Same Transaction tests as UC-5.9.41. Duration is measured alongside completion.

## Detailed Implementation

### Prerequisites
- All prerequisites from UC-5.9.41 apply — Transaction tests must be configured in ThousandEyes with Selenium scripts, running on Enterprise Agents with browser capability, and the Tests Stream — Metrics input must be delivering data to `thousandeyes_metrics`.
- **Transaction tests must be completing successfully.** `web.transaction.duration` is only emitted when the transaction completes (100% completion in UC-5.9.41). If tests are failing, fix completion first — duration data will appear once tests pass.
- **Markers defined in scripts.** Transaction scripts use markers to identify steps within the workflow (e.g., `marker('Login Page')`, `marker('Search Results')`, `marker('Checkout Complete')`). Without markers, you only get total duration — no per-step breakdown. Check each script in ThousandEyes for marker placement.
- **Baseline transaction durations documented.** Different workflows have vastly different expected durations: a health-check page might take 1 second, a complex dashboard might take 8 seconds, a data export might legitimately take 30 seconds. The 10-second threshold in the primary search is a starting point — tune per-test using a lookup.
- **Splunk role:** `srchIndexesAllowed` must include `thousandeyes_metrics`.

### Step 1 — Configure data collection
Transaction test metrics flow through the same Tests Stream — Metrics OTel input configured in UC-5.9.1. No separate input is needed.

Verify transaction duration data is present:
```spl
index=thousandeyes_metrics sourcetype="cisco:thousandeyes:metric" thousandeyes.test.type="web-transactions" earliest=-30m
| stats avg(web.transaction.duration) as avg_dur count by thousandeyes.test.name
| where isnotnull(avg_dur)
```
Each test should show a non-null duration. If `web.transaction.duration` is null but `web.transaction.completion` is populated (UC-5.9.41), the tests are failing — duration is only reported for successful completions.

**Understanding the metric:**
- `web.transaction.duration` (seconds) — total elapsed time from the browser starting the first page load to the last marker or script completion. This is wall-clock time — it includes page rendering, JavaScript execution, network round-trips, and any explicit waits in the script (e.g., `driver.sleep(1000)`).
- Unlike `http.client.request.duration` (which measures a single HTTP request), transaction duration measures the entire scripted user journey. A 3-page workflow where each page takes 3 seconds has a transaction duration of ~9+ seconds (including navigation time between pages).
- OTel v2 units: **seconds**. A value of `12.5` means 12.5 seconds total workflow time.

### Step 2 — Create the search and alert
**Total transaction duration (flags slow workflows):**
```spl
`stream_index` thousandeyes.test.type="web-transactions"
| stats avg(web.transaction.duration) as avg_duration p95(web.transaction.duration) as p95_duration max(web.transaction.duration) as max_duration by thousandeyes.test.name
| eval avg_s=round(avg_duration,2), p95_s=round(p95_duration,2), max_s=round(max_duration,2)
| where avg_s > 10
| sort -avg_s
```

**Understanding this SPL**

`stats avg ... p95 ... max` — three views of the same metric. `avg` is typical performance, `p95` is the 95th percentile (worst-case for most users), and `max` is the absolute worst. If `avg` is 8 seconds but `p95` is 25 seconds, there's a long-tail problem — some users are having a much worse experience than average (perhaps hitting a cold cache or a slow backend server).

`where avg_s > 10` — 10 seconds is the "absolute ceiling" threshold for most web workflows. Google's Core Web Vitals research shows users abandon tasks after 10 seconds. For critical workflows (login, checkout), consider 5 seconds. For complex dashboards, 15 seconds may be acceptable.

**Per-agent comparison** (detects regional performance differences):
```spl
`stream_index` thousandeyes.test.type="web-transactions"
| stats avg(web.transaction.duration) as avg_s by thousandeyes.test.name, thousandeyes.source.agent.name, thousandeyes.source.agent.location
| eval avg_s=round(avg_s,2)
| sort thousandeyes.test.name, -avg_s
```
If the same transaction takes 5 seconds from one agent but 15 seconds from another, the issue is likely network path or CDN related, not application-side.

**Week-over-week regression detection** (catches gradual degradation):
```spl
`stream_index` thousandeyes.test.type="web-transactions" earliest=-14d
| eval week=if(_time > relative_time(now(), "-7d"), "This Week", "Last Week")
| stats avg(web.transaction.duration) as avg_dur by thousandeyes.test.name, week
| xyseries thousandeyes.test.name week avg_dur
| fillnull value=0 "Last Week" "This Week"
| where 'Last Week' > 0
| eval change_pct=round(('This Week' - 'Last Week') / 'Last Week' * 100, 1)
| where change_pct > 15
| sort -change_pct
```
A >15% increase week-over-week strongly suggests a performance regression — typically caused by a code deployment, database growth, or infrastructure change.

**Duration trending (visual long-term view):**
```spl
`stream_index` thousandeyes.test.type="web-transactions" earliest=-30d
| timechart span=1d avg(web.transaction.duration) as avg_duration by thousandeyes.test.name
```

**Scheduling:** cron `*/15 * * * *`, time range `-30m to now`. Trigger when `avg_s` exceeds the per-test SLA. Throttle by `thousandeyes.test.name` for 2 hours.

### Step 3 — Validate
(a) **Manual browser test.** Open a browser, start a stopwatch, and perform the same workflow manually. The manually timed duration should be within 20% of the ThousandEyes-reported duration. If the manual test is significantly faster, the Enterprise Agent may have resource constraints (CPU, memory, network) slowing the browser engine.

(b) **Cross-reference ThousandEyes UI.** Navigate to **Cloud & Enterprise Agents → Views → Transaction** and select the same test. The UI shows a waterfall with per-page/per-marker timing. Compare total duration with what Splunk reports.

(c) **Verify only successful transactions are reported.** Run: `| stats avg(web.transaction.duration) as dur avg(web.transaction.completion) as comp by thousandeyes.test.name`. Duration should only be present for rows where `comp = 100`. If duration appears for failed tests, the metric may be reporting partial execution time.

(d) **Check for script waits.** If the transaction script includes explicit `sleep()` or `wait()` commands, those are included in the duration. A 2-second explicit wait in the script inflates the duration by 2 seconds. Review scripts for unnecessary waits.

(e) **Unit verification.** `web.transaction.duration` is in seconds. A value of `0.5` means 500 ms (fast single-page test), while `25.0` means 25 seconds (multi-page complex workflow). Verify values are reasonable for the workflow complexity.

### Step 4 — Operationalize
**Dashboard** ("Transaction Performance" — designed for application platform team):
- Row 1 — Single value tiles: "Transactions > 10s avg" (red ≥ 1), "Fastest transaction" (name + duration), "Slowest transaction" (name + duration), "WoW regression count" (transactions that slowed > 15%).
- Row 2 — Bar chart: per-test total duration (avg and p95), sorted worst-first. Reference line at 10 seconds. Colour-code: green < 5s, yellow 5–10s, orange 10–20s, red > 20s.
- Row 3 — Per-agent comparison table (for selected test): agent name | location | avg duration | p95 duration. Highlights regional performance differences.
- Row 4 — Timechart: duration trending over 30 days. Add deployment/release markers as reference lines or annotations. Correlate duration increases with deployment dates.

**Alerting:**
- Any transaction avg duration > per-test SLA → low-urgency notification to `#app-performance` (Slack/Teams). Include test name, current duration, SLA, and slowest agent.
- WoW regression > 25% for any transaction → high-urgency email to engineering manager. Include: test name, last week avg, this week avg, % change. This is a strong signal of deployment regression.
- Any transaction avg duration > 30 seconds → high-urgency page (PagerDuty). A 30-second workflow is effectively broken for users.

**Runbook** (owner: application platform team):
1. **Duration increased after deployment** → Performance regression. Check: (a) Recent code deployments (correlate with CI/CD timestamps). (b) Database schema changes or new queries. (c) New third-party dependencies (e.g., a new analytics script adding 2 seconds of load time). Action: roll back and investigate, or profile the application to identify the slow path.
2. **Specific marker/step duration increased** → That specific page or action degraded. Use the ThousandEyes waterfall view (via permalink) to identify which page element is slow (slow API call? large image? render-blocking JavaScript?).
3. **All transactions slower from all agents** → Infrastructure-wide issue. Check: (a) Network latency (UC-5.9.1). (b) DNS resolution time (UC-5.9.14). (c) Server CPU/memory. (d) Database connection pool exhaustion.
4. **All transactions slower from specific agents** → Regional issue. Check: (a) CDN edge performance for that region. (b) Network path from that agent to the application. (c) SASE/proxy performance if traffic routes through a regional PoP (UC-5.9.30).
5. **Duration oscillates (fast → slow → fast)** → Auto-scaling or load-balancer rotation. Some backend instances may be slower than others. Check if slow durations correlate with specific backend IPs.
6. **Duration stable but p95 increasing** → Long-tail problem. A small percentage of test rounds are much slower. Likely cause: cache misses, garbage collection pauses, or database lock contention affecting occasional requests.

### Step 5 — Troubleshooting

- **`web.transaction.duration` always null** — Transaction tests are failing (0% completion). Fix completion first (UC-5.9.41). Duration is only reported for successful transactions.

- **Duration seems too long (e.g., 60+ seconds)** — Check for explicit `sleep()` or `wait()` commands in the Selenium script. Also check if the test timeout is set higher than necessary in ThousandEyes (default: 180 seconds). The browser may be waiting for a slow resource to finish loading before marking the transaction complete.

- **Duration varies wildly between test rounds** — Possible causes: (a) Enterprise Agent resource contention — another process is competing for CPU during some rounds. (b) Application-side variability — cold cache vs warm cache. (c) Network path changes — some rounds take a faster route. Check per-round data: `| stats stdev(web.transaction.duration) as stddev by thousandeyes.test.name`. A coefficient of variation (stddev/avg) > 0.3 indicates high variability that needs investigation.

- **Week-over-week comparison shows null for 'Last Week'** — The test may not have been running last week, or all tests failed last week (no duration reported for failures). Use `fillnull value=0` and filter accordingly.

- **All common troubleshooting** — See UC-5.9.1 Step 5 for HEC connectivity, OAuth refresh, macro configuration, v1/v2 field name differences, and role permissions.

## SPL

```spl
`stream_index` thousandeyes.test.type="web-transactions"
| stats avg(web.transaction.duration) as avg_duration p95(web.transaction.duration) as p95_duration by thousandeyes.test.name
| eval avg_s=round(avg_duration,2), p95_s=round(p95_duration,2)
| where avg_s > 10
| sort -avg_s
```

## Visualization

(1) Bar chart: transaction duration per test. (2) Timechart: duration trending over time. (3) Percentile chart: p50/p95/p99. (4) Marker timeline: duration breakdown per step.

## Known False Positives

**Duration not reported for failed transactions.** `web.transaction.duration` is only emitted when the transaction completes successfully. A sudden drop in data volume may indicate failures, not improvement.

**Script execution time variability.** Selenium script execution speed varies with agent CPU load and browser rendering performance. Small variations (< 10%) are normal.

## References

- [Cisco ThousandEyes App for Splunk (Splunkbase 7719)](https://splunkbase.splunk.com/app/7719)
- [ThousandEyes OTel v2 — Transaction metrics](https://docs.thousandeyes.com/product-documentation/integration-guides/opentelemetry/data-model/data-model-v2/metrics)
