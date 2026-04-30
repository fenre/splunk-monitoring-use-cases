<!-- AUTO-GENERATED from UC-5.13.73.json — DO NOT EDIT -->

---
id: "5.13.73"
title: "Multi-Domain Network Health Executive Dashboard"
status: "verified"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.13.73 · Multi-Domain Network Health Executive Dashboard

> **Criticality:** Medium &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Operational, Performance &middot; **Wave:** Run &middot; **Status:** Verified

*We put all the most important network health numbers on one screen — device health, user experience, security vulnerabilities, compliance status — so your leadership can see in 30 seconds whether the network is healthy or if something needs attention. It is the single page that tells the whole story.*

---

## Description

Provides a unified executive dashboard combining health scores from Catalyst Center (campus), SD-WAN (WAN), Meraki (branch), and ThousandEyes (external paths) into a single multi-domain view.

## Value

Executives need one view of network health, not four consoles. This dashboard combines all Cisco network domains into a single composite health score.

## Implementation

1. **7538 (Catalyst, SD-WAN, optional Cyber Vision):** Configure Catalyst Center + vManage per UC-5.13.1 / UC-5.13.16 / UC-5.13.69.
2. **5580 (Meraki):** Org API to `meraki:api` in `index=cisco_network` (UC-5.13.70).
3. **7719 (ThousandEyes):** OTel stream + **`stream_index`** macro for agent-to-server tests (UC-5.13.71).
4. **Composite:** The `coalesce` terms avoid null WAN/branch in partial deployments; replace with 0 or separate panels if you need strict math.
5. **Dashboard:** Dashboard Studio (or Simple XML) with one row per domain + headline single values for `overall_health` and `te_latency_ms`.

## Detailed Implementation

### Prerequisites
- UC-5.13.1 (Device Health), UC-5.13.9 (Client Health), UC-5.13.16 (Network Health), UC-5.13.21 (Issue Summary), UC-5.13.28 (Compliance) must ALL be operational — this executive dashboard pulls KPIs from every Catalyst Center data feed.
- For cross-product panels: UC-5.13.68 (ISE), UC-5.13.69 (SD-WAN), UC-5.13.70 (Meraki), UC-5.13.71 (ThousandEyes) add value but are not required. Include them only if those integrations are deployed.
- This UC doesn't introduce new data collection — it's a pure presentation layer that combines KPIs from other UCs into a single executive view. All data feeds must already be flowing.
- Splunk Dashboard Studio is recommended for the visual design. Classic Simple XML works but Dashboard Studio's grid layout, conditional formatting, and dynamic options produce a better executive presentation.
- Create a `network_exec` Splunk role with `srchIndexesAllowed = catalyst` and read-only access. Executives should see the dashboard but not modify searches.

### Step 1 — Configure data collection
No new data collection. This UC aggregates KPIs from existing feeds. Verify all required sourcetypes are producing events:
```spl
index=catalyst earliest=-1h
| stats count by sourcetype
| sort -count
```
Required sourcetypes: `cisco:dnac:devicehealth`, `cisco:dnac:clienthealth`, `cisco:dnac:networkhealth`, `cisco:dnac:issue`, `cisco:dnac:compliance`, `cisco:dnac:securityadvisory`. All should show non-zero event counts.

### Step 2 — Create the dashboard
The executive dashboard is a **composed view** using base searches from other UCs. Each panel runs a search from the corresponding UC's SPL.

Dashboard layout (Dashboard Studio recommended):

**Row 1 — Hero KPIs (single-value tiles):**
- Network Health Score (from UC-5.13.16): `index=catalyst sourcetype="cisco:dnac:networkhealth" | where healthScore > 0 | stats latest(healthScore) as score`
- Device Fleet Health (from UC-5.13.1): `index=catalyst sourcetype="cisco:dnac:devicehealth" | stats count(eval(overallHealth<50)) as unhealthy dc(deviceName) as total | eval healthy_pct=round((total-unhealthy)*100/total,1)`
- Client Experience (from UC-5.13.9): healthy client percentage from the clienthealth summary
- Active P1/P2 Issues (from UC-5.13.23): `index=catalyst sourcetype="cisco:dnac:issue" (priority="P1" OR priority="P2") status!="RESOLVED" | stats dc(issueId) as critical_issues`
- Compliance Rate (from UC-5.13.28): `index=catalyst sourcetype="cisco:dnac:compliance" | where complianceStatus IN ("COMPLIANT","NON_COMPLIANT") | stats count(eval(complianceStatus="COMPLIANT")) as ok count as total | eval pct=round(ok*100/total,1)`
- CRITICAL PSIRTs (from UC-5.13.34): `index=catalyst sourcetype="cisco:dnac:securityadvisory" severity="CRITICAL" | where deviceCount > 0 | stats dc(advisoryId) as critical_advisories`

**Row 2 — Trending (7-day sparklines or timecharts):**
- Network health score trend (UC-5.13.17)
- Issue count trend (UC-5.13.22)
- Compliance percentage trend (UC-5.13.30)

