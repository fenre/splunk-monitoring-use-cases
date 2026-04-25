<!-- AUTO-GENERATED from UC-1.2.118.json — DO NOT EDIT -->

---
id: "1.2.118"
title: "ASR (Attack Surface Reduction) Rule Monitoring"
criticality: "critical"
splunkPillar: "Security"
---

# UC-1.2.118 · ASR (Attack Surface Reduction) Rule Monitoring

## Description

ASR rules block common attack techniques (Office macro code, credential theft, ransomware). Monitoring ASR ensures rules are enforced and detects blocked attacks.

## Value

Attack surface reduction rules stop common abuse of Office, scripting, and mail. Missing blocks or sudden policy changes after upgrades can reopen what you thought was closed.

## Implementation

Enable ASR rules in Block or Audit mode. EventCode 1121 (blocked) and 1122 (audit) log ASR triggers. Map rule GUIDs to names via lookup table (e.g., 75668C1F = "Block Office from creating executable content"). Track most-triggered rules for tuning. Alert on: high block counts (active attack), blocks suddenly stopping (rules disabled), and audit-mode triggers on sensitive rules that should be in block mode.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=WinEventLog:Microsoft-Windows-Windows Defender/Operational` (EventID 1121, 1122).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable ASR rules in Block or Audit mode. EventCode 1121 (blocked) and 1122 (audit) log ASR triggers. Map rule GUIDs to names via lookup table (e.g., 75668C1F = "Block Office from creating executable content"). Track most-triggered rules for tuning. Alert on: high block counts (active attack), blocks suddenly stopping (rules disabled), and audit-mode triggers on sensitive rules that should be in block mode.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog source="WinEventLog:Microsoft-Windows-Windows Defender/Operational" EventCode IN (1121, 1122)
| eval Mode=case(EventCode=1121,"Blocked", EventCode=1122,"Audit", 1=1,"Other")
| lookup asr_rule_names ID as RuleId OUTPUT RuleName
| stats count by host, RuleName, Mode, Path, ProcessName
| sort -count
```

Understanding this SPL

**ASR (Attack Surface Reduction) Rule Monitoring** — ASR rules block common attack techniques (Office macro code, credential theft, ransomware). Monitoring ASR ensures rules are enforced and detects blocked attacks.

Documented **Data sources**: `sourcetype=WinEventLog:Microsoft-Windows-Windows Defender/Operational` (EventID 1121, 1122). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **Mode** — often to normalize units, derive a ratio, or prepare for thresholds.
• Enriches events using `lookup` (lookup definition + optional OUTPUT fields).
• `stats` rolls up events into metrics; results are split **by host, RuleName, Mode, Path, ProcessName** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Bar chart (blocks by rule), Timechart (block trends), Table (event details).

## SPL

```spl
index=wineventlog source="WinEventLog:Microsoft-Windows-Windows Defender/Operational" EventCode IN (1121, 1122)
| eval Mode=case(EventCode=1121,"Blocked", EventCode=1122,"Audit", 1=1,"Other")
| lookup asr_rule_names ID as RuleId OUTPUT RuleName
| stats count by host, RuleName, Mode, Path, ProcessName
| sort -count
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  by All_Changes.user All_Changes.dest span=1h
| where count > 0
```

## Visualization

Bar chart (blocks by rule), Timechart (block trends), Table (event details).

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
