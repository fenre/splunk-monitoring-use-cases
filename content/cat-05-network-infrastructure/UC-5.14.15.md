<!-- AUTO-GENERATED from UC-5.14.15.json — DO NOT EDIT -->

---
id: "5.14.15"
title: "Varnish ESI Fragment Error Rate"
status: "draft"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.14.15 · Varnish ESI Fragment Error Rate

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Fault, Performance &middot; **Status:** Draft

*We watch varnish esi fragment error rate and catch issues early, before they turn into outages for the people who rely on the network.*

---

## Description

ESI failures create partial pages that are hard to spot in averages.

## Value

Speeds collaboration between CDN and app teams.

## Implementation

Limit verbose ESI debug to non-prod; aggregate counts in prod.

## SPL

```spl
index=proxy sourcetype="varnish:vsl"
| regex _raw="(?i)(ESI.*error|include.*failed)"
| stats count by host
| where count > 10
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## Known False Positives

Edge cases: multi-vendor mixes and ad hoc feeds can include lab traffic and partial visibility that mimics issues until scopes are defined. Tuning tip: match this to «Varnish ESI Fragment Error Rate» and exclude change windows, scans, and lab VLANs you already expect.

## References

- [Vendor documentation](https://varnish-cache.org/docs/trunk/users-guide/esi.html)
