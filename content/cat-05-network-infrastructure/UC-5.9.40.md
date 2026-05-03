<!-- AUTO-GENERATED from UC-5.9.40.json — DO NOT EDIT -->

---
id: "5.9.40"
title: "API Response Time Monitoring"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.9.40 · API Response Time Monitoring

> **Criticality:** High &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Performance &middot; **Wave:** Walk &middot; **Status:** Verified

*We time each step of our automated API tests to find exactly which part is slow — like timing each stop on a bus route to find where the delay happens.*

---

## Description

Tracks total API test duration and per-step duration to identify slow API workflows and pinpoint which specific API call is the bottleneck. Flags API tests where total execution exceeds 2 seconds.

## Value

API tests simulate multi-step workflows. If the overall test takes 5 seconds but step 3 (database query) takes 4 of those seconds, the bottleneck is identified immediately. Without per-step timing, teams waste time investigating the wrong endpoint. This UC provides the breakdown needed to optimize API performance and enforce SLA targets per endpoint.

## Implementation

Same API tests as UC-5.9.39. Duration is measured alongside completion.

## Detailed Implementation

### Prerequisites
- All prerequisites from UC-5.9.39 apply — API tests must be configured in ThousandEyes with multi-step workflows, and the Tests Stream — Metrics input must be delivering data to `thousandeyes_metrics`.
- **API test steps must include variable extraction.** For per-step duration to be meaningful, each step in the API test should represent a distinct API call (e.g., Step 1: authenticate, Step 2: list resources, Step 3: fetch detail, Step 4: update resource). Tests with a single step produce only `api.duration`, not step-level breakdown.
- **Baseline API performance known.** Document expected response times for each API endpoint under normal load. Without baselines, the 2-second threshold is arbitrary — a batch data export API may legitimately take 10 seconds, while a health-check endpoint should respond in under 100 ms. Consider maintaining a `thousandeyes_api_sla` lookup table with per-test expected durations.
- **Splunk role:** `srchIndexesAllowed` must include `thousandeyes_metrics`.

### Step 1 — Configure data collection
API test metrics flow through the same Tests Stream — Metrics OTel input configured in UC-5.9.1. No separate input is needed.

Verify API duration data is present:
```spl
index=thousandeyes_metrics sourcetype="cisco:thousandeyes:metric" thousandeyes.test.type="api" earliest=-30m
| stats avg(api.duration) as avg_dur count by thousandeyes.test.name
| where isnotnull(avg_dur)
```
You should see one row per API test with a non-null duration. If `api.duration` is null but `api.completion` is populated (UC-5.9.39), the test may have failed — duration is only reported for completed tests.

**Understanding the metrics:**
- `api.duration` (seconds) — total elapsed time for the entire API test workflow, from the first HTTP request of step 1 to the last HTTP response of the final step. This includes all inter-step delays, but NOT network latency from the agent to the first server — that's measured separately by associated network tests.
- `api.step.duration` (seconds) — elapsed time for a single step within the workflow. The sum of all step durations should approximately equal `api.duration`, though there may be small gaps for inter-step processing.
- Both are in **seconds** (OTel v2). A duration of `0.5` means 500 milliseconds. Multiply by 1000 for ms display.

### Step 2 — Create the search and alert
**Overall API duration (flags slow workflows):**
```spl
`stream_index` thousandeyes.test.type="api"
| stats avg(api.duration) as avg_duration p95(api.duration) as p95_duration max(api.duration) as max_duration by thousandeyes.test.name
| eval avg_duration_s=round(avg_duration,2), p95_duration_s=round(p95_duration,2), max_duration_s=round(max_duration,2)
| where avg_duration_s > 2
| sort -avg_duration_s
```

**Understanding this SPL**

`stats avg(api.duration) ... p95(api.duration) ... max(api.duration)` — three statistical views of the same metric. `avg` represents typical performance, `p95` represents worst-case-for-most-users (the 95th percentile — 5% of tests were slower than this), and `max` captures the absolute worst single execution. If `avg` is 1s but `p95` is 5s, there's high variance — some test rounds are hitting a slow code path or encountering intermittent load.

