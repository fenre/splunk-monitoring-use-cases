---
id: "9.1.21"
title: "AdminSDHolder Modification"
criticality: "critical"
splunkPillar: "Security"
---

# UC-9.1.21 · AdminSDHolder Modification

## Description

Changes to AdminSDHolder or SDProp timing can preserve attacker persistence on privileged accounts.

## Value

Changes to AdminSDHolder or SDProp timing can preserve attacker persistence on privileged accounts.

## Implementation

Enable DS change auditing on DCs. Alert on any modification to AdminSDHolder ACL or attributes. Review regularly for expected adminSDHolder propagation delays.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: Security Event Log (5136 — directory service object modified), object DN containing AdminSDHolder.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable DS change auditing on DCs. Alert on any modification to AdminSDHolder ACL or attributes. Review regularly for expected adminSDHolder propagation delays.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode=5136
| search ObjectDN="*CN=AdminSDHolder,CN=System*"
| table _time, SubjectUserName, ObjectDN, AttributeLDAPDisplayName, AttributeValue
| sort -_time
```

Understanding this SPL

**AdminSDHolder Modification** — Changes to AdminSDHolder or SDProp timing can preserve attacker persistence on privileged accounts.

Documented **Data sources**: Security Event Log (5136 — directory service object modified), object DN containing AdminSDHolder. **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog; **sourcetype**: WinEventLog:Security. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog, sourcetype="WinEventLog:Security". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Applies an explicit `search` filter to narrow the current result set.
• Pipeline stage (see **AdminSDHolder Modification**): table _time, SubjectUserName, ObjectDN, AttributeLDAPDisplayName, AttributeValue
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t count from datamodel=Change.All_Changes by All_Changes.action, All_Changes.object_category, All_Changes.user | sort - count
```

Understanding this CIM / accelerated SPL

**AdminSDHolder Modification** — Changes to AdminSDHolder or SDProp timing can preserve attacker persistence on privileged accounts.

Documented **Data sources**: Security Event Log (5136 — directory service object modified), object DN containing AdminSDHolder. **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Change.All_Changes` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (changes), Timeline, Single value (changes per quarter — expect near zero).

## SPL

```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode=5136
| search ObjectDN="*CN=AdminSDHolder,CN=System*"
| table _time, SubjectUserName, ObjectDN, AttributeLDAPDisplayName, AttributeValue
| sort -_time
```

## CIM SPL

```spl
| tstats summariesonly=t count from datamodel=Change.All_Changes by All_Changes.action, All_Changes.object_category, All_Changes.user | sort - count
```

## Visualization

Table (changes), Timeline, Single value (changes per quarter — expect near zero).

## Known False Positives

Administrative tasks, scheduled jobs or platform updates can match this pattern — correlate with change management, maintenance windows and user role before raising severity.

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
- [CIM: Change](https://docs.splunk.com/Documentation/CIM/latest/User/Change)
