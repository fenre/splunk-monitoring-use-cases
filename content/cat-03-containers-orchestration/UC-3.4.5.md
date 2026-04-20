---
id: "3.4.5"
title: "Registry Authentication and Authorization Failures"
criticality: "high"
splunkPillar: "Security"
---

# UC-3.4.5 · Registry Authentication and Authorization Failures

## Description

Failed logins and denied pushes/pulls may indicate credential abuse or misconfiguration. Detecting anomalies supports security and access troubleshooting.

## Value

Failed logins and denied pushes/pulls may indicate credential abuse or misconfiguration. Detecting anomalies supports security and access troubleshooting.

## Implementation

Forward registry audit logs to Splunk. Extract user, action, repository. Alert on high failure rates or denied actions for critical repos.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Registry audit logs (Harbor, Docker Registry, ECR).
• Ensure the following data sources are available: Registry audit log API or log files.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Forward registry audit logs to Splunk. Extract user, action, repository. Alert on high failure rates or denied actions for critical repos.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=containers sourcetype="registry:audit" (action="login_failed" OR action="pull_denied" OR action="push_denied")
| bin _time span=1h
| stats count by user, action, repository, _time
| where count > 10
| sort -count
```

Understanding this SPL

**Registry Authentication and Authorization Failures** — Failed logins and denied pushes/pulls may indicate credential abuse or misconfiguration. Detecting anomalies supports security and access troubleshooting.

Documented **Data sources**: Registry audit log API or log files. **App/TA** (typical add-on context): Registry audit logs (Harbor, Docker Registry, ECR). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: containers; **sourcetype**: registry:audit. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=containers, sourcetype="registry:audit". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Discretizes time or numeric ranges with `bin`/`bucket`.
• `stats` rolls up events into metrics; results are split **by user, action, repository, _time** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where count > 10` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t count from datamodel=Authentication.Authentication by Authentication.user, Authentication.action span=1h | sort - count
```

Understanding this CIM / accelerated SPL

**Registry Authentication and Authorization Failures** — Failed logins and denied pushes/pulls may indicate credential abuse or misconfiguration. Detecting anomalies supports security and access troubleshooting.

Documented **Data sources**: Registry audit log API or log files. **App/TA** (typical add-on context): Registry audit logs (Harbor, Docker Registry, ECR). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Authentication.Authentication` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (user, action, count), Timechart of failures, Events list.

## SPL

```spl
index=containers sourcetype="registry:audit" (action="login_failed" OR action="pull_denied" OR action="push_denied")
| bin _time span=1h
| stats count by user, action, repository, _time
| where count > 10
| sort -count
```

## CIM SPL

```spl
| tstats summariesonly=t count from datamodel=Authentication.Authentication by Authentication.user, Authentication.action span=1h | sort - count
```

## Visualization

Table (user, action, count), Timechart of failures, Events list.

## References

- [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)
