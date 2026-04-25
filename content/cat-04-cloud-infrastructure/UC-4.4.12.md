<!-- AUTO-GENERATED from UC-4.4.12.json — DO NOT EDIT -->

---
id: "4.4.12"
title: "Multi-Cloud Identity and Access Anomalies"
criticality: "high"
splunkPillar: "Security"
---

# UC-4.4.12 · Multi-Cloud Identity and Access Anomalies

## Description

Correlating identity activity across AWS IAM, Entra ID, and GCP IAM detects cross-cloud abuse and compromised identities.

## Value

Correlating identity activity across AWS IAM, Entra ID, and GCP IAM detects cross-cloud abuse and compromised identities.

## Implementation

Normalize principal IDs to a common identity (e.g. email). Ingest IAM and sign-in events from all clouds. Baseline activity per identity; alert on first-time cross-cloud activity or impossible travel across cloud regions. Use for insider threat and compromise detection.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Combined cloud TAs, identity lookup tables.
• Ensure the following data sources are available: CloudTrail (IAM), Entra ID sign-in/audit, GCP audit (IAM).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Normalize principal IDs to a common identity (e.g. email). Ingest IAM and sign-in events from all clouds. Baseline activity per identity; alert on first-time cross-cloud activity or impossible travel across cloud regions. Use for insider threat and compromise detection.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws OR index=azure OR index=gcp
| eval user=coalesce(userIdentity.principalId, userPrincipalName, protoPayload.authenticationInfo.principalEmail)
| lookup identity_normalized user OUTPUT normalized_id
| stats count dc(index) as clouds values(index) as indices by normalized_id
| where clouds >= 2
| sort -count
```

Understanding this SPL

**Multi-Cloud Identity and Access Anomalies** — Correlating identity activity across AWS IAM, Entra ID, and GCP IAM detects cross-cloud abuse and compromised identities.

Documented **Data sources**: CloudTrail (IAM), Entra ID sign-in/audit, GCP audit (IAM). **App/TA** (typical add-on context): Combined cloud TAs, identity lookup tables. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws, azure, gcp.

**Pipeline walkthrough**

• Scopes the data: index=aws, index=azure, index=gcp. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **user** — often to normalize units, derive a ratio, or prepare for thresholds.
• Enriches events using `lookup` (lookup definition + optional OUTPUT fields).
• `stats` rolls up events into metrics; results are split **by normalized_id** so each row reflects one combination of those dimensions.
• Filters the current rows with `where clouds >= 2` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (identity, clouds, activity count), Sankey (identity to cloud to action), Timeline (cross-cloud events).

## SPL

```spl
index=aws OR index=azure OR index=gcp
| eval user=coalesce(userIdentity.principalId, userPrincipalName, protoPayload.authenticationInfo.principalEmail)
| lookup identity_normalized user OUTPUT normalized_id
| stats count dc(index) as clouds values(index) as indices by normalized_id
| where clouds >= 2
| sort -count
```

## Visualization

Table (identity, clouds, activity count), Sankey (identity to cloud to action), Timeline (cross-cloud events).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
