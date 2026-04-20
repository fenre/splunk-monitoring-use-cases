---
id: "1.2.53"
title: "BitLocker Recovery Events"
criticality: "high"
splunkPillar: "Security"
---

# UC-1.2.53 · BitLocker Recovery Events

## Description

BitLocker recovery mode triggers indicate TPM issues, boot configuration changes, or potential tampering with the boot chain. Each event requires investigation.

## Value

BitLocker recovery mode triggers indicate TPM issues, boot configuration changes, or potential tampering with the boot chain. Each event requires investigation.

## Implementation

Forward BitLocker Management and Operational logs. EventCode 768/775=recovery mode (TPM unsealing failed, boot integrity compromised). Common benign triggers: BIOS updates, boot order changes. Alert on recovery events — each one should be correlated with approved change windows. Track EventCode 770 (protection suspended) — ensure it's re-enabled within 24 hours.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=WinEventLog:Microsoft-Windows-BitLocker/BitLocker Management` (EventCode 768, 770, 775, 846).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Forward BitLocker Management and Operational logs. EventCode 768/775=recovery mode (TPM unsealing failed, boot integrity compromised). Common benign triggers: BIOS updates, boot order changes. Alert on recovery events — each one should be correlated with approved change windows. Track EventCode 770 (protection suspended) — ensure it's re-enabled within 24 hours.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog source="WinEventLog:Microsoft-Windows-BitLocker*"
  EventCode IN (768, 770, 775, 846)
| eval issue=case(EventCode=768,"Recovery mode entered",EventCode=770,"Protection suspended",EventCode=775,"Recovery key used",EventCode=846,"Encryption failed")
| table _time, host, issue, VolumeName, RecoveryReason
| sort -_time
```

Understanding this SPL

**BitLocker Recovery Events** — BitLocker recovery mode triggers indicate TPM issues, boot configuration changes, or potential tampering with the boot chain. Each event requires investigation.

Documented **Data sources**: `sourcetype=WinEventLog:Microsoft-Windows-BitLocker/BitLocker Management` (EventCode 768, 770, 775, 846). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **issue** — often to normalize units, derive a ratio, or prepare for thresholds.
• Pipeline stage (see **BitLocker Recovery Events**): table _time, host, issue, VolumeName, RecoveryReason
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (recovery events), Timeline, Single value (unresolved recoveries).

## SPL

```spl
index=wineventlog source="WinEventLog:Microsoft-Windows-BitLocker*"
  EventCode IN (768, 770, 775, 846)
| eval issue=case(EventCode=768,"Recovery mode entered",EventCode=770,"Protection suspended",EventCode=775,"Recovery key used",EventCode=846,"Encryption failed")
| table _time, host, issue, VolumeName, RecoveryReason
| sort -_time
```

## Visualization

Table (recovery events), Timeline, Single value (unresolved recoveries).

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
