<!-- AUTO-GENERATED from UC-5.13.8.json — DO NOT EDIT -->

---
id: "5.13.8"
title: "Device Uptime and Reboot Tracking"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.13.8 · Device Uptime and Reboot Tracking

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Availability, Change &middot; **Wave:** Walk &middot; **Status:** Verified

*We check every morning which network devices rebooted overnight. Some reboots are planned (upgrades), but unexpected ones are early warning signs — a device that keeps restarting on its own is telling you something is wrong before it fails for good. We also track whether an upgrade actually happened, or whether the device just crashed and came back.*

---

## Description

Identifies devices that rebooted within the last 24 hours by checking their `upTime` field, surfacing unexpected reloads that may indicate hardware instability, crashloops, power issues, or unauthorised maintenance — and distinguishing them from planned firmware upgrades.

## Value

A device that rebooted overnight without a change ticket is either unstable (crashloop, power supply, memory leak reaching OOM) or was touched without authorisation. Either way, you need to know. Tracking uptime across the fleet also surfaces crash-happy devices that reboot repeatedly over weeks — the kind of slow-burning reliability problem that gets hand-waved as 'it came back up, didn't it?' until it fails during a critical period. Correlating reboot times with change records separates expected from unexpected and gives you MTBF (mean time between failure) data per device family.

## Implementation

Same data feed as UC-5.13.1. Confirm `upTime` is populated in the events (field name may vary by Catalyst Center version — check with `| fieldsummary`). Schedule as a daily morning report for the NOC: cron `0 7 * * *`, time range `-24h to now`. For real-time reboot detection, schedule every 15 minutes with `where uptime_days < 0.25` (rebooted within last 6 hours).

## Detailed Implementation

### Prerequisites
- UC-5.13.1 must be operational — same `devicehealth` data feed.
- Confirm `upTime` is extracted. Run `index=catalyst sourcetype="cisco:dnac:devicehealth" earliest=-1h | fieldsummary | search field=upTime`. If `count = 0`, the field name may differ in your TA version — try `uptime`, `systemUptime`, or `sysUpTime`. Check the raw JSON with `| head 1 | spath`.
- Understand what `upTime` represents: it's the device's uptime in **seconds** since last reload, sourced from SNMP `sysUpTime` or the Catalyst Center inventory scan. It is NOT seconds since Catalyst Center discovered the device.
- For planned-vs-unplanned classification, prepare a mechanism to correlate with change records: either an ITSM lookup (`change_records.csv` with `deviceName, start_time, end_time, change_id`) or a `catalyst_maintenance_windows` lookup.

### Step 1 — Configure data collection
No additional input configuration. The `upTime` field is included in the `devicehealth` API response. Confirm it's available:
```spl
index=catalyst sourcetype="cisco:dnac:devicehealth" earliest=-1h
| stats avg(upTime) as avg_uptime_sec, min(upTime) as min_uptime_sec by deviceType
| eval avg_uptime_days=round(avg_uptime_sec/86400,1), min_uptime_days=round(min_uptime_sec/86400,1)
| table deviceType, avg_uptime_days, min_uptime_days
```
Typical access switch fleet: average uptime 60–180 days. Core devices: 180–365+ days. If `avg_uptime_sec` is null, check field extraction.

### Step 2 — Create the search and report
```spl
index=catalyst sourcetype="cisco:dnac:devicehealth"
| stats latest(upTime) as uptime_sec latest(_time) as last_seen by deviceName, managementIpAddress, deviceType, platformId, softwareVersion
| eval uptime_days=round(uptime_sec/86400,1)
| where uptime_days < 1
| eval hours_up=round(uptime_sec/3600,1)
| sort hours_up
```

Why `latest(upTime)`: takes the most recent uptime value within the search window. A device that rebooted mid-window will show the uptime *since* the reboot, not the old uptime from before.

Why `where uptime_days < 1`: filters to devices that rebooted within the last 24 hours. Adjust to `< 7` for a weekly reboot report, or `< 0.25` (6 hours) for a near-real-time reboot alert.

Why include `softwareVersion` in the output: a reboot followed by a version change confirms a firmware upgrade. A reboot with the same version before and after suggests a crash, not a planned upgrade. Compare `softwareVersion` in this search against a historical baseline: `| lookup device_firmware_baseline deviceName OUTPUT expected_version | eval upgrade=if(softwareVersion != expected_version, "Firmware changed", "Same version")`.

