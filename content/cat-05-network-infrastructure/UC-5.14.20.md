<!-- AUTO-GENERATED from UC-5.14.20.json — DO NOT EDIT -->

---
id: "5.14.20"
title: "Varnish Pipe Session Bypass Trending"
status: "draft"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.14.20 · Varnish Pipe Session Bypass Trending

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance, Analytics &middot; **Status:** Draft

*We watch varnish pipe session bypass trending and catch issues early, before they turn into outages for the people who rely on the network.*

---

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

## Known False Positives

Edge cases: multi-vendor mixes and ad hoc feeds can include lab traffic and partial visibility that mimics issues until scopes are defined. Tuning tip: match this to «Varnish Pipe Session Bypass Trending» and exclude change windows, scans, and lab VLANs you already expect.

## References

- [Vendor documentation](https://varnish-cache.org/docs/trunk/users-guide/vcl-pipe.html)
