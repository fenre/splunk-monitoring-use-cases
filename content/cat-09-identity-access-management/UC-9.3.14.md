---
id: "9.3.14"
title: "Multi-Tenant App Access Anomalies"
criticality: "high"
splunkPillar: "Security"
---

# UC-9.3.14 · Multi-Tenant App Access Anomalies

## Description

Unexpected tenants or guest users accessing multi-tenant apps may indicate consent phishing or lateral SaaS movement.

## Value

Unexpected tenants or guest users accessing multi-tenant apps may indicate consent phishing or lateral SaaS movement.

## Implementation

Baseline B2B access patterns. Alert on new resource tenants for crown-jewel apps. Correlate with consent events (UC-9.3.12).

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_microsoft-cloudservices`.
• Ensure the following data sources are available: Entra sign-in logs (`resourceTenantId`, `crossTenantAccessType`, `homeTenantId`).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Baseline B2B access patterns. Alert on new resource tenants for crown-jewel apps. Correlate with consent events (UC-9.3.12).

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=azure sourcetype="azure:aad:signin"
| where crossTenantAccessType IN ("b2bCollaboration","passthrough") AND resourceTenantId!=homeTenantId
| stats count by userPrincipalName, appDisplayName, resourceTenantId
| where count > 10
| sort -count
```

Understanding this SPL

**Multi-Tenant App Access Anomalies** — Unexpected tenants or guest users accessing multi-tenant apps may indicate consent phishing or lateral SaaS movement.

Documented **Data sources**: Entra sign-in logs (`resourceTenantId`, `crossTenantAccessType`, `homeTenantId`). **App/TA** (typical add-on context): `Splunk_TA_microsoft-cloudservices`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: azure; **sourcetype**: azure:aad:signin. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=azure, sourcetype="azure:aad:signin". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where crossTenantAccessType IN ("b2bCollaboration","passthrough") AND resourceTenantId!=homeTenantId` — typically the threshold or rule expression for this monitoring goal.
• `stats` rolls up events into metrics; results are split **by userPrincipalName, appDisplayName, resourceTenantId** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where count > 10` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t count from datamodel=Authentication.Authentication by Authentication.action, Authentication.user, Authentication.src | sort - count
```

Understanding this CIM / accelerated SPL

**Multi-Tenant App Access Anomalies** — Unexpected tenants or guest users accessing multi-tenant apps may indicate consent phishing or lateral SaaS movement.

Documented **Data sources**: Entra sign-in logs (`resourceTenantId`, `crossTenantAccessType`, `homeTenantId`). **App/TA** (typical add-on context): `Splunk_TA_microsoft-cloudservices`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Authentication.Authentication` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (cross-tenant access), Heatmap (user × tenant), Line chart (volume).

## SPL

```spl
index=azure sourcetype="azure:aad:signin"
| where crossTenantAccessType IN ("b2bCollaboration","passthrough") AND resourceTenantId!=homeTenantId
| stats count by userPrincipalName, appDisplayName, resourceTenantId
| where count > 10
| sort -count
```

## CIM SPL

```spl
| tstats summariesonly=t count from datamodel=Authentication.Authentication by Authentication.action, Authentication.user, Authentication.src | sort - count
```

## Visualization

Table (cross-tenant access), Heatmap (user × tenant), Line chart (volume).

## Known False Positives

Administrative tasks, scheduled jobs or platform updates can match this pattern — correlate with change management, maintenance windows and user role before raising severity.

## References

- [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)
- [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)
