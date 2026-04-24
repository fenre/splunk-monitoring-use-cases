---
id: "5.13.14"
title: "Client Onboarding Failure Rate"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.13.14 · Client Onboarding Failure Rate

## Description

Monitors the percentage of clients failing to onboard successfully (DHCP, AAA, or association failures), detecting authentication and connectivity infrastructure problems.

## Value

Onboarding failures prevent users from connecting at all. High failure rates indicate RADIUS server issues, DHCP pool exhaustion, or AP capacity problems.

## Implementation

Requires UC-5.13.9. The ONBOARDING branch must be present in `scoreDetail`; if not, verify Catalyst Center release and that client health is licensed for the sites you need. Tighten the threshold from 50 if your SLOs demand stricter onboarding scores; alert with P2 routing when `affected_clients` grows.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538).
• Ensure the following data sources are available: index=catalyst, sourcetype cisco:dnac:clienthealth (Catalyst Center client health feed).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Requires UC-5.13.9. The ONBOARDING branch must be present in `scoreDetail`; if not, verify Catalyst Center release and that client health is licensed for the sites you need. Tighten the threshold from 50 if your SLOs demand stricter onboarding scores; alert with P2 routing when `affected_clients` grows.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=catalyst sourcetype="cisco:dnac:clienthealth" | spath output=categories path=scoreDetail{} | mvexpand categories | spath input=categories | where scoreCategory="ONBOARDING" | stats latest(value) as onboarding_score latest(clientCount) as affected_clients by _time | where onboarding_score < 50 | sort -affected_clients
```

Understanding this SPL

**Client Onboarding Failure Rate** — Onboarding failures prevent users from connecting at all. High failure rates indicate RADIUS server issues, DHCP pool exhaustion, or AP capacity problems.

Documented **Data sources**: index=catalyst, sourcetype cisco:dnac:clienthealth (Catalyst Center client health feed). **App/TA** (typical add-on context): `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: catalyst; **sourcetype**: cisco:dnac:clienthealth. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• **`spath path=scoreDetail{}`** on the full `scoreDetail` object (not only `scoreCategory`) is more robust; **`mvexpand`** and **`where scoreCategory="ONBOARDING"`** keep only the onboarding slice so **`value`** and **`clientCount`** refer to that lifecycle phase.
• `stats` by `_time` captures the most recent `value` and `clientCount` for that slice; `where` enforces a failing `onboarding_score` and `sort` orders by the largest `affected_clients` first for triage with AAA or DHCP teams.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table of affected waves in time, single value of worst `onboarding_score`, timechart of rolling minimum onboarding score for early warning.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:clienthealth" | spath output=categories path=scoreDetail{} | mvexpand categories | spath input=categories | where scoreCategory="ONBOARDING" | stats latest(value) as onboarding_score latest(clientCount) as affected_clients by _time | where onboarding_score < 50 | sort -affected_clients
```

## Visualization

Table of affected waves in time, single value of worst `onboarding_score`, timechart of rolling minimum onboarding score for early warning.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
