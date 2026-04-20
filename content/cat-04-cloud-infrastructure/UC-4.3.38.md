---
id: "4.3.38"
title: "GCS Bucket Policy Changes"
criticality: "critical"
splunkPillar: "Security"
---

# UC-4.3.38 · GCS Bucket Policy Changes

## Description

Public buckets and IAM relaxations are common breach paths; real-time detection limits exposure window.

## Value

Public buckets and IAM relaxations are common breach paths; real-time detection limits exposure window.

## Implementation

Alert on any allUsers/allAuthenticatedUsers binding or removal of org constraints. Weekly review of bucket-level IAM diffs. Integrate with SCC public bucket findings.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_google-cloudplatform`.
• Ensure the following data sources are available: Admin Activity `sourcetype=google:gcp:pubsub:message` (storage.setIamPermissions, bucket updates).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Alert on any allUsers/allAuthenticatedUsers binding or removal of org constraints. Weekly review of bucket-level IAM diffs. Integrate with SCC public bucket findings.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=gcp sourcetype="google:gcp:pubsub:message" protoPayload.serviceName="storage.googleapis.com" protoPayload.methodName="storage.buckets.setIamPermissions"
| spath path=protoPayload.serviceData.policy.bindings{}
| mvexpand protoPayload.serviceData.policy.bindings{} limit=500
| search bindings.members="allUsers" OR bindings.members="allAuthenticatedUsers"
| table _time protoPayload.authenticationInfo.principalEmail resource.labels.bucket_name bindings.role
```

Understanding this SPL

**GCS Bucket Policy Changes** — Public buckets and IAM relaxations are common breach paths; real-time detection limits exposure window.

Documented **Data sources**: Admin Activity `sourcetype=google:gcp:pubsub:message` (storage.setIamPermissions, bucket updates). **App/TA** (typical add-on context): `Splunk_TA_google-cloudplatform`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: gcp; **sourcetype**: google:gcp:pubsub:message. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=gcp, sourcetype="google:gcp:pubsub:message". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Extracts structured paths (JSON/XML) with `spath`.
• Expands multivalue fields with `mvexpand` — use `limit=` to cap row explosion.
• Applies an explicit `search` filter to narrow the current result set.
• Pipeline stage (see **GCS Bucket Policy Changes**): table _time protoPayload.authenticationInfo.principalEmail resource.labels.bucket_name bindings.role

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t count from datamodel=Change.All_Changes by All_Changes.action, All_Changes.object_category, All_Changes.user | sort - count
```

Understanding this CIM / accelerated SPL

**GCS Bucket Policy Changes** — Public buckets and IAM relaxations are common breach paths; real-time detection limits exposure window.

Documented **Data sources**: Admin Activity `sourcetype=google:gcp:pubsub:message` (storage.setIamPermissions, bucket updates). **App/TA** (typical add-on context): `Splunk_TA_google-cloudplatform`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Change.All_Changes` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (bucket, principal, role), Timeline (IAM changes), Single value (public buckets).

## SPL

```spl
index=gcp sourcetype="google:gcp:pubsub:message" protoPayload.serviceName="storage.googleapis.com" protoPayload.methodName="storage.buckets.setIamPermissions"
| spath path=protoPayload.serviceData.policy.bindings{}
| mvexpand protoPayload.serviceData.policy.bindings{} limit=500
| search bindings.members="allUsers" OR bindings.members="allAuthenticatedUsers"
| table _time protoPayload.authenticationInfo.principalEmail resource.labels.bucket_name bindings.role
```

## CIM SPL

```spl
| tstats summariesonly=t count from datamodel=Change.All_Changes by All_Changes.action, All_Changes.object_category, All_Changes.user | sort - count
```

## Visualization

Table (bucket, principal, role), Timeline (IAM changes), Single value (public buckets).

## References

- [Splunk_TA_google-cloudplatform](https://splunkbase.splunk.com/app/3088)
- [CIM: Change](https://docs.splunk.com/Documentation/CIM/latest/User/Change)
