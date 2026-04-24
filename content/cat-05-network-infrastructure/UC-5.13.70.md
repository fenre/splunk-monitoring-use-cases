---
id: "5.13.70"
title: "Catalyst Center + Meraki Branch Network Health"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.13.70 · Catalyst Center + Meraki Branch Network Health

## Description

Compares Catalyst Center campus network health with Meraki branch network health to identify divergence between campus and branch office performance.

## Value

Many organizations use Catalyst Center for campus and Meraki for branches. Comparing both reveals whether network problems are campus-specific, branch-specific, or universal.

## Implementation

Deploy **Cisco Catalyst Add-on (7538)** for `cisco:dnac:networkhealth` on `index=catalyst` and **Cisco Meraki Add-on (5580)** for organization API data as `sourcetype=meraki:api` (commonly `index=cisco_network` or your org standard).

1. **Meraki API:** In the Meraki TA, add an org API key and enable the inputs that produce device/network health and status (health or summary endpoints per TA version).
2. **Field names:** The SPL uses `health_score` and `status` on Meraki events — if your field names differ (`uplinkStatus`, `device status`), map them with `eval` before `stats`.
3. **Time sync:** `appendcols` is row-aligned; for production, bin `_time` on both sides to the same span (e.g. 5m) or use a **join** on discrete `_time` buckets.
4. **Thresholds:** Adjust `15` to match the noise floor for your environment.

## Detailed Implementation

Prerequisites
• UC-5.13.16 complete; `cisco:dnac:networkhealth` events with `healthScore`.
• Meraki org API with TA 5580 writing `meraki:api` to an index (here `cisco_network`) with fields for branch health/availability.

Step 1 — Meraki Add-on 5580
- Install TA 5580; create credentials with API key and select organization(s).
- Enable inputs for organization status, device health, or uplink health (names vary by version — use **Data inputs** in Splunk to confirm `sourcetype=meraki:api` and sample fields).
- Verify `health_score` exists or derive, e.g. `| eval health_score=if(healthy,"100",50)` from raw fields you do have.

Step 2 — Catalyst (7538)
- Confirm `networkhealth` input on `index=catalyst` per prior UCs; note poll interval and site scope.

Step 3 — Baseline SPL

```spl
index=catalyst sourcetype="cisco:dnac:networkhealth" | stats latest(healthScore) as campus_health by _time | appendcols [search index=cisco_network sourcetype="meraki:api" | stats avg(health_score) as branch_health count(eval(status="offline")) as offline_branches by _time] | eval campus_vs_branch=campus_health-branch_health | where abs(campus_vs_branch) > 15 | table _time campus_health branch_health offline_branches campus_vs_branch
```

Step 4 — Interpretation
- **Campus low, Meraki high:** triage SD-Access, Catalyst site, and WAN to campus.
- **Meraki branch_health low with offline devices:** use Meraki dashboard and UC drill-downs; correlate with Meraki `status` in raw events.
- **Both low:** look for regional or carrier impact.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:networkhealth" | stats latest(healthScore) as campus_health by _time | appendcols [search index=cisco_network sourcetype="meraki:api" | stats avg(health_score) as branch_health count(eval(status="offline")) as offline_branches by _time] | eval campus_vs_branch=campus_health-branch_health | where abs(campus_vs_branch) > 15 | table _time campus_health branch_health offline_branches campus_vs_branch
```

## Visualization

Dual-axis line: campus_health vs branch_health; table when `abs(campus_vs_branch) > 15`; optional single value for `offline_branches` with a threshold.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
- [Cisco Meraki Add-on (Splunkbase 5580)](https://splunkbase.splunk.com/app/5580)
