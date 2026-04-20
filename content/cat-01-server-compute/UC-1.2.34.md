---
id: "1.2.34"
title: "AppLocker / WDAC Policy Violations"
criticality: "high"
splunkPillar: "Security"
---

# UC-1.2.34 · AppLocker / WDAC Policy Violations

## Description

AppLocker/WDAC blocks track unauthorized application execution attempts. High violation rates indicate persistent threats or misconfigured policies.

## Value

AppLocker/WDAC blocks track unauthorized application execution attempts. High violation rates indicate persistent threats or misconfigured policies.

## Implementation

Enable AppLocker EXE, DLL, and Script rules in enforcement or audit mode. EventCode 8003/8006=allowed, 8004/8007=blocked. In audit mode (EventCode 8003), use data to build baseline before enforcement. Track blocked attempts per host — spikes indicate attack attempts or policy gaps. Correlate FilePath with threat intel.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=WinEventLog:Microsoft-Windows-AppLocker/EXE and DLL` (EventCode 8004, 8007).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable AppLocker EXE, DLL, and Script rules in enforcement or audit mode. EventCode 8003/8006=allowed, 8004/8007=blocked. In audit mode (EventCode 8003), use data to build baseline before enforcement. Track blocked attempts per host — spikes indicate attack attempts or policy gaps. Correlate FilePath with threat intel.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog source="WinEventLog:Microsoft-Windows-AppLocker*" EventCode IN (8004, 8007)
| eval block_type=case(EventCode=8004,"EXE blocked",EventCode=8007,"Script blocked")
| stats count by host, block_type, RuleNameOrId, FilePath, UserName
| sort -count
```

Understanding this SPL

**AppLocker / WDAC Policy Violations** — AppLocker/WDAC blocks track unauthorized application execution attempts. High violation rates indicate persistent threats or misconfigured policies.

Documented **Data sources**: `sourcetype=WinEventLog:Microsoft-Windows-AppLocker/EXE and DLL` (EventCode 8004, 8007). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **block_type** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by host, block_type, RuleNameOrId, FilePath, UserName** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  by All_Changes.user All_Changes.object_category All_Changes.action span=1h
| sort -count
```

Understanding this CIM / accelerated SPL

**AppLocker / WDAC Policy Violations** — AppLocker/WDAC blocks track unauthorized application execution attempts. High violation rates indicate persistent threats or misconfigured policies.

Documented **Data sources**: `sourcetype=WinEventLog:Microsoft-Windows-AppLocker/EXE and DLL` (EventCode 8004, 8007). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Change.All_Changes` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Bar chart (top blocked apps), Table (blocks by host), Timechart (block rate over time).

## SPL

```spl
index=wineventlog source="WinEventLog:Microsoft-Windows-AppLocker*" EventCode IN (8004, 8007)
| eval block_type=case(EventCode=8004,"EXE blocked",EventCode=8007,"Script blocked")
| stats count by host, block_type, RuleNameOrId, FilePath, UserName
| sort -count
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  by All_Changes.user All_Changes.object_category All_Changes.action span=1h
| sort -count
```

## Visualization

Bar chart (top blocked apps), Table (blocks by host), Timechart (block rate over time).

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
- [CIM: Change](https://docs.splunk.com/Documentation/CIM/latest/User/Change)
