<!-- AUTO-GENERATED from UC-5.13.16.json — DO NOT EDIT -->

---
id: "5.13.16"
title: "Network Health Score Overview"
status: "verified"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.13.16 · Network Health Score Overview

> **Criticality:** Critical &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Availability, Performance &middot; **Wave:** Crawl &middot; **Status:** Verified

*We show you one number that sums up how healthy your entire network is right now — devices, users, and applications together. When that number drops, we help you figure out whether the problem is the equipment, the Wi-Fi, or something in between. Over months, the trend shows whether your network investments are paying off.*

---

## Description

Surfaces the single aggregate network health score from Catalyst Center Assurance — the one number that tells leadership whether the network is serving users well or degrading — alongside the good/bad/total element breakdown for operations triage.

## Value

This is the number your CIO will quote in board meetings. A network health score below 80 means users are feeling it — dropped packets, slow convergence, failed client onboarding across multiple devices or sites. Catching the drop here first means you drill into UC-5.13.1 (device health) and UC-5.13.9 (client health) to isolate whether the problem is infrastructure, wireless, or application-layer, rather than waiting for the help desk to escalate. Over quarters, the trend line becomes your strongest evidence that network investments (AP refresh, IOS-XE upgrades, SDA migration) are actually improving the user experience.

## Implementation

Install `TA_cisco_catalyst` (Splunkbase 7538) on the Search Head and Heavy Forwarder. Configure a Catalyst Center account and enable the `networkhealth` input (Inputs → Create → Network Health: account `catcenter-prod`, index `catalyst`, interval `900`). Place the single-value panel prominently on the NOC dashboard. Schedule a weekly PDF report to leadership.

## Detailed Implementation

### Prerequisites
- `TA_cisco_catalyst` (Splunkbase 7538) ≥1.0 installed on Search Heads AND the Heavy Forwarder / single-instance running inputs.
- Catalyst Center **2.3.5+** for stable `healthScore`, `goodCount`, `badCount`, `totalCount` fields in the API response. Older releases may use different field names or scoring algorithms.
- Service account with **NETWORK-ADMIN-ROLE** (minimum for Assurance summary data).
- Network: HTTPS (TCP 443) from Splunk HF to Catalyst Center management IP/FQDN.
- Splunk role: users need `srchIndexesAllowed = catalyst`.
- License headroom: negligible. The `cisco:dnac:networkhealth` sourcetype produces ~1 event/poll × 96 polls/day × 500 bytes ≈ **48 KB/day** total regardless of fleet size. This is a cluster-wide aggregate, not per-device. Retain for **365+ days** — this is your cheapest long-term KPI for board reporting.
- Baseline knowledge: agree with leadership which number is the primary KPI: Catalyst Center's `healthScore` (a composite of device + client + application health) or the derived `healthy_pct` (goodCount / totalCount). Title your dashboard panel to match whichever number your CIO already cites from the Catalyst Center Assurance home page. Using a different metric creates a "duelling truth" problem in QBR meetings.

### Step 1 — Configure data collection
In the TA on the Heavy Forwarder: Inputs → Create New Input → Network Health.

| Setting | Value |
|---------|-------|
| Account | `catcenter-prod` |
| Index | `catalyst` |
| Interval | `900` (15 minutes) |

The TA authenticates to `POST /dna/system/api/v1/auth/token`, then polls `GET /dna/intent/api/v1/network-health`. Unlike device health (one event per device), this endpoint returns a **single aggregate event** per poll for the entire managed network.

Sample event:
```json
{
  "healthScore": 94,
  "goodCount": 47,
  "badCount": 3,
  "totalCount": 50,
  "healthDistir498": [...]
}
```

Verification: wait one poll interval (15 minutes), then run:
```spl
index=catalyst sourcetype="cisco:dnac:networkhealth" earliest=-30m
| table _time healthScore goodCount badCount totalCount
```
You should see 1–2 rows (depending on timing). If `healthScore` is present and numeric, the input is working. If `totalCount = 0`, Assurance may still be initialising after a Catalyst Center upgrade.

If no events arrive, check `index=_internal sourcetype=splunkd component=ExecProcessor "TA_cisco_catalyst"` for errors. Common failures: `401 Unauthorized` (credentials), `Connection refused` (URL/firewall), `SSL certificate verify failed` (self-signed cert).

Expected event volume: 1 event × 96 polls/day × ~500 bytes = **~48 KB/day**. This is the lightest Catalyst Center sourcetype and has zero licensing impact.

### Step 2 — Create the search and alert
```spl
index=catalyst sourcetype="cisco:dnac:networkhealth"
| stats latest(healthScore) as health_score latest(goodCount) as good latest(badCount) as bad latest(totalCount) as total
| eval healthy_pct=round(good*100/total,1)
| eval bad_pct=round(bad*100/total,1)
| table health_score, good, bad, total, healthy_pct, bad_pct
```

Why `latest()` not `avg()`: `healthScore` is already an Assurance-computed aggregate that blends device, client, and application signals. Taking `avg()` across multiple polls would smooth out a sudden infrastructure-wide degradation — exactly the event you need to see immediately. `latest()` gives you the current state for triage.

