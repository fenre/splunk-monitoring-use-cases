<!-- AUTO-GENERATED from UC-2.10.10.json — DO NOT EDIT -->

---
id: "2.10.10"
title: "VxRail iDRAC SEL Hardware Event Log Critical Entries"
criticality: "high"
splunkPillar: "Security"
---

# UC-2.10.10 · VxRail iDRAC SEL Hardware Event Log Critical Entries

## Description

SEL entries predict DIMM, PSU, and PCIe faults before ESXi purple screens. Security teams also watch for chassis intrusion signals.

## Value

Bridges hardware reliability and physical security monitoring for edge clusters.

## Implementation

Normalize SEL parser. Dedup recurring thermostat noise. Page on ECC/uncorrectable classes.

## SPL

```spl
index=vxrail sourcetype="vxrail:system" earliest=-24h
| eval sev=upper(severity)
| where sev="CRITICAL" OR match(lower(event_type), "(?i)thermal|uncorrectable|ecc|watchdog")
| stats count as crit by sensor_type, host_serial
```

## Visualization

Timeline critical SEL; top sensors; host breakdown.

## References

- [iDRAC SNMP and syslog reference](https://www.dell.com/support/manuals/en-us/idrac9-lifecycle-controller-v5.x-series)
