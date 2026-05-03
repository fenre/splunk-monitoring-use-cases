<!-- AUTO-GENERATED from UC-5.9.41.json — DO NOT EDIT -->

---
id: "5.9.41"
title: "Transaction Test Completion Rate"
status: "verified"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.9.41 · Transaction Test Completion Rate

> **Criticality:** Critical &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Availability &middot; **Wave:** Crawl &middot; **Status:** Verified

*We have a robot that goes through our website clicking buttons and filling in forms exactly like a real person would, so we can tell immediately if anything in the workflow is broken — before a real customer runs into the problem.*

---

## Description

Monitors Transaction test completion — Selenium-based browser scripted workflows that simulate real user journeys (login → navigate → perform action → verify result). Transaction tests are the highest-fidelity ThousandEyes test type, validating end-to-end user experience including JavaScript rendering, form submissions, and multi-page workflows.

## Value

Transaction tests are the closest approximation to real user behavior. While HTTP Server tests check a single URL and Page Load tests render a single page, Transaction tests click buttons, fill forms, navigate menus, and verify page content — exactly as a user would. When a Transaction test fails, a real user would fail too. This makes Transaction test completion the most business-critical metric: 0% completion on a checkout workflow means lost revenue, 0% completion on a login workflow means locked-out users.

## Implementation

Transaction tests require Selenium-based scripts configured in ThousandEyes. Tests run on Enterprise Agents with browser capability.

## Detailed Implementation

### Prerequisites
- All common prerequisites from UC-5.9.1 apply (app installed, OAuth authenticated, HEC configured, Tests Stream — Metrics input enabled).
- **Transaction tests configured with Selenium scripts.** Navigate to **Cloud & Enterprise Agents → Test Settings → Add New Test → Web → Transaction**. Key concepts:
  - Transaction tests use a **Selenium WebDriver script** that controls a real Chromium browser to simulate user interactions: clicking buttons, filling forms, navigating pages, and verifying content.
  - Scripts are written in the ThousandEyes Transaction Script editor or imported from the ThousandEyes Recorder browser extension.
  - **Markers** divide the script into logical steps (e.g., `markers.start('Login')`, `markers.stop('Login')`, `markers.start('Dashboard Load')`). Each marker becomes a separately timed segment in the test results — essential for identifying which part of the workflow is slow or failing.
  - Each marker also produces per-marker completion and duration metrics, enabling pinpoint troubleshooting.
  - **Assertions** validate that the page content is correct: element existence, text content, visibility. If an assertion fails, the transaction is marked as failed.
- **Enterprise Agents with browser capability required.** Transaction tests cannot run on Cloud Agents. Enterprise Agents must have: at least 2 GB RAM (4 GB recommended for complex scripts), 2 vCPU, and the BrowserBot component installed and running. The agent's Docker container or VM must have sufficient resources for headless Chromium.
- **Scripts tested in ThousandEyes Recorder.** Before deploying to production monitoring, test scripts using the ThousandEyes Recorder browser extension. This validates element selectors, wait times, and assertions against the live application.
- **Splunk role:** `srchIndexesAllowed` must include `thousandeyes_metrics`.

### Step 1 — Configure data collection
Transaction test metrics flow through the same Tests Stream — Metrics OTel input configured in UC-5.9.1. No separate input is needed.

Verify transaction data is present:
```spl
index=thousandeyes_metrics sourcetype="cisco:thousandeyes:metric" thousandeyes.test.type="web-transactions" earliest=-30m
| stats avg(web.transaction.completion) as avg_completion count by thousandeyes.test.name
```
Each test should show data. If `avg_completion` is consistently 0%, the script may have a fundamental issue (see Step 5).

**Understanding the metrics:**
- `web.transaction.completion` (percentage: 0 or 100) — 100% if the entire Selenium script executed without errors and all assertions passed. 0% if ANY step threw an error, timed out, or failed an assertion.
- `web.transaction.errors.count` (integer: 0 or 1) — 1 if an error occurred, 0 if the transaction completed cleanly. Useful for counting failure frequency.
- `web.transaction.duration` (seconds) — total workflow execution time. See UC-5.9.42.
- `marker` — the name of the current marker/step within the transaction. Enables per-step completion and duration analysis.
- Transaction tests are the **highest-fidelity** ThousandEyes test type. They simulate actual user behavior (clicks, form fills, page navigation) and validate the complete end-to-end user experience. A failed transaction test means a real user performing the same steps would fail too.

