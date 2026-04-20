---
id: "4.1.1"
title: "Unauthorized API Calls"
criticality: "high"
splunkPillar: "Security"
---

# UC-4.1.1 · Unauthorized API Calls

## Description

AccessDenied errors reveal reconnaissance activity, compromised credentials with insufficient permissions, or misconfigurations. Early indicator of attack or drift.

## Value

AccessDenied errors reveal reconnaissance activity, compromised credentials with insufficient permissions, or misconfigurations. Early indicator of attack or drift.

## Implementation

Configure CloudTrail to send logs to an S3 bucket. Set up the Splunk_TA_aws with an SQS-based S3 input for CloudTrail. Alert when a single principal gets >5 access denied errors in 10 minutes.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_aws`.
• Ensure the following data sources are available: `sourcetype=aws:cloudtrail`, CloudTrail logs.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Configure CloudTrail to send logs to an S3 bucket. Set up the Splunk_TA_aws with an SQS-based S3 input for CloudTrail. Alert when a single principal gets >5 access denied errors in 10 minutes.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:cloudtrail" errorCode="AccessDenied" OR errorCode="UnauthorizedAccess" OR errorCode="Client.UnauthorizedAccess"
| stats count by userIdentity.arn, eventName, sourceIPAddress, errorCode
| where count > 5
| sort -count
```

Understanding this SPL

**Unauthorized API Calls** — AccessDenied errors reveal reconnaissance activity, compromised credentials with insufficient permissions, or misconfigurations. Early indicator of attack or drift.

Documented **Data sources**: `sourcetype=aws:cloudtrail`, CloudTrail logs. **App/TA** (typical add-on context): `Splunk_TA_aws`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:cloudtrail. That sourcetype matches what this use case lists under Data sources.

**Detection type** for this use case: TTP — interpret thresholds and fields in that context.

**Pipeline walkthrough**

• Scopes the data: index=aws, sourcetype="aws:cloudtrail". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by userIdentity.arn, eventName, sourceIPAddress, errorCode** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where count > 5` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action="failure"
  by Authentication.user Authentication.src Authentication.app span=1h
| sort -count
```

Understanding this CIM / accelerated SPL

**Unauthorized API Calls** — AccessDenied errors reveal reconnaissance activity, compromised credentials with insufficient permissions, or misconfigurations. Early indicator of attack or drift.

Documented **Data sources**: `sourcetype=aws:cloudtrail`, CloudTrail logs. **App/TA** (typical add-on context): `Splunk_TA_aws`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Detection type** for this use case: TTP — interpret thresholds and fields in that context.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Authentication.Authentication` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (principal, API call, source IP, count), Bar chart by principal, Map (source IP GeoIP).

## SPL

```spl
index=aws sourcetype="aws:cloudtrail" errorCode="AccessDenied" OR errorCode="UnauthorizedAccess" OR errorCode="Client.UnauthorizedAccess"
| stats count by userIdentity.arn, eventName, sourceIPAddress, errorCode
| where count > 5
| sort -count
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action="failure"
  by Authentication.user Authentication.src Authentication.app span=1h
| sort -count
```

## Visualization

Table (principal, API call, source IP, count), Bar chart by principal, Map (source IP GeoIP).

## Known False Positives

Legitimate access denied for least-privilege testing or new IAM policies; verify with change management.

## References

- [Splunk Add-on for AWS](https://splunkbase.splunk.com/app/1876)
- [AWS CloudTrail](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/)
