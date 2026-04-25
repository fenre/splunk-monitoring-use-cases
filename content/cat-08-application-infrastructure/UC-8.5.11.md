<!-- AUTO-GENERATED from UC-8.5.11.json — DO NOT EDIT -->

---
id: "8.5.11"
title: "Synthetic Transaction Monitoring"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.5.11 · Synthetic Transaction Monitoring

## Description

Simulated multi-step user journeys with timing per step validate end-to-end availability and detect degradation before users report issues. Step-level timing enables pinpointing of slow components.

## Value

Simulated multi-step user journeys with timing per step validate end-to-end availability and detect degradation before users report issues. Step-level timing enables pinpointing of slow components.

## Implementation

Run synthetic tests via Splunk Synthetic Monitoring, Selenium, or Playwright. Configure tests to log JSON with test_name, step_name, step_start_time, step_end_time, overall_status, error_message. Forward to Splunk via HEC. Alert when any test fails or step duration exceeds SLA (e.g., 5s). Track step-level trends to identify regressions. Use transaction for multi-step journey correlation.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk Synthetic Monitoring, custom scripted input (Selenium, Playwright).
• Ensure the following data sources are available: Synthetic test runner output with step-level timings.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Run synthetic tests via Splunk Synthetic Monitoring, Selenium, or Playwright. Configure tests to log JSON with test_name, step_name, step_start_time, step_end_time, overall_status, error_message. Forward to Splunk via HEC. Alert when any test fails or step duration exceeds SLA (e.g., 5s). Track step-level trends to identify regressions. Use transaction for multi-step journey correlation.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=synthetic sourcetype="synthetic:test"
| eval step_duration=step_end_time-step_start_time
| where overall_status=="FAIL" OR step_duration > 5000
| stats count, avg(step_duration) as avg_step_ms by test_name, step_name
| sort -avg_step_ms
```

Understanding this SPL

**Synthetic Transaction Monitoring** — Simulated multi-step user journeys with timing per step validate end-to-end availability and detect degradation before users report issues. Step-level timing enables pinpointing of slow components.

Documented **Data sources**: Synthetic test runner output with step-level timings. **App/TA** (typical add-on context): Splunk Synthetic Monitoring, custom scripted input (Selenium, Playwright). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: synthetic; **sourcetype**: synthetic:test. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=synthetic, sourcetype="synthetic:test". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **step_duration** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where overall_status=="FAIL" OR step_duration > 5000` — typically the threshold or rule expression for this monitoring goal.
• `stats` rolls up events into metrics; results are split **by test_name, step_name** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Compare with the cache or proxy product’s own stats (CLI or UI) and a small sample of indexed events.


Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Timeline (test runs with pass/fail), Table (slow steps by test), Line chart (step duration trend), Single value (failed tests).

## SPL

```spl
index=synthetic sourcetype="synthetic:test"
| eval step_duration=step_end_time-step_start_time
| where overall_status=="FAIL" OR step_duration > 5000
| stats count, avg(step_duration) as avg_step_ms by test_name, step_name
| sort -avg_step_ms
```

## Visualization

Timeline (test runs with pass/fail), Table (slow steps by test), Line chart (step duration trend), Single value (failed tests).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
