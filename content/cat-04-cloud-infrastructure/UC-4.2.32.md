---
id: "4.2.32"
title: "Key Vault Access Audit"
criticality: "high"
splunkPillar: "Security"
---

# UC-4.2.32 · Key Vault Access Audit

## Description

Secret and key unwrap operations must be traceable for insider and breach investigations; unusual callers warrant immediate review.

## Value

Secret and key unwrap operations must be traceable for insider and breach investigations; unusual callers warrant immediate review.

## Implementation

Enable Key Vault diagnostic logs to Log Analytics or Event Hub. Alert on first-time principal, after-hours bulk access, or access from non-corporate IP ranges using lookups.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_microsoft-cloudservices`.
• Ensure the following data sources are available: `sourcetype=mscs:azure:audit` (Microsoft.KeyVault vaults), diagnostic logs.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable Key Vault diagnostic logs to Log Analytics or Event Hub. Alert on first-time principal, after-hours bulk access, or access from non-corporate IP ranges using lookups.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=azure sourcetype="mscs:azure:audit" resourceId="*vaults*" (operationName.value="SecretGet" OR operationName.value="Decrypt" OR operationName.value="UnwrapKey")
| stats count by identity.claims.name, callerIpAddress, resourceId
| sort -count
```

Understanding this SPL

**Key Vault Access Audit** — Secret and key unwrap operations must be traceable for insider and breach investigations; unusual callers warrant immediate review.

Documented **Data sources**: `sourcetype=mscs:azure:audit` (Microsoft.KeyVault vaults), diagnostic logs. **App/TA** (typical add-on context): `Splunk_TA_microsoft-cloudservices`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: azure; **sourcetype**: mscs:azure:audit. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=azure, sourcetype="mscs:azure:audit". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by identity.claims.name, callerIpAddress, resourceId** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t count from datamodel=Authentication.Authentication by Authentication.action, Authentication.user, Authentication.src | sort - count
```

Understanding this CIM / accelerated SPL

**Key Vault Access Audit** — Secret and key unwrap operations must be traceable for insider and breach investigations; unusual callers warrant immediate review.

Documented **Data sources**: `sourcetype=mscs:azure:audit` (Microsoft.KeyVault vaults), diagnostic logs. **App/TA** (typical add-on context): `Splunk_TA_microsoft-cloudservices`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Authentication.Authentication` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (identity, vault, count), Timeline (access spikes), Map (caller IP).

## SPL

```spl
index=azure sourcetype="mscs:azure:audit" resourceId="*vaults*" (operationName.value="SecretGet" OR operationName.value="Decrypt" OR operationName.value="UnwrapKey")
| stats count by identity.claims.name, callerIpAddress, resourceId
| sort -count
```

## CIM SPL

```spl
| tstats summariesonly=t count from datamodel=Authentication.Authentication by Authentication.action, Authentication.user, Authentication.src | sort - count
```

## Visualization

Table (identity, vault, count), Timeline (access spikes), Map (caller IP).

## References

- [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)
- [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)