`where avg_duration_s > 2` — 2 seconds is a reasonable general threshold for API workflows. Tune per-test using a lookup: `| lookup thousandeyes_api_sla.csv thousandeyes.test.name OUTPUT max_expected_duration_s | where avg_duration_s > max_expected_duration_s`.

**Per-step duration breakdown (identifies the bottleneck step):**
```spl
`stream_index` thousandeyes.test.type="api"
| stats avg(api.step.duration) as avg_step_s p95(api.step.duration) as p95_step_s by thousandeyes.test.name, thousandeyes.test.step, server.address, http.request.method
| eval avg_step_ms=round(avg_step_s*1000,1), p95_step_ms=round(p95_step_s*1000,1)
| sort thousandeyes.test.name, -avg_step_ms
```
This shows each step sorted by duration within each test. The slowest step is the performance bottleneck. If Step 3 (e.g., `GET /api/v2/reports`) takes 3000 ms while other steps take 100–200 ms, the bottleneck is the reports endpoint, not the overall API.

**Duration trending (detects gradual degradation):**
```spl
`stream_index` thousandeyes.test.type="api" earliest=-7d
| timechart span=1h avg(api.duration) as avg_duration by thousandeyes.test.name
```

**Step-level bottleneck identification (shows which step contributes most to total duration):**
```spl
`stream_index` thousandeyes.test.type="api" thousandeyes.test.name="$test_name$"
| stats avg(api.step.duration) as step_dur by thousandeyes.test.step
| eval step_ms=round(step_dur*1000,1)
| sort thousandeyes.test.step
```
Use as a drill-down from the overall duration table.

**Scheduling:** cron `*/15 * * * *`, time range `-30m to now`. Trigger when avg_duration exceeds the per-test SLA threshold. Throttle by `thousandeyes.test.name` for 2 hours.

### Step 3 — Validate
(a) **Manual API call comparison.** For a specific API test step, replicate the HTTP request manually using `curl` with timing:
```bash
curl -o /dev/null -s -w "Total: %{time_total}s\nTTFB: %{time_starttransfer}s\n" -X GET "https://api.example.com/v2/resource" -H "Authorization: Bearer <token>"
```
Compare `time_total` with the `api.step.duration` for the same step in Splunk. They should be within ~20% (the ThousandEyes agent adds minimal overhead).

(b) **Cross-reference ThousandEyes UI.** Navigate to **Cloud & Enterprise Agents → Views → API** and check the waterfall view for the same test. The per-step timing bars should match the Splunk data.

(c) **Verify unit conversion.** `api.duration` is in seconds. A value of `0.35` means 350 ms, not 35 seconds. Run: `| stats avg(api.duration) as raw | eval ms=round(raw*1000,1)` and verify the `ms` value is reasonable for an API call (50–5000 ms typically).

(d) **Duration vs completion correlation.** Run both UC-5.9.39 (completion) and this UC side-by-side. Duration should only appear for tests with 100% completion — failed tests don't report duration. If you see duration for failed tests, the `api.duration` metric may be measuring partial execution.

(e) **Step ordering.** Verify `thousandeyes.test.step` values match the expected step sequence. `| stats values(thousandeyes.test.step) as steps by thousandeyes.test.name` should show step identifiers that correspond to the API test configuration in ThousandEyes.

### Step 4 — Operationalize
**Dashboard** ("API Performance" — designed for API platform team):
- Row 1 — Single value tiles: "API tests > 2s avg" (red ≥ 1), "Slowest API test" (name + duration), "Average API duration across all tests" (green < 1s, yellow < 2s, red ≥ 2s).
- Row 2 — Bar chart: per-test total duration (avg and p95), sorted worst-first. Colour-code: green < 1s, yellow 1–2s, orange 2–5s, red > 5s.
- Row 3 — Stacked bar (drill-down): per-step duration breakdown for a selected test. Each stack segment represents a step. This immediately shows which step is the time hog.
- Row 4 — Timechart: duration trending over 7 days for top-5 slowest tests. Look for: gradual increase (database growth? memory leak?), step-changes (deployment regression?), periodic spikes (batch jobs competing for resources?).

