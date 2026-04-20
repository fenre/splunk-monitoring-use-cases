---
id: "1.2.81"
title: "SMBv1 Usage Detection"
criticality: "high"
splunkPillar: "Observability"
---

# UC-1.2.81 · SMBv1 Usage Detection

## Description

SMBv1 is vulnerable to EternalBlue and WannaCry. Detecting remaining SMBv1 traffic identifies systems that need upgrading or have SMBv1 re-enabled.

## Value

SMBv1 is vulnerable to EternalBlue and WannaCry. Detecting remaining SMBv1 traffic identifies systems that need upgrading or have SMBv1 re-enabled.

## Implementation

Enable SMB1 audit logging via `Set-SmbServerConfiguration -AuditSmb1Access $true`. EventCode 3000 logs each SMBv1 connection with the client name. Identify all clients still using SMBv1, then upgrade or remediate before disabling SMBv1 entirely. Alert on any new SMBv1 access after remediation is complete. MS17-010 (EternalBlue) affects unpatched SMBv1 systems.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=WinEventLog:Microsoft-Windows-SMBServer/Audit` (EventCode 3000).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable SMB1 audit logging via `Set-SmbServerConfiguration -AuditSmb1Access $true`. EventCode 3000 logs each SMBv1 connection with the client name. Identify all clients still using SMBv1, then upgrade or remediate before disabling SMBv1 entirely. Alert on any new SMBv1 access after remediation is complete. MS17-010 (EternalBlue) affects unpatched SMBv1 systems.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog source="WinEventLog:Microsoft-Windows-SMBServer/Audit" EventCode=3000
| stats count values(ClientName) as clients dc(ClientName) as client_count by host
| sort -client_count
```

Understanding this SPL

**SMBv1 Usage Detection** — SMBv1 is vulnerable to EternalBlue and WannaCry. Detecting remaining SMBv1 traffic identifies systems that need upgrading or have SMBv1 re-enabled.

Documented **Data sources**: `sourcetype=WinEventLog:Microsoft-Windows-SMBServer/Audit` (EventCode 3000). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (SMBv1 clients), Bar chart (clients per server), Single value (total SMBv1 connections — target: 0).

## SPL

```spl
index=wineventlog source="WinEventLog:Microsoft-Windows-SMBServer/Audit" EventCode=3000
| stats count values(ClientName) as clients dc(ClientName) as client_count by host
| sort -client_count
```

## Visualization

Table (SMBv1 clients), Bar chart (clients per server), Single value (total SMBv1 connections — target: 0).

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
