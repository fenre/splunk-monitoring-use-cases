<!-- AUTO-GENERATED from UC-9.1.7.json — DO NOT EDIT -->

---
id: "9.1.7"
title: "GPO Modification Detection"
criticality: "critical"
splunkPillar: "Security"
---

# UC-9.1.7 · GPO Modification Detection

## Description

GPO changes affect all domain-joined machines. Unauthorized modifications can disable security controls across the organization.

## Value

GPO changes affect all domain-joined machines. Unauthorized modifications can disable security controls across the organization.

## Implementation

Enable "Audit Directory Service Changes" via GPO. Forward DC Security logs. Alert on any GPO modification. Correlate with change management tickets. Track which GPOs are modified most frequently.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: Security Event Log (5136 — directory service object modified).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable "Audit Directory Service Changes" via GPO. Forward DC Security logs. Alert on any GPO modification. Correlate with change management tickets. Track which GPOs are modified most frequently.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode=5136
| search ObjectClass="groupPolicyContainer"
| table _time, SubjectUserName, ObjectDN, AttributeLDAPDisplayName, AttributeValue
```

Understanding this SPL

**GPO Modification Detection** — GPO changes affect all domain-joined machines. Unauthorized modifications can disable security controls across the organization.

Documented **Data sources**: Security Event Log (5136 — directory service object modified). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog; **sourcetype**: WinEventLog:Security. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog, sourcetype="WinEventLog:Security". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Applies an explicit `search` filter to narrow the current result set.
• Pipeline stage (see **GPO Modification Detection**): table _time, SubjectUserName, ObjectDN, AttributeLDAPDisplayName, AttributeValue

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  where match(All_Changes.object, "(?i)groupPolicyContainer|Policies|GPO")
  by All_Changes.user All_Changes.object span=1h
| sort -count
```

Understanding this CIM / accelerated SPL

**GPO Modification Detection** — GPO changes affect all domain-joined machines. Unauthorized modifications can disable security controls across the organization.

Documented **Data sources**: Security Event Log (5136 — directory service object modified). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Change.All_Changes` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Compare with the directory server’s admin or audit view (bind DNs, result codes) for the same time range.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (GPO changes with details), Timeline (modification events), Bar chart (changes by admin).

## SPL

```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode=5136
| search ObjectClass="groupPolicyContainer"
| table _time, SubjectUserName, ObjectDN, AttributeLDAPDisplayName, AttributeValue
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  where match(All_Changes.object, "(?i)groupPolicyContainer|Policies|GPO")
  by All_Changes.user All_Changes.object span=1h
| sort -count
```

## Visualization

Table (GPO changes with details), Timeline (modification events), Bar chart (changes by admin).

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
- [CIM: Change](https://docs.splunk.com/Documentation/CIM/latest/User/Change)
