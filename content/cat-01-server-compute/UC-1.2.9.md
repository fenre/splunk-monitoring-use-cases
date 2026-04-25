<!-- AUTO-GENERATED from UC-1.2.9.json — DO NOT EDIT -->

---
id: "1.2.9"
title: "Windows Update Compliance"
criticality: "medium"
splunkPillar: "Security"
---

# UC-1.2.9 · Windows Update Compliance

## Description

Unpatched systems are primary attack vectors. Tracking patch compliance across the fleet supports vulnerability management and regulatory requirements.

## Value

Patch evidence supports security and audit conversations with a defensible per-host view, not a dashboard guess.

## Implementation

Forward System event logs. EventCode 19 = successful update install. Create scripted input running `Get-HotFix` for comprehensive view. Dashboard showing days since last patch per host, flagging >30 days.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`, custom scripted input.
• Ensure the following data sources are available: `sourcetype=WinEventLog:System` (Event ID 19/20/43), WSUS logs, or scripted input.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Forward System event logs. EventCode 19 = successful update install. Create scripted input running `Get-HotFix` for comprehensive view. Dashboard showing days since last patch per host, flagging >30 days.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog sourcetype="WinEventLog:System" EventCode=19
| rex "(?<kb_article>KB\d+)"
| stats latest(_time) as last_update, count as updates_installed by host
| eval days_since_update = round((now() - last_update) / 86400, 0)
| where days_since_update > 30
| sort -days_since_update
```

Understanding this SPL

**Windows Update Compliance** — Unpatched systems are primary attack vectors. Tracking patch compliance across the fleet supports vulnerability management and regulatory requirements.

Documented **Data sources**: `sourcetype=WinEventLog:System` (Event ID 19/20/43), WSUS logs, or scripted input. **App/TA** (typical add-on context): `Splunk_TA_windows`, custom scripted input. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog; **sourcetype**: WinEventLog:System. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog, sourcetype="WinEventLog:System". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Extracts fields with `rex` (regular expression).
• `stats` rolls up events into metrics; results are split **by host** so each row reflects one combination of those dimensions.
• `eval` defines or adjusts **days_since_update** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where days_since_update > 30` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Change where nodename=Change.All_Changes
  by All_Changes.dest span=1d
| where count>=0
```

Understanding this CIM / accelerated SPL

CIM tstats is an approximate mirror when Windows TA field extractions and CIM tags are complete. Enable the matching data model acceleration or tstats may return no rows.



Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (host, last update, days since), Bar chart (compliance %), Heatmap by team/location.

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
index=wineventlog sourcetype="WinEventLog:System" EventCode=19
| rex "(?<kb_article>KB\d+)"
| stats latest(_time) as last_update, count as updates_installed by host
| eval days_since_update = round((now() - last_update) / 86400, 0)
| where days_since_update > 30
| sort -days_since_update
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Change where nodename=Change.All_Changes
  by All_Changes.dest span=1d
| where count>=0
```

## Visualization

Table (host, last update, days since), Bar chart (compliance %), Heatmap by team/location.

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
