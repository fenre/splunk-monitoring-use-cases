<!-- AUTO-GENERATED from UC-5.14.14.json — DO NOT EDIT -->

---
id: "5.14.14"
title: "Varnish Ban List Growth and Lurker Lag"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.14.14 · Varnish Ban List Growth and Lurker Lag

## Description

Ban lag leaves outdated objects live especially on busy news sites.

## Value

Protects editorial correctness after publishes.

## Implementation

Investigate slow lurker or excessive `ban()` calls from publishers.

## SPL

```spl
index=proxy sourcetype="varnish:stats"
| eval bans=tonumber(bans), done=tonumber(bans_completed)
| eval lag=bans-done
| where lag > 1000
| table _time, host, bans, done, lag
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## References

- [Vendor documentation](https://varnish-cache.org/docs/trunk/users-guide/purging.html)
