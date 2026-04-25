<!-- AUTO-GENERATED from UC-4.1.55.json — DO NOT EDIT -->

---
id: "4.1.55"
title: "Secrets Manager Secret Rotation and Access"
criticality: "high"
splunkPillar: "Security"
---

# UC-4.1.55 · Secrets Manager Secret Rotation and Access

## Description

Failed rotation leaves stale credentials. Unusual access patterns may indicate credential abuse. Audit supports compliance and incident response.

## Value

Failed rotation leaves stale credentials. Unusual access patterns may indicate credential abuse. Audit supports compliance and incident response.

## Implementation

CloudTrail logs Secrets Manager API. Alert on RotateSecret failures. Baseline GetSecretValue by principal and secret; alert on anomalous access (new principal, spike in access). Track rotation schedule compliance.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_aws`.
• Ensure the following data sources are available: CloudTrail (RotateSecret, GetSecretValue, DescribeSecret).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
CloudTrail logs Secrets Manager API. Alert on RotateSecret failures. Baseline GetSecretValue by principal and secret; alert on anomalous access (new principal, spike in access). Track rotation schedule compliance.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:cloudtrail" eventSource="secretsmanager.amazonaws.com" (eventName="RotateSecret" OR eventName="GetSecretValue")
| stats count by userIdentity.arn eventName requestParameters.secretId
| sort -count
```

Understanding this SPL

**Secrets Manager Secret Rotation and Access** — Failed rotation leaves stale credentials. Unusual access patterns may indicate credential abuse. Audit supports compliance and incident response.

Documented **Data sources**: CloudTrail (RotateSecret, GetSecretValue, DescribeSecret). **App/TA** (typical add-on context): `Splunk_TA_aws`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:cloudtrail. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=aws, sourcetype="aws:cloudtrail". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by userIdentity.arn eventName requestParameters.secretId** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  where match(All_Changes.app, "(?i)secretsmanager\\.amazonaws") OR match(All_Changes.object, "(?i)secret:")
  by All_Changes.user All_Changes.object All_Changes.action span=1h
| sort -count
```

Understanding this CIM / accelerated SPL

**Secrets Manager Secret Rotation and Access** — Failed rotation leaves stale credentials. Unusual access patterns may indicate credential abuse. Audit supports compliance and incident response.

Documented **Data sources**: CloudTrail (RotateSecret, GetSecretValue, DescribeSecret). **App/TA** (typical add-on context): `Splunk_TA_aws`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Change.All_Changes` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (principal, secret, action, count), Timeline (rotation events), Bar chart by secret.

## SPL

```spl
index=aws sourcetype="aws:cloudtrail" eventSource="secretsmanager.amazonaws.com" (eventName="RotateSecret" OR eventName="GetSecretValue")
| stats count by userIdentity.arn eventName requestParameters.secretId
| sort -count
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  where match(All_Changes.app, "(?i)secretsmanager\\.amazonaws") OR match(All_Changes.object, "(?i)secret:")
  by All_Changes.user All_Changes.object All_Changes.action span=1h
| sort -count
```

## Visualization

Table (principal, secret, action, count), Timeline (rotation events), Bar chart by secret.

## References

- [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)
- [CIM: Change](https://docs.splunk.com/Documentation/CIM/latest/User/Change)
