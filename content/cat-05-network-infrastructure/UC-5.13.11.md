<!-- AUTO-GENERATED from UC-5.13.11.json — DO NOT EDIT -->

---
id: "5.13.11"
title: "Poor Client Health Detection and Alerting"
status: "verified"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.13.11 · Poor Client Health Detection and Alerting

> **Criticality:** Critical &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Availability, Performance &middot; **Wave:** Walk &middot; **Status:** Verified

*We set up an alarm that goes off when too many people are having a bad network experience — either on the wired connections or the Wi-Fi. The alarm tells the team whether it is a wireless problem or a wired problem, so they know immediately which engineers to call and where to look.*

---

## Description

Alerts when the percentage of healthy clients drops below category-specific thresholds — 70% for wireless, 90% for wired — indicating a systemic issue like DHCP pool exhaustion, RADIUS failure, AP overload, or upstream switch degradation that is actively impacting user connectivity.

## Value

UC-5.13.9 shows the current health; UC-5.13.10 shows the trend. This UC *pages you* when client experience degrades beyond acceptable limits. When 30% of wireless clients are unhealthy during business hours, that translates directly to dropped VoIP calls, failed Webex joins, and a flood of help-desk tickets. The category-specific thresholds (tighter for wired, looser for wireless) prevent alert fatigue — wireless is inherently noisier, so the same threshold that works for Ethernet would fire constantly on Wi-Fi without the differentiation.

## Implementation

Same data feed as UC-5.13.9. Schedule as alert: cron `*/15 * * * *`, time range `-30m to now`, trigger on any results. Throttle by `cat_name` for 4 hours. Route to PagerDuty during business hours. Tune thresholds per campus — a university with guest Wi-Fi may need a lower threshold (60%) for wireless.

## Detailed Implementation

### Prerequisites
- UC-5.13.9 (Client Health Overview) must be operational — confirms the `clienthealth` data feed and nested JSON extraction work correctly.
- Decide on per-category thresholds before enabling the alert:
  - **WIRED threshold (default 90%)**: wired client health is typically 90–98%. Dropping below 90% indicates a switch, VLAN, or DHCP issue.
  - **WIRELESS threshold (default 70%)**: wireless is inherently noisier. Typical range is 70–90%. Dropping below 70% during business hours means significant user impact.
  - Document these thresholds in your SLA/SLO documentation. Adjust based on the first week's alert volume.
- Decide whether to alert during off-hours. Overnight, low client counts (< 20) produce volatile percentages that may false-fire. Consider restricting the alert to business hours: `| where date_hour >= 7 AND date_hour <= 19 AND NOT match(date_wday, "saturday|sunday")`.
- Configure at least one alert action: PagerDuty/On-Call, Slack, email. See Step 4.

### Step 1 — Configure data collection
No additional configuration. Same `clienthealth` input as UC-5.13.9. Confirm the nested `healthyClientsPercentage` field is present:
```spl
index=catalyst sourcetype="cisco:dnac:clienthealth" earliest=-30m
| spath output=categories path=scoreDetail{}
| mvexpand categories
| spath input=categories output=healthy_pct path=healthyClientsPercentage
| where isnotnull(healthy_pct)
| stats count
```
If count > 0, you're ready. If 0, your TA version may not include `healthyClientsPercentage` — fall back to the `value` field from `scoreCategory` (see UC-5.13.9 Step 2).

### Step 2 — Create the search and alert
```spl
index=catalyst sourcetype="cisco:dnac:clienthealth"
| spath output=categories path=scoreDetail{}
| mvexpand categories
| spath input=categories output=cat_name path=scoreCategory.scoreCategory
| spath input=categories output=healthy_pct path=healthyClientsPercentage
| spath input=categories output=client_count path=clientCount
| where isnum(healthy_pct) AND cat_name IN ("WIRED","WIRELESS")
| eval threshold=case(cat_name="WIRED",90, cat_name="WIRELESS",70)
| where healthy_pct < threshold
| table _time, cat_name, healthy_pct, client_count, threshold
```

Why separate thresholds for WIRED and WIRELESS: wireless client health is inherently lower due to RF interference, client device variability, and roaming transitions. A universal threshold of 80% would never fire for wired (typically 95%+) and fire constantly for wireless (often 70–80%). Category-specific thresholds tune the alert to be equally meaningful for both segments.

Why filter to WIRED and WIRELESS only (excluding ALL): the ALL category is a weighted average of both. Alerting on ALL would mask the source — you'd know client health dropped but not whether it's a wireless or wired problem. By alerting per category, the `cat_name` in the alert payload immediately tells the responder which team to engage.

