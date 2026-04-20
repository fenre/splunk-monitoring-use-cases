---
id: "4.3.2"
title: "IAM Policy Changes"
criticality: "critical"
splunkPillar: "Security"
---

# UC-4.3.2 · IAM Policy Changes

## Description

IAM binding changes control who can access what in GCP. Unauthorized changes to bindings on projects, folders, or organizations are critical security events.

## Value

IAM binding changes control who can access what in GCP. Unauthorized changes to bindings on projects, folders, or organizations are critical security events.

## Implementation

Forward admin activity logs via Pub/Sub. Alert on `SetIamPolicy` events, especially those granting `roles/owner` or `roles/editor`. Track with change management.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_google-cloudplatform`.
• Ensure the following data sources are available: `sourcetype=google:gcp:pubsub:message`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Forward admin activity logs via Pub/Sub. Alert on `SetIamPolicy` events, especially those granting `roles/owner` or `roles/editor`. Track with change management.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=gcp sourcetype="google:gcp:pubsub:message" protoPayload.methodName="SetIamPolicy"
| spath output=resource path=resource.labels
| spath output=principal path=protoPayload.authenticationInfo.principalEmail
| table _time principal resource protoPayload.serviceData.policyDelta.bindingDeltas{}
| sort -_time
```

Understanding this SPL

**IAM Policy Changes** — IAM binding changes control who can access what in GCP. Unauthorized changes to bindings on projects, folders, or organizations are critical security events.

Documented **Data sources**: `sourcetype=google:gcp:pubsub:message`. **App/TA** (typical add-on context): `Splunk_TA_google-cloudplatform`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: gcp; **sourcetype**: google:gcp:pubsub:message. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=gcp, sourcetype="google:gcp:pubsub:message". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Extracts structured paths (JSON/XML) with `spath`.
• Extracts structured paths (JSON/XML) with `spath`.
• Pipeline stage (see **IAM Policy Changes**): table _time principal resource protoPayload.serviceData.policyDelta.bindingDeltas{}
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  by All_Changes.user All_Changes.object_category All_Changes.action span=1h
| sort -count
```

Understanding this CIM / accelerated SPL

**IAM Policy Changes** — IAM binding changes control who can access what in GCP. Unauthorized changes to bindings on projects, folders, or organizations are critical security events.

Documented **Data sources**: `sourcetype=google:gcp:pubsub:message`. **App/TA** (typical add-on context): `Splunk_TA_google-cloudplatform`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Change.All_Changes` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Events list (critical), Table (who changed what), Timeline.

## SPL

```spl
index=gcp sourcetype="google:gcp:pubsub:message" protoPayload.methodName="SetIamPolicy"
| spath output=resource path=resource.labels
| spath output=principal path=protoPayload.authenticationInfo.principalEmail
| table _time principal resource protoPayload.serviceData.policyDelta.bindingDeltas{}
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

Events list (critical), Table (who changed what), Timeline.

## References

- [Splunk_TA_google-cloudplatform](https://splunkbase.splunk.com/app/3088)
- [CIM: Change](https://docs.splunk.com/Documentation/CIM/latest/User/Change)
