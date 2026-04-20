---
id: "1.2.79"
title: "Sysmon DNS Query Logging"
criticality: "medium"
splunkPillar: "Security"
---

# UC-1.2.79 · Sysmon DNS Query Logging

## Description

Per-process DNS query logging reveals which applications communicate with which domains. Detects DGA, C2 callbacks, and data exfiltration at the endpoint level.

## Value

Per-process DNS query logging reveals which applications communicate with which domains. Detects DGA, C2 callbacks, and data exfiltration at the endpoint level.

## Implementation

Deploy Sysmon v10+ with DNS query logging (EventCode 22). Each event records the process that made the DNS query and the resolved domain. Filter out known-good domains. Alert on processes with high unique domain counts (DGA indicator), processes that normally don't make DNS queries (LOLBin abuse), or queries to known-bad domains (threat intel lookup). Lower volume than network-level DNS logging since it's per-endpoint.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`, Sysmon required.
• Ensure the following data sources are available: `sourcetype=WinEventLog:Microsoft-Windows-Sysmon/Operational` (EventCode 22).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Deploy Sysmon v10+ with DNS query logging (EventCode 22). Each event records the process that made the DNS query and the resolved domain. Filter out known-good domains. Alert on processes with high unique domain counts (DGA indicator), processes that normally don't make DNS queries (LOLBin abuse), or queries to known-bad domains (threat intel lookup). Lower volume than network-level DNS logging since it's per-endpoint.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog sourcetype="WinEventLog:Microsoft-Windows-Sysmon/Operational" EventCode=22
| where NOT match(QueryName, "(?i)(microsoft\.com|windowsupdate\.com|office\.com|bing\.com|msftconnecttest)")
| stats count dc(QueryName) as unique_domains by Image, host
| where unique_domains > 100
| sort -unique_domains
```

Understanding this SPL

**Sysmon DNS Query Logging** — Per-process DNS query logging reveals which applications communicate with which domains. Detects DGA, C2 callbacks, and data exfiltration at the endpoint level.

Documented **Data sources**: `sourcetype=WinEventLog:Microsoft-Windows-Sysmon/Operational` (EventCode 22). **App/TA** (typical add-on context): `Splunk_TA_windows`, Sysmon required. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog; **sourcetype**: WinEventLog:Microsoft-Windows-Sysmon/Operational. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog, sourcetype="WinEventLog:Microsoft-Windows-Sysmon/Operational". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where NOT match(QueryName, "(?i)(microsoft\.com|windowsupdate\.com|office\.com|bing\.com|msftconnecttest)")` — typically the threshold or rule expression for this monitoring goal.
• `stats` rolls up events into metrics; results are split **by Image, host** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where unique_domains > 100` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (queries by process), Bar chart (top resolving processes), Sankey diagram (process→domain).

## SPL

```spl
index=wineventlog sourcetype="WinEventLog:Microsoft-Windows-Sysmon/Operational" EventCode=22
| where NOT match(QueryName, "(?i)(microsoft\.com|windowsupdate\.com|office\.com|bing\.com|msftconnecttest)")
| stats count dc(QueryName) as unique_domains by Image, host
| where unique_domains > 100
| sort -unique_domains
```

## Visualization

Table (queries by process), Bar chart (top resolving processes), Sankey diagram (process→domain).

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
