<!-- AUTO-GENERATED from UC-1.1.110.json — DO NOT EDIT -->

---
id: "1.1.110"
title: "Inactive User Detection"
criticality: "medium"
splunkPillar: "Security"
---

# UC-1.1.110 · Inactive User Detection

## Description

Inactive users with enabled accounts represent security risk and should be disabled to reduce attack surface.

## Value

Inactive users with enabled accounts represent security risk and should be disabled to reduce attack surface.

## Implementation

Track user login activity from `/var/log/auth.log` (linux_secure). Calculate days since last successful login. Alert on users inactive >90 days. Include list of inactive accounts for review and disabling.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_nix, custom scripted input`.
• Ensure the following data sources are available: `sourcetype=linux_secure`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Track user login activity from `/var/log/auth.log`. Calculate days since last login. Alert on users inactive >90 days. Include list of inactive accounts for review and disabling.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=linux_secure "Accepted"
| stats max(_time) as last_login by user, host
| eval days_inactive=(now()-last_login)/86400
| where days_inactive > 90
```

Understanding this SPL

**Inactive User Detection** — Inactive users with enabled accounts represent security risk and should be disabled to reduce attack surface.

Documented **Data sources**: `sourcetype=linux_secure`. **App/TA** (typical add-on context): `Splunk_TA_nix, custom scripted input`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: linux_secure. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=os, sourcetype=linux_secure. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by user, host** so each row reflects one combination of those dimensions.
• `eval` defines or adjusts **days_inactive** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where days_inactive > 90` — typically the threshold or rule expression for this monitoring goal.

Optional CIM / accelerated variant (successful authentication events normalized to the Authentication data model):

```spl
| tstats `summariesonly` max(_time) as last_success
  from datamodel=Authentication.Authentication
  where Authentication.action=success
  by Authentication.user Authentication.dest
| eval days_inactive=(now()-last_success)/86400
| where days_inactive > 90
```

Understanding this CIM / accelerated SPL

This variant requires **CIM** tagging of your authentication sources to **Authentication.Authentication** and **Data Model Acceleration** on the Authentication data model. Field names must align (`Authentication.user` matches your identity field).


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table, Alert

## SPL

```spl
index=os sourcetype=linux_secure "Accepted"
| stats max(_time) as last_login by user, host
| eval days_inactive=(now()-last_login)/86400
| where days_inactive > 90
```

## CIM SPL

```spl
| tstats `summariesonly` max(_time) as last_success
  from datamodel=Authentication.Authentication
  where Authentication.action=success
  by Authentication.user Authentication.dest
| eval days_inactive=(now()-last_success)/86400
| where days_inactive > 90
```

## Visualization

Table, Alert

## References

- [Splunk_TA_nix](https://splunkbase.splunk.com/app/833)
- [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)
