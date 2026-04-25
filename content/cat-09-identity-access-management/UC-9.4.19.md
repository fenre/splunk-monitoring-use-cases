<!-- AUTO-GENERATED from UC-9.4.19.json — DO NOT EDIT -->

---
id: "9.4.19"
title: "Shared Account Concurrent Login Detection"
criticality: "critical"
splunkPillar: "Security"
---

# UC-9.4.19 · Shared Account Concurrent Login Detection

## Description

Shared privileged accounts used from two locations simultaneously indicate credential sharing or theft.

## Value

Shared privileged accounts used from two locations simultaneously indicate credential sharing or theft.

## Implementation

Tune for load-balanced egress using known NAT pools. Prefer per-user vaulted accounts to eliminate shared IDs.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: PAM session logs, bastion logs.
• Ensure the following data sources are available: Session start with same `target_account` and overlapping time ranges.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Tune for load-balanced egress using known NAT pools. Prefer per-user vaulted accounts to eliminate shared IDs.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=pam sourcetype="cyberark:session"
| eval end_time=_time+duration_sec
| sort target_account, _time
| streamstats window=2 current(src) as ip1 next(src) as ip2 current(_time) as t1 next(_time) as t2 by target_account
| where ip1!=ip2 AND t2 < end_time
| table target_account, ip1, ip2, t1, t2
```

Understanding this SPL

**Shared Account Concurrent Login Detection** — Shared privileged accounts used from two locations simultaneously indicate credential sharing or theft.

Documented **Data sources**: Session start with same `target_account` and overlapping time ranges. **App/TA** (typical add-on context): PAM session logs, bastion logs. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: pam; **sourcetype**: cyberark:session. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=pam, sourcetype="cyberark:session". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **end_time** — often to normalize units, derive a ratio, or prepare for thresholds.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
• `streamstats` rolls up events into metrics; results are split **by target_account** so each row reflects one combination of those dimensions.
• Filters the current rows with `where ip1!=ip2 AND t2 < end_time` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Shared Account Concurrent Login Detection**): table target_account, ip1, ip2, t1, t2

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t count from datamodel=Authentication.Authentication by Authentication.action, Authentication.user, Authentication.src | sort - count
```

Understanding this CIM / accelerated SPL

**Shared Account Concurrent Login Detection** — Shared privileged accounts used from two locations simultaneously indicate credential sharing or theft.

Documented **Data sources**: Session start with same `target_account` and overlapping time ranges. **App/TA** (typical add-on context): PAM session logs, bastion logs. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Authentication.Authentication` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Compare with CyberArk PrivateArk/Password Vault Web Access (or BeyondTrust / vendor console) for the same sessions, vault activity, and alerts.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (concurrent sessions), Timeline, Bar chart (accounts with overlap events).

## SPL

```spl
index=pam sourcetype="cyberark:session"
| eval end_time=_time+duration_sec
| sort target_account, _time
| streamstats window=2 current(src) as ip1 next(src) as ip2 current(_time) as t1 next(_time) as t2 by target_account
| where ip1!=ip2 AND t2 < end_time
| table target_account, ip1, ip2, t1, t2
```

## CIM SPL

```spl
| tstats summariesonly=t count from datamodel=Authentication.Authentication by Authentication.action, Authentication.user, Authentication.src | sort - count
```

## Visualization

Table (concurrent sessions), Timeline, Bar chart (accounts with overlap events).

## References

- [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)
