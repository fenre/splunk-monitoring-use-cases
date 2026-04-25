<!-- AUTO-GENERATED from UC-6.2.3.json — DO NOT EDIT -->

---
id: "6.2.3"
title: "Public Bucket Detection"
criticality: "critical"
splunkPillar: "Security"
---

# UC-6.2.3 · Public Bucket Detection

## Description

Public buckets are a top cloud security risk, leading to data breaches. Immediate detection is essential for compliance.

## Value

Public buckets are a top cloud security risk, leading to data breaches. Immediate detection is essential for compliance.

## Implementation

Enable AWS Config rules for S3 public access. Ingest Config compliance data. Create critical alert for any NON_COMPLIANT result. Also monitor S3 Block Public Access settings at account level.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_aws` (Config), Azure Policy.
• Ensure the following data sources are available: AWS Config rules, S3 ACL/policy evaluations.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable AWS Config rules for S3 public access. Ingest Config compliance data. Create critical alert for any NON_COMPLIANT result. Also monitor S3 Block Public Access settings at account level.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:config:rule"
| search configRuleName="s3-bucket-public-read-prohibited" OR configRuleName="s3-bucket-public-write-prohibited"
| where complianceType="NON_COMPLIANT"
| table _time, resourceId, configRuleName, complianceType
```

Understanding this SPL

**Public Bucket Detection** — Public buckets are a top cloud security risk, leading to data breaches. Immediate detection is essential for compliance.

Documented **Data sources**: AWS Config rules, S3 ACL/policy evaluations. **App/TA** (typical add-on context): `Splunk_TA_aws` (Config), Azure Policy. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:config:rule. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=aws, sourcetype="aws:config:rule". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Applies an explicit `search` filter to narrow the current result set.
• Filters the current rows with `where complianceType="NON_COMPLIANT"` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Public Bucket Detection**): table _time, resourceId, configRuleName, complianceType


Step 3 — Validate
Compare the same metric, object name, and interval in the vendor or cloud console (array, backup, or object store) that is the source of truth for this feed.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Include who owns the cloud account and the bucket lifecycle policy, because object alerts often need a finance or app owner, not only the storage team. Consider visualizations: Single value (public bucket count — should be 0), Table (non-compliant buckets), Status indicator (red/green).

## SPL

```spl
index=aws sourcetype="aws:config:rule"
| search configRuleName="s3-bucket-public-read-prohibited" OR configRuleName="s3-bucket-public-write-prohibited"
| where complianceType="NON_COMPLIANT"
| table _time, resourceId, configRuleName, complianceType
```

## CIM SPL

```spl
| tstats `summariesonly` count as events
  from datamodel=Web.Web
  by Web.http_method Web.dest span=5m
| sort -events
```

## Visualization

Single value (public bucket count — should be 0), Table (non-compliant buckets), Status indicator (red/green).

## References

- [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)
- [CIM: Web](https://docs.splunk.com/Documentation/CIM/latest/User/Web)
