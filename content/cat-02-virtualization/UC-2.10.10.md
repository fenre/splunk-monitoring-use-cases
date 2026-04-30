<!-- AUTO-GENERATED from UC-2.10.10.json — DO NOT EDIT -->

---
id: "2.10.10"
title: "VxRail iDRAC SEL Hardware Event Log Critical Entries"
status: "verified"
criticality: "high"
splunkPillar: "Security"
---

# UC-2.10.10 · VxRail iDRAC SEL Hardware Event Log Critical Entries

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Security &middot; **Type:** Fault, Physical Security &middot; **Status:** Verified

*We keep an eye on vxRail iDRAC SEL Hardware Event Log Critical Entries and raise the alarm before it drags down real work or real outages start.*

---

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

## Known False Positives

IGEL and endpoint UMS health can warn during bulk firmware, certificate rotation, or when a single site loses WAN; use device cohorts to separate local noise from UMS issues.

## References

- [iDRAC SNMP and syslog reference](https://www.dell.com/support/manuals/en-us/idrac9-lifecycle-controller-v5.x-series)
