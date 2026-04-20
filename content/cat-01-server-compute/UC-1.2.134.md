---
id: "1.2.134"
title: "Windows Pending Reboot Detection"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-1.2.134 · Windows Pending Reboot Detection

## Description

Detect servers waiting for reboot after Windows updates. Pending reboots cause inconsistent behavior and can block security patch application.

## Value

Detect servers waiting for reboot after Windows updates. Pending reboots cause inconsistent behavior and can block security patch application.

## Implementation

Create a scripted input that checks registry: `HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Component Based Servicing\RebootPending`, `HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\PendingFileRenameOperations`, `HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\WindowsUpdate\Auto Update\RebootRequired`. Set reboot_pending=true if any exist. Run every 60-300 seconds. Report reason (e.g., "Windows Update", "Component Based Servicing"). Include in change management dashboard.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows` (scripted input).
• Ensure the following data sources are available: Registry keys (RebootRequired, PendingFileRenameOperations).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Create a scripted input that checks registry: `HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Component Based Servicing\RebootPending`, `HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\PendingFileRenameOperations`, `HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\WindowsUpdate\Auto Update\RebootRequired`. Set reboot_pending=true if any exist. Run every 60-300 seconds. Report reason (e.g., "Windows Update", "Component Based Servicing"). Include in change management dashboard.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=windows_pending_reboot host=*
| stats latest(reboot_pending) as pending by host
| search pending="true"
| stats count as pending_count
```

Understanding this SPL

**Windows Pending Reboot Detection** — Detect servers waiting for reboot after Windows updates. Pending reboots cause inconsistent behavior and can block security patch application.

Documented **Data sources**: Registry keys (RebootRequired, PendingFileRenameOperations). **App/TA** (typical add-on context): `Splunk_TA_windows` (scripted input). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: windows_pending_reboot. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=os, sourcetype=windows_pending_reboot. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Applies an explicit `search` filter to narrow the current result set.
• `stats` aggregates the pipeline (counts, distinct values, sums, percentiles, etc.) into fewer rows.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (host, pending, reason), Single value (pending reboot count), Pie chart (pending vs. current).

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
index=os sourcetype=windows_pending_reboot host=*
| stats latest(reboot_pending) as pending by host
| search pending="true"
| stats count as pending_count
```

## Visualization

Table (host, pending, reason), Single value (pending reboot count), Pie chart (pending vs. current).

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
