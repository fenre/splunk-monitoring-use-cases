---
id: "1.2.60"
title: "Code Integrity / Driver Signing Violations"
criticality: "critical"
splunkPillar: "Security"
---

# UC-1.2.60 · Code Integrity / Driver Signing Violations

## Description

Unsigned or tampered drivers loading into the kernel are a rootkit indicator. Code Integrity violations detect bypass attempts and driver-level threats.

## Value

Unsigned or tampered drivers loading into the kernel are a rootkit indicator. Code Integrity violations detect bypass attempts and driver-level threats.

## Implementation

Code Integrity events log automatically on systems with Secure Boot, HVCI, or WDAC. EventCode 3033=unsigned image loaded (audit mode), 3001=unsigned driver blocked (enforcement). Alert on all blocked events in enforcement mode. In audit mode, use data to build a driver whitelist before enabling enforcement. Cross-reference drivers with known-good hashes from Microsoft catalog.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=WinEventLog:Microsoft-Windows-CodeIntegrity/Operational` (EventCode 3001, 3002, 3003, 3004, 3033).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Code Integrity events log automatically on systems with Secure Boot, HVCI, or WDAC. EventCode 3033=unsigned image loaded (audit mode), 3001=unsigned driver blocked (enforcement). Alert on all blocked events in enforcement mode. In audit mode, use data to build a driver whitelist before enabling enforcement. Cross-reference drivers with known-good hashes from Microsoft catalog.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog source="WinEventLog:Microsoft-Windows-CodeIntegrity/Operational"
  EventCode IN (3001, 3002, 3003, 3004, 3033)
| eval issue=case(EventCode=3001,"Unsigned driver blocked",EventCode=3002,"Unable to verify",EventCode=3003,"Unsigned policy",EventCode=3004,"File hash not found",EventCode=3033,"Unsigned image loaded")
| table _time, host, issue, FileNameBuffer, ProcessNameBuffer
| sort -_time
```

Understanding this SPL

**Code Integrity / Driver Signing Violations** — Unsigned or tampered drivers loading into the kernel are a rootkit indicator. Code Integrity violations detect bypass attempts and driver-level threats.

Documented **Data sources**: `sourcetype=WinEventLog:Microsoft-Windows-CodeIntegrity/Operational` (EventCode 3001, 3002, 3003, 3004, 3033). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **issue** — often to normalize units, derive a ratio, or prepare for thresholds.
• Pipeline stage (see **Code Integrity / Driver Signing Violations**): table _time, host, issue, FileNameBuffer, ProcessNameBuffer
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (integrity violations), Timeline, Bar chart (top unsigned files), Single value (blocked loads).

## SPL

```spl
index=wineventlog source="WinEventLog:Microsoft-Windows-CodeIntegrity/Operational"
  EventCode IN (3001, 3002, 3003, 3004, 3033)
| eval issue=case(EventCode=3001,"Unsigned driver blocked",EventCode=3002,"Unable to verify",EventCode=3003,"Unsigned policy",EventCode=3004,"File hash not found",EventCode=3033,"Unsigned image loaded")
| table _time, host, issue, FileNameBuffer, ProcessNameBuffer
| sort -_time
```

## Visualization

Table (integrity violations), Timeline, Bar chart (top unsigned files), Single value (blocked loads).

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
