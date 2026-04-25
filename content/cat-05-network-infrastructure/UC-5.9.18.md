<!-- AUTO-GENERATED from UC-5.9.18.json — DO NOT EDIT -->

---
id: "5.9.18"
title: "Network Outage Event Detection"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.9.18 · Network Outage Event Detection

## Description

ThousandEyes Internet Insights uses collective intelligence from billions of daily measurements to automatically detect network outages affecting your services, including outages in ISP and cloud provider networks you do not own.

## Value

ThousandEyes Internet Insights uses collective intelligence from billions of daily measurements to automatically detect network outages affecting your services, including outages in ISP and cloud provider networks you do not own.

## Implementation

Configure the Event input in the Cisco ThousandEyes App with a ThousandEyes user and account group. Update the `event_index` macro to point to the correct index. Events are fetched at a configurable interval via the ThousandEyes API. Event types include "Network Outage", "Network Path Issue", "DNS Issue", "Server Issue", "Proxy Issue", and "Local Agent Issue".

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco ThousandEyes App for Splunk` (Splunkbase 7719).
• Ensure the following data sources are available: `index=thousandeyes`, ThousandEyes Event API.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Configure the Event input in the Cisco ThousandEyes App with a ThousandEyes user and account group. Update the `event_index` macro to point to the correct index. Events are fetched at a configurable interval via the ThousandEyes API. Event types include "Network Outage", "Network Path Issue", "DNS Issue", "Server Issue", "Proxy Issue", and "Local Agent Issue".

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
`event_index` type="Network Outage" OR type="Network Path Issue"
| stats count by type, severity, state
| sort -count
```

Understanding this SPL

**Network Outage Event Detection** — ThousandEyes Internet Insights uses collective intelligence from billions of daily measurements to automatically detect network outages affecting your services, including outages in ISP and cloud provider networks you do not own.

Documented **Data sources**: `index=thousandeyes`, ThousandEyes Event API. **App/TA** (typical add-on context): `Cisco ThousandEyes App for Splunk` (Splunkbase 7719). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

**Pipeline walkthrough**

• Invokes macro `event_index` — in Search, use the UI or expand to inspect the underlying SPL.
• `stats` rolls up events into metrics; results are split **by type, severity, state** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Compare the same tests and time window in the Cisco ThousandEyes App for Splunk dashboard or the test view at app.thousandeyes.com so Splunk’s metrics and states match the vendor. If they disagree, check streaming or HEC inputs, macros, and API or token health before retuning.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Events timeline, Table (type, severity, state, count), Pie chart by severity.

## SPL

```spl
`event_index` type="Network Outage" OR type="Network Path Issue"
| stats count by type, severity, state
| sort -count
```

## Visualization

Events timeline, Table (type, severity, state, count), Pie chart by severity.

## References

- [Splunkbase app 7719](https://splunkbase.splunk.com/app/7719)
