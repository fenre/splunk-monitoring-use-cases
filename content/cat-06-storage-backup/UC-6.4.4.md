---
id: "6.4.4"
title: "Share Permission Changes"
criticality: "high"
splunkPillar: "Security"
---

# UC-6.4.4 · Share Permission Changes

## Description

Unauthorized permission changes can expose sensitive data. Change detection supports compliance and security posture.

## Value

Unauthorized permission changes can expose sensitive data. Change detection supports compliance and security posture.

## Implementation

Enable "Audit Policy Change" and "Audit File System" via GPO. Forward Security events from file servers. Alert on any permission change to critical shares. Correlate with change management tickets.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: Windows Security Event Log (Event IDs 4670 — permissions changed, 5143 — share modified).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable "Audit Policy Change" and "Audit File System" via GPO. Forward Security events from file servers. Alert on any permission change to critical shares. Correlate with change management tickets.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode=4670 OR EventCode=5143
| table _time, Account_Name, ObjectName, ObjectServer, ProcessName
| sort -_time
```

Understanding this SPL

**Share Permission Changes** — Unauthorized permission changes can expose sensitive data. Change detection supports compliance and security posture.

Documented **Data sources**: Windows Security Event Log (Event IDs 4670 — permissions changed, 5143 — share modified). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog; **sourcetype**: WinEventLog:Security. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog, sourcetype="WinEventLog:Security". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Pipeline stage (see **Share Permission Changes**): table _time, Account_Name, ObjectName, ObjectServer, ProcessName
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (permission changes with details), Timeline (change events), Bar chart (changes by user).

## SPL

```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode=4670 OR EventCode=5143
| table _time, Account_Name, ObjectName, ObjectServer, ProcessName
| sort -_time
```

## Visualization

Table (permission changes with details), Timeline (change events), Bar chart (changes by user).

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
