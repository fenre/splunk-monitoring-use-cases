---
id: "1.3.6"
title: "macOS Gatekeeper and XProtect Status"
criticality: "medium"
splunkPillar: "Security"
---

# UC-1.3.6 · macOS Gatekeeper and XProtect Status

## Description

Verify Gatekeeper and XProtect are enabled and definitions are current. Disabled or outdated security controls increase malware risk.

## Value

Verify Gatekeeper and XProtect are enabled and definitions are current. Disabled or outdated security controls increase malware risk.

## Implementation

Create a scripted input that runs `spctl --status` (expect "assessments enabled" for Gatekeeper on). For XProtect, run `system_profiler SPInstallHistoryDataType` and parse XProtect/XProtect Remediator entries, or check `/Library/Apple/System/Library/CoreServices/XProtect.bundle/Contents/version.plist`. Run daily. Alert when Gatekeeper is disabled; alert when XProtect definitions are older than 30 days.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_nix` (scripted input).
• Ensure the following data sources are available: `spctl --status`, `system_profiler SPInstallHistoryDataType`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Create a scripted input that runs `spctl --status` (expect "assessments enabled" for Gatekeeper on). For XProtect, run `system_profiler SPInstallHistoryDataType` and parse XProtect/XProtect Remediator entries, or check `/Library/Apple/System/Library/CoreServices/XProtect.bundle/Contents/version.plist`. Run daily. Alert when Gatekeeper is disabled; alert when XProtect definitions are older than 30 days.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=macos_gatekeeper host=*
| eval xprotect_age_days = now() - strptime(xprotect_date, "%Y-%m-%d")
| where xprotect_age_days > 30
| table host xprotect_ver xprotect_date xprotect_age_days
```

Understanding this SPL

**macOS Gatekeeper and XProtect Status** — Verify Gatekeeper and XProtect are enabled and definitions are current. Disabled or outdated security controls increase malware risk.

Documented **Data sources**: `spctl --status`, `system_profiler SPInstallHistoryDataType`. **App/TA** (typical add-on context): `Splunk_TA_nix` (scripted input). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: macos_gatekeeper. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=os, sourcetype=macos_gatekeeper. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **xprotect_age_days** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where xprotect_age_days > 30` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **macOS Gatekeeper and XProtect Status**): table host xprotect_ver xprotect_date xprotect_age_days


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (host, Gatekeeper status, XProtect version), Single value (non-compliant count), Pie chart (enabled vs. disabled).

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
index=os sourcetype=macos_gatekeeper host=*
| eval xprotect_age_days = now() - strptime(xprotect_date, "%Y-%m-%d")
| where xprotect_age_days > 30
| table host xprotect_ver xprotect_date xprotect_age_days
```

## Visualization

Table (host, Gatekeeper status, XProtect version), Single value (non-compliant count), Pie chart (enabled vs. disabled).

## References

- [Splunk_TA_nix](https://splunkbase.splunk.com/app/833)
