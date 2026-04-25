<!-- AUTO-GENERATED from UC-6.4.16.json — DO NOT EDIT -->

---
id: "6.4.16"
title: "Ransomware File Extension Detection"
criticality: "critical"
splunkPillar: "Security"
---

# UC-6.4.16 · Ransomware File Extension Detection

## Description

Detects mass renames or creates with known ransomware extensions (e.g., `.locked`, `.encrypted`) faster than generic mass-modify heuristics in some campaigns.

## Value

Detects mass renames or creates with known ransomware extensions (e.g., `.locked`, `.encrypted`) faster than generic mass-modify heuristics in some campaigns.

## Implementation

Maintain lookup of ransomware extensions from threat intel. Combine with mass-delete and entropy signals. Integrate SOAR for host isolation.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`, EDR feeds.
• Ensure the following data sources are available: File create/rename events 4663 with ObjectName ending in suspicious extensions.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Maintain lookup of ransomware extensions from threat intel. Combine with mass-delete and entropy signals. Integrate SOAR for host isolation.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode=4663
| rex field=ObjectName "(?i)\.(locked|encrypted|crypt|ryuk|lockbit)(\"|$)"
| stats dc(ObjectName) as files count by Account_Name, host
| where files > 20
```

Understanding this SPL

**Ransomware File Extension Detection** — Detects mass renames or creates with known ransomware extensions (e.g., `.locked`, `.encrypted`) faster than generic mass-modify heuristics in some campaigns.

Documented **Data sources**: File create/rename events 4663 with ObjectName ending in suspicious extensions. **App/TA** (typical add-on context): `Splunk_TA_windows`, EDR feeds. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog; **sourcetype**: WinEventLog:Security. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog, sourcetype="WinEventLog:Security". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Extracts fields with `rex` (regular expression).
• `stats` rolls up events into metrics; results are split **by Account_Name, host** so each row reflects one combination of those dimensions.
• Filters the current rows with `where files > 20` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Compare the same metric, object name, and interval in the vendor or cloud console (array, backup, or object store) that is the source of truth for this feed.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Pair alerts with the file-server or security team runbook and change calendar. Consider visualizations: Table (user, host, files affected), Timeline (detection), Single value (distinct suspicious files).

## SPL

```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode=4663
| rex field=ObjectName "(?i)\.(locked|encrypted|crypt|ryuk|lockbit)(\"|$)"
| stats dc(ObjectName) as files count by Account_Name, host
| where files > 20
```

## Visualization

Table (user, host, files affected), Timeline (detection), Single value (distinct suspicious files).

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
