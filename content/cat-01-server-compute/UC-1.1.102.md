---
id: "1.1.102"
title: "EDAC Memory Error Tracking"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-1.1.102 · EDAC Memory Error Tracking

## Description

EDAC memory errors indicate hardware failures predicting imminent memory or system failure.

## Value

EDAC memory errors indicate hardware failures predicting imminent memory or system failure.

## Implementation

Monitor EDAC (Error Detection and Correction) and MCE (Machine Check Exception) logs. Create immediate alerts on memory errors with escalation to hardware team for memory replacement.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_nix, custom scripted input`.
• Ensure the following data sources are available: `sourcetype=syslog, EDAC kernel driver logs`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Monitor EDAC (Error Detection and Correction) and MCE (Machine Check Exception) logs. Create immediate alerts on memory errors with escalation to hardware team for memory replacement.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=syslog "EDAC" OR "MCE" ("error" OR "correctable" OR "uncorrectable")
| stats count by host, error_type
| where count > 0
```

Understanding this SPL

**EDAC Memory Error Tracking** — EDAC memory errors indicate hardware failures predicting imminent memory or system failure.

Documented **Data sources**: `sourcetype=syslog, EDAC kernel driver logs`. **App/TA** (typical add-on context): `Splunk_TA_nix, custom scripted input`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: syslog. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=os, sourcetype=syslog. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host, error_type** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where count > 0` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Alert, Table

## SPL

```spl
index=os sourcetype=syslog "EDAC" OR "MCE" ("error" OR "correctable" OR "uncorrectable")
| stats count by host, error_type
| where count > 0
```

## Visualization

Alert, Table

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
