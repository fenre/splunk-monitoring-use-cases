<!-- AUTO-GENERATED from UC-5.2.44.json — DO NOT EDIT -->

---
id: "5.2.44"
title: "FortiGate Security Fabric Health Monitoring (Fortinet)"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.2.44 · FortiGate Security Fabric Health Monitoring (Fortinet)

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Security &middot; **Type:** Availability, Security

*We track fabric and platform health messages on FortiGate so split links, sync issues, and serial oddities are visible before they become wide outages.*

---

## Description

Security Fabric ties FortiGate to FortiManager, FortiAnalyzer, FortiSandbox, EMS, and downstream FortiGates for synchronized policy, logging, and threat intelligence. When fabric connectivity or authorization breaks, you lose centralized management, shared object updates, and automated sandbox verdict workflows—often silently until someone notices missing logs or stale objects. Monitoring root and downstream fabric membership, heartbeat, and authorization errors gives early warning before operations and compliance gaps widen.

## Value

Operations teams monitor FortiGate Security Fabric component health across FortiManager, FortiAnalyzer, FortiSandbox, and EMS connections, detecting integration failures that degrade centralized management and threat response.

## Implementation

Ensure FortiOS event logging includes system and fabric-related categories (varies by version). Install `TA-fortinet_fortigate` and send logs via syslog or reliable forwarding. Create alerts for authorization failures, certificate issues, or loss of FortiManager reachability strings in `logdesc`/`msg`. Validate FortiManager/Analyzer versions and time sync. Test by temporarily blocking management paths in a lab to confirm detection.

## Detailed Implementation

### Prerequisites
* FortiGate Security Fabric status logs. Data in `index=fortinet` or `index=firewall` with `sourcetype=fgt_log` or `sourcetype=fgt_event`. The Fortinet TA for Splunk (Splunk_TA_fortinet_fortigate) provides field extraction. Key fields: `logid`, `subtype`, `msg`, `status`, `devname`, `devid`.
* Security Fabric: FortiGate connects to FortiManager (central management), FortiAnalyzer (logging/reporting), FortiSandbox (zero-day detection), FortiClient EMS (endpoint compliance), and downstream FortiGates (fabric hierarchy). Fabric status is reported via system event logs (logid=0100032XXX series). CLI: `diagnose sys csf`.

### Step 1 — - Configure data collection
```
# FortiGate CLI -- enable syslog to Splunk
config log syslogd setting
    set status enable
    set server <splunk-syslog-ip>
    set port 514
    set facility local7
    set format default
end

# Enable event logging for Security Fabric
config log setting
    set resolve-ip enable
    set resolve-port enable
    set log-invalid-packet enable
end
```
Verify:
```spl
index=fortinet sourcetype="fgt_event" earliest=-4h
| where match(subtype, "(?i)system") AND match(msg, "(?i)fabric|csf|fortimanager|fortianalyzer|fortisandbox|ems")
| stats count by msg, status
```

### Step 2 — - Create the search and alert

**Primary search -- Security Fabric component health:**
```spl
index=fortinet sourcetype="fgt_event" earliest=-4h
| where match(msg, "(?i)fabric|csf|fortimanager|fortianalyzer|fortisandbox|ems|fortiguard")
| eval component=case(
    match(msg, "(?i)fortimanager|fmg"), "FortiManager",
    match(msg, "(?i)fortianalyzer|faz"), "FortiAnalyzer",
    match(msg, "(?i)fortisandbox"), "FortiSandbox",
    match(msg, "(?i)ems|forticlient"), "FortiClient EMS",
    match(msg, "(?i)fortiguard"), "FortiGuard",
    match(msg, "(?i)downstream|upstream|fabric.*device"), "Fabric Device",
    1==1, "Security Fabric")
| eval health=case(
    match(status, "(?i)success|connect|up|established"), "HEALTHY",
    match(status, "(?i)fail|error|disconnect|down|timeout"), "UNHEALTHY",
    match(msg, "(?i)fail|error|disconnect|unreachable|timeout"), "UNHEALTHY",
    1==1, "UNKNOWN")
| stats count as events count(eval(health="UNHEALTHY")) as failures latest(health) as current_health latest(_time) as last_event by devname, component
| eval severity=case(
    current_health="UNHEALTHY" AND component="FortiManager", "CRITICAL -- FortiManager connection lost",
    current_health="UNHEALTHY" AND component="FortiAnalyzer", "HIGH -- FortiAnalyzer logging disrupted",
    current_health="UNHEALTHY", "WARNING -- ".component." unhealthy",
    failures > 5, "INFO -- intermittent failures detected",
    1==1, "OK")
| where severity != "OK"
| eval last_event_time=strftime(last_event, "%Y-%m-%d %H:%M:%S")
| sort severity
```

### Step 3 — - Validate
(a) CLI: `diagnose sys csf` -- show Fabric topology and status.
(b) CLI: `execute ping <fortimanager-ip>` -- verify management connectivity.
(c) FortiManager: check device status shows all FortiGates connected.

### Step 4 — - Operationalize
Dashboard ("FortiGate -- Security Fabric Health"):
* Row 1 -- Single-value: "Fabric components healthy", "Unhealthy components", "Fabric devices".
* Row 2 -- Fabric component status table.
* Row 3 -- Fabric health event timeline.

Alert: Critical (FortiManager or FortiAnalyzer disconnected): management and logging disrupted.

### Step 5 — - Troubleshooting

* **FortiManager connection lost** -- Check: (1) network reachability (`exec ping`), (2) TCP 541 (FGFM protocol) is open, (3) FortiManager is not at capacity, (4) serial number is registered in FortiManager.

* **FortiAnalyzer logging disrupted** -- Verify: `diagnose log test` generates test logs. Check FortiAnalyzer disk space and quota. TCP 514/UDP 514 connectivity.

* **FortiGuard update failures** -- Check DNS resolution (`exec ping update.fortiguard.net`). Verify FortiGuard license is valid. Consider using FortiManager as local FortiGuard distribution point.

## SPL

```spl
index=firewall sourcetype IN ("fgt_event","fortinet_fortios_event")
  (lower(_raw) LIKE "%fabric%" OR lower(logdesc) LIKE "%fabric%" OR lower(msg) LIKE "%fabric%"
   OR match(_raw, "(?i)FortiManager|FortiAnalyzer|authorization failed|certificate.*fabric"))
| eval device=coalesce(devname, dvc, host)
| stats count by device type subtype logdesc msg level
| sort -count
```

## Visualization

Table (device, subtype, message), Timeline (fabric errors), Status grid (root vs leaf FortiGate health).

## Known False Positives

Broker reconnects, backup links, and FortiManager pushes can all register as fabric or event noise.

## References

- [Splunkbase app 2846](https://splunkbase.splunk.com/app/2846)
