<!-- AUTO-GENERATED from UC-5.9.39.json — DO NOT EDIT -->

---
id: "5.9.39"
title: "API Endpoint Completion Rate"
status: "verified"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.9.39 · API Endpoint Completion Rate

> **Criticality:** Critical &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Availability &middot; **Wave:** Crawl &middot; **Status:** Verified

*We test our APIs by running through a real sequence of steps — like logging in, requesting data, and checking the answer — to make sure every part of the process works, not just the front door.*

---

## Description

Monitors ThousandEyes API test completion rate — multi-step API workflow tests that simulate real API interactions with request chaining, variable extraction, and response assertions. A completion rate below 100% indicates that the API workflow is failing at one or more steps.

## Value

API tests go beyond simple HTTP availability. They simulate a real client workflow: authenticate with OAuth, extract an access token, call a protected endpoint with the token, validate the JSON response schema, and verify specific field values. If any step fails — the auth endpoint is slow, the token format changes, the response schema breaks, or a required field is missing — the API test catches it. This is the gold standard for API monitoring because it tests the API contract, not just connectivity.

## Implementation

API tests are configured in ThousandEyes with multi-step workflows. Each step defines an HTTP request, variable extraction, and response assertions.

## Detailed Implementation

### Prerequisites
- All common prerequisites from UC-5.9.1 apply (app installed, OAuth authenticated, HEC configured, Tests Stream — Metrics input enabled).
- **API tests configured in ThousandEyes.** Navigate to **Cloud & Enterprise Agents → Test Settings → Add New Test → Web → API**. Key concepts:
  - API tests define multi-step HTTP request workflows with variable extraction and response assertions.
  - Each **step** is an HTTP request (GET, POST, PUT, DELETE) to a specific endpoint with headers, body, and assertions.
  - Steps can extract values from responses (e.g., extract an OAuth token from step 1's response) and use them as variables in subsequent steps (e.g., `Authorization: Bearer {{token}}` in step 2).
  - **Assertions** validate response: status code, response body content, JSON path values, response headers. If ANY assertion fails, the step fails.
  - Example multi-step workflow: Step 1: POST `/auth/token` (extract `access_token`), Step 2: GET `/api/v2/users` (use token, assert status=200), Step 3: POST `/api/v2/users` (create user, assert status=201), Step 4: GET `/api/v2/users/{{user_id}}` (verify creation, assert name field).
  - **Agents:** API tests can run on both Cloud Agents and Enterprise Agents. Cloud Agents work for public APIs; Enterprise Agents are needed for internal APIs.
  - **Interval:** 2–5 minutes. Avoid 1-minute intervals for API tests that create or modify data (to prevent excessive test data accumulation).
- **API credentials configured.** If the API requires authentication, credentials must be configured in the test (API key, OAuth client credentials, etc.). These are stored in ThousandEyes — not in Splunk.
- **Splunk role:** `srchIndexesAllowed` must include `thousandeyes_metrics`.

### Step 1 — Configure data collection
API test metrics flow through the same Tests Stream — Metrics OTel input configured in UC-5.9.1. No separate input is needed.

Verify API test data is present:
```spl
index=thousandeyes_metrics sourcetype="cisco:thousandeyes:metric" thousandeyes.test.type="api" earliest=-30m
| stats avg(api.completion) as avg_completion count by thousandeyes.test.name
```
Each test should show data with a non-null completion value.

**Understanding the metrics:**
- `api.completion` (percentage: 0 or 100) — overall test completion. 100% if ALL steps completed successfully (HTTP requests succeeded AND all assertions passed). 0% if ANY step failed.
- `api.step.completion` (percentage: 0 or 100) — per-step completion. Identifies exactly which step in the workflow failed.
- `api.duration` (seconds) — total time for the entire workflow. See UC-5.9.40.
- `api.step.duration` (seconds) — per-step duration. See UC-5.9.40.
- `thousandeyes.test.step` — step identifier within the workflow (step name or number).
- API tests are the highest-fidelity test type for REST APIs because they test the full API contract: authentication, request/response format, status codes, and response content — not just connectivity.

### Step 2 — Create the search and alert
**Overall API completion (flags any test with failures):**
```spl
`stream_index` thousandeyes.test.type="api"
| stats avg(api.completion) as avg_completion min(api.completion) as min_completion dc(thousandeyes.source.agent.name) as agents by thousandeyes.test.name
| where avg_completion < 100
| sort avg_completion
```

**Understanding this SPL**

`thousandeyes.test.type="api"` — filters to API tests. Other web test types (http-server, page-load, web-transactions) test different aspects of web services.

`avg(api.completion)` — average completion over the search window. 100% means every test round's complete multi-step workflow succeeded. Values < 100% indicate that some rounds failed at one or more steps.

`dc(thousandeyes.source.agent.name) as agents` — how many agents ran this test. If completion is 0% from all agents, the API is universally broken. If 0% from one agent, the issue may be agent-specific.

**Per-step completion (pinpoints the failing step):**
```spl
`stream_index` thousandeyes.test.type="api"
| stats avg(api.step.completion) as step_completion dc(thousandeyes.source.agent.name) as agents by thousandeyes.test.name, thousandeyes.test.step
| where step_completion < 100
| sort thousandeyes.test.name, step_completion
```
This is the most actionable view — it shows exactly which step in the workflow is failing. If step 1 (auth) fails, all subsequent steps also fail because they depend on the auth token. If only step 3 fails, step 3's endpoint has a problem.

**Completion timeline:**
```spl
`stream_index` thousandeyes.test.type="api" earliest=-24h
| timechart span=15m avg(api.completion) by thousandeyes.test.name
```

**Per-agent breakdown (for a specific failing test):**
```spl
`stream_index` thousandeyes.test.type="api" thousandeyes.test.name="$test_name$"
| stats avg(api.completion) as completion by thousandeyes.source.agent.name, thousandeyes.source.agent.location
| sort completion
```

**Scheduling:** cron `*/5 * * * *`, time range `-10m to now`. API failures should alert quickly — a broken API blocks dependent applications and users. Throttle by `thousandeyes.test.name` for 1 hour.

### Step 3 — Validate
(a) **Manual API test with curl/Postman.** Replicate the API workflow manually. For each step, issue the same HTTP request with the same headers and body. Compare responses with expected assertions. If curl succeeds but ThousandEyes fails, check: (i) IP-based restrictions (the API may whitelist your IP but block ThousandEyes agents). (ii) Rate limiting (the test frequency may exceed the API's rate limit).

(b) **Cross-reference ThousandEyes UI.** Navigate to **Cloud & Enterprise Agents → Views → API** and select the test. The UI shows per-step results with response bodies, status codes, and assertion results. If an assertion failed, the UI shows exactly which assertion and the actual vs expected values.

(c) **Verify step ordering.** Run `| stats values(thousandeyes.test.step) by thousandeyes.test.name` and verify the steps match the test configuration in ThousandEyes.

(d) **Check for cascading failures.** If step 1 fails, all subsequent steps should also fail (they depend on step 1's output). If step 1 fails but step 3 succeeds, there may be a test configuration issue (step 3 doesn't actually depend on step 1's variable).

(e) **Rate limit verification.** Check `| stats count by thousandeyes.test.name` over a 1-hour window. If the test runs from 5 agents every 2 minutes, that's 150 requests/hour to the API. Verify this doesn't exceed the API's rate limit.

### Step 4 — Operationalize
**Dashboard** ("API Health" — designed for API platform team):
- Row 1 — Single value tiles: "API tests 100% passing" (green), "API tests with failures" (red ≥ 1), "Overall API completion %" (green ≥ 99.9%, red < 99%).
- Row 2 — Completion timechart over 24 hours at 15-minute granularity. Each line is an API test. Red areas indicate failure periods.
- Row 3 — Per-step failure table: test name | step | avg completion | agents affected. Sorted by completion ascending. This is the primary troubleshooting view — it tells you WHICH step is broken.
- Row 4 — Detail table: test name | agent | completion — sorted worst-first. Drilldown to ThousandEyes permalink for assertion detail.

**Alerting:**
- Completion < 100% from ANY agent → low-urgency Slack notification. Include test name, failing step, and ThousandEyes permalink.
- Completion 0% from ALL agents → high-urgency page (PagerDuty). API is completely down. Include test name, all failing steps, and permalink.
- Completion drops from 100% to < 50% in one polling cycle → critical. Sudden complete failure — likely deployment regression or infrastructure outage.

**Runbook** (owner: API platform team):
1. **Step 1 (auth) failing.** Authentication service issue. Check: (a) OAuth/token endpoint availability. (b) Client credentials validity (API key expired? Client secret rotated?). (c) Auth service logs for errors. (d) Rate limiting on the auth endpoint.
2. **Step 1 passes, later step fails.** Specific API endpoint issue. Check: (a) The endpoint's application logs. (b) Response body in ThousandEyes for error messages. (c) HTTP status code (500 = server error, 404 = endpoint moved, 422 = validation error).
3. **All steps pass but assertion fails.** API contract changed. Check: (a) Was a planned API release deployed? If yes, update test assertions. (b) Was it unintentional? If yes, this is a regression — the API changed its response format. (c) Check JSON path assertions — a field may have been renamed, moved, or removed.
4. **Completion varies by agent.** The API may behave differently based on client IP or region. Check: (a) Geo-based routing to different API backends. (b) Different backend instances with configuration drift.
5. **Intermittent failures.** The API works most of the time but occasionally fails. Check: (a) Transient database connection errors. (b) Backend auto-scaling — new instances may have cold caches. (c) Concurrent request limits.

### Step 5 — Troubleshooting

- **No API test data in Splunk** — Verify API tests are configured in ThousandEyes and assigned to agents. Check that the Tests Stream — Metrics input includes the `api` test type (some deployments filter by test type in the stream configuration).

- **`api.step.completion` field missing** — Per-step metrics may require `thousandeyes.test.step` attribute, which is OTel v2-specific. Check `| fieldsummary | search field=api*`. If only `api.completion` is present (no step-level detail), the data may be v1 format.

- **Completion is always 0% even though manual API call succeeds** — Common causes: (a) ThousandEyes agent IPs blocked by API rate limiter or WAF. (b) Test credentials expired or rotated. (c) Test configuration error (wrong URL, wrong assertion). Check the ThousandEyes test results detail for the specific error.

- **API test creates duplicate data in production** — If the test includes POST/PUT steps that create resources, each test round creates data. Use a dedicated test environment or implement test data cleanup. Consider read-only API tests for production monitoring.

- **All common troubleshooting** — See UC-5.9.1 Step 5 for HEC connectivity, OAuth refresh, macro configuration, v1/v2 field name differences, and role permissions.

## SPL

```spl
`stream_index` thousandeyes.test.type="api"
| stats avg(api.completion) as avg_completion min(api.completion) as min_completion by thousandeyes.test.name, thousandeyes.source.agent.name
| where avg_completion < 100
| sort avg_completion
```

## Visualization

(1) Scoreboard: API test completion rates. (2) Table: failing API tests with step detail. (3) Timechart: completion trending. (4) Drilldown: per-step completion to identify which step failed.

## Known False Positives

**Token expiration.** If the API test relies on a long-lived API key or token that expires, all subsequent steps fail until the token is renewed. This is a test configuration issue, not an API failure.

**API rate limiting.** APIs may rate-limit the ThousandEyes agent IP. If test frequency × agent count exceeds the API rate limit, some tests fail with HTTP 429. Reduce test frequency or whitelist agent IPs.

**API schema changes.** When the API is intentionally updated (new fields, changed response structure), assertion-based tests may fail. Update test assertions after planned API changes.

## References

- [Cisco ThousandEyes App for Splunk (Splunkbase 7719)](https://splunkbase.splunk.com/app/7719)
- [ThousandEyes OTel v2 — API test metrics](https://docs.thousandeyes.com/product-documentation/integration-guides/opentelemetry/data-model/data-model-v2/metrics)
