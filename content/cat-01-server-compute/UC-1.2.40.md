---
id: "1.2.40"
title: "WHEA Hardware Error Reporting"
criticality: "high"
splunkPillar: "Observability"
---

# UC-1.2.40 · WHEA Hardware Error Reporting

## Description

Windows Hardware Error Architecture (WHEA) reports CPU, memory, and PCIe hardware errors before they cause crashes. Enables proactive hardware replacement.

## Value

Windows Hardware Error Architecture (WHEA) reports CPU, memory, and PCIe hardware errors before they cause crashes. Enables proactive hardware replacement.

## Implementation

WHEA events are logged automatically by Windows on hardware error. EventCode 18=fatal (machine check, NMI), 19=corrected (ECC memory correction, CPU thermal), 47=informational. Track corrected error rates — rising counts predict imminent failure. Correlate with specific hardware component (CPU, memory DIMM, PCIe device) from ErrorSource field. Alert on any fatal errors and on corrected error rate >10/hour.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=WinEventLog:System` (Source=Microsoft-Windows-WHEA-Logger, EventCode 17, 18, 19, 20, 47).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
WHEA events are logged automatically by Windows on hardware error. EventCode 18=fatal (machine check, NMI), 19=corrected (ECC memory correction, CPU thermal), 47=informational. Track corrected error rates — rising counts predict imminent failure. Correlate with specific hardware component (CPU, memory DIMM, PCIe device) from ErrorSource field. Alert on any fatal errors and on corrected error rate >10/hour.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog sourcetype="WinEventLog:System" Source="Microsoft-Windows-WHEA-Logger"
| eval severity=case(EventCode=18,"Fatal",EventCode=19,"Corrected",EventCode=20,"Informational",1=1,"Other")
| stats count by host, severity, ErrorSource, ErrorType
| sort -count
```

Understanding this SPL

**WHEA Hardware Error Reporting** — Windows Hardware Error Architecture (WHEA) reports CPU, memory, and PCIe hardware errors before they cause crashes. Enables proactive hardware replacement.

Documented **Data sources**: `sourcetype=WinEventLog:System` (Source=Microsoft-Windows-WHEA-Logger, EventCode 17, 18, 19, 20, 47). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog; **sourcetype**: WinEventLog:System. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog, sourcetype="WinEventLog:System". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **severity** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by host, severity, ErrorSource, ErrorType** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (errors by host and component), Line chart (corrected error trend), Single value (fatal errors — target: 0).

## SPL

```spl
index=wineventlog sourcetype="WinEventLog:System" Source="Microsoft-Windows-WHEA-Logger"
| eval severity=case(EventCode=18,"Fatal",EventCode=19,"Corrected",EventCode=20,"Informational",1=1,"Other")
| stats count by host, severity, ErrorSource, ErrorType
| sort -count
```

## Visualization

Table (errors by host and component), Line chart (corrected error trend), Single value (fatal errors — target: 0).

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
