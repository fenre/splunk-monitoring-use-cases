---
id: "1.2.56"
title: "Sysmon Network Connection Monitoring"
criticality: "high"
splunkPillar: "Security"
---

# UC-1.2.56 · Sysmon Network Connection Monitoring

## Description

Sysmon EventCode 3 logs every outbound TCP/UDP connection with the originating process. Reveals C2 callbacks, data exfiltration, and unauthorized network access.

## Value

Sysmon EventCode 3 logs every outbound TCP/UDP connection with the originating process. Reveals C2 callbacks, data exfiltration, and unauthorized network access.

## Implementation

Deploy Sysmon with network connection logging (EventCode 3, Initiated=true for outbound). Filter RFC1918 addresses to focus on external connections. High unique destination IPs from a single process suggest scanning or C2 beaconing. Alert on processes making external connections that normally shouldn't (e.g., winword.exe, excel.exe connecting outbound). Combine with DNS logs for full picture.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`, Sysmon required.
• Ensure the following data sources are available: `sourcetype=WinEventLog:Microsoft-Windows-Sysmon/Operational` (EventCode 3).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Deploy Sysmon with network connection logging (EventCode 3, Initiated=true for outbound). Filter RFC1918 addresses to focus on external connections. High unique destination IPs from a single process suggest scanning or C2 beaconing. Alert on processes making external connections that normally shouldn't (e.g., winword.exe, excel.exe connecting outbound). Combine with DNS logs for full picture.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog sourcetype="WinEventLog:Microsoft-Windows-Sysmon/Operational" EventCode=3
  Initiated="true"
| where NOT cidrmatch("10.0.0.0/8", DestinationIp) AND NOT cidrmatch("172.16.0.0/12", DestinationIp) AND NOT cidrmatch("192.168.0.0/16", DestinationIp)
| stats count dc(DestinationIp) as unique_ips by Image, host, User
| where unique_ips > 50 OR count > 500
| sort -unique_ips
```

Understanding this SPL

**Sysmon Network Connection Monitoring** — Sysmon EventCode 3 logs every outbound TCP/UDP connection with the originating process. Reveals C2 callbacks, data exfiltration, and unauthorized network access.

Documented **Data sources**: `sourcetype=WinEventLog:Microsoft-Windows-Sysmon/Operational` (EventCode 3). **App/TA** (typical add-on context): `Splunk_TA_windows`, Sysmon required. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog; **sourcetype**: WinEventLog:Microsoft-Windows-Sysmon/Operational. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog, sourcetype="WinEventLog:Microsoft-Windows-Sysmon/Operational". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where NOT cidrmatch("10.0.0.0/8", DestinationIp) AND NOT cidrmatch("172.16.0.0/12", DestinationIp) AND NOT cidrmatch("192.1…` — typically the threshold or rule expression for this monitoring goal.
• `stats` rolls up events into metrics; results are split **by Image, host, User** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where unique_ips > 50 OR count > 500` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (outbound connections by process), Network graph, Timechart (connection rate).

## SPL

```spl
index=wineventlog sourcetype="WinEventLog:Microsoft-Windows-Sysmon/Operational" EventCode=3
  Initiated="true"
| where NOT cidrmatch("10.0.0.0/8", DestinationIp) AND NOT cidrmatch("172.16.0.0/12", DestinationIp) AND NOT cidrmatch("192.168.0.0/16", DestinationIp)
| stats count dc(DestinationIp) as unique_ips by Image, host, User
| where unique_ips > 50 OR count > 500
| sort -unique_ips
```

## Visualization

Table (outbound connections by process), Network graph, Timechart (connection rate).

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
