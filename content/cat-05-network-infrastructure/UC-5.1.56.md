<!-- AUTO-GENERATED from UC-5.1.56.json — DO NOT EDIT -->

---
id: "5.1.56"
title: "Junos Chassis Alarm Monitoring (Juniper)"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.1.56 · Junos Chassis Alarm Monitoring (Juniper)

> **Criticality:** Critical &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Fault

*We help you know early when something looks wrong with junos chassis alarm monitoring so the team can act before it grows into a bigger outage.*

---

## Description

Junos raises chassis alarms for power supply loss, fan failure, FPC or PIC offline, and temperature exceedances—conditions that often need on-site hardware work before service is fully restored. Ignoring these events lets a single failed component escalate into switch-wide thermal shutdown or loss of redundancy. A clear Splunk view of major and minor chassis alarms speeds dispatch to facilities and vendor support and shortens mean time to repair for edge and campus fabrics.

## Value

NOC teams monitor Junos chassis alarms (major/minor) across FPC, PEM, fan, and routing engine components, detecting hardware conditions requiring immediate attention.

## Implementation

Forward Junos structured syslog to Splunk; install `Splunk_TA_juniper` for field normalization. Tune `search` terms to your facility naming (CHASSISD, craftd). Alert on first major alarm and on minor alarms that repeat on the same FRU within 24h. Enrich with CMDB site and rack for dispatch.

## Detailed Implementation

### Prerequisites
* Junos chassis alarm data from syslog. Data in `index=juniper` or `index=network` with `sourcetype=juniper:structured` or `sourcetype=syslog`. Key Junos syslog facilities: CHASSISD, ALARMD. CLI: `show chassis alarms`.
* Junos chassis alarms: categorized as Major (red) or Minor (yellow). Major alarms indicate conditions requiring immediate attention (PSU failure, FPC offline, RE failure). Minor alarms indicate degraded conditions (temperature warning, fan speed low). Alarms persist until condition is cleared.

### Step 1 — - Configure data collection
```
# Junos configuration -- syslog forwarding
set system syslog host <splunk-ip> any info
set system syslog host <splunk-ip> chassis any
set system syslog host <splunk-ip> match "CHASSISD|ALARMD|alarm|FPC|PIC|RE|PEM|FAN"

# Splunk inputs.conf
[udp://514]
sourcetype = juniper:structured
index = juniper
```
Verify:
```spl
index=juniper earliest=-30d
| where match(_raw, "(?i)CHASSISD|ALARMD|alarm|chassis.*alarm|major.*alarm|minor.*alarm")
| stats count by host
```

### Step 2 — - Create the search and alert

**Primary search -- Chassis alarm monitoring:**
```spl
index=juniper earliest=-24h
| where match(_raw, "(?i)CHASSISD|ALARMD|alarm|FPC.*offline|FPC.*error|PEM.*fail|fan.*fail|RE.*fail")
| eval device=coalesce(host, device_name)
| eval alarm_severity=case(
    match(_raw, "(?i)major|critical|red"), "MAJOR",
    match(_raw, "(?i)minor|yellow|warning"), "MINOR",
    1==1, "UNKNOWN")
| eval component=case(
    match(_raw, "(?i)FPC"), "FPC (Flexible PIC Concentrator)",
    match(_raw, "(?i)PIC"), "PIC (Physical Interface Card)",
    match(_raw, "(?i)RE|routing.engine"), "Routing Engine",
    match(_raw, "(?i)PEM|power"), "Power Supply (PEM)",
    match(_raw, "(?i)fan|FAN"), "Fan Tray",
    match(_raw, "(?i)CB|control.board"), "Control Board",
    match(_raw, "(?i)temp"), "Temperature",
    1==1, "Chassis")
| eval alarm_state=if(match(_raw, "(?i)clear|reset|gone|resolved"), "CLEARED", "ACTIVE")
| dedup device, component sortby -_time
| where alarm_state="ACTIVE"
| eval severity=case(
    alarm_severity="MAJOR", "CRITICAL -- major chassis alarm: ".component,
    alarm_severity="MINOR", "WARNING -- minor chassis alarm: ".component,
    1==1, "INFO")
| table device, component, alarm_severity, alarm_state, _time, severity
| sort severity
```

### Step 3 — - Validate
(a) CLI: `show chassis alarms` -- current active alarms.
(b) CLI: `show chassis environment` -- temperature, fan, PSU status.
(c) CLI: `show chassis fpc` -- FPC online/offline status.

### Step 4 — - Operationalize
Dashboard ("Juniper -- Chassis Alarms"):
* Row 1 -- Single-value: "Major alarms", "Minor alarms", "Devices alarmed".
* Row 2 -- Active alarm table.

Alert: Critical (major chassis alarm): immediate hardware investigation.

### Step 5 — - Troubleshooting

* **FPC offline** -- Check: `show chassis fpc`. May need reseating or RMA. If FPC is powered down, try: `request chassis fpc slot <n> online`.

* **PEM failure** -- Power supply failed. Check redundancy status: `show chassis environment`. Replace PEM under maintenance contract.

* **Fan failure** -- `show chassis environment` shows fan RPM. Reduced airflow causes temperature alarms. RMA fan tray. Monitor temperature while waiting for replacement.

## SPL

```spl
index=network sourcetype="juniper:junos:structured"
| search CHASSISD OR "*chassis*" OR ALARM OR "*alarm*"
| search "*Major*" OR "*Minor*" OR severity=major OR severity=minor OR "class major" OR "class minor"
| rex field=_raw max_match=0 "(?i)fru\s*type:\s*(?<fru_type>[^,\n]+)"
| stats count as alarm_events, values(_raw) as sample_messages by host, fru_type
| where alarm_events > 0
| sort -alarm_events
```

## Visualization

Chassis alarm table by host and FRU; timeline of major vs minor; single-value panel for open major alarms.

## Known False Positives

Hardware sensor warnings during power redundancy testing, scheduled maintenance, or environmental swings. Lab gear often logs benign transitions.

## References

- [CIM: Alerts](https://docs.splunk.com/Documentation/CIM/latest/User/Alerts)
