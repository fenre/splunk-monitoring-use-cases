<!-- AUTO-GENERATED from UC-2.2.4.json — DO NOT EDIT -->

---
id: "2.2.4"
title: "Live Migration Tracking"
criticality: "low"
splunkPillar: "Observability"
---

# UC-2.2.4 · Live Migration Tracking

## Description

Audit trail for VM mobility. Excessive live migrations may indicate cluster imbalance or storage issues.

## Value

Audit trail for VM mobility. Excessive live migrations may indicate cluster imbalance or storage issues.

## Implementation

Collected via standard Hyper-V event log monitoring. Create an audit report. Alert on migration failures or excessive frequency.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows` (Hyper-V).
• Ensure the following data sources are available: `sourcetype=WinEventLog:Microsoft-Windows-Hyper-V-VMMS-Admin`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Collected via standard Hyper-V event log monitoring. Create an audit report. Alert on migration failures or excessive frequency.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog sourcetype="WinEventLog:Microsoft-Windows-Hyper-V-VMMS-Admin" "migration" ("completed" OR "started")
| rex "Virtual machine '(?<vm_name>[^']+)'"
| table _time host vm_name Message
| sort -_time
```

Understanding this SPL

**Live Migration Tracking** — Audit trail for VM mobility. Excessive live migrations may indicate cluster imbalance or storage issues.

Documented **Data sources**: `sourcetype=WinEventLog:Microsoft-Windows-Hyper-V-VMMS-Admin`. **App/TA** (typical add-on context): `Splunk_TA_windows` (Hyper-V). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog; **sourcetype**: WinEventLog:Microsoft-Windows-Hyper-V-VMMS-Admin. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog, sourcetype="WinEventLog:Microsoft-Windows-Hyper-V-VMMS-Admin". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Extracts fields with `rex` (regular expression).
• Pipeline stage (see **Live Migration Tracking**): table _time host vm_name Message
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (timeline), Count by host/day.

## SPL

```spl
index=wineventlog sourcetype="WinEventLog:Microsoft-Windows-Hyper-V-VMMS-Admin" "migration" ("completed" OR "started")
| rex "Virtual machine '(?<vm_name>[^']+)'"
| table _time host vm_name Message
| sort -_time
```

## Visualization

Table (timeline), Count by host/day.

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