Why include `platformId`: correlates reboots with specific hardware models. A cluster of reboots across all `C9300-48P` devices may indicate a platform-specific firmware bug or power supply issue.

Schedule as Report (daily morning brief): cron `0 7 * * *`, time range `-24h to now`. Output to `#network-ops` Slack and the Catalyst Center dashboard.

Schedule as Alert (near-real-time reboot detection): cron `*/15 * * * *`, time range `-30m to now`, trigger on `where hours_up < 6`, throttle by `deviceName` for `24h`.

### Step 3 — Validate
(a) If you recently upgraded a device via SWIM, run the search and confirm the device appears with `hours_up` matching the time since the upgrade. Also verify `softwareVersion` reflects the new firmware.

(b) Cross-reference with `show version` on a known device via CLI. The `upTime` from Splunk (converted to days) should match the `uptime is X days` output from the device's CLI.

(c) Run over a 30-day window: `index=catalyst sourcetype="cisco:dnac:devicehealth" | stats latest(upTime) as uptime_sec by deviceName | eval uptime_days=round(uptime_sec/86400,1) | where uptime_days < 30 | stats count as rebooted_devices`. This count should roughly match the number of upgrade/maintenance events in your ITSM for the same period.

(d) Check for upTime field consistency: `index=catalyst sourcetype="cisco:dnac:devicehealth" | stats count(eval(isnull(upTime))) as null_uptime, count as total | eval null_pct=round(null_uptime*100/total,1)`. If `null_pct > 5%`, some device types don't report upTime — investigate which models are affected.

(e) Vendor UI parity: compare the uptime shown in **Catalyst Center > Provision > Inventory > [device] > Device Info** with the value from Splunk. They should match within one poll cycle.

### Step 4 — Operationalize
Dashboard placement:
- **Row on the Device Health Overview dashboard** or a dedicated "Change and Reboot Tracking" dashboard.
- Table of recently-rebooted devices with hours_up, platformId, softwareVersion, and a "Planned?" column populated from the ITSM lookup.
- Single value: "Devices rebooted in last 24h" (yellow threshold ≥ 3, red ≥ 10).
- 30-day trend: `| timechart span=1d dc(eval(if(uptime_days<1,deviceName,null()))) as daily_reboots`. A sudden spike indicates a batch upgrade or a correlated failure event.

Runbook (owner: NOC / Network Engineering):
1. Open the daily reboot report. For each device with `hours_up < 24`:
2. Check the ITSM/change lookup: is this a planned reboot? If yes, verify the firmware version changed as expected. Mark as planned.
3. If unplanned: SSH to the device and run `show version | include reload`. Look for the reload reason:
   - `Reload Reason: PowerOn` → power failure (check UPS, PDU, PoE source)
   - `Reload Reason: Reload command` → someone issued a manual reload (check UC-5.13.46 for who made changes)
   - `Reload Reason: Critical Software Exception` → crashdump (collect `show crashdump` output, open TAC case, check PSIRTs)
   - `Reload Reason: s/w reset - Loss of RP neighbor` → stack member failure (check physical stack cabling)
4. If the same device reboots repeatedly (2+ times in 7 days): open a problem ticket. Run `index=catalyst sourcetype="cisco:dnac:devicehealth" deviceName="<device>" | timechart span=1h latest(upTime)` to visualise the reboot pattern.
5. If multiple devices of the same `platformId` reboot simultaneously: suspect a correlated cause — power, firmware bug, or broadcast storm. Escalate.

MTBF reporting (monthly):
- Query: `index=catalyst sourcetype="cisco:dnac:devicehealth" earliest=-90d | stats latest(upTime) as current_uptime by deviceName, platformId | eval uptime_days=round(current_uptime/86400,0) | stats avg(uptime_days) as avg_mtbf_days by platformId | sort avg_mtbf_days`. Platforms with `avg_mtbf_days < 30` need investigation.

### Step 5 — Troubleshooting

- **`upTime` is null for all devices** — field name mismatch. Run `| head 1 | spath` on a raw event and search for any field containing "up" or "time". Common variants: `uptime`, `sysUpTime`, `systemUptime`. Adjust the SPL field name accordingly.

- **`upTime` is present but stays constant across polls** — the TA may be caching the value. Check `_time` of consecutive events for the same device — if `_time` advances but `upTime` doesn't, the API is returning stale data. Restart the input or check Catalyst Center's inventory refresh schedule.

