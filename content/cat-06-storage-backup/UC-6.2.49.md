<!-- AUTO-GENERATED from UC-6.2.49.json — DO NOT EDIT -->

---
id: "6.2.49"
title: "TrueNAS CPU temperature and fan speed thermal threshold monitoring"
criticality: "high"
splunkPillar: "Observability"
---

# UC-6.2.49 · TrueNAS CPU temperature and fan speed thermal threshold monitoring

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

## References

- [TrueNAS SCALE API documentation](https://www.truenas.com/docs/scale/scaletutorials/toptoolbar/reportinggraphs/)
- [TrueNAS CORE/SCALE docs — alerts](https://www.truenas.com/docs/)
