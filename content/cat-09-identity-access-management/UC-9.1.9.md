<!-- AUTO-GENERATED from UC-9.1.9.json — DO NOT EDIT -->

---
id: "9.1.9"
title: "LDAP Query Performance"
criticality: "medium"
splunkPillar: "Security"
---

# UC-9.1.9 · LDAP Query Performance

## Description

Expensive LDAP queries degrade DC performance affecting authentication for all users. Detection enables query optimization.

## Value

Expensive LDAP queries degrade DC performance affecting authentication for all users. Detection enables query optimization.

## Implementation

Enable LDAP search diagnostics (registry key: "15 Field Engineering" value "Expensive Search Results Threshold" = 10000). Forward Directory Service logs. Alert on queries visiting >10K entries. Identify and optimize expensive applications.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`, Directory Service diagnostics.
• Ensure the following data sources are available: Directory Service event log (Event ID 1644 — expensive search), Field Engineering diagnostics.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable LDAP search diagnostics (registry key: "15 Field Engineering" value "Expensive Search Results Threshold" = 10000). Forward Directory Service logs. Alert on queries visiting >10K entries. Identify and optimize expensive applications.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog sourcetype="WinEventLog:Directory Service" EventCode=1644
| rex "Entries Visited\s+:\s+(?<entries_visited>\d+)"
| where entries_visited > 10000
| table _time, ComputerName, entries_visited, Message
```

Understanding this SPL

**LDAP Query Performance** — Expensive LDAP queries degrade DC performance affecting authentication for all users. Detection enables query optimization.

Documented **Data sources**: Directory Service event log (Event ID 1644 — expensive search), Field Engineering diagnostics. **App/TA** (typical add-on context): `Splunk_TA_windows`, Directory Service diagnostics. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog; **sourcetype**: WinEventLog:Directory Service. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog, sourcetype="WinEventLog:Directory Service". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Extracts fields with `rex` (regular expression).
• Filters the current rows with `where entries_visited > 10000` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **LDAP Query Performance**): table _time, ComputerName, entries_visited, Message


Step 3 — Validate
Compare with Event Viewer on domain controllers (or exported Security logs) and with Active Directory Users and Computers for the same objects and time window.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (expensive queries), Bar chart (queries by source application), Line chart (expensive query frequency).

## SPL

```spl
index=wineventlog sourcetype="WinEventLog:Directory Service" EventCode=1644
| rex "Entries Visited\s+:\s+(?<entries_visited>\d+)"
| where entries_visited > 10000
| table _time, ComputerName, entries_visited, Message
```

## Visualization

Table (expensive queries), Bar chart (queries by source application), Line chart (expensive query frequency).

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
