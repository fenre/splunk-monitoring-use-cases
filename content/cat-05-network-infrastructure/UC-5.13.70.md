<!-- AUTO-GENERATED from UC-5.13.70.json — DO NOT EDIT -->

---
id: "5.13.70"
title: "Catalyst Center + Meraki Branch Network Health"
status: "verified"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.13.70 · Catalyst Center + Meraki Branch Network Health

> **Criticality:** Medium &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Performance, Availability &middot; **Wave:** Run &middot; **Status:** Verified

*We combine the health scores from two different network management systems — the campus network (Catalyst Center) and the branch network (Meraki) — into a single view per building. This shows your team the full picture instead of checking two separate dashboards and hoping someone notices when both say different things about the same location.*

---

## Description

Compares Catalyst Center campus network health with Meraki branch network health to identify divergence between campus and branch office performance.

## Value

Many organizations use Catalyst Center for campus and Meraki for branches. Comparing both reveals whether network problems are campus-specific, branch-specific, or universal.

## Implementation

1. Confirm the Cisco DNA Center add-on is ingesting cisco:dnac:networkhealth with healthScore. 2. Enable Devices Availabilities and Assurance Alerts inputs in Splunk_TA_cisco_meraki. 3. The composed branch_health = availability% - (open_alerts * 0.5). 4. combined_health is the average of the two. Tune weights to your reporting preference and present in a single executive dashboard.

## Detailed Implementation

### Prerequisites
- Install and configure the required add-on or app: `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538) + `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
- Ensure the following data sources are available: Cisco DNA Center for Splunk app (sourcetype=cisco:dnac:networkhealth) for the campus side, plus Splunk_TA_cisco_meraki Devices Availabilities + Assurance Alerts inputs for the Meraki branch side. NOTE: Meraki does not expose a single numeric 'branch health score'; this UC composes one from device availability % and open-alert count..
- For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

### Step 1 — Configure data collection
1. Confirm the Cisco DNA Center add-on is ingesting cisco:dnac:networkhealth with healthScore. 2. Enable Devices Availabilities and Assurance Alerts inputs in Splunk_TA_cisco_meraki. 3. The composed branch_health = availability% - (open_alerts * 0.5). 4. combined_health is the average of the two. Tune weights to your reporting preference and present in a single executive dashboard.

### Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=catalyst sourcetype="cisco:dnac:networkhealth"
| stats latest(healthScore) as campus_health by _time
| appendcols [
    search index=meraki sourcetype="meraki:devicesavailabilities" earliest=-1h
    | stats sum(eval(if(status="online",1,0))) as online,
            count as total
    | eval branch_availability = round(online*100/total, 1)
  ]
| appendcols [
    search index=meraki sourcetype="meraki:assurancealerts" earliest=-24h
    | stats count as branch_open_alerts
  ]
| eval branch_health = round(branch_availability - (branch_open_alerts*0.5), 1)
| eval combined_health = round((campus_health + branch_health) / 2, 1)
| table _time, campus_health, branch_availability, branch_open_alerts, branch_health, combined_health
```

#### Understanding this SPL

**Catalyst Center + Meraki Branch Network Health** — Many organizations use Catalyst Center for campus and Meraki for branches. Comparing both reveals whether network problems are campus-specific, branch-specific, or universal.

Documented **Data sources**: Cisco DNA Center for Splunk app (sourcetype=cisco:dnac:networkhealth) for the campus side, plus Splunk_TA_cisco_meraki Devices Availabilities + Assurance Alerts inputs for the Meraki branch side. NOTE: Meraki does not expose a single numeric 'branch health score'; this UC composes one from device availability % and open-alert count. **App/TA** (typical add-on context): `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538) + `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: catalyst; **sourcetype**: cisco:dnac:networkhealth. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

- Scopes the data: index=catalyst, sourcetype="cisco:dnac:networkhealth". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
- `stats` rolls up events into metrics; results are split **by _time** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
- Adds columns from a subsearch with `appendcols`.
- Adds columns from a subsearch with `appendcols`.
- `eval` defines or adjusts **branch_health** — often to normalize units, derive a ratio, or prepare for thresholds.
- `eval` defines or adjusts **combined_health** — often to normalize units, derive a ratio, or prepare for thresholds.
- Pipeline stage (see **Catalyst Center + Meraki Branch Network Health**): table _time, campus_health, branch_availability, branch_open_alerts, branch_health, combined_health


### Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

### Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Dual-axis line: campus_health vs branch_health; table when `abs(campus_vs_branch) > 15`; optional single value for `offline_branches` with a threshold.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:networkhealth"
| stats latest(healthScore) as campus_health by _time
| appendcols [
    search index=meraki sourcetype="meraki:devicesavailabilities" earliest=-1h
    | stats sum(eval(if(status="online",1,0))) as online,
            count as total
    | eval branch_availability = round(online*100/total, 1)
  ]
| appendcols [
    search index=meraki sourcetype="meraki:assurancealerts" earliest=-24h
    | stats count as branch_open_alerts
  ]
| eval branch_health = round(branch_availability - (branch_open_alerts*0.5), 1)
| eval combined_health = round((campus_health + branch_health) / 2, 1)
| table _time, campus_health, branch_availability, branch_open_alerts, branch_health, combined_health
```

## Visualization

Dual-axis line: campus_health vs branch_health; table when `abs(campus_vs_branch) > 15`; optional single value for `offline_branches` with a threshold.

## Known False Positives

**Meraki cloud connectivity issue causing stale Meraki health data while campus data is current.** If the Meraki dashboard API is slow or unavailable, the Meraki health data in Splunk may be stale while Catalyst Center data is fresh. Distinguish by comparing the latest `_time` from both sourcetypes. Suppress by alerting when the Meraki data staleness exceeds 2x the expected poll interval.

**Different health score scales between Catalyst Center and Meraki.** Catalyst Center uses 0-100 while Meraki may use a different scale or calculation method. A direct numeric comparison may not be meaningful. Distinguish by checking the health score normalization — if Meraki scores cluster around 80-100 while campus scores cluster around 60-80, the scales may not be comparable. Suppress by normalizing both scores to percentile rank within their own distribution before comparing.

**Branch site maintenance causing Meraki health drop for one location while campus is stable.** A single branch office undergoing renovation or equipment replacement will lower the Meraki average. Distinguish by checking whether the Meraki health drop is localized to one network or site. Do not suppress — enrich the alert with the specific branch context.

**Meraki API rate limiting causing incomplete health data.** The Meraki Dashboard API has rate limits that may prevent the TA from collecting health data for all organizations/networks in a single poll. Distinguish by checking `index=_internal` for Meraki TA errors related to HTTP 429 rate limiting. Suppress by increasing the Meraki poll interval or splitting organizations across multiple inputs.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
- [Cisco Meraki Add-on (Splunkbase 5580)](https://splunkbase.splunk.com/app/5580)
- [Catalyst Center Network Health API — Cisco DevNet](https://developer.cisco.com/docs/catalyst-center/#!get-overall-network-health)
