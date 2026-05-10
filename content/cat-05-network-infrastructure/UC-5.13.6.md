<!-- AUTO-GENERATED from UC-5.13.6.json — DO NOT EDIT -->

---
id: "5.13.6"
title: "Device Reachability Loss Detection"
status: "verified"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.13.6 · Device Reachability Loss Detection

> **Criticality:** Critical &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Availability, Fault &middot; **Wave:** Walk &middot; **Status:** Verified

*We keep track of which network devices have gone completely offline — not just feeling unwell, but actually unreachable. We measure how long each one has been down and flag the ones that have been offline too long for immediate attention, because every minute an unreachable device stays down, the people connected to it have no network.*

---

## Description

Detects devices that Catalyst Center can no longer reach via ICMP/SNMP, calculates how long each device has been unreachable, and classifies the severity — distinguishing a 5-minute blip from a 3-hour confirmed outage that needs immediate escalation.

## Value

An unreachable device is the most severe network health state — it means zero forwarding, zero management, zero visibility. Every minute of unreachability is a minute of user impact for every client downstream. This UC goes beyond UC-5.13.3's threshold alert by adding *duration* and *severity classification*: a device unreachable for 2 minutes is likely a planned reload; a device unreachable for 90 minutes is a P1 incident that needs escalation, not just a notification. The duration field also feeds MTTR calculations and SLA reporting.

## Implementation

Same data feed as UC-5.13.1. Schedule as alert every 5 minutes for fastest detection: cron `*/5 * * * *`, time range `-20m to now`, trigger on any results where `duration_min > 15` (filters out brief reloads). Throttle by `deviceName` for 4 hours. Route to PagerDuty with `severity` in the alert payload.

## Detailed Implementation

### Prerequisites
- UC-5.13.1 must be operational — same `devicehealth` data feed.
- Understand the difference between `overallHealth` and `reachabilityHealth`: `overallHealth` is a composite score (can be 30 but device is still reachable). `reachabilityHealth` is binary — `Reachable` or `Unreachable`. This UC cares only about the binary reachability state.
- Decide on your duration threshold for alerting. Default: `duration_min > 15` (filters out brief reloads during planned maintenance). Stricter environments may alert on `duration_min > 5` for core devices.
- Ensure NTP synchronisation between Splunk and Catalyst Center — the `duration_min` calculation depends on accurate `_time` values.

### Step 1 — Configure data collection
No additional configuration. Same `devicehealth` input as UC-5.13.1. Confirm reachability data is present:
```spl
index=catalyst sourcetype="cisco:dnac:devicehealth" earliest=-1h
| stats count by reachabilityHealth
```
You should see rows for `Reachable` (majority) and possibly `Unreachable` (if any devices are currently down). If `reachabilityHealth` is null for all events, the TA version may not extract this field — check `| fieldsummary | search field=reachabilityHealth`.

### Step 2 — Create the search and alert
```spl
index=catalyst sourcetype="cisco:dnac:devicehealth" reachabilityHealth="Unreachable"
| stats count as polls_unreachable earliest(_time) as first_unreachable latest(_time) as last_seen by deviceName, managementIpAddress, deviceType, siteId
| eval duration_min=round((last_seen-first_unreachable)/60,0)
| eval severity=case(duration_min>60,"Extended outage", duration_min>15,"Confirmed down", 1==1,"Recently detected")
| sort -duration_min
```

Why `earliest(_time)` and `latest(_time)`: this tells you when the device was *first* seen unreachable within the search window and when it was *last* confirmed unreachable. The difference is the observed outage duration. A device that was unreachable in one poll and reachable in the next has `duration_min ≈ 0` (transient). A device unreachable across 6 polls has `duration_min ≈ 90` (confirmed down).

Why `polls_unreachable` count: this adds confidence. A device with `duration_min=60` and `polls_unreachable=4` was unreachable in 4 consecutive polls — that's confirmed. A device with `duration_min=60` and `polls_unreachable=1` was only seen once — could be a data anomaly.

Why the three severity bands: (1) "Recently detected" (< 15 min) — might be a planned reload, don't page yet. (2) "Confirmed down" (15–60 min) — the device didn't come back after a reload window, investigate. (3) "Extended outage" (> 60 min) — this is a genuine outage, escalate.

Schedule as Alert:
- Cron: `*/5 * * * *` (every 5 minutes for fastest detection)
- Time range: `-30m to now` (covers 2 poll cycles)
- Trigger: `Number of results where severity != "Recently detected" > 0`
- Throttle: by `deviceName` for `4h`
- Alert action: PagerDuty high-urgency for core/distribution devices, low-urgency for access switches (use `device_criticality` lookup from UC-5.13.3)

