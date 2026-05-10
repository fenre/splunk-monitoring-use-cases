<!-- AUTO-GENERATED from UC-5.13.18.json — DO NOT EDIT -->

---
id: "5.13.18"
title: "Network Health Degradation Alerting"
status: "verified"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.13.18 · Network Health Degradation Alerting

> **Criticality:** Critical &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Availability, Fault &middot; **Wave:** Walk &middot; **Status:** Verified

*We set up an alarm that goes off when the whole network is in trouble — not just one device, but many devices at once. This kind of widespread problem usually means something big happened, like a power failure or a bad software update, and the alarm makes sure the team leader knows immediately so they can coordinate a proper response instead of engineers fixing symptoms one at a time.*

---

## Description

Fires an alert when the aggregate network health score drops below 70 or when more than 10% of managed elements are unhealthy, indicating a systemic multi-device degradation event that individual device alerts (UC-5.13.3) may not escalate correctly because no single device crossed its threshold — this catches correlated failures that collectively represent a major incident.

## Value

UC-5.13.3 pages you when one device is sick. This UC pages you when the *network* is sick — multiple devices degrading simultaneously in a way that drops the aggregate score. A campus-wide score below 70 means the problem is systemic: a spanning tree convergence event, a firmware push gone wrong, a shared upstream failure, or an HVAC failure causing thermal throttling across a building. The aggregate alert ensures you don't miss correlated failures that individually fall just above device-level thresholds but collectively represent a P1 incident. It's the difference between 'switch A is unhealthy' (one ticket) and 'the entire building is degraded' (incident commander).

## Implementation

Same data feed as UC-5.13.16. Schedule as alert: cron `*/15 * * * *`, time range `-30m to now`, trigger on any results. Throttle for 4 hours. This is a high-severity alert — route to the network operations lead, not just the on-call engineer. A campus-wide health drop is an incident, not a ticket.

## Detailed Implementation

### Prerequisites
- UC-5.13.16 (Network Health Overview) must be operational — same `networkhealth` data feed.
- Decide on thresholds before enabling:
  - `healthScore < 70`: Catalyst Center Assurance considers < 70 as "Poor" for the aggregate network. Adjust to < 80 for stricter environments (hospitals, financial trading floors).
  - `bad_pct > 10%`: more than 10% of managed elements unhealthy simultaneously. Adjust based on fleet size — a 500-device campus with 50 unhealthy devices is very different from a 50-device branch with 5.
- This is a **high-severity infrastructure-wide alert**. Configure routing to the network operations *lead*, not just the on-call engineer. A campus-wide health drop is an incident declaration trigger, not a routine ticket.
- Configure at least one alert action before enabling. A critical alert that fires but doesn't page anyone is worse than no alert.
- Splunk capability: the user saving the alert needs `schedule_search` and `list_settings`.

### Step 1 — Configure data collection
Same `networkhealth` input as UC-5.13.16. No additional configuration. Confirm data is flowing:
```spl
index=catalyst sourcetype="cisco:dnac:networkhealth" earliest=-30m
| stats latest(healthScore) as score, latest(badCount) as bad, latest(totalCount) as total
```
All three values should be non-null and reasonable. `score` is typically 80–95 for a healthy campus. `total` should match your managed device count. `bad` should be 0–5% of total in steady state.

### Step 2 — Create the search and alert
```spl
index=catalyst sourcetype="cisco:dnac:networkhealth"
| where healthScore > 0 AND totalCount > 0
| stats latest(healthScore) as health_score latest(badCount) as bad latest(totalCount) as total
| eval bad_pct=round(bad*100/total,1)
| where health_score < 70 OR bad_pct > 10
| table health_score, bad, total, bad_pct
```

Why `where healthScore > 0 AND totalCount > 0` first: filters Assurance recomputation artifacts (healthScore = 0) and empty API responses (totalCount = 0). Without this, the alert fires on every recomputation cycle — typically every hour — generating constant false pages.

Why two trigger conditions (`health_score < 70 OR bad_pct > 10`): these catch different failure modes.
- The `healthScore` threshold catches **concentrated degradation**: a single core switch failure drops the score by 15+ points because Assurance weights critical infrastructure heavily, even though only 1 device is affected.
- The `bad_pct` threshold catches **distributed degradation**: many access switches individually just below their health thresholds, collectively representing a building-wide or campus-wide issue.
- Together they ensure both concentrated and distributed failures trigger the alert.