Why show both `healthScore` and `healthy_pct`: they measure different things. `healthScore` is Catalyst Center's proprietary weighted composite (influenced by the severity and role of unhealthy elements). `healthy_pct` is a simple ratio of goodCount / totalCount. In most steady-state environments they agree within 5 points. When they diverge — e.g. `healthScore=60` but `healthy_pct=94%` — it means a small number of critical devices (core, WLC) are unhealthy, dragging the weighted score down while the headcount ratio looks fine. That divergence IS the signal.

Why no CIM variant: the network health score is a proprietary Assurance construct that does not map to any CIM data model. It is not a raw hardware metric (like CPU load) or a standard protocol metric (like interface errors). Do not force it into CIM — it would misrepresent the data.

Schedule as Alert: cron `*/15 * * * *`, time range `-1h to now`, trigger when `health_score < 70`, throttle for `4h`. For executive-facing weekly PDFs, schedule a separate saved search with `earliest=-7d@d latest=@d` and a timechart.

### Step 3 — Validate
(a) In Catalyst Center, navigate to **Assurance > Health** (the top-level dashboard). Note the **Overall Network Health** score displayed as a large number or gauge. In Splunk, run the Step 2 search. The `health_score` should match within 1–2 points (poll timing difference).

(b) Verify `goodCount + badCount ≤ totalCount`. If `goodCount + badCount < totalCount`, some elements are in an unknown or intermediate state — this is normal during Assurance initialisation but should not persist.

(c) Confirm ingest cadence: `index=catalyst sourcetype="cisco:dnac:networkhealth" | timechart span=15m count`. Expect exactly 1 event per 15-minute bucket. Zero for an entire hour indicates a stalled input.

(d) Run `| timechart latest(healthScore) as score` over 24h. The line should show smooth gradual changes during steady state. Sudden drops to 0 that recover within one poll are Assurance recomputation artifacts — filter with `| where healthScore > 0`.

(e) Cross-validate against device health: `index=catalyst sourcetype="cisco:dnac:devicehealth" | stats count(eval(overallHealth<50)) as bad_devices, dc(deviceName) as total_devices`. The ratio should roughly correspond to `badCount / totalCount` from network health (not exactly, because network health also weighs client and application factors).

### Step 4 — Operationalize
Dashboard (recommended layout — this goes in the **top row** of every Catalyst Center dashboard as the "hero" metric):
- Row 1 — Single value gauge: `health_score` as a large number with radial gauge (green ≥ 85, yellow 70–85, red < 70). Label it with the same name used in your CIO's slide deck. Next to it: three stat tiles for good / bad / total.
- Row 2 — Timechart: `healthScore` over 24h (from UC-5.13.17) with a horizontal SLO reference line at 85 or your agreed target. Annotate with change windows from `catalyst_maintenance_windows` lookup.
- Row 3 — Drilldown buttons: "Drill to Device Health" (UC-5.13.1), "Drill to Client Health" (UC-5.13.9), "Drill to Issues" (UC-5.13.21). These buttons should pass the current time range as a token.
- Time-picker presets: "Last 1 hour" (incident), "Last 24 hours" (daily ops), "Last 30 days" (executive review), "Last 90 days" (capacity planning).

Alerting:
- PagerDuty/On-Call: trigger when `health_score < 70` for 2+ consecutive polls during business hours. This is a severe network-wide event — it should page the network operations lead, not just an individual engineer.
- Slack/Teams: `#exec-network-health` for any drop below 85 — informational, no paging. This channel is for the CIO's team to see in real time.

Runbook (owner: Network Operations lead):
1. Confirm the score in Catalyst Center > Assurance > Health. If Splunk and Catalyst Center agree, the degradation is real.
2. Check `badCount` — how many elements are unhealthy? If 1–2, this is a single-device impact (common: core switch reload, WLC failover). Drill to UC-5.13.1 (device health) to identify the specific device(s).
3. If `badCount` is high (>10% of totalCount), this is a widespread event. Check UC-5.13.21 (issues) for the dominant issue category — usually "Connectivity" or "Onboarding" during a major event.
4. Check whether `totalCount` changed compared to the previous poll. If it dropped, devices were removed from management (decommission or discovery failure). If it increased, new devices were added (PnP onboarding) and are still initialising.
5. Check planned maintenance: `index=catalyst sourcetype="cisco:dnac:audit:logs" earliest=-4h` for recent template pushes, upgrades, or configuration changes.
6. If the score dropped below 70 during business hours with no maintenance window, escalate to incident commander and begin multi-domain triage across UC-5.13.1, UC-5.13.9, and UC-5.13.21.

Capacity/SLO review (cadence: monthly, owner: Network Architecture):
- Query: `index=catalyst sourcetype="cisco:dnac:networkhealth" | bin _time span=1d | stats avg(healthScore) as daily_score by _time | where daily_score < 85 | stats count as days_below_slo`.
- Action: if `days_below_slo > 3` in a 30-day period, open a remediation project to identify the chronic contributors (usually a handful of sites or device families dragging the score down).

### Step 5 — Troubleshooting

