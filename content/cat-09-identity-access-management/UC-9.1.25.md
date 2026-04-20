---
id: "9.1.25"
title: "AD Forest Trust Changes"
criticality: "critical"
splunkPillar: "Security"
---

# UC-9.1.25 · AD Forest Trust Changes

## Description

Trust direction and selective authentication changes alter cross-forest attack surface; distinct from one-off session events.

## Value

Trust direction and selective authentication changes alter cross-forest attack surface; distinct from one-off session events.

## Implementation

Forward all DC Security logs. Require CAB approval for trust changes. Alert on selective auth disablement or inbound trust creation.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: Security Event Log (4706 — trust modified, 4713 — trust deleted, 4716 — trusted domain information modified).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Forward all DC Security logs. Require CAB approval for trust changes. Alert on selective auth disablement or inbound trust creation.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode IN (4706,4713,4716)
| table _time, SubjectUserName, TargetDomainName, TrustType, TrustDirection, SidFiltering
| sort -_time
```

Understanding this SPL

**AD Forest Trust Changes** — Trust direction and selective authentication changes alter cross-forest attack surface; distinct from one-off session events.

Documented **Data sources**: Security Event Log (4706 — trust modified, 4713 — trust deleted, 4716 — trusted domain information modified). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog; **sourcetype**: WinEventLog:Security. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog, sourcetype="WinEventLog:Security". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Pipeline stage (see **AD Forest Trust Changes**): table _time, SubjectUserName, TargetDomainName, TrustType, TrustDirection, SidFiltering
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t count from datamodel=Change.All_Changes by All_Changes.action, All_Changes.object_category, All_Changes.user | sort - count
```

Understanding this CIM / accelerated SPL

**AD Forest Trust Changes** — Trust direction and selective authentication changes alter cross-forest attack surface; distinct from one-off session events.

Documented **Data sources**: Security Event Log (4706 — trust modified, 4713 — trust deleted, 4716 — trusted domain information modified). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Change.All_Changes` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (trust changes), Timeline, Single value (changes per year).

## SPL

```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode IN (4706,4713,4716)
| table _time, SubjectUserName, TargetDomainName, TrustType, TrustDirection, SidFiltering
| sort -_time
```

## CIM SPL

```spl
| tstats summariesonly=t count from datamodel=Change.All_Changes by All_Changes.action, All_Changes.object_category, All_Changes.user | sort - count
```

## Visualization

Table (trust changes), Timeline, Single value (changes per year).

## Known False Positives

Administrative tasks, scheduled jobs or platform updates can match this pattern — correlate with change management, maintenance windows and user role before raising severity.

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
- [CIM: Change](https://docs.splunk.com/Documentation/CIM/latest/User/Change)
