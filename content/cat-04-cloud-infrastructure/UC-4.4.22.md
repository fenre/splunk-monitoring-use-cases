---
id: "4.4.22"
title: "Cross-Cloud Identity Federation Monitoring"
criticality: "high"
splunkPillar: "Security"
---

# UC-4.4.22 · Cross-Cloud Identity Federation Monitoring

## Description

Federation misconfiguration or token abuse spans IdPs and cloud consoles; unified visibility reduces blind spots for lateral movement across AWS, Azure, and GCP.

## Value

Federation misconfiguration or token abuse spans IdPs and cloud consoles; unified visibility reduces blind spots for lateral movement across AWS, Azure, and GCP.

## Implementation

Normalize federated principal fields into a common `user` or `subject` via `eval`/`lookup`. Ingest IdP logs (Okta, Entra ID) via HEC if available and join on session ID. Alert on unusual federation volume, new IdP thumbprint, or cross-cloud sessions within minutes for the same user.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_aws`, `Splunk_TA_microsoft-cloudservices`, `Splunk_TA_google-cloudplatform`.
• Ensure the following data sources are available: `sourcetype=aws:cloudtrail` (AssumeRoleWithSAML, federation), `sourcetype=mscs:azure:audit` (federated sign-ins), `sourcetype=google:gcp:pubsub:message` (SAML/OIDC audit).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Normalize federated principal fields into a common `user` or `subject` via `eval`/`lookup`. Ingest IdP logs (Okta, Entra ID) via HEC if available and join on session ID. Alert on unusual federation volume, new IdP thumbprint, or cross-cloud sessions within minutes for the same user.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
(index=aws sourcetype="aws:cloudtrail" eventName="AssumeRoleWithSAML")
 OR (index=azure sourcetype="mscs:azure:audit" identity.claims.http://schemas.xmlsoap.org/ws/2005/05/identity/claims/nameidentifier=)
 OR (index=gcp sourcetype="google:gcp:pubsub:message" protoPayload.methodName="google.iam.admin.v1.IAM.SignBlob")
| eval cloud=case(isnotnull(index) AND index="aws","aws", index="azure","azure", index="gcp","gcp",1=1,"unknown")
| bin _time span=1h
| stats count by cloud, user, _time
| sort -count
```

Understanding this SPL

**Cross-Cloud Identity Federation Monitoring** — Federation misconfiguration or token abuse spans IdPs and cloud consoles; unified visibility reduces blind spots for lateral movement across AWS, Azure, and GCP.

Documented **Data sources**: `sourcetype=aws:cloudtrail` (AssumeRoleWithSAML, federation), `sourcetype=mscs:azure:audit` (federated sign-ins), `sourcetype=google:gcp:pubsub:message` (SAML/OIDC audit). **App/TA** (typical add-on context): `Splunk_TA_aws`, `Splunk_TA_microsoft-cloudservices`, `Splunk_TA_google-cloudplatform`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws, azure, gcp; **sourcetype**: aws:cloudtrail, mscs:azure:audit, google:gcp:pubsub:message. Those sourcetypes align with what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=aws, index=azure, index=gcp, sourcetype="aws:cloudtrail". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **cloud** — often to normalize units, derive a ratio, or prepare for thresholds.
• Discretizes time or numeric ranges with `bin`/`bucket`.
• `stats` rolls up events into metrics; results are split **by cloud, user, _time** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t count from datamodel=Authentication.Authentication by Authentication.user | sort - count
```

Understanding this CIM / accelerated SPL

**Cross-Cloud Identity Federation Monitoring** — Federation misconfiguration or token abuse spans IdPs and cloud consoles; unified visibility reduces blind spots for lateral movement across AWS, Azure, and GCP.

Documented **Data sources**: `sourcetype=aws:cloudtrail` (AssumeRoleWithSAML, federation), `sourcetype=mscs:azure:audit` (federated sign-ins), `sourcetype=google:gcp:pubsub:message` (SAML/OIDC audit). **App/TA** (typical add-on context): `Splunk_TA_aws`, `Splunk_TA_microsoft-cloudservices`, `Splunk_TA_google-cloudplatform`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Authentication.Authentication` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (cloud, user, count), Timeline (federation events), Sankey or chord (IdP to cloud role).

## SPL

```spl
(index=aws sourcetype="aws:cloudtrail" eventName="AssumeRoleWithSAML")
 OR (index=azure sourcetype="mscs:azure:audit" identity.claims.http://schemas.xmlsoap.org/ws/2005/05/identity/claims/nameidentifier=)
 OR (index=gcp sourcetype="google:gcp:pubsub:message" protoPayload.methodName="google.iam.admin.v1.IAM.SignBlob")
| eval cloud=case(isnotnull(index) AND index="aws","aws", index="azure","azure", index="gcp","gcp",1=1,"unknown")
| bin _time span=1h
| stats count by cloud, user, _time
| sort -count
```

## CIM SPL

```spl
| tstats summariesonly=t count from datamodel=Authentication.Authentication by Authentication.user | sort - count
```

## Visualization

Table (cloud, user, count), Timeline (federation events), Sankey or chord (IdP to cloud role).

## References

- [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)
- [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)
- [Splunk_TA_google-cloudplatform](https://splunkbase.splunk.com/app/3088)
- [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)
