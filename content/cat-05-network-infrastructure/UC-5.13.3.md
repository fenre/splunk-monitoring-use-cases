<!-- AUTO-GENERATED from UC-5.13.3.json — DO NOT EDIT -->

---
id: "5.13.3"
title: "Unhealthy Device Detection and Alerting"
status: "verified"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.13.3 · Unhealthy Device Detection and Alerting

> **Criticality:** Critical &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Availability, Fault &middot; **Wave:** Crawl &middot; **Status:** Verified

*We set up an alarm that goes off when any network device gets sick or goes offline. The alarm tells the on-call engineer exactly which device it is, where it is, and how bad the problem is — so they can start fixing it within minutes instead of waiting for someone to notice something is slow.*

---

## Description

Fires an alert when any managed network device drops below a health score of 50 or becomes unreachable, surfacing the device name, IP, type, and site so the NOC can begin triage within the current poll cycle — typically within 15 minutes of the degradation event.

## Value

UC-5.13.1 shows health scores for browsing; this UC *pages you* when something breaks. A device health score below 50 means active user impact — dropped packets, slow convergence, failed client onboarding — and the faster you know about it, the shorter the outage. Configuring the alert with throttling and escalation tiers means the right engineer gets paged once (not 50 times for the same failure), and a P1 core switch down gets a different urgency than a P3 access switch in a low-traffic area.

## Implementation

Same data feed as UC-5.13.1 — no additional input. Save this search as a scheduled alert: cron `*/15 * * * *`, time range `-30m to now`, trigger on `Number of results > 0`, throttle by `deviceName` for 4 hours. Configure alert actions for PagerDuty/On-Call, Slack, and optionally ServiceNow incident creation.

## Detailed Implementation

### Prerequisites
- UC-5.13.1 must be operational — this alert uses the same `devicehealth` data feed. No additional input configuration required.
- Decide on your threshold before enabling the alert. The default `overallHealth < 50` aligns with Catalyst Center's "Poor" band. Stricter environments may use `< 70` for core devices (filter by `deviceType` or a `critical_devices` lookup). Less noisy environments may start with `< 25` and tighten over time.
- Decide on escalation tiers: which devices get P1 pages (core, distribution, WLCs) vs P2 notifications (access switches, APs)? Maintain a `device_criticality` lookup with `deviceName` → `tier` mapping.
- Configure at least one alert action before enabling: PagerDuty/On-Call, Slack webhook, email, or ServiceNow incident creation. See Step 4.
- Splunk capability: the user saving the alert needs `schedule_search` and `list_settings` capabilities.

### Step 1 — Configure data collection
No additional configuration. Same `devicehealth` input as UC-5.13.1. Confirm data is flowing:
```spl
index=catalyst sourcetype="cisco:dnac:devicehealth" earliest=-30m | stats count
```
If count > 0, you're ready. If not, see UC-5.13.1 Step 1.

### Step 2 — Create the search and alert
```spl
index=catalyst sourcetype="cisco:dnac:devicehealth"
| where overallHealth < 50 OR reachabilityHealth="Unreachable"
| stats latest(overallHealth) as health_score latest(reachabilityHealth) as reachability latest(_time) as last_seen by deviceName, managementIpAddress, deviceType, siteId
| sort health_score
```

Why `< 50` as the default threshold: Catalyst Center's Assurance engine categorises scores below 50 as "Poor" — this is the band where active user impact is likely. Below 25 is "Critical" in Assurance. The threshold is a starting point; tune it based on your first week of alert volume (see Step 4).

Why `OR reachabilityHealth="Unreachable"`: a device can have `overallHealth = null` (Assurance not computed) but `reachabilityHealth = Unreachable` (ICMP/SNMP failed). The OR catches both Assurance-detected degradation and hard connectivity loss.

Why `latest()` by device: if the search time range covers multiple polls (e.g., `-30m` = 2 polls at 900s interval), `latest()` ensures you see the *most recent* health score, not an average. A device that recovered in the second poll should not alert.

Why `where` before `stats` (not after): filtering early reduces the data volume that `stats` processes. In a 2,000-device fleet, this drops from 2,000 events to typically 0–10 — a significant performance improvement for a search that runs every 15 minutes.

