---
id: "1.2.72"
title: "WinRM / Remote PowerShell Connections"
criticality: "high"
splunkPillar: "Security"
---

# UC-1.2.72 · WinRM / Remote PowerShell Connections

## Description

WinRM enables remote command execution via PowerShell Remoting. Monitoring inbound WinRM sessions detects lateral movement and unauthorized remote management.

## Value

WinRM enables remote command execution via PowerShell Remoting. Monitoring inbound WinRM sessions detects lateral movement and unauthorized remote management.

## Implementation

Enable WinRM Operational log on all servers. EventCode 6/91=new WinRM session established, 161=authentication failure. Baseline expected WinRM sources (jump servers, SCCM, monitoring tools). Alert on WinRM sessions from non-authorized IPs or workstations. In restricted environments, consider disabling WinRM on servers that don't require it. Correlate with PowerShell Script Block Logging for full command visibility.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=WinEventLog:Microsoft-Windows-WinRM/Operational` (EventCode 6, 91, 161).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable WinRM Operational log on all servers. EventCode 6/91=new WinRM session established, 161=authentication failure. Baseline expected WinRM sources (jump servers, SCCM, monitoring tools). Alert on WinRM sessions from non-authorized IPs or workstations. In restricted environments, consider disabling WinRM on servers that don't require it. Correlate with PowerShell Script Block Logging for full command visibility.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog source="WinEventLog:Microsoft-Windows-WinRM/Operational"
  EventCode IN (6, 91, 161)
| eval action=case(EventCode=6,"Session created",EventCode=91,"Session created (user)",EventCode=161,"Auth failed")
| stats count by host, action, User, IpAddress
| sort -count
```

Understanding this SPL

**WinRM / Remote PowerShell Connections** — WinRM enables remote command execution via PowerShell Remoting. Monitoring inbound WinRM sessions detects lateral movement and unauthorized remote management.

Documented **Data sources**: `sourcetype=WinEventLog:Microsoft-Windows-WinRM/Operational` (EventCode 6, 91, 161). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **action** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by host, action, User, IpAddress** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (WinRM sessions by source), Network graph (source→dest), Timeline, Bar chart (sessions per host).

## SPL

```spl
index=wineventlog source="WinEventLog:Microsoft-Windows-WinRM/Operational"
  EventCode IN (6, 91, 161)
| eval action=case(EventCode=6,"Session created",EventCode=91,"Session created (user)",EventCode=161,"Auth failed")
| stats count by host, action, User, IpAddress
| sort -count
```

## Visualization

Table (WinRM sessions by source), Network graph (source→dest), Timeline, Bar chart (sessions per host).

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
