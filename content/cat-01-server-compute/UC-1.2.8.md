<!-- AUTO-GENERATED from UC-1.2.8.json — DO NOT EDIT -->

---
id: "1.2.8"
title: "Privileged Group Changes"
criticality: "critical"
splunkPillar: "Security"
---

# UC-1.2.8 · Privileged Group Changes

## Description

Additions to Domain Admins, Enterprise Admins, or Schema Admins grant extreme privilege. Unauthorized changes could mean full domain compromise.

## Value

Mistakes or theft in these groups are a fast path to a full environment takeover—tight, timely review is the point.

## Implementation

Collect Security logs from all domain controllers. Create a real-time alert on these event codes filtered to privileged groups (Domain Admins, Enterprise Admins, Schema Admins, Administrators). Require correlation with change ticket.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=WinEventLog:Security`, EventCodes 4728, 4732, 4756 (member added); 4729, 4733, 4757 (member removed).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Collect Security logs from all domain controllers. Create a real-time alert on these event codes filtered to privileged groups (Domain Admins, Enterprise Admins, Schema Admins, Administrators). Require correlation with change ticket.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog sourcetype="WinEventLog:Security" (EventCode=4728 OR EventCode=4732 OR EventCode=4756 OR EventCode=4729 OR EventCode=4733 OR EventCode=4757)
| eval action=case(EventCode IN (4728,4732,4756), "Added", EventCode IN (4729,4733,4757), "Removed")
| table _time action TargetUserName MemberName Group_Name SubjectUserName host
| sort -_time
```

Understanding this SPL

**Privileged Group Changes** — Additions to Domain Admins, Enterprise Admins, or Schema Admins grant extreme privilege. Unauthorized changes could mean full domain compromise.

Documented **Data sources**: `sourcetype=WinEventLog:Security`, EventCodes 4728, 4732, 4756 (member added); 4729, 4733, 4757 (member removed). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog; **sourcetype**: WinEventLog:Security. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog, sourcetype="WinEventLog:Security". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **action** — often to normalize units, derive a ratio, or prepare for thresholds.
• Pipeline stage (see **Privileged Group Changes**): table _time action TargetUserName MemberName Group_Name SubjectUserName host
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Change where nodename=Change.All_Changes
  by All_Changes.object All_Changes.user All_Changes.action span=1h
| where count>0
```

Understanding this CIM / accelerated SPL

**Privileged Group Changes** — Additions to Domain Admins, Enterprise Admins, or Schema Admins grant extreme privilege. Unauthorized changes could mean full domain compromise.

Documented **Data sources**: `sourcetype=WinEventLog:Security`, EventCodes 4728, 4732, 4756 (member added); 4729, 4733, 4757 (member removed). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Authentication.Authentication` — enable acceleration for that model.
• Applies an explicit `search` filter to narrow the current result set.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Events timeline, Table with action details, Alert panel (critical).

## SPL

```spl
index=wineventlog sourcetype="WinEventLog:Security" (EventCode=4728 OR EventCode=4732 OR EventCode=4756 OR EventCode=4729 OR EventCode=4733 OR EventCode=4757)
| eval action=case(EventCode IN (4728,4732,4756), "Added", EventCode IN (4729,4733,4757), "Removed")
| table _time action TargetUserName MemberName Group_Name SubjectUserName host
| sort -_time
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Change where nodename=Change.All_Changes
  by All_Changes.object All_Changes.user All_Changes.action span=1h
| where count>0
```

## Visualization

Events timeline, Table with action details, Alert panel (critical).

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
- [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)
