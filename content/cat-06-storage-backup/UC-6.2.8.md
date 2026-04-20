---
id: "6.2.8"
title: "Bucket Policy Change Audit"
criticality: "critical"
splunkPillar: "Security"
---

# UC-6.2.8 · Bucket Policy Change Audit

## Description

Unexpected bucket policy or IAM policy changes can expose data. Audit trail supports SOC2/PCI evidence and fast rollback.

## Value

Unexpected bucket policy or IAM policy changes can expose data. Audit trail supports SOC2/PCI evidence and fast rollback.

## Implementation

Ingest CloudTrail S3 and IAM policy events. Enrich with CMDB owner. Alert on changes outside change windows or from non-break-glass principals.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_aws` (CloudTrail), Azure Activity Log.
• Ensure the following data sources are available: `PutBucketPolicy`, `DeleteBucketPolicy`, `SetContainerAcl` (Azure equivalents).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Ingest CloudTrail S3 and IAM policy events. Enrich with CMDB owner. Alert on changes outside change windows or from non-break-glass principals.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:cloudtrail" eventName IN ("PutBucketPolicy","DeleteBucketPolicy","PutBucketAcl")
| table _time, requestParameters.bucketName, userIdentity.arn, sourceIPAddress, eventName
| sort -_time
```

Understanding this SPL

**Bucket Policy Change Audit** — Unexpected bucket policy or IAM policy changes can expose data. Audit trail supports SOC2/PCI evidence and fast rollback.

Documented **Data sources**: `PutBucketPolicy`, `DeleteBucketPolicy`, `SetContainerAcl` (Azure equivalents). **App/TA** (typical add-on context): `Splunk_TA_aws` (CloudTrail), Azure Activity Log. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:cloudtrail. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=aws, sourcetype="aws:cloudtrail". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Pipeline stage (see **Bucket Policy Change Audit**): table _time, requestParameters.bucketName, userIdentity.arn, sourceIPAddress, eventName
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Timeline (policy changes), Table (bucket, user, action), Single value (changes last 24h).

## SPL

```spl
index=aws sourcetype="aws:cloudtrail" eventName IN ("PutBucketPolicy","DeleteBucketPolicy","PutBucketAcl")
| table _time, requestParameters.bucketName, userIdentity.arn, sourceIPAddress, eventName
| sort -_time
```

## Visualization

Timeline (policy changes), Table (bucket, user, action), Single value (changes last 24h).

## References

- [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)
