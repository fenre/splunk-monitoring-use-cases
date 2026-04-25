<!-- AUTO-GENERATED from UC-2.2.13.json — DO NOT EDIT -->

---
id: "2.2.13"
title: "Hyper-V Event Log Error Trending"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-2.2.13 · Hyper-V Event Log Error Trending

## Description

Trending Hyper-V event log errors reveals emerging hardware issues, driver problems, and configuration drift. A sudden increase in VMMS, VMWP, or VID errors often precedes VM failures. Baseline comparison distinguishes noise from genuine problems.

## Value

Trending Hyper-V event log errors reveals emerging hardware issues, driver problems, and configuration drift. A sudden increase in VMMS, VMWP, or VID errors often precedes VM failures. Baseline comparison distinguishes noise from genuine problems.

## Implementation

Collect all Hyper-V event log channels (VMMS-Admin, Worker-Admin, VID-Admin, Hypervisor-Admin). Baseline error rates over 30 days per host. Alert when error count exceeds 2 standard deviations above the mean. Investigate by drilling into specific EventCodes.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows` (Hyper-V).
• Ensure the following data sources are available: `sourcetype=WinEventLog:Microsoft-Windows-Hyper-V-*`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Collect all Hyper-V event log channels (VMMS-Admin, Worker-Admin, VID-Admin, Hypervisor-Admin). Baseline error rates over 30 days per host. Alert when error count exceeds 2 standard deviations above the mean. Investigate by drilling into specific EventCodes.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog sourcetype="WinEventLog:Microsoft-Windows-Hyper-V-*" Type="Error"
| bin _time span=1h
| stats count by _time, host, sourcetype
| eventstats avg(count) as avg_errors, stdev(count) as stdev_errors by host, sourcetype
| eval upper=avg_errors + (2*stdev_errors)
| where count > upper AND count > 5
| table _time, host, sourcetype, count, avg_errors, upper
```

Understanding this SPL

**Hyper-V Event Log Error Trending** — Trending Hyper-V event log errors reveals emerging hardware issues, driver problems, and configuration drift. A sudden increase in VMMS, VMWP, or VID errors often precedes VM failures. Baseline comparison distinguishes noise from genuine problems.

Documented **Data sources**: `sourcetype=WinEventLog:Microsoft-Windows-Hyper-V-*`. **App/TA** (typical add-on context): `Splunk_TA_windows` (Hyper-V). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog; **sourcetype**: WinEventLog:Microsoft-Windows-Hyper-V-*. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog, sourcetype="WinEventLog:Microsoft-Windows-Hyper-V-*". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Discretizes time or numeric ranges with `bin`/`bucket`.
• `stats` rolls up events into metrics; results are split **by _time, host, sourcetype** so each row reflects one combination of those dimensions.
• `eventstats` rolls up events into metrics; results are split **by host, sourcetype** so each row reflects one combination of those dimensions.
• `eval` defines or adjusts **upper** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where count > upper AND count > 5` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Hyper-V Event Log Error Trending**): table _time, host, sourcetype, count, avg_errors, upper

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.

Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (errors over time), Table (anomalous periods), Bar chart (error types).

## SPL

```spl
index=wineventlog sourcetype="WinEventLog:Microsoft-Windows-Hyper-V-*" Type="Error"
| bin _time span=1h
| stats count by _time, host, sourcetype
| eventstats avg(count) as avg_errors, stdev(count) as stdev_errors by host, sourcetype
| eval upper=avg_errors + (2*stdev_errors)
| where count > upper AND count > 5
| table _time, host, sourcetype, count, avg_errors, upper
```

## Visualization

Line chart (errors over time), Table (anomalous periods), Bar chart (error types).

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
