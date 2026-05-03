<!-- AUTO-GENERATED from UC-5.1.11.json — DO NOT EDIT -->

---
id: "5.1.11"
title: "Power Supply / Fan Failures"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.1.11 · Power Supply / Fan Failures

> **Criticality:** Critical &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Fault

*We raise the alarm if power supplies or fans report trouble, so a closet does not overheat or lose redundancy without you knowing.*

---

## Description

Hardware failures reduce redundancy. A second failure causes outage.

## Value

NOC teams detect power supply and fan failures on network devices, identifying loss of hardware redundancy that puts devices at risk of thermal shutdown or complete power failure.

## Implementation

Forward syslog. Poll ENVMON-MIB. Alert immediately on hardware failure. Include device location for dispatch.

## Detailed Implementation

### Prerequisites
* Power supply and fan failure syslog messages. Data in `index=network` with `sourcetype=cisco:ios` or vendor-specific sourcetypes. Key mnemonics: Cisco `%ENVMON-2-FAN_FAILED`, `%C6KPWR-4-DISABLED`, `%PLATFORM_ENV-1-FAN`, `%PLATFORM_ENV-1-PSU`; generic `%SYS-2-MALLOCFAIL`.
* Power supply redundancy loss means the device is running on a single PSU -- the next PSU failure causes complete outage. Fan failures lead to thermal shutdown if not addressed promptly.

### Step 1 — - Configure data collection
```
# Cisco IOS -- environmental monitoring is logged by default
# SNMP: poll CISCO-ENVMON-MIB
# ciscoEnvMonFanStatusDescr (.1.3.6.1.4.1.9.9.13.1.4.1.2)
# ciscoEnvMonSupplyStatusDescr (.1.3.6.1.4.1.9.9.13.1.5.1.2)
# ciscoEnvMonSupplyState (.1.3.6.1.4.1.9.9.13.1.5.1.3)
```
Verify:
```spl
index=network earliest=-30d
| where match(_raw, "(?i)FAN|PSU|POWER.*SUPPLY|power.*fail|fan.*fail|ENVMON|PLATFORM_ENV")
| stats count by host
```

### Step 2 — - Create the search and alert

**Primary search -- Hardware failure event monitoring:**
```spl
index=network earliest=-30d
| where match(_raw, "(?i)FAN.*FAIL|FAN.*DOWN|PSU.*FAIL|POWER.*FAIL|ENVMON.*(FAN|SUPPLY)|PLATFORM_ENV|redundancy.*lost|power.*absent")
| eval device=coalesce(host, device_name)
| eval component=case(
    match(_raw, "(?i)fan"), "FAN",
    match(_raw, "(?i)psu|power.*supply|power.*module"), "PSU",
    1==1, "HARDWARE")
| eval status=case(
    match(_raw, "(?i)fail|down|absent|removed|critical"), "FAILED",
    match(_raw, "(?i)ok|normal|good|inserted"), "OK",
    1==1, "WARNING")
| dedup device, component sortby -_time
| where status != "OK"
| eval severity=case(
    component="PSU" AND status="FAILED", "CRITICAL -- power supply failure (redundancy lost)",
    component="FAN" AND status="FAILED", "CRITICAL -- fan failure (thermal shutdown risk)",
    1==1, "WARNING")
| table device, component, status, _time, severity
| sort severity
```

### Step 3 — - Validate
(a) CLI: `show environment all` -- check PSU and fan status.
(b) CLI: `show power inline` (for PoE switches) -- verify power budget.
(c) Check for correlating temperature alarms (UC-5.1.15).

### Step 4 — - Operationalize
Dashboard ("Network -- Hardware Health"):
* Row 1 -- Single-value: "PSU failures", "Fan failures", "Devices at risk".
* Row 2 -- Hardware failure event timeline.

Alert: Critical (PSU/fan failure): dispatch field service or RMA.

### Step 5 — - Troubleshooting

* **PSU failure** -- Check: LED indicators, power cable, circuit breaker. If redundant PSU available, device continues operating but with no redundancy. Order replacement immediately.

* **Fan failure** -- Device will begin thermal throttling. Monitor temperature (UC-5.1.15). If temperature exceeds threshold, device will shut down to prevent damage. RMA fan tray.

* **Intermittent PSU status** -- May indicate loose power cable or failing PSU capacitor. Reseat cable; if continues, replace PSU.

## SPL

```spl
index=network sourcetype="cisco:ios" "%FAN-3-FAN_FAILED" OR "%PLATFORM_ENV-1-PSU" OR "%ENVIRONMENTAL-1-ALERT"
| table _time host _raw | sort -_time
```

## Visualization

Status indicator per device, Events list (critical).

## Known False Positives

Hardware sensor warnings during power redundancy testing, scheduled maintenance, or environmental swings. Lab gear often logs benign transitions.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
