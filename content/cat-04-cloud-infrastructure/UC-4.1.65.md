<!-- AUTO-GENERATED from UC-4.1.65.json — DO NOT EDIT -->

---
id: "4.1.65"
title: "GuardDuty Severity Analysis"
criticality: "high"
splunkPillar: "Security"
---

# UC-4.1.65 · GuardDuty Severity Analysis

## Description

Prioritizing GuardDuty findings by severity and type reduces noise and speeds triage versus raw event volume.

## Value

Prioritizing GuardDuty findings by severity and type reduces noise and speeds triage versus raw event volume.

## Implementation

Normalize severity (8–10 = high). Auto-suppress known pen-test ranges via lookup. Weekly trend of finding types. SOAR integration for HIGH and above with runbooks per `type`.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_aws`.
• Ensure the following data sources are available: `sourcetype=aws:cloudwatch:guardduty`, GuardDuty S3 export.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Normalize severity (8–10 = high). Auto-suppress known pen-test ranges via lookup. Weekly trend of finding types. SOAR integration for HIGH and above with runbooks per `type`.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:cloudwatch:guardduty"
| stats count by severity, type, accountId
| sort -count
```

Understanding this SPL

**GuardDuty Severity Analysis** — Prioritizing GuardDuty findings by severity and type reduces noise and speeds triage versus raw event volume.

Documented **Data sources**: `sourcetype=aws:cloudwatch:guardduty`, GuardDuty S3 export. **App/TA** (typical add-on context): `Splunk_TA_aws`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:cloudwatch:guardduty. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=aws, sourcetype="aws:cloudwatch:guardduty". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by severity, type, accountId** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Intrusion_Detection.IDS_Attacks
  where (match(lower(IDS_Attacks.severity), "high|critical|severe")
         OR (isnum(IDS_Attacks.severity) AND IDS_Attacks.severity >= 7))
  by IDS_Attacks.signature IDS_Attacks.severity IDS_Attacks.src span=1h
| sort -count
```

Understanding this CIM / accelerated SPL

**GuardDuty Severity Analysis** — Prioritizing GuardDuty findings by severity and type reduces noise and speeds triage versus raw event volume.

Documented **Data sources**: `sourcetype=aws:cloudwatch:guardduty`, GuardDuty S3 export. **App/TA** (typical add-on context): `Splunk_TA_aws`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Intrusion_Detection.IDS_Attacks` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Bar chart (findings by type), Pie chart (severity), Table (account, type, count).

## SPL

```spl
index=aws sourcetype="aws:cloudwatch:guardduty"
| stats count by severity, type, accountId
| sort -count
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Intrusion_Detection.IDS_Attacks
  where (match(lower(IDS_Attacks.severity), "high|critical|severe")
         OR (isnum(IDS_Attacks.severity) AND IDS_Attacks.severity >= 7))
  by IDS_Attacks.signature IDS_Attacks.severity IDS_Attacks.src span=1h
| sort -count
```

## Visualization

Bar chart (findings by type), Pie chart (severity), Table (account, type, count).

## References

- [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)
- [CIM: Intrusion_Detection](https://docs.splunk.com/Documentation/CIM/latest/User/Intrusion_Detection)
