---
id: "6.4.5"
title: "Large File Transfer Detection"
criticality: "high"
splunkPillar: "Security"
---

# UC-6.4.5 · Large File Transfer Detection

## Description

Unusually large file copies may indicate data exfiltration. Detection supports data loss prevention and insider threat programs.

## Value

Unusually large file copies may indicate data exfiltration. Detection supports data loss prevention and insider threat programs.

## Implementation

Monitor file read events and correlate with SMB session data for volume estimates. Baseline normal transfer patterns per user. Alert when transfers exceed threshold (e.g., >1GB in single session). Correlate with HR/departure lists.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`, network flow data.
• Ensure the following data sources are available: Windows file audit logs, SMB session logs.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Monitor file read events and correlate with SMB session data for volume estimates. Baseline normal transfer patterns per user. Alert when transfers exceed threshold (e.g., >1GB in single session). Correlate with HR/departure lists.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode=4663 AccessMask="0x1"
| stats sum(Size) as total_bytes, dc(ObjectName) as file_count by Account_Name, src
| eval total_gb=round(total_bytes/1024/1024/1024,2)
| where total_gb > 1
| sort -total_gb
```

Understanding this SPL

**Large File Transfer Detection** — Unusually large file copies may indicate data exfiltration. Detection supports data loss prevention and insider threat programs.

Documented **Data sources**: Windows file audit logs, SMB session logs. **App/TA** (typical add-on context): `Splunk_TA_windows`, network flow data. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog; **sourcetype**: WinEventLog:Security. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog, sourcetype="WinEventLog:Security". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by Account_Name, src** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **total_gb** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where total_gb > 1` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (users with large transfers), Bar chart (transfer volume by user), Line chart (daily transfer volume trend).

## SPL

```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode=4663 AccessMask="0x1"
| stats sum(Size) as total_bytes, dc(ObjectName) as file_count by Account_Name, src
| eval total_gb=round(total_bytes/1024/1024/1024,2)
| where total_gb > 1
| sort -total_gb
```

## Visualization

Table (users with large transfers), Bar chart (transfer volume by user), Line chart (daily transfer volume trend).

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
