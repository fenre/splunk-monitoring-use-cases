<!-- AUTO-GENERATED from UC-5.1.7.json — DO NOT EDIT -->

---
id: "5.1.7"
title: "Configuration Change Detection"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.1.7 · Configuration Change Detection

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Security &middot; **Type:** Configuration, Compliance

*We log who changed a switch or router config and when, so you can line up what happened in the network with your approved change tickets.*

---

## Description

Unauthorized config changes are a top cause of outages. Essential for compliance.

## Value

Operations teams track network device configuration changes with administrator attribution, enabling rapid change correlation with incidents and compliance audit.

## Implementation

Forward syslog. Enable archive logging. Alert on any config change. Correlate with change tickets.

## Detailed Implementation

### Prerequisites
* Configuration change syslog messages. Data in `index=network` with `sourcetype=cisco:ios` or vendor-specific sourcetypes. Key mnemonics: Cisco `%SYS-5-CONFIG_I`, `%PARSER-5-CFGLOG_LOGGEDCMD`; Juniper `UI_COMMIT`, `UI_COMMIT_COMPLETED`; Arista `SYS-5-CONFIG_I`.
* Configuration changes are a top cause of network outages. Tracking who changed what and when enables rapid rollback, compliance auditing, and change correlation with incidents.

### Step 1 — - Configure data collection
```
# Cisco IOS -- enable config change logging
archive
 log config
  logging enable
  logging size 200
  notify syslog contenttype plaintext
  hidekeys

logging host <splunk-syslog-ip>
logging trap informational
```
Verify:
```spl
index=network earliest=-24h
| where match(_raw, "(?i)CONFIG_I|CONFIG.*CHANGE|CFGLOG|COMMIT|config.*changed|configured.*from")
| stats count by host
```

### Step 2 — - Create the search and alert

**Primary search -- Configuration change detection:**
```spl
index=network earliest=-24h
| where match(_raw, "(?i)CONFIG_I|CONFIG.*CHANGE|CFGLOG|COMMIT|config.*changed|configured.*from|running-config")
| rex field=_raw "(?i)(?:by|user)\s+(?<config_user>\S+)"
| rex field=_raw "(?i)(?:console|vty|line)\s*(?<access_method>\S+)"
| rex field=_raw "(?i)(?:from|source)\s+(?<source_ip>\d+\.\d+\.\d+\.\d+)"
| eval user=coalesce(config_user, user, admin, "unknown")
| eval method=coalesce(access_method, if(match(_raw, "(?i)console"), "console", if(match(_raw, "(?i)vty|ssh|telnet"), "remote", "unknown")))
| eval device=coalesce(host, device_name)
| eval change_type=case(
    match(_raw, "(?i)COMMIT"), "COMMIT",
    match(_raw, "(?i)running.*startup|write"), "SAVE",
    match(_raw, "(?i)CONFIG_I|config.*change"), "CONFIG_CHANGE",
    1==1, "OTHER")
| stats count as changes dc(user) as unique_admins values(user) as admins values(source_ip) as source_ips latest(_time) as last_change by device, change_type
| eval severity=case(
    change_type="CONFIG_CHANGE" AND match(mvjoin(source_ips, ","), "unknown"), "WARNING -- config change from unknown source",
    changes > 10, "INFO -- high config change frequency",
    1==1, "INFO")
| eval last_change_time=strftime(last_change, "%Y-%m-%d %H:%M:%S")
| table device, change_type, changes, admins, source_ips, last_change_time, severity
| sort severity, -changes
```

### Step 3 — - Validate
(a) CLI: `show archive log config all` (Cisco) -- verify logged commands.
(b) CLI: `show running-config | include Last` -- check last config change time.
(c) Cross-reference with change management tickets.

### Step 4 — - Operationalize
Dashboard ("Network -- Configuration Changes"):
* Row 1 -- Single-value: "Config changes (24h)", "Devices changed", "Administrators active".
* Row 2 -- Configuration change timeline.
* Row 3 -- Change audit trail table.

Alert: Warning (config change outside maintenance window): unauthorized change.

### Step 5 — - Troubleshooting

* **Unauthorized change** -- Check user identity and source IP. Cross-reference with AAA/TACACS+ logs. Verify change management approval.

* **Config not saved** -- Running-config changed but not written to startup. Check: `show startup-config` vs `show running-config`. Risk: changes lost on reload.

* **Correlate config change with outage** -- Overlay config change events with interface down/BGP flap events. Time-based correlation identifies change-induced incidents.

## SPL

```spl
index=network sourcetype="cisco:ios" "%SYS-5-CONFIG_I"
| rex "Configured from (?<config_source>\S+) by (?<user>\S+)"
| table _time host user config_source
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  by All_Changes.user All_Changes.command All_Changes.action span=1h
| sort -count
```

## Visualization

Table (device, user, time), Timeline, Single value (changes last 24h).

## Known False Positives

Authorized changes during change windows, scheduled compliance pushes, or device decommissioning will trigger this. Correlate to tickets before escalating.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
