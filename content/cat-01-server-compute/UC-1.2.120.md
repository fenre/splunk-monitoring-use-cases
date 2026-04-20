---
id: "1.2.120"
title: "BitLocker Recovery & Compliance Monitoring"
criticality: "high"
splunkPillar: "Security"
---

# UC-1.2.120 · BitLocker Recovery & Compliance Monitoring

## Description

BitLocker protects data at rest. Monitoring recovery events detects unauthorized hardware changes, and compliance tracking ensures all endpoints are encrypted.

## Value

BitLocker protects data at rest. Monitoring recovery events detects unauthorized hardware changes, and compliance tracking ensures all endpoints are encrypted.

## Implementation

Monitor BitLocker Management log for encryption status changes. Protection off (770) may indicate maintenance or attack — correlate with change tickets. Volume recovery (773) means the recovery key was needed — investigate hardware changes or TPM issues. Track recovery password backup to AD (776) for compliance. Run a scripted input querying `manage-bde -status` for real-time encryption state across all volumes. Alert on any protection suspension on servers.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=WinEventLog:Microsoft-Windows-BitLocker/BitLocker Management` (EventCode 770, 771, 773, 774, 775).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Monitor BitLocker Management log for encryption status changes. Protection off (770) may indicate maintenance or attack — correlate with change tickets. Volume recovery (773) means the recovery key was needed — investigate hardware changes or TPM issues. Track recovery password backup to AD (776) for compliance. Run a scripted input querying `manage-bde -status` for real-time encryption state across all volumes. Alert on any protection suspension on servers.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog source="*BitLocker*" EventCode IN (770, 771, 773, 774, 775, 776, 778)
| eval Status=case(EventCode=770,"Protection_Off", EventCode=771,"Protection_Resumed", EventCode=773,"Volume_Recovery", EventCode=774,"Key_Rotated", EventCode=775,"Auto_Unlock_Enabled", EventCode=776,"Recovery_Password_Backup", EventCode=778,"TPM_Error", 1=1,"Other")
| stats count by host, Status, VolumeName
| sort -count
```

Understanding this SPL

**BitLocker Recovery & Compliance Monitoring** — BitLocker protects data at rest. Monitoring recovery events detects unauthorized hardware changes, and compliance tracking ensures all endpoints are encrypted.

Documented **Data sources**: `sourcetype=WinEventLog:Microsoft-Windows-BitLocker/BitLocker Management` (EventCode 770, 771, 773, 774, 775). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **Status** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by host, Status, VolumeName** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Dashboard (encryption compliance %), Table (events), Alert on protection suspension.

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
index=wineventlog source="*BitLocker*" EventCode IN (770, 771, 773, 774, 775, 776, 778)
| eval Status=case(EventCode=770,"Protection_Off", EventCode=771,"Protection_Resumed", EventCode=773,"Volume_Recovery", EventCode=774,"Key_Rotated", EventCode=775,"Auto_Unlock_Enabled", EventCode=776,"Recovery_Password_Backup", EventCode=778,"TPM_Error", 1=1,"Other")
| stats count by host, Status, VolumeName
| sort -count
```

## Visualization

Dashboard (encryption compliance %), Table (events), Alert on protection suspension.

## References

- [Monitor BitLocker Management log for encryption status changes. Protection off](https://splunkbase.splunk.com/app/770)
- [correlate with change tickets. Volume recovery](https://splunkbase.splunk.com/app/773)
