<!-- AUTO-GENERATED from UC-4.1.71.json — DO NOT EDIT -->

---
id: "4.1.71"
title: "Systems Manager Patch Compliance"
criticality: "medium"
splunkPillar: "Security"
---

# UC-4.1.71 · Systems Manager Patch Compliance

## Description

Patch baselines reduce exploit exposure; instance-level compliance gaps show outdated AMIs or broken agents.

## Value

Patch baselines reduce exploit exposure; instance-level compliance gaps show outdated AMIs or broken agents.

## Implementation

Schedule `AWS-RunPatchBaseline` and ingest compliance association results. Dashboard by OU and environment tag. Alert when CRITICAL severity patches are non-compliant past SLA window.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_aws`.
• Ensure the following data sources are available: `sourcetype=aws:ssm:compliance`, SSM Inventory association.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Schedule `AWS-RunPatchBaseline` and ingest compliance association results. Dashboard by OU and environment tag. Alert when CRITICAL severity patches are non-compliant past SLA window.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:ssm:compliance" ComplianceType="Patch"
| stats latest(status) as patch_status by resourceId, PatchSeverity
| where patch_status!="Compliant"
| stats count by resourceId
| sort -count
```

Understanding this SPL

**Systems Manager Patch Compliance** — Patch baselines reduce exploit exposure; instance-level compliance gaps show outdated AMIs or broken agents.

Documented **Data sources**: `sourcetype=aws:ssm:compliance`, SSM Inventory association. **App/TA** (typical add-on context): `Splunk_TA_aws`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:ssm:compliance. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=aws, sourcetype="aws:ssm:compliance". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by resourceId, PatchSeverity** so each row reflects one combination of those dimensions.
• Filters the current rows with `where patch_status!="Compliant"` — typically the threshold or rule expression for this monitoring goal.
• `stats` rolls up events into metrics; results are split **by resourceId** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Updates.Updates
  where match(Updates.status, "(?i)non-?compliant|missing|failed|not.?installed")
  by Updates.dest Updates.app span=1d
| sort -count
```

Understanding this CIM / accelerated SPL

**Systems Manager Patch Compliance** — Patch baselines reduce exploit exposure; instance-level compliance gaps show outdated AMIs or broken agents.

Documented **Data sources**: `sourcetype=aws:ssm:compliance`, SSM Inventory association. **App/TA** (typical add-on context): `Splunk_TA_aws`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Updates.Updates` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (instance, missing count), Pie chart (compliant %), Bar chart (severity).

## SPL

```spl
index=aws sourcetype="aws:ssm:compliance" ComplianceType="Patch"
| stats latest(status) as patch_status by resourceId, PatchSeverity
| where patch_status!="Compliant"
| stats count by resourceId
| sort -count
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Updates.Updates
  where match(Updates.status, "(?i)non-?compliant|missing|failed|not.?installed")
  by Updates.dest Updates.app span=1d
| sort -count
```

## Visualization

Table (instance, missing count), Pie chart (compliant %), Bar chart (severity).

## References

- [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)
- [CIM: Updates](https://docs.splunk.com/Documentation/CIM/latest/User/Updates)