### Step 2 — Create the search and alert
**Transaction completion overview (flags any workflow with failures):**
```spl
`stream_index` thousandeyes.test.type="web-transactions"
| stats avg(web.transaction.completion) as avg_completion sum(web.transaction.errors.count) as total_errors dc(thousandeyes.source.agent.name) as agents by thousandeyes.test.name
| where avg_completion < 100
| sort avg_completion
```

**Understanding this SPL**

`avg(web.transaction.completion)` — average completion across all agents and test rounds. 100% = every round completed successfully. Values < 100% indicate failures. Because completion is binary (0 or 100), the average directly represents the success rate: 75% means 75% of rounds succeeded.

`sum(web.transaction.errors.count) as total_errors` — total error count across all rounds. A high number indicates frequent failures.

`dc(thousandeyes.source.agent.name) as agents` — number of agents running this test. Correlate with failures: if 3 agents run the test and only 1 shows failures, the issue may be agent-specific.

**Per-marker completion (pinpoints the failing step in the workflow):**
```spl
`stream_index` thousandeyes.test.type="web-transactions"
| stats avg(web.transaction.completion) as completion by thousandeyes.test.name, marker
| where completion < 100
| sort thousandeyes.test.name, completion
```
This is the most actionable view — it shows which step in the user journey is failing. If the "Login" marker fails, the login page is broken. If the "Checkout" marker fails, the payment flow is broken.

**Completion timeline:**
```spl
`stream_index` thousandeyes.test.type="web-transactions" earliest=-24h
| timechart span=15m avg(web.transaction.completion) by thousandeyes.test.name
```

**Error trending (detects increasing failure rates):**
```spl
`stream_index` thousandeyes.test.type="web-transactions" earliest=-7d
| timechart span=1d sum(web.transaction.errors.count) as errors by thousandeyes.test.name
```

**Scheduling:** cron `*/5 * * * *`, time range `-10m to now`. Transaction failures represent critical user-facing issues — a failed checkout workflow means lost revenue. Throttle by `thousandeyes.test.name` for 1 hour.