Schedule as Alert:
- Cron: `*/15 * * * *` (every 15 minutes, aligned with poll interval)
- Time range: `-30m to now` (covers 2 poll cycles for reliability — a device must be unhealthy in the most recent data, but the `-30m` window ensures we don't miss events due to indexing lag)
- Trigger: "Number of results > 0"
- Throttle: suppress by `deviceName` for `4h` — the same unhealthy device should not re-page within the same incident window
- Severity: set Splunk alert severity to "High" for all results, or use the per-device `severity` eval from the visualization section

For stricter P1 alerting on critical infrastructure only:
```spl
index=catalyst sourcetype="cisco:dnac:devicehealth"
| where (overallHealth < 25 OR reachabilityHealth="Unreachable")
| lookup device_criticality deviceName OUTPUT tier
| where tier="critical"
| stats latest(overallHealth) as health_score latest(reachabilityHealth) as reachability by deviceName, managementIpAddress, deviceType, siteId
| sort health_score
```
Schedule this variant every `*/5 * * * *` with a shorter throttle (1h) for fastest response on core infrastructure.

### Step 3 — Validate
(a) Intentional test: identify a device currently showing health > 80 in Catalyst Center. In a lab environment, shut down an uplink to force a health score drop. Within 2 poll cycles (30 minutes), the alert should fire with that device in the results.

(b) Historical validation: run the Step 2 search over the last 7 days (`earliest=-7d`). Every row should correspond to a real issue that your team would have wanted to know about. If it surfaces devices that were intentionally down for maintenance, add them to the `catalyst_maintenance_windows` lookup.

(c) Threshold tuning: run `index=catalyst sourcetype="cisco:dnac:devicehealth" | where overallHealth < 50 | stats dc(deviceName) as affected_devices by _time | timechart span=1d max(affected_devices)`. If you're seeing > 20 devices/day below threshold, the threshold may be too high for your environment — consider starting at `< 25` and tightening.

(d) False positive check: review the last 5 alerts. Were they all actionable? If any were Assurance recomputation artifacts (score = 0, many devices, recovered immediately), add the `| where overallHealth > 0` filter or the two-consecutive-poll guard.

(e) Confirm throttling works: trigger the alert twice within 4 hours for the same device. You should receive only one notification.

### Step 4 — Operationalize
Alert actions (configure in Splunk → Settings → Alerts → Edit Actions):

**PagerDuty / Splunk On-Call:**
- Routing key: map to the network operations on-call team
- Severity: `critical` for `reachabilityHealth=Unreachable` or `health_score < 25`; `warning` for `health_score` 25–49
- Custom details: include `deviceName`, `managementIpAddress`, `health_score`, `siteId`, and a link to the Device 360 in Catalyst Center (`https://<catcenter>/dna/assurance/device/<deviceId>/overview`)

**Slack / Microsoft Teams:**
- Webhook URL: `#network-ops` channel
- Message: "Device alert: {deviceName} health={health_score} reachability={reachability} site={siteId}"
- Include a link to the Splunk alert results

**ServiceNow (optional):**
- Create incident with category "Network", subcategory "Infrastructure"
- Map `siteId` to ServiceNow location using a lookup
- Set priority based on device criticality tier

Runbook (owner: NOC Tier 1 on-call):
1. Open the alert results. Note the `deviceName`, `health_score`, and `reachability`.
2. If `reachabilityHealth = Unreachable`: this is a hard down. Ping the `managementIpAddress` from the NOC jumpbox. If ping fails, check physical connectivity (power, cabling, upstream switch port status). Escalate to Tier 2 if not resolved in 15 minutes.
3. If `health_score < 50` but device is reachable: open UC-5.13.1 and check which subscore is lowest:
   - `cpuScore` low → SSH to device, `show processes cpu sorted | head 10`. Look for runaway process.
   - `memoryScore` low → `show memory platform`. Check for known memory leak PSIRTs (UC-5.13.34).
   - `interDeviceLinkScore` low → check upstream/downstream interface status. `show interfaces status | include down`.
4. Check UC-5.13.21 (Assurance Issues) for a correlated issue detection from Catalyst Center's AI engine.
5. Check planned maintenance: `index=catalyst sourcetype="cisco:dnac:audit:logs" deviceName="<device>" earliest=-4h`.
6. If the alert is for a known maintenance window, acknowledge and close. Update the `catalyst_maintenance_windows` lookup.
7. If unresolved after 30 minutes, escalate to Tier 2 with the device details, subscore breakdown, and correlation data.

Tuning cadence (weekly for first month, then monthly):
- Review alert volume: `| stats count by deviceName | sort -count`. Devices with > 10 alerts/week are either chronically unhealthy (needs remediation, not alerting) or false-positive generators (needs lookup exception).
- Adjust threshold up or down based on actionability. Target: 2–5 actionable alerts/day.

### Step 5 — Troubleshooting

- **Alert fires on every poll cycle for the same device** — throttling is not configured. Edit the alert: Settings → Throttle → check "Suppress triggering for" → 4 hours → field `deviceName`.

- **Alert fires for 50+ devices simultaneously** — Assurance recomputation cycle. Add `| where overallHealth > 0` to the search. If it persists, the Catalyst Center cluster may be under stress — check `index=_internal sourcetype=splunkd "TA_cisco_catalyst" "503"` for API errors.

- **Alert never fires even though you can see unhealthy devices in UC-5.13.1** — check the alert schedule and time range. Common mistake: alert time range set to `-15m` but poll interval is 900s, so some polls fall outside the window. Use `-30m` to cover 2 poll cycles.

- **Alert fires for devices during planned maintenance** — maintain a `catalyst_maintenance_windows` lookup with columns `deviceName`, `start_time`, `end_time`. Add `| lookup catalyst_maintenance_windows deviceName OUTPUT end_time | where isnull(end_time) OR now() > end_time` to the search.

- **False positives from new devices (PnP onboarding)** — new devices report low scores until Assurance builds a baseline. Add `| lookup catalyst_new_devices deviceName OUTPUT onboard_time | where isnull(onboard_time) OR (now() - onboard_time) > 7200` to exclude devices onboarded within the last 2 hours.

- **Alert actions not triggering** — check `index=_internal sourcetype=splunkd component=AlertManager "UC-5.13.3"` for action execution errors. Common: PagerDuty routing key expired, Slack webhook URL changed, ServiceNow credentials rotated.

- **Too many alerts (> 20/day)** — the threshold is too high for your environment. Options: (a) lower to `< 25`; (b) add a `device_criticality` lookup and alert only on `tier=critical`; (c) require two consecutive bad polls before alerting.

- **Device shows health=0 but is actually fine** — the device model may not be supported by Assurance scoring (some Meraki devices, legacy Catalyst 3k). Filter with `| where isnum(overallHealth) AND overallHealth > 0` and add the device to a `catalyst_unsupported_devices` lookup.

**IPv6 Note:** ICMPv6 is architecturally critical for IPv6 — it carries NDP (Neighbor Discovery), Path MTU Discovery, and Multicast Listener Discovery. Unlike ICMP for IPv4, blocking ICMPv6 breaks IPv6 connectivity entirely. Ensure firewall policies permit at minimum ICMPv6 types 1-4 (Destination Unreachable, Packet Too Big, Time Exceeded, Parameter Problem) and types 133-137 (RS, RA, NS, NA, Redirect). See RFC 4890 for filtering recommendations.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:devicehealth"
| where overallHealth < 50 OR reachabilityHealth="Unreachable"
| stats latest(overallHealth) as health_score latest(reachabilityHealth) as reachability latest(_time) as last_seen by deviceName, managementIpAddress, deviceType, siteId
| sort health_score
```

## Visualization

(1) Alert results table: deviceName, health_score, reachability, deviceType, siteId, managementIpAddress, last_seen — sorted worst-first. (2) Single value tile: count of currently-alerting devices (red threshold ≥ 1). (3) Sparkline of alert frequency over 7 days from `| timechart span=1d count` to detect whether alert volume is increasing. (4) Optional severity breakdown: `| eval severity=case(reachabilityHealth="Unreachable","Critical", health_score<25,"High", health_score<50,"Medium")`.

## Known False Positives

**Assurance recomputation cycle dropping scores to 0 briefly.** During the Assurance engine's periodic recomputation (typically near the top of each hour), `overallHealth` may report as 0 for many devices in a 2–3 minute window. Distinguish by checking whether the drop affects > 30% of devices simultaneously and recovers on the next poll. Suppress by requiring two consecutive polls below threshold: use a summary index or lookup to store the previous poll's state and alert only when `health_score < 50` in both the current and previous poll.

**New device onboarding via PnP.** Devices onboarded via Plug and Play report low or zero health scores until Assurance builds a baseline (30–60 minutes). Distinguish by correlating with `index=catalyst sourcetype="cisco:dnac:device"` for devices with `upTime` < 2 hours. Suppress with a `catalyst_new_devices` lookup that excludes devices onboarded within the last 2 hours.

**Catalyst Center cluster upgrade causing API staleness.** During upgrades (2–6 hours), the API may return stale data or HTTP 503 errors, causing health scores to freeze or disappear. Distinguish by checking TA logs for `503` or `timeout` errors. Suppress with a `catalyst_maintenance_windows` lookup.

**Single-subscore drop pulling composite below 50.** A `cpuScore` spike to 20 on an otherwise healthy device can pull `overallHealth` below 50 even though the device is functionally fine. Distinguish by checking subscores: `| stats latest(cpuScore) latest(memoryScore) latest(interDeviceLinkScore) by deviceName`. If only one subscore is low, the triage path is different (see runbook).

## References

- [Cisco Catalyst Add-on for Splunk (Splunkbase 7538)](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center Intent API — Device Health endpoint](https://developer.cisco.com/docs/catalyst-center/#!get-overall-network-device-health)
- [Catalyst Center Integration Guide (this repo)](docs/guides/catalyst-center.md)
- [Splunk Alert Actions — PagerDuty, Webhook, Email](https://docs.splunk.com/Documentation/Splunk/latest/Alert/Setupalertactions)
