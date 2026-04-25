<!-- AUTO-GENERATED from UC-6.4.2.json — DO NOT EDIT -->

---
id: "6.4.2"
title: "Ransomware Indicator Detection"
criticality: "critical"
splunkPillar: "Security"
---

# UC-6.4.2 · Ransomware Indicator Detection

## Description

Ransomware causes mass file encryption in minutes. Detecting the pattern early can limit damage by triggering automated isolation.

## Value

Ransomware causes mass file encryption in minutes. Detecting the pattern early can limit damage by triggering automated isolation.

## Implementation

Enable file audit logging on critical file shares. Create high-urgency alert for mass file modification patterns (>100 unique files modified by one user in 1 minute). Integrate with SOAR for automated account disable/network isolation.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`, custom alert logic.
• Ensure the following data sources are available: Windows Security Event Log (4663, 4656, 4659 — file create/modify/delete).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable file audit logging on critical file shares. Create high-urgency alert for mass file modification patterns (>100 unique files modified by one user in 1 minute). Integrate with SOAR for automated account disable/network isolation.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode=4663
| bucket _time span=1m
| stats dc(ObjectName) as unique_files count by Account_Name, _time
| where unique_files > 100 AND count > 500
```

Understanding this SPL

**Ransomware Indicator Detection** — Ransomware causes mass file encryption in minutes. Detecting the pattern early can limit damage by triggering automated isolation.

Documented **Data sources**: Windows Security Event Log (4663, 4656, 4659 — file create/modify/delete). **App/TA** (typical add-on context): `Splunk_TA_windows`, custom alert logic. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog; **sourcetype**: WinEventLog:Security. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog, sourcetype="WinEventLog:Security". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Discretizes time or numeric ranges with `bin`/`bucket`.
• `stats` rolls up events into metrics; results are split **by Account_Name, _time** so each row reflects one combination of those dimensions.
• Filters the current rows with `where unique_files > 100 AND count > 500` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Compare the same metric, object name, and interval in the vendor or cloud console (array, backup, or object store) that is the source of truth for this feed.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Pair alerts with the file-server or security team runbook and change calendar. Consider visualizations: Single value (files modified per minute — current), Line chart (modification rate over time), Table (users with anomalous activity).

## SPL

```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode=4663
| bucket _time span=1m
| stats dc(ObjectName) as unique_files count by Account_Name, _time
| where unique_files > 100 AND count > 500
```

## Visualization

Single value (files modified per minute — current), Line chart (modification rate over time), Table (users with anomalous activity).

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
