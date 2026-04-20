---
id: "4.3.18"
title: "Cloud IAM Policy and Binding Changes (Beyond SetIamPolicy)"
criticality: "high"
splunkPillar: "Security"
---

# UC-4.3.18 · Cloud IAM Policy and Binding Changes (Beyond SetIamPolicy)

## Description

IAM policy and custom role changes affect who can access resources. Broader than SetIamPolicy — includes role create/delete and org policy.

## Value

IAM policy and custom role changes affect who can access resources. Broader than SetIamPolicy — includes role create/delete and org policy.

## Implementation

Forward IAM and Admin API audit logs. Alert on CreateRole, DeleteRole, SetIamPolicy on project/folder/org. Track custom role changes. Correlate with security review process.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_google-cloudplatform`.
• Ensure the following data sources are available: Audit logs (iam.googleapis.com, admin.googleapis.com).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Forward IAM and Admin API audit logs. Alert on CreateRole, DeleteRole, SetIamPolicy on project/folder/org. Track custom role changes. Correlate with security review process.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=gcp sourcetype="google:gcp:pubsub:message" protoPayload.serviceName="iam.googleapis.com" (protoPayload.methodName=*Create* OR protoPayload.methodName=*Delete* OR protoPayload.methodName=*Update*)
| table _time protoPayload.authenticationInfo.principalEmail protoPayload.methodName resource.labels
| sort -_time
```

Understanding this SPL

**Cloud IAM Policy and Binding Changes (Beyond SetIamPolicy)** — IAM policy and custom role changes affect who can access resources. Broader than SetIamPolicy — includes role create/delete and org policy.

Documented **Data sources**: Audit logs (iam.googleapis.com, admin.googleapis.com). **App/TA** (typical add-on context): `Splunk_TA_google-cloudplatform`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: gcp; **sourcetype**: google:gcp:pubsub:message. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=gcp, sourcetype="google:gcp:pubsub:message". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Pipeline stage (see **Cloud IAM Policy and Binding Changes (Beyond SetIamPolicy)**): table _time protoPayload.authenticationInfo.principalEmail protoPayload.methodName resource.labels
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  by All_Changes.user All_Changes.object_category All_Changes.action span=1h
| sort -count
```

Understanding this CIM / accelerated SPL

**Cloud IAM Policy and Binding Changes (Beyond SetIamPolicy)** — IAM policy and custom role changes affect who can access resources. Broader than SetIamPolicy — includes role create/delete and org policy.

Documented **Data sources**: Audit logs (iam.googleapis.com, admin.googleapis.com). **App/TA** (typical add-on context): `Splunk_TA_google-cloudplatform`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Change.All_Changes` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (principal, method, resource), Timeline (IAM changes), Bar chart by method.

## SPL

```spl
index=gcp sourcetype="google:gcp:pubsub:message" protoPayload.serviceName="iam.googleapis.com" (protoPayload.methodName=*Create* OR protoPayload.methodName=*Delete* OR protoPayload.methodName=*Update*)
| table _time protoPayload.authenticationInfo.principalEmail protoPayload.methodName resource.labels
| sort -_time
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  by All_Changes.user All_Changes.object_category All_Changes.action span=1h
| sort -count
```

## Visualization

Table (principal, method, resource), Timeline (IAM changes), Bar chart by method.

## References

- [Splunk_TA_google-cloudplatform](https://splunkbase.splunk.com/app/3088)
- [CIM: Change](https://docs.splunk.com/Documentation/CIM/latest/User/Change)
