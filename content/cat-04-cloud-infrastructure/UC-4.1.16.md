<!-- AUTO-GENERATED from UC-4.1.16.json — DO NOT EDIT -->

---
id: "4.1.16"
title: "KMS Key Usage Audit"
criticality: "medium"
splunkPillar: "Security"
---

# UC-4.1.16 · KMS Key Usage Audit

## Description

Encryption key usage audit ensures data protection compliance. Unusual key access patterns may indicate unauthorized data decryption.

## Value

Encryption key usage audit ensures data protection compliance. Unusual key access patterns may indicate unauthorized data decryption.

## Implementation

CloudTrail captures all KMS API calls. Monitor for unusual Decrypt call volumes or access from unexpected principals. Track key rotation compliance.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_aws`.
• Ensure the following data sources are available: `sourcetype=aws:cloudtrail`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
CloudTrail captures all KMS API calls. Monitor for unusual Decrypt call volumes or access from unexpected principals. Track key rotation compliance.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:cloudtrail" (eventName="Decrypt" OR eventName="Encrypt" OR eventName="GenerateDataKey") eventSource="kms.amazonaws.com"
| stats count by userIdentity.arn, requestParameters.keyId, eventName
| sort -count
```

Understanding this SPL

**KMS Key Usage Audit** — Encryption key usage audit ensures data protection compliance. Unusual key access patterns may indicate unauthorized data decryption.

Documented **Data sources**: `sourcetype=aws:cloudtrail`. **App/TA** (typical add-on context): `Splunk_TA_aws`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:cloudtrail. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=aws, sourcetype="aws:cloudtrail". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by userIdentity.arn, requestParameters.keyId, eventName** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  where match(All_Changes.app, "(?i)kms\\.amazonaws") OR match(All_Changes.object, "(?i)kms:|key/")
  by All_Changes.user All_Changes.object All_Changes.action span=1h
| sort -count
```

Understanding this CIM / accelerated SPL

**KMS Key Usage Audit** — Encryption key usage audit ensures data protection compliance. Unusual key access patterns may indicate unauthorized data decryption.

Documented **Data sources**: `sourcetype=aws:cloudtrail`. **App/TA** (typical add-on context): `Splunk_TA_aws`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Change.All_Changes` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (principal, key, action, count), Trend line, Bar chart.

## SPL

```spl
index=aws sourcetype="aws:cloudtrail" (eventName="Decrypt" OR eventName="Encrypt" OR eventName="GenerateDataKey") eventSource="kms.amazonaws.com"
| stats count by userIdentity.arn, requestParameters.keyId, eventName
| sort -count
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  where match(All_Changes.app, "(?i)kms\\.amazonaws") OR match(All_Changes.object, "(?i)kms:|key/")
  by All_Changes.user All_Changes.object All_Changes.action span=1h
| sort -count
```

## Visualization

Table (principal, key, action, count), Trend line, Bar chart.

## References

- [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)
- [CIM: Change](https://docs.splunk.com/Documentation/CIM/latest/User/Change)
