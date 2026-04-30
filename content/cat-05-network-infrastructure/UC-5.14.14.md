<!-- AUTO-GENERATED from UC-5.14.14.json — DO NOT EDIT -->

---
id: "5.14.14"
title: "Varnish Ban List Growth and Lurker Lag"
status: "draft"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.14.14 · Varnish Ban List Growth and Lurker Lag

> **Criticality:** Medium &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Performance, Operational &middot; **Status:** Draft

*We watch varnish ban list growth and lurker lag and catch issues early, before they turn into outages for the people who rely on the network.*

---

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

## Known False Positives

Edge cases: multi-vendor mixes and ad hoc feeds can include lab traffic and partial visibility that mimics issues until scopes are defined. Tuning tip: match this to «Varnish Ban List Growth and Lurker Lag» and exclude change windows, scans, and lab VLANs you already expect.

## References

- [Vendor documentation](https://varnish-cache.org/docs/trunk/users-guide/purging.html)
