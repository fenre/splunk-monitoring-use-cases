---
id: "5.9.23"
title: "Internet Outage Correlation with Internal Alerts"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.9.23 · Internet Outage Correlation with Internal Alerts

## Description

Correlating ThousandEyes outage events with internal monitoring alerts enables rapid determination of whether an issue is caused by an external internet problem or an internal infrastructure failure, significantly reducing MTTR.

## Value

Correlating ThousandEyes outage events with internal monitoring alerts enables rapid determination of whether an issue is caused by an external internet problem or an internal infrastructure failure, significantly reducing MTTR.

## Implementation

This correlation use case combines ThousandEyes outage events with internal alerting systems (ITSI episodes, Splunk alerts, or ServiceNow incidents). When a ThousandEyes "Network Outage" event is active and aligns with internal service degradation, the root cause is likely external. Adjust the join logic to match your naming conventions.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco ThousandEyes App for Splunk` (Splunkbase 7719).
• Ensure the following data sources are available: `index=thousandeyes` (events), plus internal monitoring indexes.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
This correlation use case combines ThousandEyes outage events with internal alerting systems (ITSI episodes, Splunk alerts, or ServiceNow incidents). When a ThousandEyes "Network Outage" event is active and aligns with internal service degradation, the root cause is likely external. Adjust the join logic to match your naming conventions.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
`event_index` type="Network Outage" state="active"
| rename thousandeyes.test.name as test_name
| join type=outer max=1 test_name [
  search index=itsi_tracked_alerts severity="critical"
  | rename service_name as test_name
]
| table _time, type, severity, test_name, service_name, state
| sort -_time
```

Understanding this SPL

**Internet Outage Correlation with Internal Alerts** — Correlating ThousandEyes outage events with internal monitoring alerts enables rapid determination of whether an issue is caused by an external internet problem or an internal infrastructure failure, significantly reducing MTTR.

Documented **Data sources**: `index=thousandeyes` (events), plus internal monitoring indexes. **App/TA** (typical add-on context): `Cisco ThousandEyes App for Splunk` (Splunkbase 7719). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

**Pipeline walkthrough**

• Invokes macro `event_index` — in Search, use the UI or expand to inspect the underlying SPL.
• Renames fields with `rename` for clarity or joins.
• Joins to a subsearch with `join` — set `max=` to match cardinality and avoid silent truncation.
• Pipeline stage (see **Internet Outage Correlation with Internal Alerts**): table _time, type, severity, test_name, service_name, state
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Combined timeline (TE events + internal alerts), Table, Dashboard with dual panels.

## SPL

```spl
`event_index` type="Network Outage" state="active"
| rename thousandeyes.test.name as test_name
| join type=outer max=1 test_name [
  search index=itsi_tracked_alerts severity="critical"
  | rename service_name as test_name
]
| table _time, type, severity, test_name, service_name, state
| sort -_time
```

## Visualization

Combined timeline (TE events + internal alerts), Table, Dashboard with dual panels.

## References

- [Splunkbase app 7719](https://splunkbase.splunk.com/app/7719)
