<!-- AUTO-GENERATED from UC-1.1.114.json — DO NOT EDIT -->

---
id: "1.1.114"
title: "Open File Handle Per-Process Monitoring"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-1.1.114 · Open File Handle Per-Process Monitoring

## Description

High open file handle counts per process can exhaust system limits causing application failures.

## Value

High open file handle counts per process can exhaust system limits causing application failures.

## Implementation

Use Splunk_TA_nix lsof input to track open files per process. Create alerts for processes approaching system limit. Include breakdown of file types (sockets, regular files, pipes).

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_nix`.
• Ensure the following data sources are available: `sourcetype=lsof`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Use Splunk_TA_nix lsof input to track open files per process. Create alerts for processes approaching system limit. Include breakdown of file types (sockets, regular files, pipes).

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=lsof host=*
| stats count as open_files by host, process, pid
| where open_files > 1000
```

Understanding this SPL

**Open File Handle Per-Process Monitoring** — High open file handle counts per process can exhaust system limits causing application failures.

Documented **Data sources**: `sourcetype=lsof`. **App/TA** (typical add-on context): `Splunk_TA_nix`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: lsof. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=os, sourcetype=lsof. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host, process, pid** so each row reflects one combination of those dimensions.
• Filters the current rows with `where open_files > 1000` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table, Gauge

## SPL

```spl
index=os sourcetype=lsof host=*
| stats count as open_files by host, process, pid
| where open_files > 1000
```

## Visualization

Table, Gauge

## References

- [Splunk_TA_nix](https://splunkbase.splunk.com/app/833)
