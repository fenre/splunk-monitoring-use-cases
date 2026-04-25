<!-- AUTO-GENERATED from UC-9.4.11.json — DO NOT EDIT -->

---
id: "9.4.11"
title: "Identity Sync Failure Detection"
criticality: "critical"
splunkPillar: "Security"
---

# UC-9.4.11 · Identity Sync Failure Detection

## Description

Sync failures cause stale or missing identities in target systems, leading to access denials or orphaned accounts. Detection enables quick remediation.

## Value

Sync failures cause stale or missing identities in target systems, leading to access denials or orphaned accounts. Detection enables quick remediation.

## Implementation

Ingest sync job results from IdP and HR-driven connectors. Alert on any failed run or error count >0. Track sync latency and delta size. Report on sync health by target.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Identity sync / SCIM connector logs.
• Ensure the following data sources are available: Sync job logs, connector error logs.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Ingest sync job results from IdP and HR-driven connectors. Alert on any failed run or error count >0. Track sync latency and delta size. Report on sync health by target.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=iam sourcetype="sync:job"
| where status="failed" OR error_count > 0
| stats latest(_time) as last_failure, values(error_message) as errors by connector, target_system
| table connector, target_system, last_failure, errors
```

Understanding this SPL

**Identity Sync Failure Detection** — Sync failures cause stale or missing identities in target systems, leading to access denials or orphaned accounts. Detection enables quick remediation.

Documented **Data sources**: Sync job logs, connector error logs. **App/TA** (typical add-on context): Identity sync / SCIM connector logs. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: iam; **sourcetype**: sync:job. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=iam, sourcetype="sync:job". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where status="failed" OR error_count > 0` — typically the threshold or rule expression for this monitoring goal.
• `stats` rolls up events into metrics; results are split **by connector, target_system** so each row reflects one combination of those dimensions.
• Pipeline stage (see **Identity Sync Failure Detection**): table connector, target_system, last_failure, errors

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t count from datamodel=Authentication.Authentication by Authentication.action, Authentication.user, Authentication.src | sort - count
```

Understanding this CIM / accelerated SPL

**Identity Sync Failure Detection** — Sync failures cause stale or missing identities in target systems, leading to access denials or orphaned accounts. Detection enables quick remediation.

Documented **Data sources**: Sync job logs, connector error logs. **App/TA** (typical add-on context): Identity sync / SCIM connector logs. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Authentication.Authentication` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Compare results with the authoritative identity source (directory, IdP, or PAM) for the same time range and with known change or maintenance tickets.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (failed syncs), Single value (sync success %), Timeline (failure events).

## SPL

```spl
index=iam sourcetype="sync:job"
| where status="failed" OR error_count > 0
| stats latest(_time) as last_failure, values(error_message) as errors by connector, target_system
| table connector, target_system, last_failure, errors
```

## CIM SPL

```spl
| tstats summariesonly=t count from datamodel=Authentication.Authentication by Authentication.action, Authentication.user, Authentication.src | sort - count
```

## Visualization

Table (failed syncs), Single value (sync success %), Timeline (failure events).

## References

- [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)
