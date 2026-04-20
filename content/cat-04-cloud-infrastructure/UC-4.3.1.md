---
id: "4.3.1"
title: "Audit Log Monitoring"
criticality: "high"
splunkPillar: "Security"
---

# UC-4.3.1 · Audit Log Monitoring

## Description

GCP audit logs capture all admin activity and data access. Foundational for security monitoring and compliance in GCP environments.

## Value

GCP audit logs capture all admin activity and data access. Foundational for security monitoring and compliance in GCP environments.

## Implementation

Create a Pub/Sub topic and subscription. Configure a log sink to route audit logs to Pub/Sub. Set up Splunk_TA_google-cloudplatform with a Pub/Sub input. Alert on destructive operations (delete, setIamPolicy).

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_google-cloudplatform`.
• Ensure the following data sources are available: `sourcetype=google:gcp:pubsub:message` (via Pub/Sub).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Create a Pub/Sub topic and subscription. Configure a log sink to route audit logs to Pub/Sub. Set up Splunk_TA_google-cloudplatform with a Pub/Sub input. Alert on destructive operations (delete, setIamPolicy).

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=gcp sourcetype="google:gcp:pubsub:message" logName="*activity"
| spath output=method path=protoPayload.methodName
| spath output=principal path=protoPayload.authenticationInfo.principalEmail
| stats count by principal, method
| sort -count
```

Understanding this SPL

**Audit Log Monitoring** — GCP audit logs capture all admin activity and data access. Foundational for security monitoring and compliance in GCP environments.

Documented **Data sources**: `sourcetype=google:gcp:pubsub:message` (via Pub/Sub). **App/TA** (typical add-on context): `Splunk_TA_google-cloudplatform`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: gcp; **sourcetype**: google:gcp:pubsub:message. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=gcp, sourcetype="google:gcp:pubsub:message". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Extracts structured paths (JSON/XML) with `spath`.
• Extracts structured paths (JSON/XML) with `spath`.
• `stats` rolls up events into metrics; results are split **by principal, method** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  by All_Changes.user All_Changes.object_category All_Changes.action span=1h
| sort -count
```

Understanding this CIM / accelerated SPL

**Audit Log Monitoring** — GCP audit logs capture all admin activity and data access. Foundational for security monitoring and compliance in GCP environments.

Documented **Data sources**: `sourcetype=google:gcp:pubsub:message` (via Pub/Sub). **App/TA** (typical add-on context): `Splunk_TA_google-cloudplatform`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Change.All_Changes` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (principal, method, count), Bar chart, Timeline.

## SPL

```spl
index=gcp sourcetype="google:gcp:pubsub:message" logName="*activity"
| spath output=method path=protoPayload.methodName
| spath output=principal path=protoPayload.authenticationInfo.principalEmail
| stats count by principal, method
| sort -count
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  by All_Changes.user All_Changes.object_category All_Changes.action span=1h
| sort -count
```

## Visualization

Table (principal, method, count), Bar chart, Timeline.

## References

- [Splunk_TA_google-cloudplatform](https://splunkbase.splunk.com/app/3088)
- [CIM: Change](https://docs.splunk.com/Documentation/CIM/latest/User/Change)
