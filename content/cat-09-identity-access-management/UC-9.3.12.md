---
id: "9.3.12"
title: "Consent Grant Abuse"
criticality: "critical"
splunkPillar: "Security"
---

# UC-9.3.12 · Consent Grant Abuse

## Description

Users granting excessive delegated permissions to malicious OAuth apps is a common attack; monitoring consent events enables revocation.

## Value

Users granting excessive delegated permissions to malicious OAuth apps is a common attack; monitoring consent events enables revocation.

## Implementation

Ingest consent-related audit events. Alert on consent to apps with high privilege (`RoleManagement.ReadWrite.Directory`) or new publisher IDs. Integrate with admin consent workflow.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_microsoft-cloudservices`.
• Ensure the following data sources are available: Entra audit logs (`Consent to application`, `Add OAuth2PermissionGrant`).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Ingest consent-related audit events. Alert on consent to apps with high privilege (`RoleManagement.ReadWrite.Directory`) or new publisher IDs. Integrate with admin consent workflow.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=azure sourcetype="azure:aad:audit"
| search "Consent" OR activityDisplayName="Add OAuth2PermissionGrant"
| spath path=targetResources{}
| mvexpand targetResources{} limit=500
| spath input=targetResources{} path=displayName
| table _time, initiatedBy.user.userPrincipalName, displayName, activityDisplayName
| sort -_time
```

Understanding this SPL

**Consent Grant Abuse** — Users granting excessive delegated permissions to malicious OAuth apps is a common attack; monitoring consent events enables revocation.

Documented **Data sources**: Entra audit logs (`Consent to application`, `Add OAuth2PermissionGrant`). **App/TA** (typical add-on context): `Splunk_TA_microsoft-cloudservices`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: azure; **sourcetype**: azure:aad:audit. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=azure, sourcetype="azure:aad:audit". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Applies an explicit `search` filter to narrow the current result set.
• Extracts structured paths (JSON/XML) with `spath`.
• Expands multivalue fields with `mvexpand` — use `limit=` to cap row explosion.
• Extracts structured paths (JSON/XML) with `spath`.
• Pipeline stage (see **Consent Grant Abuse**): table _time, initiatedBy.user.userPrincipalName, displayName, activityDisplayName
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t count from datamodel=Change.All_Changes by All_Changes.action, All_Changes.object_category, All_Changes.user | sort - count
```

Understanding this CIM / accelerated SPL

**Consent Grant Abuse** — Users granting excessive delegated permissions to malicious OAuth apps is a common attack; monitoring consent events enables revocation.

Documented **Data sources**: Entra audit logs (`Consent to application`, `Add OAuth2PermissionGrant`). **App/TA** (typical add-on context): `Splunk_TA_microsoft-cloudservices`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Change.All_Changes` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (consent events), Bar chart (apps by consent count), Pie chart (user vs admin consent).

## SPL

```spl
index=azure sourcetype="azure:aad:audit"
| search "Consent" OR activityDisplayName="Add OAuth2PermissionGrant"
| spath path=targetResources{}
| mvexpand targetResources{} limit=500
| spath input=targetResources{} path=displayName
| table _time, initiatedBy.user.userPrincipalName, displayName, activityDisplayName
| sort -_time
```

## CIM SPL

```spl
| tstats summariesonly=t count from datamodel=Change.All_Changes by All_Changes.action, All_Changes.object_category, All_Changes.user | sort - count
```

## Visualization

Table (consent events), Bar chart (apps by consent count), Pie chart (user vs admin consent).

## Known False Positives

Administrative tasks, scheduled jobs or platform updates can match this pattern — correlate with change management, maintenance windows and user role before raising severity.

## References

- [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)
- [CIM: Change](https://docs.splunk.com/Documentation/CIM/latest/User/Change)
