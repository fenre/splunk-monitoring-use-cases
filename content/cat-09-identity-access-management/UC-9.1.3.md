<!-- AUTO-GENERATED from UC-9.1.3.json — DO NOT EDIT -->

---
id: "9.1.3"
title: "Privileged Group Membership Changes"
criticality: "critical"
splunkPillar: "Security"
---

# UC-9.1.3 · Privileged Group Membership Changes

## Description

Adding accounts to Domain Admins or Enterprise Admins (EventCode 4728/4732/4756) in minutes limits blast radius from stolen Tier-0 credentials. Immediate detection supports audit evidence for privileged access changes and enables rapid containment before lateral movement escalates.

## Value

Adding accounts to Domain Admins or Enterprise Admins (EventCode 4728/4732/4756) in minutes limits blast radius from stolen Tier-0 credentials. Immediate detection supports audit evidence for privileged access changes and enables rapid containment before lateral movement escalates.

## Implementation

Forward DC Security logs. Create alert for any membership change to privileged groups (Domain Admins, Enterprise Admins, Schema Admins, Backup Operators). Integrate with change management for validation.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: Security Event Log (4728 — member added to security-enabled global group, 4732 — local group, 4756 — universal group).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Forward DC Security logs. Create alert for any membership change to privileged groups (Domain Admins, Enterprise Admins, Schema Admins, Backup Operators). Integrate with change management for validation.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode IN (4728,4732,4756)
| search TargetUserName IN ("Domain Admins","Enterprise Admins","Schema Admins","Administrators")
| table _time, MemberName, TargetUserName, SubjectUserName
```

Understanding this SPL

**Privileged Group Membership Changes** — Adding accounts to Domain Admins or Enterprise Admins (EventCode 4728/4732/4756) in minutes limits blast radius from stolen Tier-0 credentials. Immediate detection supports audit evidence for privileged access changes and enables rapid containment before lateral movement escalates.

Documented **Data sources**: Security Event Log (4728 — member added to security-enabled global group, 4732 — local group, 4756 — universal group). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog; **sourcetype**: WinEventLog:Security. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog, sourcetype="WinEventLog:Security". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Applies an explicit `search` filter to narrow the current result set.
• Pipeline stage (see **Privileged Group Membership Changes**): table _time, MemberName, TargetUserName, SubjectUserName

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Change.Auditing_Changes
  where Auditing_Changes.action="modified"
  by Auditing_Changes.user,Auditing_Changes.object,Auditing_Changes.dest span=1h
| sort -count
```

Understanding this CIM / accelerated SPL

**Privileged Group Membership Changes** — Adding accounts to Domain Admins or Enterprise Admins (EventCode 4728/4732/4756) in minutes limits blast radius from stolen Tier-0 credentials. Immediate detection supports audit evidence for privileged access changes and enables rapid containment before lateral movement escalates.

Documented **Data sources**: Security Event Log (4728 — member added to security-enabled global group, 4732 — local group, 4756 — universal group). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Change.Auditing_Changes` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Compare with Event Viewer on domain controllers (or exported Security logs) and with Active Directory Users and Computers for the same objects and time window.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (membership changes), Timeline (change events), Single value (changes this week).

## SPL

```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode IN (4728,4732,4756)
| search TargetUserName IN ("Domain Admins","Enterprise Admins","Schema Admins","Administrators")
| table _time, MemberName, TargetUserName, SubjectUserName
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Change.Auditing_Changes
  where Auditing_Changes.action="modified"
  by Auditing_Changes.user,Auditing_Changes.object,Auditing_Changes.dest span=1h
| sort -count
```

## Visualization

Table (membership changes), Timeline (change events), Single value (changes this week).

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
- [CIM: Change](https://docs.splunk.com/Documentation/CIM/latest/User/Change)
