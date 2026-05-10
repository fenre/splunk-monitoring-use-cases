<!-- AUTO-GENERATED from UC-5.13.73.json — DO NOT EDIT -->

---
id: "5.13.73"
title: "Multi-Domain Network Health Executive Dashboard"
status: "verified"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.13.73 · Multi-Domain Network Health Executive Dashboard

> **Criticality:** Medium &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Operations, Performance &middot; **Wave:** Run &middot; **Status:** Verified

*We put all the most important network health numbers on one screen — device health, user experience, security vulnerabilities, compliance status — so your leadership can see in 30 seconds whether the network is healthy or if something needs attention. It is the single page that tells the whole story.*

---

## Description

Provides a unified executive dashboard combining health scores from Catalyst Center (campus), SD-WAN (WAN), Meraki (branch), and ThousandEyes (external paths) into a single multi-domain view.

## Value

Executives need one view of network health, not four consoles. This dashboard combines all Cisco network domains into a single composite health score.

## Implementation

1. Verify all three source pipelines are populated: cisco:dnac:networkhealth (campus), cisco:sdwan:* (WAN), and meraki:devicesavailabilities + meraki:assurancealerts (branch). 2. Compose the Meraki branch_health from availability % minus a 0.3 weight per open alert. 3. enterprise_health is the simple average of campus / WAN / branch. 4. Render as a single-value tile per tier plus a combined gauge.

## Detailed Implementation

### Prerequisites
- Install and configure the required add-on or app: `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538) + `Cisco ThousandEyes App for Splunk` (Splunkbase 7719) + `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
- Ensure the following data sources are available: Cisco DNA Center add-on (sourcetype=cisco:dnac:networkhealth), Cisco SD-WAN add-on (sourcetype=cisco:sdwan:*), and Splunk_TA_cisco_meraki Devices Availabilities + Assurance Alerts inputs. The Meraki branch tier composes a synthetic health score from availability % minus (open_alerts * 0.3)..
- For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

### Step 1 — Configure data collection
1. Verify all three source pipelines are populated: cisco:dnac:networkhealth (campus), cisco:sdwan:* (WAN), and meraki:devicesavailabilities + meraki:assurancealerts (branch). 2. Compose the Meraki branch_health from availability % minus a 0.3 weight per open alert. 3. enterprise_health is the simple average of campus / WAN / branch. 4. Render as a single-value tile per tier plus a combined gauge.

### Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=catalyst sourcetype="cisco:dnac:networkhealth"
| stats latest(healthScore) as campus_health
| appendcols [
    search index=sdwan sourcetype="cisco:sdwan:*"
    | stats latest(health_score) as wan_health
  ]
| appendcols [
    search index=meraki sourcetype="meraki:devicesavailabilities" earliest=-1h
    | stats sum(eval(if(status="online",1,0))) as online,
            count as total
    | eval branch_health = round(online*100/total, 1)
  ]
| appendcols [
    search index=meraki sourcetype="meraki:assurancealerts" earliest=-24h
    | stats count as branch_alerts
  ]
| eval branch_health = round(branch_health - (branch_alerts*0.3), 1)
| eval enterprise_health = round((campus_health + wan_health + branch_health) / 3, 1)
| table campus_health, wan_health, branch_health, branch_alerts, enterprise_health
```

#### Understanding this SPL

**Multi-Domain Network Health Executive Dashboard** — Executives need one view of network health, not four consoles. This dashboard combines all Cisco network domains into a single composite health score.

Documented **Data sources**: Cisco DNA Center add-on (sourcetype=cisco:dnac:networkhealth), Cisco SD-WAN add-on (sourcetype=cisco:sdwan:*), and Splunk_TA_cisco_meraki Devices Availabilities + Assurance Alerts inputs. The Meraki branch tier composes a synthetic health score from availability % minus (open_alerts * 0.3). **App/TA** (typical add-on context): `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538) + `Cisco ThousandEyes App for Splunk` (Splunkbase 7719) + `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: catalyst; **sourcetype**: cisco:dnac:networkhealth. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

- Scopes the data: index=catalyst, sourcetype="cisco:dnac:networkhealth". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
- `stats` aggregates the pipeline (counts, distinct values, sums, percentiles, etc.) into fewer rows.
- Adds columns from a subsearch with `appendcols`.
- Adds columns from a subsearch with `appendcols`.
- Adds columns from a subsearch with `appendcols`.
- `eval` defines or adjusts **branch_health** — often to normalize units, derive a ratio, or prepare for thresholds.
- `eval` defines or adjusts **enterprise_health** — often to normalize units, derive a ratio, or prepare for thresholds.
- Pipeline stage (see **Multi-Domain Network Health Executive Dashboard**): table campus_health, wan_health, branch_health, branch_alerts, enterprise_health


### Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

### Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Executive row: large single values for campus_health, wan_health, branch_health, te_latency_ms, overall_health; treemap of domain status; link-out drilldowns to UC-5.13.68–5.13.72 panel searches.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:networkhealth"
| stats latest(healthScore) as campus_health
| appendcols [
    search index=sdwan sourcetype="cisco:sdwan:*"
    | stats latest(health_score) as wan_health
  ]
| appendcols [
    search index=meraki sourcetype="meraki:devicesavailabilities" earliest=-1h
    | stats sum(eval(if(status="online",1,0))) as online,
            count as total
    | eval branch_health = round(online*100/total, 1)
  ]
| appendcols [
    search index=meraki sourcetype="meraki:assurancealerts" earliest=-24h
    | stats count as branch_alerts
  ]
| eval branch_health = round(branch_health - (branch_alerts*0.3), 1)
| eval enterprise_health = round((campus_health + wan_health + branch_health) / 3, 1)
| table campus_health, wan_health, branch_health, branch_alerts, enterprise_health
```

## Visualization

Executive row: large single values for campus_health, wan_health, branch_health, te_latency_ms, overall_health; treemap of domain status; link-out drilldowns to UC-5.13.68–5.13.72 panel searches.

## Known False Positives

**One domain's data source offline making the multi-domain dashboard incomplete.** If one of the data sources (SD-WAN, Meraki, ThousandEyes) is not configured or temporarily unavailable, its health score will be null or missing. Distinguish by checking whether the missing score corresponds to a data source that is not deployed in this environment. Suppress by using `| fillnull value="N/A"` for undeployed data sources and noting which domains are active in the dashboard header.

**Different health score scales across domains making side-by-side comparison misleading.** Campus (0-100), WAN (may use different scale), and Meraki (different methodology) health scores may not be directly comparable. Distinguish by checking the typical range for each domain — if they cluster at different ranges, direct comparison is inappropriate. Suppress by normalizing all scores to a common scale (e.g., percentile rank within each domain) before presenting in the executive dashboard.

**Maintenance window in one domain creating a dip that the executive dashboard shows as a cross-domain problem.** A WAN circuit maintenance may cause the WAN health column to drop while all other domains are healthy. Distinguish by checking whether only one domain is affected. Suppress by adding per-domain maintenance window annotations to the dashboard.

**Executive audience misinterpreting a single-domain dip as a systemic issue.** The multi-domain dashboard is designed for executive consumption. A localized issue in one domain may be interpreted as a broader problem. No SPL suppression — mitigate by adding contextual annotations (trend sparklines, domain-specific drill-downs) so the executive can see that the issue is contained.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
- [Cisco ThousandEyes App (Splunkbase 7719)](https://splunkbase.splunk.com/app/7719)
- [Cisco Meraki Add-on (Splunkbase 5580)](https://splunkbase.splunk.com/app/5580)
