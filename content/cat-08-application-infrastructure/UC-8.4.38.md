<!-- AUTO-GENERATED from UC-8.4.38.json — DO NOT EDIT -->

---
id: "8.4.38"
title: "PHP-FPM Memory per Worker Trend from Status and Host Metrics"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.4.38 · PHP-FPM Memory per Worker Trend from Status and Host Metrics

## Description

Rightsizing `pm.max_children` needs approximate RSS per PHP worker. Comparing FPM process counts with host or cgroup memory avoids OOM kills during traffic spikes while limiting over-provisioning.

## Value

Reduces user-facing latency and 5xx rates by exposing pool saturation, slow scripts, and worker stability before front proxies fail.

## Implementation

Ingest `ps` or `top` snapshot via TA-nix; alias mem field. For container hosts, use cAdvisor/kube stats joined on pod/host.

## SPL

```spl
index=web sourcetype="phpfpm:status"
| eval ap=tonumber(active_processes), tp=tonumber(total_processes)
| join type=left host [
    search index=os sourcetype=ps earliest=-2m
    | stats latest(mem_used) as rss_kb by host
]
| eval approx_mb_per_worker=if(tp>0, round(rss_kb/1024/tp,2), null())
| timechart span=15m avg(approx_mb_per_worker) by pool
```

## Visualization

Time series (pool utilization, queue, latency percentiles), single value alerts, top charts for scripts and methods.

## References

- [CIM: Web](https://docs.splunk.com/Documentation/CIM/latest/User/Web)
- [PHP-FPM configuration](https://www.php.net/manual/en/fpm.configuration.php#pm.max-children)
