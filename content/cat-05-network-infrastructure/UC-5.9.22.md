---
id: "5.9.22"
title: "Local Agent Issue Monitoring"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.9.22 · Local Agent Issue Monitoring

## Description

Detects when the source of a test failure is the agent itself (local network, DNS, or connectivity issue at the agent location), preventing false attribution of problems to the destination service.

## Value

Detects when the source of a test failure is the agent itself (local network, DNS, or connectivity issue at the agent location), preventing false attribution of problems to the destination service.

## Implementation

"Local Agent Issue" events indicate that the test failure originated at the agent's local environment, not the remote target. These help filter out false positives in outage detection. Correlate with agent health data to identify sites with recurring local problems.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco ThousandEyes App for Splunk` (Splunkbase 7719).
• Ensure the following data sources are available: `index=thousandeyes`, ThousandEyes Event API.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
"Local Agent Issue" events indicate that the test failure originated at the agent's local environment, not the remote target. These help filter out false positives in outage detection. Correlate with agent health data to identify sites with recurring local problems.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
`event_index` type="Local Agent Issue"
| stats count by severity, state
| sort -count
```

Understanding this SPL

**Local Agent Issue Monitoring** — Detects when the source of a test failure is the agent itself (local network, DNS, or connectivity issue at the agent location), preventing false attribution of problems to the destination service.

Documented **Data sources**: `index=thousandeyes`, ThousandEyes Event API. **App/TA** (typical add-on context): `Cisco ThousandEyes App for Splunk` (Splunkbase 7719). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

**Pipeline walkthrough**

• Invokes macro `event_index` — in Search, use the UI or expand to inspect the underlying SPL.
• `stats` rolls up events into metrics; results are split **by severity, state** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Events timeline, Table by agent, Single value (active local issues).

## SPL

```spl
`event_index` type="Local Agent Issue"
| stats count by severity, state
| sort -count
```

## Visualization

Events timeline, Table by agent, Single value (active local issues).

## References

- [Splunkbase app 7719](https://splunkbase.splunk.com/app/7719)
