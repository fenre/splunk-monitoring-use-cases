---
id: "4.4.25"
title: "Multi-Cloud Secret Management Audit"
criticality: "critical"
splunkPillar: "Security"
---

# UC-4.4.25 · Multi-Cloud Secret Management Audit

## Description

Secrets touched across AWS Secrets Manager, Azure Key Vault, and GCP Secret Manager must be auditable for least-privilege reviews and breach investigations.

## Value

Secrets touched across AWS Secrets Manager, Azure Key Vault, and GCP Secret Manager must be auditable for least-privilege reviews and breach investigations.

## Implementation

Enrich with HR or CMDB owner for service principals. Alert on first-time accessor, after-hours bulk reads, or secrets read from unexpected regions. Retention aligned to compliance policy.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_aws`, `Splunk_TA_microsoft-cloudservices`, `Splunk_TA_google-cloudplatform`.
• Ensure the following data sources are available: `sourcetype=aws:cloudtrail` (secretsmanager, kms), `sourcetype=mscs:azure:audit` (Key Vault), `sourcetype=google:gcp:pubsub:message` (secretmanager.googleapis.com).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enrich with HR or CMDB owner for service principals. Alert on first-time accessor, after-hours bulk reads, or secrets read from unexpected regions. Retention aligned to compliance policy.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
(index=aws sourcetype="aws:cloudtrail" eventSource="secretsmanager.amazonaws.com" eventName="GetSecretValue")
 OR (index=azure sourcetype="mscs:azure:audit" resourceId="*vaults*")
 OR (index=gcp sourcetype="google:gcp:pubsub:message" protoPayload.serviceName="secretmanager.googleapis.com")
| eval principal=coalesce(userIdentity.arn, identity.claims.appid, protoPayload.authenticationInfo.principalEmail)
| stats count by principal, index
| sort -count
```

Understanding this SPL

**Multi-Cloud Secret Management Audit** — Secrets touched across AWS Secrets Manager, Azure Key Vault, and GCP Secret Manager must be auditable for least-privilege reviews and breach investigations.

Documented **Data sources**: `sourcetype=aws:cloudtrail` (secretsmanager, kms), `sourcetype=mscs:azure:audit` (Key Vault), `sourcetype=google:gcp:pubsub:message` (secretmanager.googleapis.com). **App/TA** (typical add-on context): `Splunk_TA_aws`, `Splunk_TA_microsoft-cloudservices`, `Splunk_TA_google-cloudplatform`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws, azure, gcp; **sourcetype**: aws:cloudtrail, mscs:azure:audit, google:gcp:pubsub:message. Those sourcetypes align with what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=aws, index=azure, index=gcp, sourcetype="aws:cloudtrail". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **principal** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by principal, index** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t count from datamodel=Authentication.Authentication by Authentication.action, Authentication.user, Authentication.src | sort - count
```

Understanding this CIM / accelerated SPL

**Multi-Cloud Secret Management Audit** — Secrets touched across AWS Secrets Manager, Azure Key Vault, and GCP Secret Manager must be auditable for least-privilege reviews and breach investigations.

Documented **Data sources**: `sourcetype=aws:cloudtrail` (secretsmanager, kms), `sourcetype=mscs:azure:audit` (Key Vault), `sourcetype=google:gcp:pubsub:message` (secretmanager.googleapis.com). **App/TA** (typical add-on context): `Splunk_TA_aws`, `Splunk_TA_microsoft-cloudservices`, `Splunk_TA_google-cloudplatform`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Authentication.Authentication` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (principal, cloud, access count), Bar chart (top accessors), Timeline (spikes).

## SPL

```spl
(index=aws sourcetype="aws:cloudtrail" eventSource="secretsmanager.amazonaws.com" eventName="GetSecretValue")
 OR (index=azure sourcetype="mscs:azure:audit" resourceId="*vaults*")
 OR (index=gcp sourcetype="google:gcp:pubsub:message" protoPayload.serviceName="secretmanager.googleapis.com")
| eval principal=coalesce(userIdentity.arn, identity.claims.appid, protoPayload.authenticationInfo.principalEmail)
| stats count by principal, index
| sort -count
```

## CIM SPL

```spl
| tstats summariesonly=t count from datamodel=Authentication.Authentication by Authentication.action, Authentication.user, Authentication.src | sort - count
```

## Visualization

Table (principal, cloud, access count), Bar chart (top accessors), Timeline (spikes).

## References

- [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)
- [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)
- [Splunk_TA_google-cloudplatform](https://splunkbase.splunk.com/app/3088)
- [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)
