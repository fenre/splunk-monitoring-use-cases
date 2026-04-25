<!-- AUTO-GENERATED from UC-9.4.8.json — DO NOT EDIT -->

---
id: "9.4.8"
title: "API Token Usage Anomaly"
criticality: "high"
splunkPillar: "Security"
---

# UC-9.4.8 · API Token Usage Anomaly

## Description

Unusual API token usage may indicate token theft or abuse. Detection supports least-privilege and incident response.

## Value

Unusual API token usage may indicate token theft or abuse. Detection supports least-privilege and incident response.

## Implementation

Ingest token usage from IdP and API gateways. Baseline normal usage per token. Alert on new IPs, high request volume, or off-hours spikes. Rotate tokens on anomaly.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Cloud identity TAs, API gateway logs.
• Ensure the following data sources are available: Token audit logs, API request logs.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Ingest token usage from IdP and API gateways. Baseline normal usage per token. Alert on new IPs, high request volume, or off-hours spikes. Rotate tokens on anomaly.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=iam sourcetype="api:token_audit"
| bin _time span=1h
| stats dc(ip) as unique_ips, count as requests by token_id, _time
| where unique_ips > 3 OR requests > 1000
| sort -requests
```

Understanding this SPL

**API Token Usage Anomaly** — Unusual API token usage may indicate token theft or abuse. Detection supports least-privilege and incident response.

Documented **Data sources**: Token audit logs, API request logs. **App/TA** (typical add-on context): Cloud identity TAs, API gateway logs. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: iam; **sourcetype**: api:token_audit. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=iam, sourcetype="api:token_audit". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Discretizes time or numeric ranges with `bin`/`bucket`.
• `stats` rolls up events into metrics; results are split **by token_id, _time** so each row reflects one combination of those dimensions.
• Filters the current rows with `where unique_ips > 3 OR requests > 1000` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t count from datamodel=Authentication.Authentication by Authentication.action, Authentication.user, Authentication.src | sort - count
```

Understanding this CIM / accelerated SPL

**API Token Usage Anomaly** — Unusual API token usage may indicate token theft or abuse. Detection supports least-privilege and incident response.

Documented **Data sources**: Token audit logs, API request logs. **App/TA** (typical add-on context): Cloud identity TAs, API gateway logs. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Authentication.Authentication` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Compare results with the authoritative identity source (directory, IdP, or PAM) for the same time range and with known change or maintenance tickets.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (anomalous tokens), Line chart (requests by token), Bar chart (unique IPs per token).

## SPL

```spl
index=iam sourcetype="api:token_audit"
| bin _time span=1h
| stats dc(ip) as unique_ips, count as requests by token_id, _time
| where unique_ips > 3 OR requests > 1000
| sort -requests
```

## CIM SPL

```spl
| tstats summariesonly=t count from datamodel=Authentication.Authentication by Authentication.action, Authentication.user, Authentication.src | sort - count
```

## Visualization

Table (anomalous tokens), Line chart (requests by token), Bar chart (unique IPs per token).

## References

- [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)
