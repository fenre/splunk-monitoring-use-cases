---
id: "4.1.74"
title: "IAM Access Analyzer Findings"
criticality: "medium"
splunkPillar: "Security"
---

# UC-4.1.74 · IAM Access Analyzer Findings

## Description

Access Analyzer identifies unintended external access to S3, IAM roles, KMS keys, and other resources—reducing public exposure risk.

## Value

Access Analyzer identifies unintended external access to S3, IAM roles, KMS keys, and other resources—reducing public exposure risk.

## Implementation

Enable organization-wide analyzer. Send findings to EventBridge and Splunk. Auto-remediate public S3 where policy allows or ticket owners. Weekly review of new external access paths.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_aws`.
• Ensure the following data sources are available: Access Analyzer findings export (EventBridge, Security Hub), `sourcetype=aws:cloudwatch:events`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable organization-wide analyzer. Send findings to EventBridge and Splunk. Auto-remediate public S3 where policy allows or ticket owners. Weekly review of new external access paths.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:cloudwatch:events" detail-type="Access Analyzer Finding" detail.status="ACTIVE"
| stats count by detail.resourceType, detail.principal.awsAccountId, detail.isPublic
| sort -count
```

Understanding this SPL

**IAM Access Analyzer Findings** — Access Analyzer identifies unintended external access to S3, IAM roles, KMS keys, and other resources—reducing public exposure risk.

Documented **Data sources**: Access Analyzer findings export (EventBridge, Security Hub), `sourcetype=aws:cloudwatch:events`. **App/TA** (typical add-on context): `Splunk_TA_aws`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:cloudwatch:events. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=aws, sourcetype="aws:cloudwatch:events". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by detail.resourceType, detail.principal.awsAccountId, detail.isPublic** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (resource type, account, public), Bar chart (findings by type), Single value (active findings).

## SPL

```spl
index=aws sourcetype="aws:cloudwatch:events" detail-type="Access Analyzer Finding" detail.status="ACTIVE"
| stats count by detail.resourceType, detail.principal.awsAccountId, detail.isPublic
| sort -count
```

## Visualization

Table (resource type, account, public), Bar chart (findings by type), Single value (active findings).

## References

- [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)