Why `latest()` not `avg()`: one event per poll for the entire network. `latest()` gives the most recent aggregate state, which is what you want for real-time alerting. `avg()` across multiple polls would smooth a sudden drop — exactly the signal you need to see immediately.

Why this is different from UC-5.13.3 (Device Health Alerting): UC-5.13.3 fires when an individual device drops below threshold. This UC fires when the *aggregate network* drops below threshold. A campus with 500 devices where 30 are individually at health=55 (above UC-5.13.3's threshold of 50) but the aggregate score is 68 (below this UC's threshold of 70) — only this UC catches that distributed degradation.

Schedule as Alert:
- Cron: `*/15 * * * *` (every 15 minutes, aligned with poll interval)
- Time range: `-30m to now` (covers 2 poll cycles for reliability)
- Trigger: "Number of results > 0"
- Throttle: `4h` (suppress repeat alerts for the same ongoing incident)
- Severity: Critical

### Step 3 — Validate
(a) Threshold calibration: run the search over 30 days WITHOUT the `where health_score < 70 OR bad_pct > 10` filter. Plot `health_score` and `bad_pct` as a timechart. The thresholds should be set just below the normal operating range. If `health_score` typically hovers at 85–95, a threshold of 70 gives 15–25 points of headroom — aggressive enough to catch real events, conservative enough to avoid noise.

(b) Historical check: how many times would this alert have fired in the last 30 days? Each firing should correspond to a real incident or maintenance window. If it fires > 3×/week, the thresholds are too tight. If it never fires during a known incident, they're too loose.

(c) Cross-reference: during a known incident last month, verify the alert would have fired by running the search over that time window.

(d) Verify the `healthScore > 0` filter removes Assurance recomputation dips: compare results with and without the filter over 7 days. The filtered version should have fewer results.

(e) Confirm alert action delivery: trigger a test by temporarily lowering the threshold to `< 100` (will fire on any data), verify the PagerDuty/Slack notification arrives, then restore the real threshold.

(f) Vendor UI parity: when the alert fires, open **Catalyst Center > Assurance > Health** and verify the score matches the Splunk alert value.

### Step 4 — Operationalize
Alerting:
- **PagerDuty/Splunk On-Call**: high-urgency page to the network operations lead (not just the on-call engineer). This is an infrastructure-wide event that may require incident declaration.
- Custom details: include `health_score`, `bad` (unhealthy device count), `total`, `bad_pct`, and drilldown links to UC-5.13.1 (Device Health), UC-5.13.5 (Health by Site), UC-5.13.9 (Client Health).
- **Slack/Teams**: `#incident-network` channel for immediate visibility across the operations team. Do not use a general ops channel — this alert deserves its own incident channel.

Runbook (owner: Network Operations Lead — this is an **incident-level** runbook, not a ticket-level one):
1. **Confirm the degradation** in **Catalyst Center > Assurance > Health**. If Catalyst Center also shows degraded health, the problem is real. If Catalyst Center shows healthy but Splunk shows degraded, investigate data collection (TA) health.
2. **Check the scope**:
   - Open UC-5.13.1 (Device Health): how many devices are unhealthy? Which types (switches, routers, WLCs)?
   - Open UC-5.13.5 (Health by Site): is the degradation localised to one site or campus-wide?
   - Open UC-5.13.9 (Client Health): are users affected? If client health is also degraded, users are feeling it.
3. **If localised** (one site, one device type): this is likely a localised infrastructure event.
   - Power failure at that site → contact facilities.
   - Upstream link down → check the distribution/core switch (UC-5.13.1).
   - Switch stack failure → dispatch on-site team.
4. **If campus-wide** (multiple sites, multiple device types): this is a systemic event. Common causes:
   - **Firmware push gone wrong**: check `index=catalyst sourcetype="cisco:dnac:audit:logs"` for recent SWIM activity. If confirmed, pause the SWIM task and assess rollback.
   - **Spanning tree convergence**: check `index=network sourcetype=cisco:ios "STP"` for topology changes. Multiple STP events correlating with the health drop confirms this.
   - **RADIUS/ISE failure**: check `index=ise` for ISE health. If ISE is down, all 802.1X-dependent services fail simultaneously.
   - **DNS/DHCP infrastructure failure**: check DNS/DHCP server health.
5. **If `bad` count is growing** across consecutive polls: the situation is escalating. Declare an incident and begin multi-domain triage across UC-5.13.1, UC-5.13.9, and UC-5.13.21.
6. **If the alert corresponds to a planned maintenance window**: acknowledge and note the change ID. The alert will auto-clear when devices recover.
7. **Post-incident**: document the timeline, root cause, and remediation in the incident record. Track MTTR with UC-5.13.77.

