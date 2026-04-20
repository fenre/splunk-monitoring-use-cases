---
id: "6.4.14"
title: "SMB Share Access Audit"
criticality: "high"
splunkPillar: "Security"
---

# UC-6.4.14 · SMB Share Access Audit

## Description

Summarizes successful and denied access to sensitive shares for insider threat and access reviews. Extends object-level 4663 views with share-level rollups.

## Value

Summarizes successful and denied access to sensitive shares for insider threat and access reviews. Extends object-level 4663 views with share-level rollups.

## Implementation

Enable share auditing on critical shares. Tune volume to avoid noise; focus on privileged groups. Alert on access to “restricted” shares from unexpected subnets via lookup.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: Security Event ID 5140 (share accessed), 4663 for sensitive paths.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable share auditing on critical shares. Tune volume to avoid noise; focus on privileged groups. Alert on access to “restricted” shares from unexpected subnets via lookup.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode=5140
| stats count by Share_Name, Account_Name, ComputerName
| where count > 1000
| sort -count
```

Understanding this SPL

**SMB Share Access Audit** — Summarizes successful and denied access to sensitive shares for insider threat and access reviews. Extends object-level 4663 views with share-level rollups.

Documented **Data sources**: Security Event ID 5140 (share accessed), 4663 for sensitive paths. **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog; **sourcetype**: WinEventLog:Security. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog, sourcetype="WinEventLog:Security". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by Share_Name, Account_Name, ComputerName** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where count > 1000` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (share, user, count), Bar chart (top shares by access count), Heatmap (share × hour).

## SPL

```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode=5140
| stats count by Share_Name, Account_Name, ComputerName
| where count > 1000
| sort -count
```

## Visualization

Table (share, user, count), Bar chart (top shares by access count), Heatmap (share × hour).

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
