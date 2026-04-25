<!-- AUTO-GENERATED from UC-4.3.28.json — DO NOT EDIT -->

---
id: "4.3.28"
title: "VPC Service Controls Violations"
criticality: "critical"
splunkPillar: "Security"
---

# UC-4.3.28 · VPC Service Controls Violations

## Description

Real-time violation tracking complements perimeter design reviews and catches data exfiltration paths early.

## Value

Real-time violation tracking complements perimeter design reviews and catches data exfiltration paths early.

## Implementation

Ensure VPC SC dry-run and enforce modes both log. Route to SIEM with severity by service (BigQuery, GCS). Weekly review of top principals for false positives.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_google-cloudplatform`.
• Ensure the following data sources are available: Access Context Manager audit via `sourcetype=google:gcp:pubsub:message`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Ensure VPC SC dry-run and enforce modes both log. Route to SIEM with severity by service (BigQuery, GCS). Weekly review of top principals for false positives.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=gcp sourcetype="google:gcp:pubsub:message" protoPayload.serviceName="accesscontextmanager.googleapis.com"
| search violation OR denied OR blocked
| stats count by protoPayload.authenticationInfo.principalEmail, resource.labels.project_id
| sort -count
```

Understanding this SPL

**VPC Service Controls Violations** — Real-time violation tracking complements perimeter design reviews and catches data exfiltration paths early.

Documented **Data sources**: Access Context Manager audit via `sourcetype=google:gcp:pubsub:message`. **App/TA** (typical add-on context): `Splunk_TA_google-cloudplatform`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: gcp; **sourcetype**: google:gcp:pubsub:message. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=gcp, sourcetype="google:gcp:pubsub:message". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Applies an explicit `search` filter to narrow the current result set.
• `stats` rolls up events into metrics; results are split **by protoPayload.authenticationInfo.principalEmail, resource.labels.project_id** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (principal, project, count), Timeline (violations), Pie chart (service).

## SPL

```spl
index=gcp sourcetype="google:gcp:pubsub:message" protoPayload.serviceName="accesscontextmanager.googleapis.com"
| search violation OR denied OR blocked
| stats count by protoPayload.authenticationInfo.principalEmail, resource.labels.project_id
| sort -count
```

## Visualization

Table (principal, project, count), Timeline (violations), Pie chart (service).

## References

- [Splunk_TA_google-cloudplatform](https://splunkbase.splunk.com/app/3088)
