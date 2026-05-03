<!-- AUTO-GENERATED from UC-5.1.9.json — DO NOT EDIT -->

---
id: "5.1.9"
title: "Device Uptime / Reload Tracking"
criticality: "medium"
splunkPillar: "Security"
---

# UC-5.1.9 · Device Uptime / Reload Tracking

> **Criticality:** Medium &middot; **Difficulty:** Beginner &middot; **Pillar:** Security &middot; **Type:** Availability, Fault

*We help you know early when something looks wrong with device uptime / reload tracking so the team can act before it grows into a bigger outage.*

---

## Description

Unexpected reboots indicate hardware failure or unauthorized reload.

## Value

Operations teams track network device uptime, reload events, and crash history to identify unstable devices requiring firmware upgrades, hardware replacement, or power infrastructure improvements.

## Implementation

Poll SNMP sysUpTime. Forward syslog reload messages. Alert when uptime drops. Cross-reference with maintenance windows.

## Detailed Implementation

### Prerequisites
* Device uptime and reload syslog messages. Data in `index=network` with `sourcetype=cisco:ios` or vendor-specific sourcetypes. Key mnemonics: Cisco `%SYS-5-RESTART`, `%SYS-5-RELOAD`; SNMP `sysUpTime` OID (.1.3.6.1.2.1.1.3.0).
* Unexpected reloads indicate hardware failure, software crash, power loss, or manual intervention. Tracking reload frequency and uptime trends helps identify unstable devices requiring RMA or firmware upgrade.

### Step 1 — - Configure data collection
```
# SNMP polling for sysUpTime
[snmp_uptime]
interval = 300
sourcetype = snmp:uptime
index = network
# OID: sysUpTime (.1.3.6.1.2.1.1.3.0) -- hundredths of a second

# Syslog captures reload events automatically
```
Verify:
```spl
index=network earliest=-30d
| where match(_raw, "(?i)RESTART|RELOAD|reboot|uptime|System returned|warm.?start|cold.?start")
| stats count by host
```

### Step 2 — - Create the search and alert

**Primary search -- Device reload event tracking:**
```spl
index=network earliest=-30d
| where match(_raw, "(?i)RESTART|RELOAD|reboot|System returned|warm.?start|cold.?start|reason.*reload|crashinfo")
| eval device=coalesce(host, device_name)
| eval reload_type=case(
    match(_raw, "(?i)crash|exception|watchdog|assert"), "CRASH",
    match(_raw, "(?i)power.*cycle|power.*fail|power.*loss"), "POWER_LOSS",
    match(_raw, "(?i)manual|admin|reload.*command"), "MANUAL",
    match(_raw, "(?i)upgrade|firmware|image"), "UPGRADE",
    1==1, "UNKNOWN")
| rex field=_raw "(?i)(?:reason|Reason).*?[:\s]+(?<reload_reason>[^,\n]+)"
| stats count as reloads count(eval(reload_type="CRASH")) as crashes count(eval(reload_type="POWER_LOSS")) as power_events latest(_time) as last_reload latest(reload_type) as last_type by device
| eval severity=case(
    crashes > 0, "CRITICAL -- software crash detected",
    reloads > 3, "WARNING -- frequent reloads (".reloads." in 30d)",
    power_events > 0, "WARNING -- power loss event",
    1==1, "INFO")
| where severity != "INFO"
| eval last_reload_time=strftime(last_reload, "%Y-%m-%d %H:%M:%S")
| sort severity, -reloads
```

### Step 3 — - Validate
(a) CLI: `show version | include uptime` -- verify current uptime.
(b) CLI: `show reload cause` (Cisco) -- check last reload reason.
(c) CLI: `dir crashinfo:` -- check for crash dumps requiring TAC analysis.

### Step 4 — - Operationalize
Dashboard ("Network -- Device Uptime & Reloads"):
* Row 1 -- Single-value: "Reloads (30d)", "Crashes", "Devices < 24h uptime".
* Row 2 -- Reload event timeline.
* Row 3 -- Device uptime ranking.

Alert: Critical (crash/exception): collect crashinfo, open TAC case.

### Step 5 — - Troubleshooting

* **Software crash** -- Collect `show tech-support` and `crashinfo` file. Check bug database for known issues with current firmware version. Consider upgrade to fixed release.

* **Power loss events** -- Check UPS, redundant power supplies, and facility power. CLI: `show environment power` to verify PSU status.

* **Frequent reloads on single device** -- May indicate failing hardware (memory DIMM, supervisor). Run diagnostics: `diagnostic start module <x> test all`.

## SPL

```spl
index=network sourcetype="cisco:ios" "%SYS-5-RESTART" OR "%SYS-5-RELOAD"
| table _time host _raw | sort -_time
```

## Visualization

Table (device, uptime), Timeline, Single value (unexpected reboots).

## Known False Positives

Planned power cycles, hitless upgrades, and RMA burn-in reset counters—treat as noise when the change record matches.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
