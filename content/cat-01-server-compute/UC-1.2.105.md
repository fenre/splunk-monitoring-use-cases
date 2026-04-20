---
id: "1.2.105"
title: "Windows Defender Exclusion Monitoring"
criticality: "critical"
splunkPillar: "Security"
---

# UC-1.2.105 · Windows Defender Exclusion Monitoring

## Description

Attackers add Defender exclusions to hide malware. Monitoring exclusion changes detects evasion techniques and ensures antivirus coverage remains complete.

## Value

Attackers add Defender exclusions to hide malware. Monitoring exclusion changes detects evasion techniques and ensures antivirus coverage remains complete.

## Implementation

Monitor Defender configuration changes (EventID 5007) and filter for exclusion modifications. Track path, extension, and process exclusions. Alert on any exclusion added outside of change management, especially for temp directories, user profiles, or common malware paths. Maintain a whitelist of approved exclusions and alert on deviations. Critical for detecting MITRE ATT&CK T1562.001 (Impair Defenses).

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=WinEventLog:Microsoft-Windows-Windows Defender/Operational` (EventID 5007).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Monitor Defender configuration changes (EventID 5007) and filter for exclusion modifications. Track path, extension, and process exclusions. Alert on any exclusion added outside of change management, especially for temp directories, user profiles, or common malware paths. Maintain a whitelist of approved exclusions and alert on deviations. Critical for detecting MITRE ATT&CK T1562.001 (Impair Defenses).

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog source="WinEventLog:Microsoft-Windows-Windows Defender/Operational" EventCode=5007
| where match(New_Value, "(?i)exclusions")
| rex field=New_Value "Exclusions\\\\(?<ExclusionType>[^\\\\]+)\\\\(?<ExclusionValue>.+)"
| table _time, host, ExclusionType, ExclusionValue, Old_Value, New_Value
| sort -_time
```

Understanding this SPL

**Windows Defender Exclusion Monitoring** — Attackers add Defender exclusions to hide malware. Monitoring exclusion changes detects evasion techniques and ensures antivirus coverage remains complete.

Documented **Data sources**: `sourcetype=WinEventLog:Microsoft-Windows-Windows Defender/Operational` (EventID 5007). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where match(New_Value, "(?i)exclusions")` — typically the threshold or rule expression for this monitoring goal.
• Extracts fields with `rex` (regular expression).
• Pipeline stage (see **Windows Defender Exclusion Monitoring**): table _time, host, ExclusionType, ExclusionValue, Old_Value, New_Value
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (exclusion changes), Alert on unauthorized exclusions, Trend chart.

## SPL

```spl
index=wineventlog source="WinEventLog:Microsoft-Windows-Windows Defender/Operational" EventCode=5007
| where match(New_Value, "(?i)exclusions")
| rex field=New_Value "Exclusions\\\\(?<ExclusionType>[^\\\\]+)\\\\(?<ExclusionValue>.+)"
| table _time, host, ExclusionType, ExclusionValue, Old_Value, New_Value
| sort -_time
```

## Visualization

Table (exclusion changes), Alert on unauthorized exclusions, Trend chart.

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
