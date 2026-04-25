<!-- AUTO-GENERATED from UC-1.2.93.json — DO NOT EDIT -->

---
id: "1.2.93"
title: "Group Policy Object (GPO) Modification Auditing"
criticality: "critical"
splunkPillar: "Security"
---

# UC-1.2.93 · Group Policy Object (GPO) Modification Auditing

## Description

GPO changes affect all domain-joined systems. Unauthorized GPO modifications can deploy malware, weaken security, or exfiltrate credentials at scale.

## Value

A surprise GPO change can push malware paths, open firewall holes, or weaken password rules fleet-wide. Auditing the directory objects behind policy blocks silent drift and insider edits.

## Implementation

Enable Audit Directory Service Changes. Track GPO creation (5137) and modification (5136) on domain controllers. Alert on GPO changes outside change windows, by non-admin accounts, or modifications to security-sensitive GPOs (password policy, audit policy, software restriction). Correlate with change management tickets.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=WinEventLog:Security` (EventCode 5136, 5137).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable Audit Directory Service Changes. Track GPO creation (5137) and modification (5136) on domain controllers. Alert on GPO changes outside change windows, by non-admin accounts, or modifications to security-sensitive GPOs (password policy, audit policy, software restriction). Correlate with change management tickets.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog EventCode IN (5136, 5137) ObjectClass="groupPolicyContainer"
| eval Action=case(EventCode=5136,"Modified", EventCode=5137,"Created", 1=1,"Other")
| table _time, host, SubjectUserName, Action, ObjectDN, AttributeLDAPDisplayName, AttributeValue
| sort -_time
```

Understanding this SPL

**Group Policy Object (GPO) Modification Auditing** — GPO changes affect all domain-joined systems. Unauthorized GPO modifications can deploy malware, weaken security, or exfiltrate credentials at scale.

Documented **Data sources**: `sourcetype=WinEventLog:Security` (EventCode 5136, 5137). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **Action** — often to normalize units, derive a ratio, or prepare for thresholds.
• Pipeline stage (see **Group Policy Object (GPO) Modification Auditing**): table _time, host, SubjectUserName, Action, ObjectDN, AttributeLDAPDisplayName, AttributeValue
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  by All_Changes.user All_Changes.object_category All_Changes.action span=1h
| sort -count
```

Understanding this CIM / accelerated SPL

**Group Policy Object (GPO) Modification Auditing** — GPO changes affect all domain-joined systems. Unauthorized GPO modifications can deploy malware, weaken security, or exfiltrate credentials at scale.

Documented **Data sources**: `sourcetype=WinEventLog:Security` (EventCode 5136, 5137). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Change.All_Changes` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Timeline (GPO changes), Table (modification details), Alert on unauthorized changes.

## SPL

```spl
index=wineventlog EventCode IN (5136, 5137) ObjectClass="groupPolicyContainer"
| eval Action=case(EventCode=5136,"Modified", EventCode=5137,"Created", 1=1,"Other")
| table _time, host, SubjectUserName, Action, ObjectDN, AttributeLDAPDisplayName, AttributeValue
| sort -_time
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  by All_Changes.user All_Changes.dest span=1h
| where count > 0
```

## Visualization

Timeline (GPO changes), Table (modification details), Alert on unauthorized changes.

## References

- [Enable Audit Directory Service Changes. Track GPO creation](https://splunkbase.splunk.com/app/5137)
- [and modification](https://splunkbase.splunk.com/app/5136)
- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
- [CIM: Change](https://docs.splunk.com/Documentation/CIM/latest/User/Change)
