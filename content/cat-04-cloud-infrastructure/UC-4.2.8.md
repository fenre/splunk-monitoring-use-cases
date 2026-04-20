---
id: "4.2.8"
title: "Azure Key Vault Access Audit"
criticality: "high"
splunkPillar: "Security"
---

# UC-4.2.8 · Azure Key Vault Access Audit

## Description

Key Vault stores secrets, keys, and certificates. Unauthorized or anomalous access could indicate credential theft or data breach preparation.

## Value

Key Vault stores secrets, keys, and certificates. Unauthorized or anomalous access could indicate credential theft or data breach preparation.

## Implementation

Enable Key Vault diagnostic logging. Monitor all access operations. Alert on failed access attempts and unusual access patterns (new principals accessing secrets).

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_microsoft-cloudservices`.
• Ensure the following data sources are available: `sourcetype=mscs:azure:diagnostics` (Key Vault diagnostics).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable Key Vault diagnostic logging. Monitor all access operations. Alert on failed access attempts and unusual access patterns (new principals accessing secrets).

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=azure sourcetype="mscs:azure:diagnostics" Category="AuditEvent" ResourceType="VAULTS"
| stats count by identity.claim.upn, operationName, ResultType
| where ResultType!="Success"
| sort -count
```

Understanding this SPL

**Azure Key Vault Access Audit** — Key Vault stores secrets, keys, and certificates. Unauthorized or anomalous access could indicate credential theft or data breach preparation.

Documented **Data sources**: `sourcetype=mscs:azure:diagnostics` (Key Vault diagnostics). **App/TA** (typical add-on context): `Splunk_TA_microsoft-cloudservices`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: azure; **sourcetype**: mscs:azure:diagnostics, VAULTS. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=azure, sourcetype="mscs:azure:diagnostics". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by identity.claim.upn, operationName, ResultType** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where ResultType!="Success"` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (user, operation, result), Timeline, Bar chart by operation.

## SPL

```spl
index=azure sourcetype="mscs:azure:diagnostics" Category="AuditEvent" ResourceType="VAULTS"
| stats count by identity.claim.upn, operationName, ResultType
| where ResultType!="Success"
| sort -count
```

## Visualization

Table (user, operation, result), Timeline, Bar chart by operation.

## References

- [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)
