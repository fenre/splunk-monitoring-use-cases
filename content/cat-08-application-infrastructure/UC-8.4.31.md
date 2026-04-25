<!-- AUTO-GENERATED from UC-8.4.31.json — DO NOT EDIT -->

---
id: "8.4.31"
title: "PHP-FPM Active Workers Approaching max_children Saturation"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-8.4.31 · PHP-FPM Active Workers Approaching max_children Saturation

## Description

When nearly all `max_children` workers are active, new requests queue at the FPM listen socket or fail at the reverse proxy. Sustained high utilization is the leading indicator of saturation.

## Value

Lets capacity owners add workers or rebalance traffic before users experience errors.

## Implementation

Splunk_TA_nix + custom `inputs.conf` `[script://.../phpfpm_status.sh]` indexing `pm.status_path` JSON. Alert when `active_processes/max_children` ≥85% for 15m.

## SPL

```spl
index=web sourcetype="phpfpm:status"
| eval maxc=tonumber(max_children), act=tonumber(active_processes)
| eval util_pct=if(maxc>0, round(100*act/maxc,1), null())
| where util_pct >= 85
| timechart span=5m max(util_pct) as pool_util_pct by pool, host
```

## Visualization

Time series (pool utilization, queue, latency percentiles), single value alerts, top charts for scripts and methods.

## References

- [CIM: Web](https://docs.splunk.com/Documentation/CIM/latest/User/Web)
- [PHP-FPM configuration](https://www.php.net/manual/en/install.fpm.configuration.php)