### Step 3 — Validate
(a) If you have a lab environment, shut down a switch's management interface. Within 2 poll cycles (30 minutes), the search should return that device with `severity="Recently detected"`. After 15 more minutes, it should transition to "Confirmed down".

(b) Check historical data: `index=catalyst sourcetype="cisco:dnac:devicehealth" reachabilityHealth="Unreachable" earliest=-7d | stats dc(deviceName) as unreachable_devices`. Compare this number with your known outage history for the past week.

(c) Validate duration accuracy: pick a device that was unreachable during a known maintenance window. The `first_unreachable` and `duration_min` should align with the maintenance window start and duration.

(d) Cross-reference with **Catalyst Center > Assurance > Health > Device** filtered to "Unreachable". The device list should match.

(e) Confirm the search returns no results when all devices are healthy (expected state). If it returns results during steady state, those are genuinely unreachable devices that need investigation.

### Step 4 — Operationalize
Dashboard placement:
- **Row 2** on the Device Health Overview dashboard, next to UC-5.13.1's table.
- Table of unreachable devices with duration and severity, colour-coded.
- Single-value tile: "Unreachable Devices" (red if > 0).
- Timeline panel (Gantt-style) showing outage bars per device over 24h.

Alerting (see Step 2 for schedule):
- PagerDuty: route by device criticality. Core switch unreachable > 15 min = P1 page. Access switch unreachable > 60 min = P2 notification.
- Slack: post all unreachable detections to `#network-ops` regardless of severity.

Runbook (owner: NOC Tier 1):
1. Confirm the device is genuinely unreachable: ping `managementIpAddress` from the NOC jumpbox.
2. If ping succeeds: Catalyst Center's probe may be failing from its side. Check Catalyst Center > Assurance > Device 360 for the device. If it shows Reachable there, the issue is between Catalyst Center and the device (firewall, routing, proxy).
3. If ping fails: the device is hard down.
   - Check power: contact facilities for the building/IDF where the device is located.
   - Check upstream: log into the upstream switch and check `show interfaces status | include <downstream-port>`. If the port is down, it's a cabling or power issue.
   - Check console: if the device has a console server, connect and check for crash output or boot loop.
4. For core/distribution devices: escalate immediately to Tier 2 and notify the incident commander. Every minute of core device outage impacts all downstream users.
5. For access switches: check the user impact. If the switch serves a low-occupancy area (storage room, unused office), schedule remediation during the next maintenance window.
6. After resolution: verify the device returns to `Reachable` in the next poll. If it doesn't, check whether the management IP or VLAN changed during the recovery.

SLA reporting:
- MTTR query: `index=catalyst sourcetype="cisco:dnac:devicehealth" reachabilityHealth="Unreachable" earliest=-30d | stats earliest(_time) as down_start by deviceName | join type=left deviceName [search index=catalyst sourcetype="cisco:dnac:devicehealth" reachabilityHealth="Reachable" earliest=-30d | stats earliest(_time) as up_start by deviceName | where up_start > down_start] | eval recovery_min=round((up_start-down_start)/60,0) | stats avg(recovery_min) as avg_mttr_min`. Track this monthly for SLA compliance.

### Step 5 — Troubleshooting

- **Device shows Unreachable but is actually operational** — Catalyst Center's management probe uses ICMP and SNMP from the Catalyst Center cluster's management interface. A firewall or ACL blocking these protocols from Catalyst Center will cause false Unreachable reports. Check: `show access-lists` on the device and verify Catalyst Center's management IP is permitted.

- **All devices show Unreachable simultaneously** — this usually indicates a Catalyst Center cluster issue (API returning stale data or probe engine down), not a network-wide outage. Check `index=_internal sourcetype=splunkd "TA_cisco_catalyst" "503"`. If 503 errors appear, the Catalyst Center cluster is under stress.

- **Device is Unreachable but `overallHealth` is not 0** — possible. `overallHealth` may retain a cached value from the last successful probe while `reachabilityHealth` has already transitioned to Unreachable. Always trust `reachabilityHealth` over `overallHealth` for connectivity status.

- **`duration_min` shows 0 but device is clearly down** — the search window is too narrow. The device became unreachable within the current 15-minute poll, so `earliest(_time) ≈ latest(_time)`. Wait one more poll cycle for `duration_min` to increase.

