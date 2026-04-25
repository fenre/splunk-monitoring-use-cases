<!-- AUTO-GENERATED from UC-1.2.77.json — DO NOT EDIT -->

---
id: "1.2.77"
title: "SPN Modification (Targeted Kerberoasting)"
criticality: "critical"
splunkPillar: "Security"
---

# UC-1.2.77 · SPN Modification (Targeted Kerberoasting)

## Description

Attackers add SPNs to admin accounts to make them Kerberoastable. Monitoring SPN changes on sensitive accounts catches this setup before the actual attack.

## Value

When an SPN is added to a high-privilege user, that account can be attacked offline for passwords. Catching the change in the directory log helps you stop the setup before tickets are cracked.

## Implementation

EventCode 5136 with AttributeLDAPDisplayName=servicePrincipalName tracks SPN additions (OperationType %%14674=value added) and removals. Alert on any SPN added to user accounts in privileged groups (Domain Admins, Enterprise Admins, Schema Admins). Legitimate SPN changes are rare and tied to service deployments. Cross-reference with Kerberoasting detection (UC-1.2.37).

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=WinEventLog:Security` (EventCode 5136, attribute servicePrincipalName).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
EventCode 5136 with AttributeLDAPDisplayName=servicePrincipalName tracks SPN additions (OperationType %%14674=value added) and removals. Alert on any SPN added to user accounts in privileged groups (Domain Admins, Enterprise Admins, Schema Admins). Legitimate SPN changes are rare and tied to service deployments. Cross-reference with Kerberoasting detection (UC-1.2.37).

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode=5136
  AttributeLDAPDisplayName="servicePrincipalName"
| table _time, host, SubjectUserName, ObjectDN, AttributeValue, OperationType
| where OperationType="%%14674"
| sort -_time
```

Understanding this SPL

**SPN Modification (Targeted Kerberoasting)** — Attackers add SPNs to admin accounts to make them Kerberoastable. Monitoring SPN changes on sensitive accounts catches this setup before the actual attack.

Documented **Data sources**: `sourcetype=WinEventLog:Security` (EventCode 5136, attribute servicePrincipalName). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog; **sourcetype**: WinEventLog:Security. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog, sourcetype="WinEventLog:Security". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Pipeline stage (see **SPN Modification (Targeted Kerberoasting)**): table _time, host, SubjectUserName, ObjectDN, AttributeValue, OperationType
• Filters the current rows with `where OperationType="%%14674"` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (5136 SPN add/remove in `Change`):

```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  where like(All_Changes.object,"%servicePrincipalName%")
  by All_Changes.user All_Changes.object All_Changes.action span=1h
| where count >= 1
```

Enable **data model acceleration** on `Change` (All_Changes). The primary `AttributeLDAPDisplayName` filter in Step 2 is the strictest; align CIM `object` to the object DN in 5136.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (SPN changes), Single value (changes to admin accounts — target: 0), Timeline.

## SPL

```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode=5136
  AttributeLDAPDisplayName="servicePrincipalName"
| table _time, host, SubjectUserName, ObjectDN, AttributeValue, OperationType
| where OperationType="%%14674"
| sort -_time
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  where like(All_Changes.object,"%servicePrincipalName%")
  by All_Changes.user All_Changes.object All_Changes.action span=1h
| where count >= 1
```

## Visualization

Table (SPN changes), Single value (changes to admin accounts — target: 0), Timeline.

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
- [CIM: Change](https://docs.splunk.com/Documentation/CIM/latest/User/Change)
