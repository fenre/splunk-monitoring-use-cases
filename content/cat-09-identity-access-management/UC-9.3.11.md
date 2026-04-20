---
id: "9.3.11"
title: "Federated Trust Modifications"
criticality: "critical"
splunkPillar: "Security"
---

# UC-9.3.11 · Federated Trust Modifications

## Description

Adding SAML/OIDC federation to new domains or apps expands blast radius; auditing trust metadata changes is essential.

## Value

Adding SAML/OIDC federation to new domains or apps expands blast radius; auditing trust metadata changes is essential.

## Implementation

Alert on new federation partners, domain verification, or IdP metadata uploads. Require security review for new trust relationships.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_microsoft-cloudservices`, `Splunk_TA_okta`.
• Ensure the following data sources are available: Entra `Add federation to domain`, Okta `trustedOrigin.*` / `idp.*` lifecycle events.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Alert on new federation partners, domain verification, or IdP metadata uploads. Require security review for new trust relationships.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=azure sourcetype="azure:aad:audit" activityDisplayName="Add external user"
   OR activityDisplayName="Add federation to domain"
| table _time, initiatedBy.user.userPrincipalName, targetResources{}.displayName, activityDisplayName
| sort -_time
```

Understanding this SPL

**Federated Trust Modifications** — Adding SAML/OIDC federation to new domains or apps expands blast radius; auditing trust metadata changes is essential.

Documented **Data sources**: Entra `Add federation to domain`, Okta `trustedOrigin.*` / `idp.*` lifecycle events. **App/TA** (typical add-on context): `Splunk_TA_microsoft-cloudservices`, `Splunk_TA_okta`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: azure; **sourcetype**: azure:aad:audit. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=azure, sourcetype="azure:aad:audit". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Pipeline stage (see **Federated Trust Modifications**): table _time, initiatedBy.user.userPrincipalName, targetResources{}.displayName, activityDisplayName
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t count from datamodel=Change.All_Changes by All_Changes.action, All_Changes.object_category, All_Changes.user | sort - count
```

Understanding this CIM / accelerated SPL

**Federated Trust Modifications** — Adding SAML/OIDC federation to new domains or apps expands blast radius; auditing trust metadata changes is essential.

Documented **Data sources**: Entra `Add federation to domain`, Okta `trustedOrigin.*` / `idp.*` lifecycle events. **App/TA** (typical add-on context): `Splunk_TA_microsoft-cloudservices`, `Splunk_TA_okta`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Change.All_Changes` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Timeline (trust changes), Table (actor, target), Single value (new trusts per quarter).

## SPL

```spl
index=azure sourcetype="azure:aad:audit" activityDisplayName="Add external user"
   OR activityDisplayName="Add federation to domain"
| table _time, initiatedBy.user.userPrincipalName, targetResources{}.displayName, activityDisplayName
| sort -_time
```

## CIM SPL

```spl
| tstats summariesonly=t count from datamodel=Change.All_Changes by All_Changes.action, All_Changes.object_category, All_Changes.user | sort - count
```

## Visualization

Timeline (trust changes), Table (actor, target), Single value (new trusts per quarter).

## Known False Positives

Administrative tasks, scheduled jobs or platform updates can match this pattern — correlate with change management, maintenance windows and user role before raising severity.

## References

- [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)
- [Splunk_TA_okta](https://splunkbase.splunk.com/app/6553)
- [CIM: Change](https://docs.splunk.com/Documentation/CIM/latest/User/Change)