- **Alert fires for devices during every planned maintenance** — maintain `catalyst_maintenance_windows` lookup and filter. See UC-5.13.3 Step 5 for the lookup format.

- **Device shows Unreachable, team investigates, but by the time they check it's Reachable** — the device had a brief outage (reload, power cycle) and recovered before investigation. Check `polls_unreachable` — if it's 1, the outage lasted only one poll cycle (< 15 minutes). Consider increasing the duration threshold for alerting.

- **NTP skew causing incorrect duration calculations** — if Splunk and Catalyst Center use different time sources, `_time` stamps may not align. Check `index=catalyst sourcetype="cisco:dnac:devicehealth" | eval lag=_indextime-_time | stats avg(lag) p95(lag)`. Lag > 300s indicates clock skew — fix NTP on the forwarder.

- **Device returns from Unreachable but health score stays low** — expected behaviour. After a device comes back online, Assurance needs 2–4 poll cycles to rebuild the health score. The device will show `Reachable` with `overallHealth < 50` during this recovery period.

**IPv6 Note:** ICMPv6 is architecturally critical for IPv6 — it carries NDP (Neighbor Discovery), Path MTU Discovery, and Multicast Listener Discovery. Unlike ICMP for IPv4, blocking ICMPv6 breaks IPv6 connectivity entirely. Ensure firewall policies permit at minimum ICMPv6 types 1-4 (Destination Unreachable, Packet Too Big, Time Exceeded, Parameter Problem) and types 133-137 (RS, RA, NS, NA, Redirect). See RFC 4890 for filtering recommendations.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:devicehealth" reachabilityHealth="Unreachable"
| stats count as polls_unreachable earliest(_time) as first_unreachable latest(_time) as last_seen by deviceName, managementIpAddress, deviceType, siteId
| eval duration_min=round((last_seen-first_unreachable)/60,0)
| eval severity=case(duration_min>60,"Extended outage", duration_min>15,"Confirmed down", 1==1,"Recently detected")
| sort -duration_min
```

## Visualization

(1) Table: deviceName, managementIpAddress, deviceType, siteId, first_unreachable, duration_min, severity — sorted by duration descending. Colour-code: red for Extended outage, orange for Confirmed down, yellow for Recently detected. (2) Single value: count of currently unreachable devices (red threshold ≥ 1). (3) Timeline panel showing first_unreachable to last_seen per device as horizontal bars. (4) Optional map: plot unreachable devices by site location if geo data is available.

## Known False Positives

**Planned device reload during maintenance window.** A device undergoing a firmware upgrade or reload will report as Unreachable for 3–10 minutes (switches) or 10–30 minutes (routers with large configs). Distinguish by correlating with `index=catalyst sourcetype="cisco:dnac:audit:logs"` for upgrade tasks or ITSM change records. Suppress by filtering devices in `catalyst_maintenance_windows` lookup or by only alerting when `duration_min > 30`.

**Catalyst Center ICMP/SNMP probe failure from Catalyst Center side.** If the Catalyst Center cluster itself is under high load, its reachability probes may time out even though the device is healthy. Distinguish by checking whether multiple devices across different sites simultaneously became unreachable — that pattern points to a Catalyst Center probe issue, not a multi-site outage. Correlate with `index=_internal sourcetype=splunkd "TA_cisco_catalyst" "503"` for API health.

**Device behind a firewall that blocks ICMP/SNMP from Catalyst Center.** A firewall rule change or ACL update can block the management probes while the device remains operational for users. Distinguish by checking whether the device is still forwarding traffic (correlate with NetFlow or syslog). Fix the firewall rule — do not suppress, because this represents a genuine loss of management visibility.

**Virtual domain scope mismatch hiding the recovery.** If the service account cannot see the device after a virtual domain change, the device appears perpetually unreachable in Splunk. Distinguish by logging into Catalyst Center with a broader-scoped account and checking the device's actual status. Fix the virtual domain assignment.

## References

- [Cisco Catalyst Add-on for Splunk (Splunkbase 7538)](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center Intent API — Device Health endpoint](https://developer.cisco.com/docs/catalyst-center/#!get-overall-network-device-health)
- [Catalyst Center Integration Guide (this repo)](docs/guides/catalyst-center.md)
- [Catalyst Center Device Reachability Monitoring — Cisco Docs](https://www.cisco.com/c/en/us/td/docs/cloud-systems-management/network-automation-and-management/catalyst-center-assurance/assurance-overview.html)
