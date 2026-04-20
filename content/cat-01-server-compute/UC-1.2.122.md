---
id: "1.2.122"
title: "Local Account Creation & Modification"
criticality: "critical"
splunkPillar: "Security"
---

# UC-1.2.122 · Local Account Creation & Modification

## Description

Creating local accounts is a persistence technique. On domain-joined systems, local account creation is rare and suspicious.

## Value

Creating local accounts is a persistence technique. On domain-joined systems, local account creation is rare and suspicious.

## Implementation

Track local account creation (4720), enabling (4722), password reset (4724), and modification (4738). On domain-joined servers, local account creation is almost always suspicious. Alert on any local account creation, especially when performed by non-admin processes or via net.exe/net1.exe. Filter out managed service accounts and known automation. MITRE ATT&CK T1136.001.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=WinEventLog:Security` (EventCode 4720, 4722, 4724, 4738).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Track local account creation (4720), enabling (4722), password reset (4724), and modification (4738). On domain-joined servers, local account creation is almost always suspicious. Alert on any local account creation, especially when performed by non-admin processes or via net.exe/net1.exe. Filter out managed service accounts and known automation. MITRE ATT&CK T1136.001.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog EventCode IN (4720, 4722, 4724, 4738) NOT TargetDomainName IN ("NT AUTHORITY", "NT-AUTORITÄT")
| eval Action=case(EventCode=4720,"Account_Created", EventCode=4722,"Account_Enabled", EventCode=4724,"Password_Reset", EventCode=4738,"Account_Changed", 1=1,"Other")
| table _time, host, Action, TargetUserName, TargetDomainName, SubjectUserName
| sort -_time
```

Understanding this SPL

**Local Account Creation & Modification** — Creating local accounts is a persistence technique. On domain-joined systems, local account creation is rare and suspicious.

Documented **Data sources**: `sourcetype=WinEventLog:Security` (EventCode 4720, 4722, 4724, 4738). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **Action** — often to normalize units, derive a ratio, or prepare for thresholds.
• Pipeline stage (see **Local Account Creation & Modification**): table _time, host, Action, TargetUserName, TargetDomainName, SubjectUserName
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  by All_Changes.user All_Changes.object_category All_Changes.action span=1h
| sort -count
```

Understanding this CIM / accelerated SPL

**Local Account Creation & Modification** — Creating local accounts is a persistence technique. On domain-joined systems, local account creation is rare and suspicious.

Documented **Data sources**: `sourcetype=WinEventLog:Security` (EventCode 4720, 4722, 4724, 4738). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Change.All_Changes` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (account events), Alert on creation, Timeline.

## SPL

```spl
index=wineventlog EventCode IN (4720, 4722, 4724, 4738) NOT TargetDomainName IN ("NT AUTHORITY", "NT-AUTORITÄT")
| eval Action=case(EventCode=4720,"Account_Created", EventCode=4722,"Account_Enabled", EventCode=4724,"Password_Reset", EventCode=4738,"Account_Changed", 1=1,"Other")
| table _time, host, Action, TargetUserName, TargetDomainName, SubjectUserName
| sort -_time
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  by All_Changes.user All_Changes.object_category All_Changes.action span=1h
| sort -count
```

## Visualization

Table (account events), Alert on creation, Timeline.

## References

- [Track local account creation](https://splunkbase.splunk.com/app/4720)
- [enabling](https://splunkbase.splunk.com/app/4722)
- [password reset](https://splunkbase.splunk.com/app/4724)
- [CIM: Change](https://docs.splunk.com/Documentation/CIM/latest/User/Change)
