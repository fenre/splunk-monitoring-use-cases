---
id: "9.3.9"
title: "OAuth Token Abuse"
criticality: "critical"
splunkPillar: "Security"
---

# UC-9.3.9 · OAuth Token Abuse

## Description

Excessive refresh grants, scope expansion, or token use from new ASNs indicates stolen refresh tokens or malicious OAuth clients.

## Value

Excessive refresh grants, scope expansion, or token use from new ASNs indicates stolen refresh tokens or malicious OAuth clients.

## Implementation

Baseline grants per user and client. Alert on burst refresh or grants from many IPs. Revoke client on anomaly. Mirror logic for `azure:aad:signin` with `tokenIssuerType`.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_okta`, Entra sign-in + Graph audit, API gateway logs.
• Ensure the following data sources are available: `app.oauth2.token.grant`, Entra `TokenIssuance` / `Update application` (consent).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Baseline grants per user and client. Alert on burst refresh or grants from many IPs. Revoke client on anomaly. Mirror logic for `azure:aad:signin` with `tokenIssuerType`.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=okta sourcetype="OktaIM2:log" eventType="app.oauth2.token.grant"
| stats count, dc(client.ipAddress) as ips by actor.alternateId, client_id
| where count > 200 OR ips > 5
| sort -count
```

Understanding this SPL

**OAuth Token Abuse** — Excessive refresh grants, scope expansion, or token use from new ASNs indicates stolen refresh tokens or malicious OAuth clients.

Documented **Data sources**: `app.oauth2.token.grant`, Entra `TokenIssuance` / `Update application` (consent). **App/TA** (typical add-on context): `Splunk_TA_okta`, Entra sign-in + Graph audit, API gateway logs. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: okta; **sourcetype**: OktaIM2:log. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=okta, sourcetype="OktaIM2:log". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by actor.alternateId, client_id** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where count > 200 OR ips > 5` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t count from datamodel=Authentication.Authentication by Authentication.action, Authentication.user, Authentication.src | sort - count
```

Understanding this CIM / accelerated SPL

**OAuth Token Abuse** — Excessive refresh grants, scope expansion, or token use from new ASNs indicates stolen refresh tokens or malicious OAuth clients.

Documented **Data sources**: `app.oauth2.token.grant`, Entra `TokenIssuance` / `Update application` (consent). **App/TA** (typical add-on context): `Splunk_TA_okta`, Entra sign-in + Graph audit, API gateway logs. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Authentication.Authentication` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (abusive clients), Line chart (grants over time), Bar chart (by client_id).

## SPL

```spl
index=okta sourcetype="OktaIM2:log" eventType="app.oauth2.token.grant"
| stats count, dc(client.ipAddress) as ips by actor.alternateId, client_id
| where count > 200 OR ips > 5
| sort -count
```

## CIM SPL

```spl
| tstats summariesonly=t count from datamodel=Authentication.Authentication by Authentication.action, Authentication.user, Authentication.src | sort - count
```

## Visualization

Table (abusive clients), Line chart (grants over time), Bar chart (by client_id).

## Known False Positives

Administrative tasks, scheduled jobs or platform updates can match this pattern — correlate with change management, maintenance windows and user role before raising severity.

## References

- [Splunk_TA_okta](https://splunkbase.splunk.com/app/6553)
- [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)
