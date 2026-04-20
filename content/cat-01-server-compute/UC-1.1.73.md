---
id: "1.1.73"
title: "PAM Authentication Failure Tracking"
criticality: "high"
splunkPillar: "Security"
---

# UC-1.1.73 · PAM Authentication Failure Tracking

## Description

PAM failures indicate authentication issues or brute-force attack attempts against user accounts.

## Value

PAM failures indicate authentication issues or brute-force attack attempts against user accounts.

## Implementation

Monitor PAM logs for authentication failures. Track failures per user and source IP. Create alerts for multiple failures from single IP within short timeframe indicating brute force.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_nix, custom scripted input`.
• Ensure the following data sources are available: `sourcetype=linux_secure`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Monitor PAM logs for authentication failures. Track failures per user and source IP. Create alerts for multiple failures from single IP within short timeframe indicating brute force.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=linux_secure pam "authentication failure"
| stats count as failures by host, user, src
| where failures > 5
```

Understanding this SPL

**PAM Authentication Failure Tracking** — PAM failures indicate authentication issues or brute-force attack attempts against user accounts.

Documented **Data sources**: `sourcetype=linux_secure`. **App/TA** (typical add-on context): `Splunk_TA_nix, custom scripted input`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: linux_secure. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=os, sourcetype=linux_secure. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host, user, src** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where failures > 5` — typically the threshold or rule expression for this monitoring goal.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=failure
  by Authentication.user Authentication.src span=1h
| where count > 10
```

Understanding this CIM / accelerated SPL

**PAM Authentication Failure Tracking** — PAM failures indicate authentication issues or brute-force attack attempts against user accounts.

Documented **Data sources**: `sourcetype=linux_secure`. **App/TA** (typical add-on context): `Splunk_TA_nix, custom scripted input`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Authentication.Authentication` — enable acceleration for that model.
• Filters the current rows with `where count > 10` — typically the threshold or rule expression for this monitoring goal.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table, Timechart

## SPL

```spl
index=os sourcetype=linux_secure pam "authentication failure"
| stats count as failures by host, user, src
| where failures > 5
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=failure
  by Authentication.user Authentication.src span=1h
| where count > 10
```

## Visualization

Table, Timechart

## References

- [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)
