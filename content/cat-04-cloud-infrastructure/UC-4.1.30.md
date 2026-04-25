<!-- AUTO-GENERATED from UC-4.1.30.json — DO NOT EDIT -->

---
id: "4.1.30"
title: "CloudTrail Log File Delivery Failures"
criticality: "critical"
splunkPillar: "Security"
---

# UC-4.1.30 · CloudTrail Log File Delivery Failures

## Description

Failed CloudTrail delivery means audit gaps. Attackers may target trail deletion or S3 permissions to hide activity.

## Value

Failed CloudTrail delivery means audit gaps. Attackers may target trail deletion or S3 permissions to hide activity.

## Implementation

Enable CloudTrail log file validation. Monitor for DeleteTrail, PutBucketPolicy on the trail bucket, or S3 access denied to trail bucket. Use AWS Config or custom Lambda to validate delivery and alert on gaps.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_aws`.
• Ensure the following data sources are available: CloudTrail insight events, S3 bucket event notifications, or CloudWatch Logs for trail validation.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable CloudTrail log file validation. Monitor for DeleteTrail, PutBucketPolicy on the trail bucket, or S3 access denied to trail bucket. Use AWS Config or custom Lambda to validate delivery and alert on gaps.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:cloudtrail" eventName="DeleteTrail" OR eventName="PutBucketPolicy" requestParameters.name=*
| table _time userIdentity.arn eventName requestParameters.bucketName
| sort -_time
```

Understanding this SPL

**CloudTrail Log File Delivery Failures** — Failed CloudTrail delivery means audit gaps. Attackers may target trail deletion or S3 permissions to hide activity.

Documented **Data sources**: CloudTrail insight events, S3 bucket event notifications, or CloudWatch Logs for trail validation. **App/TA** (typical add-on context): `Splunk_TA_aws`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:cloudtrail. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=aws, sourcetype="aws:cloudtrail". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Pipeline stage (see **CloudTrail Log File Delivery Failures**): table _time userIdentity.arn eventName requestParameters.bucketName
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  where match(All_Changes.action, "(?i)DeleteTrail|StopLogging|UpdateTrail|PutBucketPolicy|PutEventSelectors") OR match(All_Changes.object, "(?i)cloudtrail|trail")
  by All_Changes.user All_Changes.object All_Changes.action span=1h
| sort -count
```

Understanding this CIM / accelerated SPL

**CloudTrail Log File Delivery Failures** — Failed CloudTrail delivery means audit gaps. Attackers may target trail deletion or S3 permissions to hide activity.

Documented **Data sources**: CloudTrail insight events, S3 bucket event notifications, or CloudWatch Logs for trail validation. **App/TA** (typical add-on context): `Splunk_TA_aws`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Change.All_Changes` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Events list (critical), Table (trail, bucket, event), Timeline.

## SPL

```spl
index=aws sourcetype="aws:cloudtrail" eventName="DeleteTrail" OR eventName="PutBucketPolicy" requestParameters.name=*
| table _time userIdentity.arn eventName requestParameters.bucketName
| sort -_time
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  where match(All_Changes.action, "(?i)DeleteTrail|StopLogging|UpdateTrail|PutBucketPolicy|PutEventSelectors") OR match(All_Changes.object, "(?i)cloudtrail|trail")
  by All_Changes.user All_Changes.object All_Changes.action span=1h
| sort -count
```

## Visualization

Events list (critical), Table (trail, bucket, event), Timeline.

## References

- [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)
- [CIM: Change](https://docs.splunk.com/Documentation/CIM/latest/User/Change)