**Row 3 — Top Issues (tables):**
- Top 5 unhealthiest devices (UC-5.13.1 sorted by health, head 5)
- Top 5 worst sites (UC-5.13.5 or UC-5.13.19)
- Top 5 active P1/P2 issues (UC-5.13.23)

**Row 4 — Cross-product (optional, if integrations are deployed):**
- ISE auth failure correlation (UC-5.13.68)
- ThousandEyes path quality (UC-5.13.71)
- Meraki branch health (UC-5.13.70)

Each panel uses a base search from the referenced UC. Use Dashboard Studio's chain searches to share the `index=catalyst` base filter across panels for performance.

Time picker: default "Last 24 hours" with presets for "Last 4 hours" (incident) and "Last 7 days" (weekly review).

Why a composed dashboard rather than a standalone search: the executive dashboard doesn't need its own SPL — it draws from the KPIs already validated in individual UCs. This ensures the numbers are consistent: the "unhealthy devices" count on the exec dashboard matches what the NOC sees in UC-5.13.1 because they use the same search logic.

### Step 3 — Validate
(a) Open each panel and verify the number matches the corresponding UC's output. The Network Health Score should match UC-5.13.16. The P1/P2 count should match UC-5.13.23. Any discrepancy means the panel's search logic diverged from the source UC.

(b) Check all panels load within 30 seconds. If any panel is slow, add `earliest=-20m` to narrow the time range for that panel (sacrifice history for speed on the exec dashboard).

(c) Present the dashboard to a non-technical executive. Ask: "Do you understand what each number means and whether it's good or bad?" If not, improve the colour thresholds and labels.

(d) Compare with **Catalyst Center > Assurance > Health** landing page. The executive dashboard should tell a similar story but with Splunk's advantages: longer history, cross-product correlation, and compliance/PSIRT dimensions that Catalyst Center's landing page doesn't prominently feature.

### Step 4 — Operationalize
- **CIO weekly review**: the executive dashboard is the first slide in the weekly technology review. The CIO looks at Row 1 KPIs for 30 seconds and knows whether the network is healthy.
- **Board reporting**: export Row 1 + Row 2 as a quarterly PDF. The trending sparklines show quarter-over-quarter improvement.
- **Incident commander**: during a major incident, this dashboard provides the multi-domain view that no individual UC offers alone. It answers "how bad is it across all dimensions?"
- **New employee onboarding**: this dashboard is the first thing a new network engineer should see — it gives them the full picture of the network's current state.

Runbook (owner: Network Operations Lead):
1. Daily morning: glance at Row 1 KPIs. All green → no action. Any red → drill into the corresponding UC.
2. Weekly: review Row 2 trending. All stable or improving → no action. Degrading trend → identify the UC that shows the root cause.
3. During incidents: use this dashboard for the status update to management. "Network health is at 72, down from 90. 15 devices are unhealthy, concentrated at Building C. Client health is at 65% healthy. 3 P1 issues are active."

### Step 5 — Troubleshooting

- **Panels show "No results"** — the corresponding data feed isn't flowing. Check `| stats count by sourcetype` for the missing sourcetype.

- **Dashboard is slow to load** — too many panels querying long time ranges. Solutions: (a) use base searches with chain searches to share the index scan; (b) narrow individual panel time ranges; (c) use accelerated data models where available.

- **Numbers don't match individual UCs** — the panel search logic has diverged. Copy the exact SPL from the source UC to ensure consistency.

- **Cross-product panels show no data** — those integrations (ISE, ThousandEyes, Meraki) aren't deployed. Hide the panels or show "Integration not configured" placeholder text.

- **Executives want different metrics** — this is the most common request. Add/remove panels based on what the CIO actually looks at. The dashboard should reflect THEIR priorities, not the engineering team's.

- **Want to add non-Catalyst-Center metrics** — the exec dashboard can include panels from any Splunk index. Add server health (cat-1), cloud health (cat-4), or security posture (cat-10) panels for a true multi-domain view.

- **Colour thresholds feel wrong** — adjust based on your network's steady state. If network health is typically 92, set green ≥ 85, yellow 70–85, red < 70. If it's typically 80, use green ≥ 75, yellow 60–75, red < 60.

- **PDF export looks different from the dashboard** — Dashboard Studio PDF rendering has limitations. Test the export before sending to the CIO.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:networkhealth" | stats latest(healthScore) as campus_health | appendcols [search index=sdwan sourcetype="cisco:sdwan:*" | stats latest(health_score) as wan_health] | appendcols [search index=cisco_network sourcetype="meraki:api" | stats avg(health_score) as branch_health] | appendcols [search `stream_index` thousandeyes.test.type="agent-to-server" | stats avg(network.latency) as te_latency_s | eval te_latency_ms=round(te_latency_s*1000,1)] | eval overall_health=round((campus_health+coalesce(wan_health,campus_health)+coalesce(branch_health,campus_health))/3,1) | table campus_health wan_health branch_health te_latency_ms overall_health
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