Why include `client_count` in the output: it provides context for the alert. "70% healthy with 500 clients" is very different from "70% healthy with 5 clients." Low client count alerts may be noise (see Known False Positives).

Why not use `eval poor_pct = 100 - healthy_pct` instead: expressing the alert in terms of "healthy % below threshold" is more intuitive for operators than "unhealthy % above threshold." The mental model is "we expect 80%+ healthy; we're at 65% — that's bad." But either approach is equivalent.

Schedule as Alert:
- Cron: `*/15 * * * *` (every 15 minutes, aligned with poll interval)
- Time range: `-30m to now` (covers 2 poll cycles)
- Trigger: "Number of results > 0"
- Throttle: by `cat_name` for `4h`
- Business-hours-only variant: add `| where date_hour >= 7 AND date_hour <= 19` to avoid off-hours noise

### Step 3 — Validate
(a) Threshold calibration: run the search over the last 7 days WITHOUT the `| where healthy_pct < threshold` filter. Plot `healthy_pct` as a timechart per `cat_name`. The thresholds should be set just below the normal operating range — if WIRELESS typically hovers at 78%, a threshold of 70% gives 8 points of headroom. If it hovers at 85%, raise the threshold to 80%.

(b) Alert fire check: if the search returns results for the last 24 hours, these are genuine breaches. Verify each one corresponds to a real user-experience problem by correlating with help-desk ticket data or user complaints.

(c) Off-hours noise check: run the search filtered to `date_hour < 7 OR date_hour > 19`. If it returns many results during off-hours, add the business-hours filter or the `| where client_count > 20` guard.

(d) False positive rate: over 7 days, count alerts vs actionable incidents. Target: > 80% actionable. If too many false positives, raise the threshold or add the 2-consecutive-polls guard.

(e) Cross-reference with **Catalyst Center > Assurance > Health > Client Health** during a known breach. The percentage shown in the GUI should match the Splunk alert value within 2 points.

### Step 4 — Operationalize
Alert actions:

**PagerDuty / Splunk On-Call:**
- Routing key: network operations on-call
- Severity: `high` for WIRED breaches (wired drops are rarer and more severe), `warning` for WIRELESS breaches
- Custom details: `cat_name`, `healthy_pct`, `threshold`, `client_count`, and links to UC-5.13.12 (by SSID) and UC-5.13.13 (by site) for drilldown

**Slack / Teams:**
- `#network-ops`: all client health alerts
- Message: "Client Health Alert: {cat_name} healthy at {healthy_pct}% (threshold {threshold}%) — {client_count} clients affected"

Runbook (owner: NOC Tier 1):
1. Open the alert. Note `cat_name` (WIRED or WIRELESS) and `healthy_pct`.
2. **If WIRELESS**: open UC-5.13.12 (Client Health by SSID). Is the degradation on one SSID (e.g., guest) or all SSIDs?
   - Single SSID: suspect SSID-specific issue (RADIUS policy, VLAN, QoS). Escalate to wireless team.
   - All SSIDs: suspect infrastructure issue. Check UC-5.13.42 (RSSI/SNR) for RF quality. If RSSI is fine, check DHCP and DNS.
3. **If WIRED**: open UC-5.13.1 (Device Health) filtered to switches. Is a specific access switch unhealthy?
   - Yes: the degradation is localised. Check the switch's port status and uplink.
   - No: suspect shared infrastructure (DHCP server, RADIUS, upstream router). Check UC-5.13.16 (Network Health) for aggregate impact.
4. Open UC-5.13.13 (Client Health by Site). Is the degradation localised to one building or campus-wide?
   - One building: physical infrastructure issue (UPS, HVAC, cabling). Contact facilities.
   - Campus-wide: systemic issue. Escalate to incident commander.
5. Correlate with UC-5.13.21 (Issues): did Catalyst Center's AI detect a related Assurance issue?
6. After resolution, verify `healthy_pct` recovers above threshold in the next 1–2 polls.

Tuning cadence: review thresholds monthly for the first quarter. Adjust based on seasonal patterns (higher load during term vs holidays for schools, business season for retail).

### Step 5 — Troubleshooting

- **Alert fires constantly (> 5x/day)** — threshold too tight for your environment. Run the 7-day calibration search from Step 3(a) and set the threshold 5–10 points below the normal operating range. Also consider adding `| where client_count > 20` to filter low-population noise.

