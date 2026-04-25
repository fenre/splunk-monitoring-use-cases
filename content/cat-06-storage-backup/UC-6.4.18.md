<!-- AUTO-GENERATED from UC-6.4.18.json — DO NOT EDIT -->

---
id: "6.4.18"
title: "File Deletion Volume Anomaly"
criticality: "critical"
splunkPillar: "Security"
---

# UC-6.4.18 · File Deletion Volume Anomaly

## Description

Sudden spike in delete operations may indicate ransomware preparation, malicious insider, or script error. Complements mass-modify ransomware use cases.

## Value

Sudden spike in delete operations may indicate ransomware preparation, malicious insider, or script error. Complements mass-modify ransomware use cases.

## Implementation

Enable auditing on delete for sensitive trees. Baseline deletes per user/share. Alert on statistical outliers. Exclude known maintenance accounts via lookup.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: Event ID 4660 (object deleted), 4663 with Delete access.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable auditing on delete for sensitive trees. Baseline deletes per user/share. Alert on statistical outliers. Exclude known maintenance accounts via lookup.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode IN (4660,4663) AccessMask="*DELETE*"
| bucket _time span=1m
| stats count as deletes by Account_Name, ShareName, _time
| eventstats avg(deletes) as avg_d, stdev(deletes) as stdev_d by Account_Name
| where deletes > avg_d + 4*stdev_d AND deletes > 50
```

Understanding this SPL

**File Deletion Volume Anomaly** — Sudden spike in delete operations may indicate ransomware preparation, malicious insider, or script error. Complements mass-modify ransomware use cases.

Documented **Data sources**: Event ID 4660 (object deleted), 4663 with Delete access. **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog; **sourcetype**: WinEventLog:Security. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog, sourcetype="WinEventLog:Security". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Discretizes time or numeric ranges with `bin`/`bucket`.
• `stats` rolls up events into metrics; results are split **by Account_Name, ShareName, _time** so each row reflects one combination of those dimensions.
• `eventstats` rolls up events into metrics; results are split **by Account_Name** so each row reflects one combination of those dimensions.
• Filters the current rows with `where deletes > avg_d + 4*stdev_d AND deletes > 50` — typically the threshold or rule expression for this monitoring goal.

Step 3 — Validate
Compare the same metric, object name, and interval in the vendor or cloud console (array, backup, or object store) that is the source of truth for this feed.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Pair alerts with the file-server or security team runbook and change calendar. Consider visualizations: Timeline (delete bursts), Table (user, share, delete count), Line chart (deletes per minute).

## SPL

```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode IN (4660,4663) AccessMask="*DELETE*"
| bucket _time span=1m
| stats count as deletes by Account_Name, ShareName, _time
| eventstats avg(deletes) as avg_d, stdev(deletes) as stdev_d by Account_Name
| where deletes > avg_d + 4*stdev_d AND deletes > 50
```

## Visualization

Timeline (delete bursts), Table (user, share, delete count), Line chart (deletes per minute).

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
