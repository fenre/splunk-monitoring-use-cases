<!-- AUTO-GENERATED from UC-4.4.2.json — DO NOT EDIT -->

---
id: "4.4.2"
title: "Cross-Cloud Identity Correlation"
criticality: "medium"
splunkPillar: "Security"
---

# UC-4.4.2 · Cross-Cloud Identity Correlation

## Description

Users often have identities across AWS/Azure/GCP. Correlating activity provides unified view for security investigation and insider threat detection.

## Value

Users often have identities across AWS/Azure/GCP. Correlating activity provides unified view for security investigation and insider threat detection.

## Implementation

Create a lookup table mapping cloud identities to a normalized user (e.g., email). Combine audit logs from all three providers. Dashboard showing cross-cloud activity per user.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Combined cloud TAs + lookup tables.
• Ensure the following data sources are available: All cloud audit logs.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Create a lookup table mapping cloud identities to a normalized user (e.g., email). Combine audit logs from all three providers. Dashboard showing cross-cloud activity per user.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws OR index=azure OR index=gcp
| eval cloud=case(index="aws","AWS", index="azure","Azure", index="gcp","GCP")
| eval user=coalesce(userIdentity.arn, userPrincipalName, protoPayload.authenticationInfo.principalEmail)
| lookup cloud_identity_map user OUTPUT normalized_user
| stats count, dc(cloud) as clouds_active, values(cloud) as clouds by normalized_user
| where clouds_active > 1
| sort -count
```

Understanding this SPL

**Cross-Cloud Identity Correlation** — Users often have identities across AWS/Azure/GCP. Correlating activity provides unified view for security investigation and insider threat detection.

Documented **Data sources**: All cloud audit logs. **App/TA** (typical add-on context): Combined cloud TAs + lookup tables. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws, azure, gcp.

**Pipeline walkthrough**

• Scopes the data: index=aws, index=azure, index=gcp. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **cloud** — often to normalize units, derive a ratio, or prepare for thresholds.
• `eval` defines or adjusts **user** — often to normalize units, derive a ratio, or prepare for thresholds.
• Enriches events using `lookup` (lookup definition + optional OUTPUT fields).
• `stats` rolls up events into metrics; results are split **by normalized_user** so each row reflects one combination of those dimensions.
• Filters the current rows with `where clouds_active > 1` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (user, clouds, activity count), Sankey diagram (user to cloud to action).

## SPL

```spl
index=aws OR index=azure OR index=gcp
| eval cloud=case(index="aws","AWS", index="azure","Azure", index="gcp","GCP")
| eval user=coalesce(userIdentity.arn, userPrincipalName, protoPayload.authenticationInfo.principalEmail)
| lookup cloud_identity_map user OUTPUT normalized_user
| stats count, dc(cloud) as clouds_active, values(cloud) as clouds by normalized_user
| where clouds_active > 1
| sort -count
```

## Visualization

Table (user, clouds, activity count), Sankey diagram (user to cloud to action).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
