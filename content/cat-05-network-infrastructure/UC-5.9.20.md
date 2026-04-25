<!-- AUTO-GENERATED from UC-5.9.20.json — DO NOT EDIT -->

---
id: "5.9.20"
title: "DNS Issue Event Tracking"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.9.20 · DNS Issue Event Tracking

## Description

ThousandEyes Internet Insights automatically detects DNS infrastructure issues that deviate from established baselines, surfacing problems in third-party DNS services before they cause widespread outages.

## Value

ThousandEyes Internet Insights automatically detects DNS infrastructure issues that deviate from established baselines, surfacing problems in third-party DNS services before they cause widespread outages.

## Implementation

Events with type "DNS Issue" are fetched via the Event input at the configured interval. Filter by `severity` (high, medium, low) and `state` (active, resolved) to focus on current issues. Correlate with DNS availability metrics from UC-5.10.6.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco ThousandEyes App for Splunk` (Splunkbase 7719).
• Ensure the following data sources are available: `index=thousandeyes`, ThousandEyes Event API.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Events with type "DNS Issue" are fetched via the Event input at the configured interval. Filter by `severity` (high, medium, low) and `state` (active, resolved) to focus on current issues. Correlate with DNS availability metrics from UC-5.10.6.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
`event_index` type="DNS Issue"
| stats count by severity, state, thousandeyes.test.name
| sort -count
```

Understanding this SPL

**DNS Issue Event Tracking** — ThousandEyes Internet Insights automatically detects DNS infrastructure issues that deviate from established baselines, surfacing problems in third-party DNS services before they cause widespread outages.

Documented **Data sources**: `index=thousandeyes`, ThousandEyes Event API. **App/TA** (typical add-on context): `Cisco ThousandEyes App for Splunk` (Splunkbase 7719). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

**Pipeline walkthrough**

• Invokes macro `event_index` — in Search, use the UI or expand to inspect the underlying SPL.
• `stats` rolls up events into metrics; results are split **by severity, state, thousandeyes.test.name** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Compare the same tests and time window in the Cisco ThousandEyes App for Splunk dashboard or the test view at app.thousandeyes.com so Splunk’s metrics and states match the vendor. If they disagree, check streaming or HEC inputs, macros, and API or token health before retuning.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Events timeline, Table (test, severity, state), Single value (active DNS issues).

## SPL

```spl
`event_index` type="DNS Issue"
| stats count by severity, state, thousandeyes.test.name
| sort -count
```

## Visualization

Events timeline, Table (test, severity, state), Single value (active DNS issues).

## References

- [Splunkbase app 7719](https://splunkbase.splunk.com/app/7719)