- **No events at all** — `networkhealth` input not enabled, or TA not installed on the Heavy Forwarder. Check: TA → Inputs → confirm Network Health is present and enabled. On the CLI: `$SPLUNK_HOME/bin/splunk btool inputs list --debug | grep -i networkhealth`. Check `splunkd.log` for `ExecProcessor` entries.

- **`healthScore` is null or missing** — Assurance is not running or not licensed. Verify in **Catalyst Center > System > Licensing** that DNA Advantage or Premier is active. Also check: Assurance may be disabled for the site scope the service account can see.

- **Score stuck at 0 for extended periods** — Assurance recomputation hung. In Catalyst Center, check **System > Settings > Assurance** for engine status. If the Assurance engine shows "Initialising" for > 1 hour after an upgrade, open a Cisco TAC case.

- **`totalCount = 0` but devices exist in inventory** — the API returned an empty response, typically during a Catalyst Center restart or upgrade. Filter with `| where totalCount > 0`. If it persists beyond 2 hours after the upgrade, restart the Assurance service in Catalyst Center.

- **`healthScore` and `healthy_pct` diverge significantly** — this is working as designed. `healthScore` is weighted by device role/criticality; `healthy_pct` is a flat ratio. When they diverge, a small number of high-impact devices (core, WLC) are unhealthy. Drill to UC-5.13.1 sorted by health_score ascending to find them.

- **Score drops every night at the same time then recovers** — planned maintenance or RRM optimisation window. Validate with `index=catalyst sourcetype="cisco:dnac:audit:logs" earliest=-24h | timechart count by auditRequestType` to see if administrative activity clusters at that time. Annotate the dashboard with the maintenance window.

- **401 Unauthorized in TA logs** — service account password expired or was changed. Check `index=_internal sourcetype=splunkd "TA_cisco_catalyst" "401"`. Rotate the credential in the TA: Configuration → Account → Edit.

- **Score seems too high (100% when users are complaining)** — `healthScore` is a synthetic composite that can mask localised problems. A single building with bad Wi-Fi won't move the campus-wide score if 95% of the network is healthy. This is the inherent limitation of a single-number metric. Use UC-5.13.19 (Network Health by Site) to get site-level granularity, and UC-5.13.9 (Client Health) for the user-experience dimension that `healthScore` may underweight.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:networkhealth"
| stats latest(healthScore) as health_score latest(goodCount) as good latest(badCount) as bad latest(totalCount) as total
| eval healthy_pct=round(good*100/total,1)
| eval bad_pct=round(bad*100/total,1)
| table health_score, good, bad, total, healthy_pct, bad_pct
```

## Visualization

(1) Single value tile: `health_score` as a large gauge (green ≥ 85, yellow 70–85, red < 70) — this is the hero metric on the dashboard. (2) Three-column stat row: good / bad / total with `healthy_pct` and `bad_pct`. (3) Timechart from UC-5.13.17 showing `healthScore` over 24h with an SLO reference line at 85. (4) Optional week-over-week comparison: this week vs last week `healthScore` average for trend context.

## Known False Positives

**Catalyst Center Assurance data refresh cycle temporarily showing zero health.** During the Assurance engine's periodic recomputation, `healthScore` may briefly report as 0 while `goodCount` and `badCount` reset. Distinguish by checking whether `healthScore=0` AND `totalCount=0` simultaneously — if totalCount also drops, the API returned incomplete data. Suppress by adding `| where totalCount>0` to filter recomputation artifacts.

**Single high-impact device failure skewing the aggregate score.** A core router or distribution switch failure can drop the network health score significantly even though `badCount` increases by only 1-2. Distinguish by correlating with `index=catalyst sourcetype="cisco:dnac:devicehealth"` for devices with `overallHealth<25` to identify the specific devices driving the score drop. Do not suppress — this is a real event, but enrich the alert with the specific device(s) causing the drop.

**Planned network maintenance window affecting health score.** During a maintenance window involving multiple device reloads, the aggregate health score drops as devices go through their upgrade cycle. Distinguish by correlating with ITSM change records or `index=catalyst sourcetype="cisco:dnac:audit:logs"` for scheduled activity. Suppress by using a `catalyst_maintenance_windows` lookup and annotating the health score display with maintenance periods.

**Catalyst Center scope change adding or removing devices from management.** When devices are added to or removed from Catalyst Center management, `totalCount` changes, which shifts `healthScore`. Distinguish by comparing `totalCount` across consecutive polls — if it changed, the score shift may be due to inventory change rather than health degradation. Suppress by tracking `totalCount` baseline and alerting only when `healthScore` drops AND `totalCount` remains stable.

## References

- [Cisco Catalyst Add-on for Splunk (Splunkbase 7538)](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center Intent API — Network Health endpoint](https://developer.cisco.com/docs/catalyst-center/#!get-overall-network-health)
- [Catalyst Center Integration Guide (this repo)](../../docs/guides/catalyst-center.md)
- [Catalyst Center Assurance Overview — Cisco Documentation](https://www.cisco.com/c/en/us/td/docs/cloud-systems-management/network-automation-and-management/catalyst-center-assurance/assurance-overview.html)
