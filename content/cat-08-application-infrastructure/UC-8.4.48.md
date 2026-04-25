<!-- AUTO-GENERATED from UC-8.4.48.json — DO NOT EDIT -->

---
id: "8.4.48"
title: "PHP-FPM Connection Refused Rate Correlated with Pool Saturation"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.4.48 · PHP-FPM Connection Refused Rate Correlated with Pool Saturation

## Description

Upstream connection refused errors timed with FPM at `max_children` confirm worker exhaustion rather than network partitions.

## Value

Narrows blame between PHP, proxy, and network teams during incidents.

## Implementation

Ingest nginx/haproxy error logs; time-align with `phpfpm:status` snapshots. Adjust join window for poll interval.

## SPL

```spl
index=web (sourcetype="nginx:error" OR sourcetype="haproxy:http")
| regex _raw="(?i)(connect\(\) failed.*9000|Connection refused)"
| bin _time span=1m
| stats count as refused by host, _time
| join host _time [
    search index=web sourcetype="phpfpm:status" earliest=-2m latest=+2m
    | bin _time span=1m
    | stats max(active_processes) as act max(max_children) as mc by host, _time
]
| eval saturated=if(mc>0 AND act>=mc*0.95, 1, 0)
| where refused > 0 AND saturated == 1
```

## Visualization

Time series (pool utilization, queue, latency percentiles), single value alerts, top charts for scripts and methods.

## References

- [PHP-FPM configuration](https://www.nginx.com/resources/wiki/start/topics/tutorials/config_pitfalls/)
