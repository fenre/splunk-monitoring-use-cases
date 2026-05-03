<!-- AUTO-GENERATED from UC-5.1.14.json — DO NOT EDIT -->

---
id: "5.1.14"
title: "SNMP Authentication Failures"
status: "verified"
criticality: "medium"
splunkPillar: "Security"
---

# UC-5.1.14 · SNMP Authentication Failures

> **Criticality:** Medium &middot; **Difficulty:** Beginner &middot; **Pillar:** Security &middot; **Type:** Security &middot; **Status:** Verified

*We help you know early when something looks wrong with snmp authentication failures so the team can act before it grows into a bigger outage.*

---

## Description

Failed SNMP auth indicates unauthorized polling or reconnaissance.

## Value

Security teams detect SNMP authentication failures across network devices, identifying brute-force attempts, unauthorized scanning, and misconfigured monitoring tools with stale credentials.

## Implementation

Forward syslog. Alert on repeated failures from unknown sources.

## Detailed Implementation

### Prerequisites
* SNMP authentication failure messages. Data in `index=network` with `sourcetype=cisco:ios` or vendor-specific sourcetypes. Key mnemonics: Cisco `%SNMP-3-AUTHFAIL`; SNMP trap `authenticationFailure`.
* SNMP authentication failures: indicate incorrect community strings (SNMPv2c) or USM credentials (SNMPv3) being used against network devices. Could be: misconfigured monitoring tools, old community strings, or unauthorized SNMP scanning/brute-force attempts.

### Step 1 — - Configure data collection
```
# Cisco IOS -- enable SNMP auth failure logging
snmp-server enable traps snmp authentication
logging host <splunk-syslog-ip>

# Best practice: use SNMPv3 with authentication and encryption
snmp-server group MONITOR v3 priv
snmp-server user splunkmon MONITOR v3 auth sha <auth-pass> priv aes 128 <priv-pass>
```
Verify:
```spl
index=network earliest=-24h
| where match(_raw, "(?i)SNMP.*AUTH|snmp.*authentication.*fail|AUTHFAIL")
| stats count by host
```

### Step 2 — - Create the search and alert

**Primary search -- SNMP authentication failure analysis:**
```spl
index=network earliest=-24h
| where match(_raw, "(?i)SNMP.*AUTH|snmp.*authentication.*fail|AUTHFAIL")
| rex field=_raw "(?i)(?:from|host|IP)\s+(?<source_ip>\d+\.\d+\.\d+\.\d+)"
| eval src=coalesce(source_ip, src_ip, src)
| eval device=coalesce(host, device_name)
| iplocation src prefix=src_
| bin _time span=1h
| stats count as failures dc(device) as devices_targeted values(device) as targets by src, src_Country
| eval severity=case(
    failures > 100, "CRITICAL -- SNMP brute-force attempt",
    devices_targeted > 10, "WARNING -- SNMP scanning across multiple devices",
    failures > 20, "WARNING -- repeated SNMP auth failures",
    1==1, "INFO")
| where severity != "INFO"
| sort severity, -failures
```

### Step 3 — - Validate
(a) CLI: `show snmp` -- check SNMP configuration and community strings.
(b) Verify source IPs against known monitoring systems (Splunk, SolarWinds, PRTG, LibreNMS).
(c) Check if old community strings are still configured on monitoring tools.

### Step 4 — - Operationalize
Dashboard ("Network -- SNMP Auth Failures"):
* Row 1 -- Single-value: "Auth failures (24h)", "Unique sources", "Devices targeted".
* Row 2 -- SNMP auth failure timeline by source.

Alert: Critical (>100 failures from single source): brute-force or scan.

### Step 5 — - Troubleshooting

* **Known monitoring tool causing failures** -- Update community string or SNMPv3 credentials on the monitoring tool. Verify SNMP version matches (v2c vs v3).

* **Unknown source IP** -- Investigate: may be unauthorized scanning. Block at ACL: `access-list 99 deny host <ip>` applied to SNMP access: `snmp-server community <string> RO 99`.

* **Migrate to SNMPv3** -- SNMPv2c community strings are sent in plaintext. Migrate to SNMPv3 with auth+priv for secure monitoring.

## SPL

```spl
index=network sourcetype="cisco:ios" "%SNMP-3-AUTHFAIL"
| rex "from (?<src>\S+)" | stats count by host, src | sort -count
```

## Visualization

Table, Map, Timeline.

## Known False Positives

Legitimate NMS IP moves, new pollers, or SNMPv3 key rotations look like failures until the device ACL and views are updated.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
