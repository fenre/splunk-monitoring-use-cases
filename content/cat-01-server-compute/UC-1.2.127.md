<!-- AUTO-GENERATED from UC-1.2.127.json — DO NOT EDIT -->

---
id: "1.2.127"
title: "Automatic Windows Update Compliance"
criticality: "high"
splunkPillar: "Security"
---

# UC-1.2.127 · Automatic Windows Update Compliance

## Description

Unpatched systems are the primary attack surface. Tracking Windows Update status across all systems ensures timely patching and compliance reporting.

## Value

Stale patch state is how most large incidents start. Making update success, failure, and age visible per host supports both vulnerability risk and audit questions on build standards.

## Implementation

Monitor Windows Update Client Operational log. Track successful installs (19), failed installs (20), restart required (25), download failures (31). Calculate days since last successful update for each host. Alert on: systems not updated in 30+ days, repeated installation failures, and systems stuck in "restart required" state. Supplement with `wmic qfe list` scripted input for installed KB inventory. Essential for vulnerability management and audit compliance.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=WinEventLog:Microsoft-Windows-WindowsUpdateClient/Operational`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Monitor Windows Update Client Operational log. Track successful installs (19), failed installs (20), restart required (25), download failures (31). Calculate days since last successful update for each host. Alert on: systems not updated in 30+ days, repeated installation failures, and systems stuck in "restart required" state. Supplement with `wmic qfe list` scripted input for installed KB inventory. Essential for vulnerability management and audit compliance.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog source="WinEventLog:Microsoft-Windows-WindowsUpdateClient/Operational" EventCode IN (19, 20, 25, 31, 35)
| eval Status=case(EventCode=19,"Install_Success", EventCode=20,"Install_Failed", EventCode=25,"Restart_Required", EventCode=31,"Download_Failed", EventCode=35,"Download_Success", 1=1,"Other")
| stats latest(_time) as LastUpdate latest(Status) as LastStatus count(eval(Status="Install_Failed")) as FailCount by host
| eval DaysSinceUpdate=round((now()-LastUpdate)/86400, 0)
| where DaysSinceUpdate>30 OR FailCount>0
| sort -DaysSinceUpdate
```

Understanding this SPL

**Automatic Windows Update Compliance** — Unpatched systems are the primary attack surface. Tracking Windows Update status across all systems ensures timely patching and compliance reporting.

Documented **Data sources**: `sourcetype=WinEventLog:Microsoft-Windows-WindowsUpdateClient/Operational`. **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **Status** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by host** so each row reflects one combination of those dimensions.
• `eval` defines or adjusts **DaysSinceUpdate** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where DaysSinceUpdate>30 OR FailCount>0` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (compliance status), Single value (% compliant), Bar chart (days since update).

Scripted input (generic example)
This use case relies on a scripted input. In the app's local/inputs.conf add a stanza such as:

```ini
[script://$SPLUNK_HOME/etc/apps/YourApp/bin/collect.sh]
interval = 300
sourcetype = your_sourcetype
index = main
disabled = 0
```

The script should print one event per line (e.g. key=value). Example minimal script (bash):

```bash
#!/usr/bin/env bash
# Output metrics or events, one per line
echo "metric=value timestamp=$(date +%s)"
```

For full details (paths, scheduling, permissions), see the Implementation guide: docs/implementation-guide.md

## SPL

```spl
index=wineventlog source="WinEventLog:Microsoft-Windows-WindowsUpdateClient/Operational" EventCode IN (19, 20, 25, 31, 35)
| eval Status=case(EventCode=19,"Install_Success", EventCode=20,"Install_Failed", EventCode=25,"Restart_Required", EventCode=31,"Download_Failed", EventCode=35,"Download_Success", 1=1,"Other")
| stats latest(_time) as LastUpdate latest(Status) as LastStatus count(eval(Status="Install_Failed")) as FailCount by host
| eval DaysSinceUpdate=round((now()-LastUpdate)/86400, 0)
| where DaysSinceUpdate>30 OR FailCount>0
| sort -DaysSinceUpdate
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  by All_Changes.dest span=1d
| where count > 0
```

## Visualization

Table (compliance status), Single value (% compliant), Bar chart (days since update).

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
