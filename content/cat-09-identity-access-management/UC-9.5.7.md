---
id: "9.5.7"
title: "Duo Authentication Denials"
criticality: "high"
splunkPillar: "Security"
---

# UC-9.5.7 · Duo Authentication Denials

## Description

Denied logins (fraud, policy, or lockout) indicate attacks or misconfigurations; volume and user patterns guide response.

## Value

Denied logins (fraud, policy, or lockout) indicate attacks or misconfigurations; volume and user patterns guide response.

## Implementation

Ingest Duo Authentication API or proxy logs with the TA. Map `result`, `reason`, `factor`, and `application`. Baseline per-user and global deny rates. Alert on spikes and on denies from many IPs for one user.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Cisco Duo TA.
• Ensure the following data sources are available: `sourcetype=duo:authentication`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Ingest Duo Authentication API or proxy logs with the TA. Map `result`, `reason`, `factor`, and `application`. Baseline per-user and global deny rates. Alert on spikes and on denies from many IPs for one user.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=duo sourcetype="duo:authentication" result="deny"
| bin _time span=1h
| stats count by user, ip, application
| where count > 10
| sort -count
```

Understanding this SPL

**Duo Authentication Denials** — Denied logins (fraud, policy, or lockout) indicate attacks or misconfigurations; volume and user patterns guide response.

Documented **Data sources**: `sourcetype=duo:authentication`. **App/TA** (typical add-on context): Cisco Duo TA. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: duo; **sourcetype**: duo:authentication. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=duo, sourcetype="duo:authentication". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Discretizes time or numeric ranges with `bin`/`bucket`.
• `stats` rolls up events into metrics; results are split **by user, ip, application** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where count > 10` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t count from datamodel=Authentication.Authentication by Authentication.user span=1h | sort - count
```

Understanding this CIM / accelerated SPL

**Duo Authentication Denials** — Denied logins (fraud, policy, or lockout) indicate attacks or misconfigurations; volume and user patterns guide response.

Documented **Data sources**: `sourcetype=duo:authentication`. **App/TA** (typical add-on context): Cisco Duo TA. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Authentication.Authentication` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (user, IP, count), Line chart (denials over time), Bar chart (denials by application).

## SPL

```spl
index=duo sourcetype="duo:authentication" result="deny"
| bin _time span=1h
| stats count by user, ip, application
| where count > 10
| sort -count
```

## CIM SPL

```spl
| tstats summariesonly=t count from datamodel=Authentication.Authentication by Authentication.user span=1h | sort - count
```

## Visualization

Table (user, IP, count), Line chart (denials over time), Bar chart (denials by application).

## Known False Positives

Administrative tasks, scheduled jobs or platform updates can match this pattern — correlate with change management, maintenance windows and user role before raising severity.

## References

- [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)
