<!-- AUTO-GENERATED from UC-8.4.34.json — DO NOT EDIT -->

---
id: "8.4.34"
title: "PHP-FPM Process Manager Type Comparison (static vs dynamic vs ondemand)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-8.4.34 · PHP-FPM Process Manager Type Comparison (static vs dynamic vs ondemand)

## Description

`pm=static`, `dynamic`, and `ondemand` change how processes scale under load. Comparing peak active workers across modes validates whether the chosen policy matches traffic shape.

## Value

Avoids wrong-mode configs that waste RAM or starve bursts.

## Implementation

Normalize `process_manager` field from JSON status; tag hosts in `transforms.conf`. Review hourly peaks vs `max_children` per pm mode.

## SPL

```spl
index=web sourcetype="phpfpm:status"
| eval pm=coalesce(process_manager, pm)
| bin _time span=1h
| stats values(pm) as pm_mode latest(max_children) as max_children max(active_processes) as peak_active by pool, host, _time
| timechart span=1h max(peak_active) by pm_mode
```

## Visualization

Time series (pool utilization, queue, latency percentiles), single value alerts, top charts for scripts and methods.

## References

- [CIM: Web](https://docs.splunk.com/Documentation/CIM/latest/User/Web)
- [PHP-FPM configuration](https://www.php.net/manual/en/fpm.configuration.php#pm)
