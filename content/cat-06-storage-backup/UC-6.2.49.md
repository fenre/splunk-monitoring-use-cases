<!-- AUTO-GENERATED from UC-6.2.49.json — DO NOT EDIT -->

---
id: "6.2.49"
title: "TrueNAS CPU temperature and fan speed thermal threshold monitoring"
status: "draft"
criticality: "high"
splunkPillar: "Observability"
---

# UC-6.2.49 · TrueNAS CPU temperature and fan speed thermal threshold monitoring

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Physical, Safety &middot; **Status:** Draft

*We help you see how object storage is growing, who can reach it, and when something is exposed or mis-tagged, so cloud storage stays under control.*

---

## Description

Thermal excursions throttle CPUs and accelerate component wear, often preceding random reboots that threaten ZFS integrity.

## Value

Reduces hardware-induced corruption risk and datacenter fire safety exposure for edge TrueNAS appliances.

## Implementation

Calibrate thresholds per chassis model in a lookup. Suppress alerts during known HVAC maintenance windows.

## SPL

```spl
index=storage sourcetype="truenas:alert" earliest=-1h
| search thermal OR temperature OR fan OR RPM
| eval temp_c=coalesce(cpu_temp_c, temp_c)
| eval fan_rpm=coalesce(fan_rpm, fan1_rpm)
| where temp_c > 85 OR fan_rpm < 1000
| stats latest(temp_c) as cpu_c latest(fan_rpm) as fan by hostname, sensor
```

## Visualization

Gauge (temp), table (host, sensor).

## Known False Positives

Short spikes during approved changes, maintenance windows, or known batch jobs can match the rule; confirm against the vendor console and change calendar.

## References

- [TrueNAS SCALE API documentation](https://www.truenas.com/docs/scale/scaletutorials/toptoolbar/reportinggraphs/)
- [TrueNAS CORE/SCALE docs — alerts](https://www.truenas.com/docs/)
