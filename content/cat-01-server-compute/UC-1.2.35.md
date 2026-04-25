<!-- AUTO-GENERATED from UC-1.2.35.json — DO NOT EDIT -->

---
id: "1.2.35"
title: "Windows Defender Threat Detections"
criticality: "critical"
splunkPillar: "Security"
---

# UC-1.2.35 · Windows Defender Threat Detections

## Description

Real-time visibility into endpoint AV detections across the fleet. Delayed response to malware detections increases blast radius.

## Value

Server-side detections are high stakes—faster handoff to IR or isolation limits spread.

## Implementation

Forward Windows Defender Operational log from all endpoints. EventCode 1116=threat detected, 1117=action taken, 1006/1007=malware detected/acted on. Alert immediately on detections with Severity "Severe" or "High". Track remediation success (1117 following 1116). Monitor for EventCode 5001 (real-time protection disabled) as a separate critical alert.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=WinEventLog:Microsoft-Windows-Windows Defender/Operational` (EventCode 1006, 1007, 1116, 1117).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Forward Windows Defender Operational log from all endpoints. EventCode 1116=threat detected, 1117=action taken, 1006/1007=malware detected/acted on. Alert immediately on detections with Severity "Severe" or "High". Track remediation success (1117 following 1116). Monitor for EventCode 5001 (real-time protection disabled) as a separate critical alert.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog source="WinEventLog:Microsoft-Windows-Windows Defender/Operational"
  EventCode IN (1006, 1007, 1116, 1117)
| eval action=case(EventCode=1006,"Detected",EventCode=1007,"Action taken",EventCode=1116,"Detected",EventCode=1117,"Action taken")
| table _time, host, action, "Threat Name", "Severity ID", Path, "Detection User"
| sort -_time
```

Understanding this SPL

**Windows Defender Threat Detections** — Real-time visibility into endpoint AV detections across the fleet. Delayed response to malware detections increases blast radius.

Documented **Data sources**: `sourcetype=WinEventLog:Microsoft-Windows-Windows Defender/Operational` (EventCode 1006, 1007, 1116, 1117). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **action** — often to normalize units, derive a ratio, or prepare for thresholds.
• Pipeline stage (see **Windows Defender Threat Detections**): table _time, host, action, "Threat Name", "Severity ID", Path, "Detection User"
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Change where nodename=Change.All_Changes
  by All_Changes.dest All_Changes.object span=1h
| where count>0
```

Understanding this CIM / accelerated SPL

CIM tstats is an approximate mirror when Windows TA field extractions and CIM tags are complete. Enable the matching data model acceleration or tstats may return no rows.



Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (recent detections), Bar chart (threat categories), Single value (unresolved threats), Map (affected hosts).

## SPL

```spl
index=wineventlog source="WinEventLog:Microsoft-Windows-Windows Defender/Operational"
  EventCode IN (1006, 1007, 1116, 1117)
| eval action=case(EventCode=1006,"Detected",EventCode=1007,"Action taken",EventCode=1116,"Detected",EventCode=1117,"Action taken")
| table _time, host, action, "Threat Name", "Severity ID", Path, "Detection User"
| sort -_time
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Change where nodename=Change.All_Changes
  by All_Changes.dest All_Changes.object span=1h
| where count>0
```

## Visualization

Table (recent detections), Bar chart (threat categories), Single value (unresolved threats), Map (affected hosts).

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
