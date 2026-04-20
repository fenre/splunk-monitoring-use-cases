---
id: "1.2.111"
title: "Windows Firewall Rule Tampering"
criticality: "critical"
splunkPillar: "Security"
---

# UC-1.2.111 · Windows Firewall Rule Tampering

## Description

Attackers disable or modify firewall rules to enable lateral movement, C2 communication, and data exfiltration. Rule changes outside maintenance windows indicate compromise.

## Value

Attackers disable or modify firewall rules to enable lateral movement, C2 communication, and data exfiltration. Rule changes outside maintenance windows indicate compromise.

## Implementation

Collect Windows Firewall With Advanced Security log. Track rule additions (2004), modifications (2005), deletions (2006), and bulk deletion (2033 — extremely suspicious). Alert on: allow-inbound rules for unusual ports, rules permitting all traffic, rules created by non-admin processes, and any rule changes on servers outside change windows. Correlate with process creation to identify the modifying application.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=WinEventLog:Microsoft-Windows-Windows Firewall With Advanced Security/Firewall` (EventCode 2004, 2005, 2006, 2033).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Collect Windows Firewall With Advanced Security log. Track rule additions (2004), modifications (2005), deletions (2006), and bulk deletion (2033 — extremely suspicious). Alert on: allow-inbound rules for unusual ports, rules permitting all traffic, rules created by non-admin processes, and any rule changes on servers outside change windows. Correlate with process creation to identify the modifying application.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog source="WinEventLog:Microsoft-Windows-Windows Firewall With Advanced Security/Firewall" EventCode IN (2004, 2005, 2006, 2033)
| eval Action=case(EventCode=2004,"Rule_Added", EventCode=2005,"Rule_Modified", EventCode=2006,"Rule_Deleted", EventCode=2033,"All_Rules_Deleted", 1=1,"Other")
| table _time, host, Action, RuleName, ApplicationPath, Direction, Protocol, LocalPort, RemotePort, ModifyingUser
| sort -_time
```

Understanding this SPL

**Windows Firewall Rule Tampering** — Attackers disable or modify firewall rules to enable lateral movement, C2 communication, and data exfiltration. Rule changes outside maintenance windows indicate compromise.

Documented **Data sources**: `sourcetype=WinEventLog:Microsoft-Windows-Windows Firewall With Advanced Security/Firewall` (EventCode 2004, 2005, 2006, 2033). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **Action** — often to normalize units, derive a ratio, or prepare for thresholds.
• Pipeline stage (see **Windows Firewall Rule Tampering**): table _time, host, Action, RuleName, ApplicationPath, Direction, Protocol, LocalPort, RemotePort, ModifyingUser
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (rule changes), Timeline (change frequency), Alert on suspicious modifications.

## SPL

```spl
index=wineventlog source="WinEventLog:Microsoft-Windows-Windows Firewall With Advanced Security/Firewall" EventCode IN (2004, 2005, 2006, 2033)
| eval Action=case(EventCode=2004,"Rule_Added", EventCode=2005,"Rule_Modified", EventCode=2006,"Rule_Deleted", EventCode=2033,"All_Rules_Deleted", 1=1,"Other")
| table _time, host, Action, RuleName, ApplicationPath, Direction, Protocol, LocalPort, RemotePort, ModifyingUser
| sort -_time
```

## Visualization

Table (rule changes), Timeline (change frequency), Alert on suspicious modifications.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
