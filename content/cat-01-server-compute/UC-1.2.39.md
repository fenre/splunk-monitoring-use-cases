<!-- AUTO-GENERATED from UC-1.2.39.json — DO NOT EDIT -->

---
id: "1.2.39"
title: "Domain Trust Changes"
criticality: "critical"
splunkPillar: "Security"
---

# UC-1.2.39 · Domain Trust Changes

## Description

Unauthorized trust relationships can grant external domains access to internal resources. Trust modifications are rare and high-impact.

## Value

Trust changes are rare and high impact—tight change correlation is the difference between a drill and a real incident review.

## Implementation

EventCode 4706=new trust, 4707=trust removed, 4716=trust modified. These events are extremely rare in stable environments. Alert on all trust changes with critical priority. Verify against approved change requests. Pay attention to trust direction (inbound trusts grant access TO your domain) and trust type (external vs. forest trusts).

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=WinEventLog:Security` (EventCode 4706, 4707, 4716).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
EventCode 4706=new trust, 4707=trust removed, 4716=trust modified. These events are extremely rare in stable environments. Alert on all trust changes with critical priority. Verify against approved change requests. Pay attention to trust direction (inbound trusts grant access TO your domain) and trust type (external vs. forest trusts).

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode IN (4706, 4707, 4716)
| eval action=case(EventCode=4706,"Trust created",EventCode=4707,"Trust removed",EventCode=4716,"Trust modified")
| table _time, host, action, SubjectUserName, TrustDirection, TrustType, TrustedDomain
| sort -_time
```

Understanding this SPL

**Domain Trust Changes** — Unauthorized trust relationships can grant external domains access to internal resources. Trust modifications are rare and high-impact.

Documented **Data sources**: `sourcetype=WinEventLog:Security` (EventCode 4706, 4707, 4716). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog; **sourcetype**: WinEventLog:Security. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog, sourcetype="WinEventLog:Security". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **action** — often to normalize units, derive a ratio, or prepare for thresholds.
• Pipeline stage (see **Domain Trust Changes**): table _time, host, action, SubjectUserName, TrustDirection, TrustType, TrustedDomain
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Change where nodename=Change.All_Changes
  by All_Changes.user All_Changes.object All_Changes.action span=1h
| where count>0
```

Understanding this CIM / accelerated SPL

**Domain Trust Changes** — Unauthorized trust relationships can grant external domains access to internal resources. Trust modifications are rare and high-impact.

Documented **Data sources**: `sourcetype=WinEventLog:Security` (EventCode 4706, 4707, 4716). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Change.All_Changes` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (trust changes), Single value (count — target: 0 outside planned changes), Alert.

## SPL

```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode IN (4706, 4707, 4716)
| eval action=case(EventCode=4706,"Trust created",EventCode=4707,"Trust removed",EventCode=4716,"Trust modified")
| table _time, host, action, SubjectUserName, TrustDirection, TrustType, TrustedDomain
| sort -_time
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Change where nodename=Change.All_Changes
  by All_Changes.user All_Changes.object All_Changes.action span=1h
| where count>0
```

## Visualization

Table (trust changes), Single value (count — target: 0 outside planned changes), Alert.

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
- [CIM: Change](https://docs.splunk.com/Documentation/CIM/latest/User/Change)
