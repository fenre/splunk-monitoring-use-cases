---
id: "1.2.84"
title: "Sysmon Named Pipe Monitoring"
criticality: "high"
splunkPillar: "Security"
---

# UC-1.2.84 · Sysmon Named Pipe Monitoring

## Description

Named pipes are used for inter-process communication and by tools like Cobalt Strike, Mimikatz, and PsExec. Detecting unusual named pipes reveals C2 and lateral movement.

## Value

Named pipes are used for inter-process communication and by tools like Cobalt Strike, Mimikatz, and PsExec. Detecting unusual named pipes reveals C2 and lateral movement.

## Implementation

Deploy Sysmon with PipeCreated (17) and PipeConnected (18) monitoring. Known malicious pipe names: `MSSE-*` (Metasploit), `msagent_*` (Cobalt Strike), `postex_*` (Cobalt Strike post-exploitation), `status_*` (default Cobalt Strike). Also detect PsExec pipes (`PSEXESVC`). Baseline normal pipes per application role, then alert on anomalies.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`, Sysmon required.
• Ensure the following data sources are available: `sourcetype=WinEventLog:Microsoft-Windows-Sysmon/Operational` (EventCode 17, 18).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Deploy Sysmon with PipeCreated (17) and PipeConnected (18) monitoring. Known malicious pipe names: `MSSE-*` (Metasploit), `msagent_*` (Cobalt Strike), `postex_*` (Cobalt Strike post-exploitation), `status_*` (default Cobalt Strike). Also detect PsExec pipes (`PSEXESVC`). Baseline normal pipes per application role, then alert on anomalies.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog sourcetype="WinEventLog:Microsoft-Windows-Sysmon/Operational"
  EventCode IN (17, 18)
| where match(PipeName, "(?i)(MSSE-|msagent_|postex_|status_|mojo\.|cobaltstrike|beacon)")
| table _time, host, EventCode, PipeName, Image, User
| sort -_time
```

Understanding this SPL

**Sysmon Named Pipe Monitoring** — Named pipes are used for inter-process communication and by tools like Cobalt Strike, Mimikatz, and PsExec. Detecting unusual named pipes reveals C2 and lateral movement.

Documented **Data sources**: `sourcetype=WinEventLog:Microsoft-Windows-Sysmon/Operational` (EventCode 17, 18). **App/TA** (typical add-on context): `Splunk_TA_windows`, Sysmon required. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog; **sourcetype**: WinEventLog:Microsoft-Windows-Sysmon/Operational. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog, sourcetype="WinEventLog:Microsoft-Windows-Sysmon/Operational". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where match(PipeName, "(?i)(MSSE-|msagent_|postex_|status_|mojo\.|cobaltstrike|beacon)")` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Sysmon Named Pipe Monitoring**): table _time, host, EventCode, PipeName, Image, User
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (pipe events), Bar chart (top pipe names), Timeline, Alert on known-bad patterns.

## SPL

```spl
index=wineventlog sourcetype="WinEventLog:Microsoft-Windows-Sysmon/Operational"
  EventCode IN (17, 18)
| where match(PipeName, "(?i)(MSSE-|msagent_|postex_|status_|mojo\.|cobaltstrike|beacon)")
| table _time, host, EventCode, PipeName, Image, User
| sort -_time
```

## Visualization

Table (pipe events), Bar chart (top pipe names), Timeline, Alert on known-bad patterns.

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
