<!-- AUTO-GENERATED from UC-4.1.4.json — DO NOT EDIT -->

---
id: "4.1.4"
title: "IAM Policy Changes"
criticality: "high"
splunkPillar: "Security"
---

# UC-4.1.4 · IAM Policy Changes

## Description

IAM policy changes affect who can do what across the entire AWS account. Unauthorized policy attachments can grant admin access.

## Value

IAM policy changes affect who can do what across the entire AWS account. Unauthorized policy attachments can grant admin access.

## Implementation

Alert on all IAM policy modifications. Critical alert when AdministratorAccess or PowerUserAccess policies are attached. Track with change management.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_aws`.
• Ensure the following data sources are available: `sourcetype=aws:cloudtrail`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Alert on all IAM policy modifications. Critical alert when AdministratorAccess or PowerUserAccess policies are attached. Track with change management.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:cloudtrail" (eventName="CreatePolicy" OR eventName="AttachUserPolicy" OR eventName="AttachRolePolicy" OR eventName="PutUserPolicy" OR eventName="PutRolePolicy" OR eventName="CreateRole")
| table _time userIdentity.arn eventName requestParameters.policyArn requestParameters.roleName
| sort -_time
```

Understanding this SPL

**IAM Policy Changes** — IAM policy changes affect who can do what across the entire AWS account. Unauthorized policy attachments can grant admin access.

Documented **Data sources**: `sourcetype=aws:cloudtrail`. **App/TA** (typical add-on context): `Splunk_TA_aws`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:cloudtrail. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=aws, sourcetype="aws:cloudtrail". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Pipeline stage (see **IAM Policy Changes**): table _time userIdentity.arn eventName requestParameters.policyArn requestParameters.roleName
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  where All_Changes.object_category="policy" OR match(All_Changes.object, "(?i)IAMPolicy|iam:policy")
  by All_Changes.user All_Changes.object All_Changes.action span=1h
| sort -count
```

Understanding this CIM / accelerated SPL

**IAM Policy Changes** — IAM policy changes affect who can do what across the entire AWS account. Unauthorized policy attachments can grant admin access.

Documented **Data sources**: `sourcetype=aws:cloudtrail`. **App/TA** (typical add-on context): `Splunk_TA_aws`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Change.All_Changes` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table, Timeline, Bar chart by event type.

## SPL

```spl
index=aws sourcetype="aws:cloudtrail" (eventName="CreatePolicy" OR eventName="AttachUserPolicy" OR eventName="AttachRolePolicy" OR eventName="PutUserPolicy" OR eventName="PutRolePolicy" OR eventName="CreateRole")
| table _time userIdentity.arn eventName requestParameters.policyArn requestParameters.roleName
| sort -_time
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  where All_Changes.object_category="policy" OR match(All_Changes.object, "(?i)IAMPolicy|iam:policy")
  by All_Changes.user All_Changes.object All_Changes.action span=1h
| sort -count
```

## Visualization

Table, Timeline, Bar chart by event type.

## References

- [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)
- [CIM: Change](https://docs.splunk.com/Documentation/CIM/latest/User/Change)