- **All APs show very short uptime** — APs frequently reload when RRM pushes RF profile changes or when the WLC issues a rolling AP upgrade. This is normal operational behaviour for APs. Filter APs out for meaningful infrastructure reboot tracking: `| where deviceType != "Cisco Aironet Access Point"`.

- **Device shows uptime reset but was never unreachable** — SSO (Stateful Switchover) on a redundant supervisor resets the uptime counter on the standby without causing a forwarding outage. The device was always reachable and forwarding, but the supervisor switched. This is a false positive for "outage" but a true positive for "something changed" — decide per your policy whether to alert.

- **`uptime_days` shows negative values** — clock skew between the device and Catalyst Center causing `upTime` to be calculated incorrectly. Check NTP on the device.

- **Firmware version didn't change but device rebooted** — not necessarily planned. Could be a crash-and-recover (device reloads the same image). Check `show version | include reload` for the reload reason.

- **Too many reboots reported in a large fleet** — with 2,000+ devices, even a 0.1%/day natural reboot rate produces 2 devices/day. Set the alert threshold appropriately and focus investigation on unplanned reboots only.

- **MTBF data unreliable** — `upTime` only reflects time since the most recent reboot. If a device rebooted 3 times in 90 days, you only see the uptime since the last reboot, not the full reboot history. For true MTBF, track reboots over time with a summary index: `| where uptime_days < 1 | collect index=catalyst_summary sourcetype=reboot_events`.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:devicehealth"
| stats latest(upTime) as uptime_sec latest(_time) as last_seen by deviceName, managementIpAddress, deviceType, platformId, softwareVersion
| eval uptime_days=round(uptime_sec/86400,1)
| where uptime_days < 1
| eval hours_up=round(uptime_sec/3600,1)
| sort hours_up
```

## Visualization

(1) Table: deviceName, hours_up, managementIpAddress, deviceType, platformId, softwareVersion — sorted by hours_up ascending (most recent reboots first). (2) Single value: count of devices rebooted in last 24h. (3) Timechart from a variant search: `| timechart span=1d dc(eval(if(uptime_days<1, deviceName, null()))) as rebooted_devices` over 30 days to show reboot frequency trends. (4) Lookup-enriched column: join with ITSM change records to mark each reboot as "planned" or "unplanned".

## Known False Positives

**Planned firmware upgrade via Catalyst Center SWIM.** Devices upgraded through Catalyst Center's Software Image Management reload as part of the upgrade process. Distinguish by correlating with `index=catalyst sourcetype="cisco:dnac:swim"` for recent upgrade activity or `index=catalyst sourcetype="cisco:dnac:audit:logs"` for SWIM task entries. Suppress by joining with an ITSM change-record lookup: `| lookup change_records deviceName, start_time, end_time OUTPUT change_id | where isnotnull(change_id)` to flag planned reboots.

**StackWise virtual or VSS switchover causing uptime reset on the standby.** In StackWise Virtual or VSS configurations, a switchover resets the uptime on the formerly-standby supervisor, even though the switch never went offline from a forwarding perspective. Distinguish by checking whether the device was unreachable during the uptime reset window — if it was always reachable (UC-5.13.6 shows no unreachability), the reboot was a controlled switchover. Suppress by maintaining a `stacking_pairs` lookup that identifies paired devices.

**NTP correction causing sysUpTime recalculation.** A large NTP correction on a device can cause sysUpTime to appear to reset, reporting a short uptime without an actual reboot. Distinguish by checking whether the device's `reachabilityHealth` was continuously `Reachable` during the apparent reboot window. Suppress by requiring `reachabilityHealth = Unreachable` in at least one poll within 2 hours of the short uptime — this confirms a genuine reload.

**AP power cycle by PoE cycling at the upstream switch.** When a switch port bounces (PoE reset, cable reseat), the connected AP reboots and reports short uptime. Distinguish by checking whether the AP's upstream switch port also showed a status change. Do not suppress — this is a real reboot, but the root cause is the switch port, not the AP.

## References

- [Cisco Catalyst Add-on for Splunk (Splunkbase 7538)](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center Intent API — Device Health endpoint](https://developer.cisco.com/docs/catalyst-center/#!get-overall-network-device-health)
- [Catalyst Center Integration Guide (this repo)](../../docs/guides/catalyst-center.md)
- [IOS-XE sysUpTime and reload tracking — Cisco Docs](https://www.cisco.com/c/en/us/td/docs/ios-xml/ios/sys-image-mgmt/configuration/xe-16/sysimgmgmt-xe-16-book.html)
