<!-- AUTO-GENERATED from UC-5.14.32.json — DO NOT EDIT -->

---
id: "5.14.32"
title: "Squid Delay Pool Throttling Signals"
status: "draft"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.14.32 · Squid Delay Pool Throttling Signals

> **Criticality:** Medium &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Performance, Governance &middot; **Status:** Draft

*We watch squid delay pool throttling signals and catch issues early, before they turn into outages for the people who rely on the network.*

---

## Description

Fair-use rules should be observable, not silent.

## Value

Supports regulatory bandwidth management.

## Implementation

Avoid verbose debug in prod; use short cache log notices or manager counters.

## SPL

```spl
index=proxy sourcetype="squid:cache"
| regex _raw="(?i)Delay pool|delay_pool"
| bin _time span=5m
| stats count by host, _time
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## Known False Positives

Edge cases: multi-vendor mixes and ad hoc feeds can include lab traffic and partial visibility that mimics issues until scopes are defined. Tuning tip: match this to «Squid Delay Pool Throttling Signals» and exclude change windows, scans, and lab VLANs you already expect.

## References

- [Vendor documentation](http://www.squid-cache.org/Doc/config/delay_pools/)