Capacity/SLO review (monthly, owner: Network Architecture):
- Track alert frequency: `| search savedsearch="UC-5.13.18 alert" | stats count by date_month`. Increasing alert frequency indicates network stability is declining.
- Review threshold appropriateness: is the 70-point threshold still aligned with the SLO? If the fleet grew and the baseline shifted, adjust.

### Step 5 — Troubleshooting

- **Alert fires every 15 minutes for the same ongoing incident** — throttling not configured. Set throttle to 4 hours in the alert settings. The throttle field should be empty (no field-based throttle for aggregate alerts).

- **Alert fires during every maintenance window** — maintain `catalyst_maintenance_windows` lookup and add: `| lookup catalyst_maintenance_windows _time OUTPUT in_window | where in_window != "yes"` to the search.

- **Alert never fires even during known incidents** — thresholds too loose. Lower `health_score` threshold from 70 to 80, or lower `bad_pct` from 10 to 5. Run the historical check from Step 3(b) to calibrate.

- **Alert fires for single-device failures** — the `healthScore` metric is weighted, so a single core device failure can drop the score below 70 even with `bad = 1`. Add `| where bad > 2` if you want to filter single-device events to UC-5.13.3 only.

- **`healthScore` is null** — Assurance not running. See UC-5.13.16 Step 5.

- **`bad_pct` looks wrong** — `totalCount` may include device types that don't report health (APs in some versions, third-party devices). The denominator may be larger than expected. Cross-reference with UC-5.13.4 (Device Health by Category) for the actual counted fleet per type.

- **Alert fires at the same time every day** — RRM optimisation or scheduled backup window causing a brief health dip. Check the timing against your network's known scheduled activities and either annotate or suppress that window.

- **Alert actions not triggering** — check `index=_internal sourcetype=splunkd component=AlertManager` for the alert name. Common issues: PagerDuty integration key expired, Slack webhook URL changed, email relay misconfigured.

- **`healthScore` and `bad_pct` trigger at different times** — expected. `healthScore` is weighted (core device failures cause disproportionate drops). `bad_pct` is unweighted (counts devices equally). They catch different failure patterns, which is the design intent.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:networkhealth"
| where healthScore > 0 AND totalCount > 0
| stats latest(healthScore) as health_score latest(badCount) as bad latest(totalCount) as total
| eval bad_pct=round(bad*100/total,1)
| where health_score < 70 OR bad_pct > 10
| table health_score, bad, total, bad_pct
```

## Visualization

(1) Alert results: health_score, bad, total, bad_pct — colour-coded red. (2) Single value: current health_score as a large gauge (same as UC-5.13.16 but with the alert context). (3) Timechart from UC-5.13.17 showing the health score drop in context. (4) Drilldown links to UC-5.13.1 (which devices?), UC-5.13.5 (which sites?), UC-5.13.9 (are clients affected?).

## Known False Positives

**Planned maintenance window affecting aggregate health score.** During a firmware upgrade involving multiple devices, the aggregate score drops as devices reload. Distinguish by correlating with ITSM change records or `index=catalyst sourcetype="cisco:dnac:audit:logs"` for upgrade tasks. Suppress with `catalyst_maintenance_windows` lookup.

**Assurance recomputation cycle.** Brief drops to 0 during Assurance recomputation are filtered by `where healthScore > 0` in the SPL. If the filter is removed, false alerts will fire at the top of each hour.

**Single high-impact device failure inflating the score drop.** A core switch failure adds 1 to `badCount` but drops `healthScore` by 10+ points due to weighted scoring. Distinguish by checking whether `bad = 1` — a single-device failure should be handled by UC-5.13.3, not this aggregate alert. Consider adding `| where bad > 2` to filter single-device events.

**Catalyst Center scope change.** Adding or removing devices from management changes `totalCount`, shifting `bad_pct`. Distinguish by tracking `totalCount` stability: if `totalCount` changed significantly between consecutive polls, the score shift may be an inventory change rather than health degradation.

## References

- [Cisco Catalyst Add-on for Splunk (Splunkbase 7538)](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center Intent API — Network Health endpoint](https://developer.cisco.com/docs/catalyst-center/#!get-overall-network-health)
- [Catalyst Center Integration Guide (this repo)](docs/guides/catalyst-center.md)
- [Splunk Alert Actions — PagerDuty, Webhook, Email](https://docs.splunk.com/Documentation/Splunk/latest/Alert/Setupalertactions)
