<!-- AUTO-GENERATED from UC-5.9.41.json — DO NOT EDIT -->

---
id: "5.9.41"
title: "Transaction Test Completion Rate (ThousandEyes)"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.9.41 · Transaction Test Completion Rate (ThousandEyes)

## Description

Transaction tests execute scripted multi-step user workflows (login, navigate, submit form, verify result). Completion rate below 100% means users cannot complete critical business processes.

## Value

Transaction tests execute scripted multi-step user workflows (login, navigate, submit form, verify result). Completion rate below 100% means users cannot complete critical business processes.

## Implementation

Create Transaction tests in ThousandEyes using Selenium-based scripted workflows that simulate real user journeys. The OTel metric `web.transaction.completion` reports 100% on success and 0% on error. `web.transaction.errors.count` returns 1 when an error occurs and 0 otherwise. The Splunk App Application dashboard includes a "Transaction Completion (%)" panel.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco ThousandEyes App for Splunk` (Splunkbase 7719).
• Ensure the following data sources are available: `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics (Transaction tests).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Create Transaction tests in ThousandEyes using Selenium-based scripted workflows that simulate real user journeys. The OTel metric `web.transaction.completion` reports 100% on success and 0% on error. `web.transaction.errors.count` returns 1 when an error occurs and 0 otherwise. The Splunk App Application dashboard includes a "Transaction Completion (%)" panel.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
`stream_index` thousandeyes.test.type="web-transactions"
| stats avg(web.transaction.completion) as avg_completion sum(web.transaction.errors.count) as total_errors by thousandeyes.test.name
| where avg_completion < 100 OR total_errors > 0
| sort avg_completion
```

Understanding this SPL

**Transaction Test Completion Rate (ThousandEyes)** — Transaction tests execute scripted multi-step user workflows (login, navigate, submit form, verify result). Completion rate below 100% means users cannot complete critical business processes.

Documented **Data sources**: `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics (Transaction tests). **App/TA** (typical add-on context): `Cisco ThousandEyes App for Splunk` (Splunkbase 7719). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

**Pipeline walkthrough**

• Invokes macro `stream_index` — in Search, use the UI or expand to inspect the underlying SPL.
• `stats` rolls up events into metrics; results are split **by thousandeyes.test.name** so each row reflects one combination of those dimensions.
• Filters the current rows with `where avg_completion < 100 OR total_errors > 0` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Compare the same tests and time window in the Cisco ThousandEyes App for Splunk dashboard or the test view at app.thousandeyes.com so Splunk’s metrics and states match the vendor. If they disagree, check streaming or HEC inputs, macros, and API or token health before retuning.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Single value (completion %), Line chart (completion over time), Table (test, completion, errors).

Scripted input (generic example)
This use case relies on a scripted input. In the app's local/inputs.conf add a stanza such as:

```ini
[script://$SPLUNK_HOME/etc/apps/YourApp/bin/collect.sh]
interval = 300
sourcetype = your_sourcetype
index = main
disabled = 0
```

The script should print one event per line (e.g. key=value). Example minimal script (bash):

```bash
#!/usr/bin/env bash
# Output metrics or events, one per line
echo "metric=value timestamp=$(date +%s)"
```

For full details (paths, scheduling, permissions), see the Implementation guide: docs/implementation-guide.md

## SPL

```spl
`stream_index` thousandeyes.test.type="web-transactions"
| stats avg(web.transaction.completion) as avg_completion sum(web.transaction.errors.count) as total_errors by thousandeyes.test.name
| where avg_completion < 100 OR total_errors > 0
| sort avg_completion
```

## Visualization

Single value (completion %), Line chart (completion over time), Table (test, completion, errors).

## References

- [Splunkbase app 7719](https://splunkbase.splunk.com/app/7719)