**Alerting:**
- Any API test avg duration > SLA threshold → low-urgency notification to `#api-platform` (Slack/Teams). Include test name, current duration, SLA threshold, and which step is slowest.
- Any API test p95 duration > 3× SLA threshold → high-urgency page (PagerDuty). A p95 this far above SLA means many users are experiencing unacceptable latency.
- Sustained increase: avg duration increases > 50% week-over-week → capacity planning notification.

**Runbook** (owner: API platform team):
1. **Identify the bottleneck step.** Run the per-step breakdown. The slowest step determines the investigation path.
2. **Step 1 (auth) is slow** → Authentication service bottleneck. Check OAuth provider health, token endpoint latency, credential rotation status.
3. **Data retrieval step is slow** → Backend service or database bottleneck. Check: (a) Database query execution plans. (b) Connection pool exhaustion. (c) Cache miss rates. (d) Competing workloads on the database host.
4. **Write/update step is slow** → Write amplification, transaction locks, or replication lag. Check database replication status and lock waits.
5. **All steps slow uniformly** → Network path issue between the ThousandEyes agent and the API server. Check UC-5.9.1 (latency) for the same target. If network latency increased, the API isn't slow — the network is.
6. **Duration varies widely between agents** → The API may be behind a load balancer routing to backends with different performance characteristics. Compare per-agent results to identify if specific backend instances are slow.
7. **Duration increased after deployment** → Regression. Correlate timing with deployment records. Rollback or investigate the change.

### Step 5 — Troubleshooting

- **`api.duration` always null** — Duration is only reported for tests that complete successfully (100% completion). If all tests are failing (UC-5.9.39), fix completion first — duration data will appear once tests pass.

- **`api.step.duration` missing but `api.duration` is present** — Per-step metrics may not be available if the API test has only one step, or if the ThousandEyes data version doesn't include step-level detail. Check `| fieldsummary | search field=api.step*`.

- **Sum of step durations doesn't equal total duration** — There's inter-step processing time (variable extraction, assertion evaluation) not captured in `api.step.duration`. A 10–20% gap is normal.

- **Duration spikes at specific times** — Check for: (a) Scheduled batch jobs competing for API server resources. (b) Database backup windows. (c) Auto-scaling events (new instances warming up). Overlay the timechart with infrastructure metrics to identify resource contention.

- **All common troubleshooting** — See UC-5.9.1 Step 5 for HEC connectivity, OAuth refresh, macro configuration, v1/v2 field name differences, and role permissions.

## SPL

```spl
`stream_index` thousandeyes.test.type="api"
| stats avg(api.duration) as avg_duration p95(api.duration) as p95_duration by thousandeyes.test.name
| eval avg_duration_s=round(avg_duration,2), p95_duration_s=round(p95_duration,2)
| where avg_duration_s > 2
| sort -avg_duration_s
```

## Visualization

(1) Bar chart: API test total duration. (2) Stacked bar: per-step duration breakdown. (3) Timechart: duration trending. (4) Table: slowest steps across all tests.

## Known False Positives

**Duration not reported on failure.** `api.duration` may not be emitted for failed tests. Check completion first.

**Variable server-side processing.** Some API calls have inherently variable response times (database-heavy queries, batch operations). Establish per-test baselines.

## References

- [Cisco ThousandEyes App for Splunk (Splunkbase 7719)](https://splunkbase.splunk.com/app/7719)
- [ThousandEyes OTel v2 — API metrics](https://docs.thousandeyes.com/product-documentation/integration-guides/opentelemetry/data-model/data-model-v2/metrics)
