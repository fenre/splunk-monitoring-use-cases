<!-- AUTO-GENERATED from UC-5.13.14.json — DO NOT EDIT -->

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
• **UC-5.13.9**; confirm an **ONBOARDING** (or equivalent) `scoreCategory` row exists in `scoreDetail` in raw JSON. Names differ by release—if `ONBOARDING` is missing, check Catalyst release notes and Client health in the UI.
• Cisco Catalyst Add-on (7538); `clienthealth` to `cisco:dnac:clienthealth` on `index=catalyst`.
• Assurance licensing for the sites in scope. See `docs/implementation-guide.md`.

Step 1 — Configure data collection
• TA `clienthealth` input; default 900s poll to Intent client health API.
• If onboarding is only calculated for wireless, wired-only sites may not populate this row—document “N/A” behavior in the runbook.

Step 2 — Create the search and alert
```spl
index=catalyst sourcetype="cisco:dnac:clienthealth" | spath output=categories path=scoreDetail{} | mvexpand categories | spath input=categories | where scoreCategory="ONBOARDING" | stats latest(value) as onboarding_score latest(clientCount) as affected_clients by _time | where onboarding_score < 50 | sort -affected_clients
```

Understanding this SPL
• Flatten `scoreDetail`, keep only the ONBOARDING slice, then `stats` per `_time` for latest score and client count. Adjust the **50** threshold to your SLO (e.g. 60 or 70) if “Poor” in Assurance is stricter.
• Sorting by `affected_clients` focuses tickets on the worst population impact first.
• For alerting, add `by siteId` in a follow-on if the TA enriches site, or join to a site lookup from a parallel search.

**Pipeline walkthrough**
• `spath` / `mvexpand` / `where scoreCategory` isolates the onboarding health band; `where onboarding_score < 50` is the failure filter.

Step 3 — Validate
• In Catalyst, open Client health and confirm an onboarding or association-health concept exists for the same period; compare `value` to Splunk for one poll window.
• If zero rows always, the category string may be `ONBOARD` or a localized label—dump `| stats values(scoreCategory)` after flattening.

Step 4 — Operationalize
• P2-style alert when `affected_clients` exceeds a floor or `onboarding_score` stays under threshold for two consecutive runs; include links to ISE, DHCP scope status, and WLC radio/load.
• Dashboard: timechart of minimum onboarding score for early warning, plus a table of worst recent polls.

Step 5 — Troubleshooting
• False positives: planned AAA/DHCP change windows—use a maintenance lookup to suppress. Large zero rows: empty `value` on some platforms—`where isnum(value)` before threshold.


## SPL

```spl
index=catalyst sourcetype="cisco:dnac:clienthealth" | spath output=categories path=scoreDetail{} | mvexpand categories | spath input=categories | where scoreCategory="ONBOARDING" | stats latest(value) as onboarding_score latest(clientCount) as affected_clients by _time | where onboarding_score < 50 | sort -affected_clients
```

## Visualization

Table of affected waves in time, single value of worst `onboarding_score`, timechart of rolling minimum onboarding score for early warning.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
- [Catalyst Center Integration Guide](docs/guides/catalyst-center.md)
