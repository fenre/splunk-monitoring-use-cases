---
id: "1.2.129"
title: "Sysmon Driver/Image Load Monitoring"
criticality: "high"
splunkPillar: "Security"
---

# UC-1.2.129 · Sysmon Driver/Image Load Monitoring

## Description

Monitoring driver and DLL loads catches rootkits, vulnerable drivers, and DLL side-loading attacks that evade process-level monitoring.

## Value

Monitoring driver and DLL loads catches rootkits, vulnerable drivers, and DLL side-loading attacks that evade process-level monitoring.

## Implementation

Sysmon EventCode 6 (DriverLoad) monitors kernel driver loads. Alert on unsigned drivers — all legitimate drivers should be signed. EventCode 7 (ImageLoad) monitors DLL loads (high volume — use targeted config). Focus on unsigned DLLs loaded from unusual paths. Track BYOVD (Bring Your Own Vulnerable Driver) attacks by maintaining a list of known-vulnerable driver hashes. MITRE ATT&CK T1068, T1574.002.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=WinEventLog:Microsoft-Windows-Sysmon/Operational` (EventCode 6, 7).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Sysmon EventCode 6 (DriverLoad) monitors kernel driver loads. Alert on unsigned drivers — all legitimate drivers should be signed. EventCode 7 (ImageLoad) monitors DLL loads (high volume — use targeted config). Focus on unsigned DLLs loaded from unusual paths. Track BYOVD (Bring Your Own Vulnerable Driver) attacks by maintaining a list of known-vulnerable driver hashes. MITRE ATT&CK T1068, T1574.002.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog EventCode=6 Signed="false"
| table _time, host, ImageLoaded, Hashes, Signature, SignatureStatus
| sort -_time
| append [search index=wineventlog EventCode=7 Signed="false" | where NOT match(ImageLoaded, "(?i)(windows\\\\system32|program files)") | table _time, host, Image, ImageLoaded, Hashes, SignatureStatus]
```

Understanding this SPL

**Sysmon Driver/Image Load Monitoring** — Monitoring driver and DLL loads catches rootkits, vulnerable drivers, and DLL side-loading attacks that evade process-level monitoring.

Documented **Data sources**: `sourcetype=WinEventLog:Microsoft-Windows-Sysmon/Operational` (EventCode 6, 7). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Pipeline stage (see **Sysmon Driver/Image Load Monitoring**): table _time, host, ImageLoaded, Hashes, Signature, SignatureStatus
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
• Appends rows from a subsearch with `append`.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (unsigned loads), Alert on unsigned kernel drivers, Timechart.

## SPL

```spl
index=wineventlog EventCode=6 Signed="false"
| table _time, host, ImageLoaded, Hashes, Signature, SignatureStatus
| sort -_time
| append [search index=wineventlog EventCode=7 Signed="false" | where NOT match(ImageLoaded, "(?i)(windows\\\\system32|program files)") | table _time, host, Image, ImageLoaded, Hashes, SignatureStatus]
```

## Visualization

Table (unsigned loads), Alert on unsigned kernel drivers, Timechart.

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
