<!-- AUTO-GENERATED from UC-5.14.13.json — DO NOT EDIT -->

---
id: "5.14.13"
title: "Varnish Grace and Keep Serving Stale Content Frequency"
status: "draft"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.14.13 · Varnish Grace and Keep Serving Stale Content Frequency

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance, Reliability &middot; **Status:** Draft

*We watch varnish grace and keep serving stale content frequency and catch issues early, before they turn into outages for the people who rely on the network.*

---

## Description

Stale serving shields origins but can confuse content owners if unexplained.

## Value

Balances resilience versus freshness commitments.

## Implementation

Tune thresholds against editorial SLOs; document VCL `grace`/`keep`.

## SPL

```spl
index=proxy sourcetype="varnish:vsl"
| regex _raw="(?i)(grace|stale|hit-for-pass)"
| bin _time span=15m
| stats count by host, _time
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## Known False Positives

Edge cases: multi-vendor mixes and ad hoc feeds can include lab traffic and partial visibility that mimics issues until scopes are defined. Tuning tip: match this to «Varnish Grace and Keep Serving Stale Content Frequency» and exclude change windows, scans, and lab VLANs you already expect.

## References

- [Vendor documentation](https://varnish-cache.org/docs/trunk/users-guide/vcl-grace.html)