- **Alert never fires even when users complain** — threshold too loose, or `healthyClientsPercentage` is always null (TA doesn't extract it). Check with `| head 1 | spath` for the actual field name. Also check whether the `clienthealth` input is running.

- **Alert fires for WIRELESS every night at 3 AM** — low overnight client count producing volatile percentages. Add business-hours filter: `| where date_hour >= 7 AND date_hour <= 19`. Or add `| where client_count > 20`.

- **Alert fires during every campus event** — guest SSID onboarding surge. Add guest SSID filtering per the Known False Positives guidance, or raise the wireless threshold for venues that host regular events.

- **Both WIRED and WIRELESS fire simultaneously** — shared-infrastructure problem (DHCP, DNS, RADIUS, upstream link). This is a high-severity event — escalate immediately. Correlate with UC-5.13.16 (Network Health) and UC-5.13.21 (Issues).

- **`cat_name` shows unexpected values** — Catalyst Center may add new category names between versions. Run `| stats values(cat_name)` and update the `IN ("WIRED","WIRELESS")` filter if new categories appear.

- **Alert actions not triggering** — check `index=_internal sourcetype=splunkd component=AlertManager` for the alert name. Common: PagerDuty routing key expired, Slack webhook URL changed.

- **Healthy percentage in Splunk doesn't match the Catalyst Center GUI** — time window and timezone differences. Catalyst Center may default to "last 1 hour" while Splunk searches over `-30m`. Align the windows and ensure both use the same timezone.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:clienthealth"
| spath output=categories path=scoreDetail{}
| mvexpand categories
| spath input=categories output=cat_name path=scoreCategory.scoreCategory
| spath input=categories output=healthy_pct path=healthyClientsPercentage
| spath input=categories output=client_count path=clientCount
| where isnum(healthy_pct) AND cat_name IN ("WIRED","WIRELESS")
| eval threshold=case(cat_name="WIRED",90, cat_name="WIRELESS",70)
| where healthy_pct < threshold
| table _time, cat_name, healthy_pct, client_count, threshold
```

## Visualization

(1) Alert results table: cat_name, healthy_pct, client_count, threshold — colour-coded red for breaches. (2) Single value: "Client health alerts active" (red if > 0). (3) Context panel: timechart of healthy_pct from UC-5.13.10 for the last 24h to show whether this is a sudden drop or gradual degradation. (4) Drilldown links to UC-5.13.12 (by SSID) and UC-5.13.13 (by site) for isolation.

## Known False Positives

**Guest SSID onboarding surge during campus events.** Large gatherings (conferences, orientations) spike guest wireless client count while depressing the average wireless health. Guest devices have inherently lower health (older hardware, varied drivers). Distinguish by checking whether `clientCount` increased significantly and whether the drop is concentrated in guest SSIDs. Suppress by using separate thresholds for guest and corporate wireless, or by filtering guest SSIDs from this alert entirely and monitoring them in UC-5.13.12.

**RRM channel reoptimisation causing temporary wireless disruption.** When Catalyst Center's RRM engine adjusts AP channels or power levels, wireless clients briefly reassociate, causing a dip in WIRELESS healthy percentage while WIRED remains stable. Distinguish by correlating with `index=catalyst sourcetype="cisco:dnac:wireless:rf"` for channel changes. Suppress by requiring the WIRELESS breach to persist for 2+ consecutive polls.

**DHCP renewal window causing mass client reconnection.** A scheduled DHCP scope renewal or DHCP server restart forces all affected clients to renegotiate, temporarily dropping health scores. Distinguish by correlating with DHCP server logs for renewal events in the same window. Suppress by requiring 2+ consecutive polls below threshold.

**Off-hours low client count producing volatile percentages.** At 3 AM with only 5 wireless clients connected, a single unhealthy device produces 20% unhealthy — below the 70% threshold. Mathematically correct but operationally meaningless. Suppress by adding `| where client_count > 20` to require a minimum client population before alerting, or by restricting the alert schedule to business hours only.

## References

- [Cisco Catalyst Add-on for Splunk (Splunkbase 7538)](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center Intent API — Client Health endpoint](https://developer.cisco.com/docs/catalyst-center/#!get-overall-client-health)
- [Catalyst Center Integration Guide (this repo)](docs/guides/catalyst-center.md)
- [Splunk Alert Actions — PagerDuty, Webhook, Email](https://docs.splunk.com/Documentation/Splunk/latest/Alert/Setupalertactions)
