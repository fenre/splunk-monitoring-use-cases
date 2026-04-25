<!-- AUTO-GENERATED from UC-5.14.20.json — DO NOT EDIT -->

---
id: "5.14.20"
title: "Varnish Pipe Session Bypass Trending"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.14.20 · Varnish Pipe Session Bypass Trending

## Description

Unexpected pipe volume loads origin more than dashboards suggest.

## Value

Explains origin spikes during large uploads.

## Implementation

Pipe mode disables caching for those requests; watch WebSocket or upload paths.

## SPL

```spl
index=proxy sourcetype="varnish:vsl"
| regex _raw="(?i)VCL_pipe|Link\s+pipe"
| bin _time span=5m
| stats count as pipe_sess by host, _time
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## References

- [Vendor documentation](https://varnish-cache.org/docs/trunk/users-guide/vcl-pipe.html)