### Step 3 — Validate
(a) **Manual user journey.** Open a browser and perform the exact same steps the transaction script automates: login, navigate, perform action, verify result. If your manual test succeeds but ThousandEyes fails, the script may have a stale element selector (the UI was updated but the script wasn't).

(b) **Cross-reference ThousandEyes UI.** Navigate to **Cloud & Enterprise Agents → Views → Transaction** and select the test. The UI shows per-marker results with screenshots (if configured), timings, and error messages. A red marker shows exactly where the transaction failed.

(c) **Check screenshots.** If the transaction test has screenshots enabled, the ThousandEyes UI shows browser screenshots at each marker. This reveals visual issues (page not rendering correctly, unexpected modal dialogs, CAPTCHA challenges) that text-based assertions miss.

(d) **Verify marker coverage.** Run `| stats values(marker) by thousandeyes.test.name` and verify all expected markers are present. Missing markers indicate that the script never reached that point in the workflow (it failed earlier).

(e) **Agent resource verification.** Transaction tests are resource-intensive. Check agent health: in ThousandEyes, navigate to **Cloud & Enterprise Agents → Agent Settings** and check CPU/memory utilization. Agents running multiple transaction tests simultaneously may run out of resources.

### Step 4 — Operationalize
**Dashboard** ("Transaction Monitoring" — designed for QA and application team):
- Row 1 — Scoreboard: one tile per transaction test showing completion %. Green = 100%, red = < 100%. This should be the most prominent element — each tile represents a critical user workflow.
- Row 2 — Per-marker detail table: test | marker | completion %. Sorted by completion ascending. Shows exactly where failures occur in each workflow.
- Row 3 — Completion timechart over 24 hours. Reveals temporal patterns: failures during deployments, business-hours congestion, or time-based content changes.
- Row 4 — Error trend over 7 days: daily error count per test. Increasing errors = worsening issue.

**Alerting:**
- Completion < 100% for ANY production transaction → immediate page (PagerDuty). Transaction failures represent direct user impact. Include: test name, failing marker, agent, ThousandEyes permalink.
- Completion 0% from ALL agents → critical incident. The workflow is completely broken. Immediate all-hands escalation.
- Error count increases > 50% day-over-day → low-urgency notification. May indicate a new regression.

**Runbook** (owner: QA / application / SRE team):
1. **All markers failing from all agents.** Application is completely down or the login page is broken (everything depends on login). Check: (a) Application health endpoints. (b) Database connectivity. (c) Load balancer health. (d) Recent deployments.
2. **Specific marker failing from all agents.** That specific page or action is broken. Check: (a) The element the script interacts with — was the UI changed? (b) The API endpoint the page calls. (c) The ThousandEyes screenshot for visual context.
3. **One agent failing, others succeeding.** Agent-specific issue: (a) Agent resource exhaustion (CPU/memory). (b) Network connectivity from that agent to the application. (c) DNS resolution difference at that agent's location.
4. **`errors.count` increasing over days.** New regression introduced. Correlate with deployment timestamps. Check if the increasing errors match a specific marker (= regression in that specific page/flow).
5. **Script fails after application update.** The most common cause of transaction test failures is UI changes that break Selenium selectors. The application team changed a button ID, moved an element, or renamed a page. Update the script to match the new UI. Best practice: use stable element selectors (data-testid attributes) instead of brittle selectors (CSS class names, XPath positions).

### Step 5 — Troubleshooting

- **Script works in ThousandEyes Recorder but fails on production agent** — Common causes: (a) Browser version mismatch between Recorder (your Chrome) and agent (headless Chromium). (b) Screen resolution difference — responsive layouts render differently. (c) Network access — the agent may not have access to all resources the page loads (blocked by proxy, firewall, or DNS). (d) Missing waits — the Recorder may have had implicit delays from human interaction speed, but the agent executes instantly. Add explicit waits (`driver.sleep(2000)` or `driver.wait()` for element visibility).

- **Intermittent failures (works 80% of the time)** — Likely a race condition or timing issue. Common causes: (a) JavaScript not fully loaded before the script clicks an element. Solution: add `driver.wait(until.elementIsVisible(...), 10000)` before clicks. (b) Animations or transitions that delay element interactability. (c) A/B testing or personalization serving different page versions.

- **Completion always 0%** — The script has a fundamental error. Check: (a) First marker — does the script even navigate to the correct URL? (b) Authentication — are credentials valid? (c) Element selectors — do the selectors match the current UI?

- **`web.transaction.completion` field missing** — Check `thousandeyes.data.version`. In OTel v1, the field may be named differently. Run `| fieldsummary | search field=web.transaction*`.

- **All common troubleshooting** — See UC-5.9.1 Step 5 for HEC connectivity, OAuth refresh, macro configuration, and role permissions.

## SPL

```spl
`stream_index` thousandeyes.test.type="web-transactions"
| stats avg(web.transaction.completion) as avg_completion sum(web.transaction.errors.count) as total_errors by thousandeyes.test.name, thousandeyes.source.agent.name
| where avg_completion < 100
| sort avg_completion
```

## Visualization

(1) Scoreboard: transaction completion rates. (2) Table: failing transactions with error details. (3) Timechart: completion trending. (4) Marker breakdown: completion per step/marker within the transaction.

## Known False Positives

**Script maintenance.** UI changes (moved buttons, renamed fields, new page flow) break the Selenium script. This is a script maintenance issue, not an application failure. Update scripts after UI releases.

**Test environment differences.** Transaction tests running against a staging environment may see different behavior than production.

**Dynamic content.** Pages with dynamic content (randomized layouts, A/B tests, geographically personalized content) may cause assertion failures.

## References

- [Cisco ThousandEyes App for Splunk (Splunkbase 7719)](https://splunkbase.splunk.com/app/7719)
- [ThousandEyes OTel v2 — Transaction metrics](https://docs.thousandeyes.com/product-documentation/integration-guides/opentelemetry/data-model/data-model-v2/metrics)
