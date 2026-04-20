---
id: "9.4.7"
title: "Federated Identity Provider Health"
criticality: "critical"
splunkPillar: "Security"
---

# UC-9.4.7 · Federated Identity Provider Health

## Description

IdP outages block all federated application access. Health monitoring ensures SSO availability and rapid incident response.

## Value

IdP outages block all federated application access. Health monitoring ensures SSO availability and rapid incident response.

## Implementation

Poll IdP health endpoints (e.g., SAML metadata, OIDC discovery) every 60 seconds. Ingest federation errors from app and IdP logs. Alert on status unhealthy or latency >5s. Correlate with user-reported SSO issues.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: IdP monitoring, SAML/OIDC audit logs.
• Ensure the following data sources are available: IdP health endpoints, federation error logs.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll IdP health endpoints (e.g., SAML metadata, OIDC discovery) every 60 seconds. Ingest federation errors from app and IdP logs. Alert on status unhealthy or latency >5s. Correlate with user-reported SSO issues.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=iam sourcetype="idp:health"
| stats latest(status) as status, latest(response_ms) as latency by idp_host, tenant
| where status!="healthy" OR latency > 5000
| table idp_host, tenant, status, latency
```

Understanding this SPL

**Federated Identity Provider Health** — IdP outages block all federated application access. Health monitoring ensures SSO availability and rapid incident response.

Documented **Data sources**: IdP health endpoints, federation error logs. **App/TA** (typical add-on context): IdP monitoring, SAML/OIDC audit logs. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: iam; **sourcetype**: idp:health. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=iam, sourcetype="idp:health". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by idp_host, tenant** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where status!="healthy" OR latency > 5000` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Federated Identity Provider Health**): table idp_host, tenant, status, latency

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t count from datamodel=Authentication.Authentication by Authentication.action, Authentication.user, Authentication.src | sort - count
```

Understanding this CIM / accelerated SPL

**Federated Identity Provider Health** — IdP outages block all federated application access. Health monitoring ensures SSO availability and rapid incident response.

Documented **Data sources**: IdP health endpoints, federation error logs. **App/TA** (typical add-on context): IdP monitoring, SAML/OIDC audit logs. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Authentication.Authentication` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Status grid (IdP × health), Single value (IdP uptime %), Line chart (latency trend).

## SPL

```spl
index=iam sourcetype="idp:health"
| stats latest(status) as status, latest(response_ms) as latency by idp_host, tenant
| where status!="healthy" OR latency > 5000
| table idp_host, tenant, status, latency
```

## CIM SPL

```spl
| tstats summariesonly=t count from datamodel=Authentication.Authentication by Authentication.action, Authentication.user, Authentication.src | sort - count
```

## Visualization

Status grid (IdP × health), Single value (IdP uptime %), Line chart (latency trend).

## Known False Positives

Administrative tasks, scheduled jobs or platform updates can match this pattern — correlate with change management, maintenance windows and user role before raising severity.

## References

- [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)
