<!-- AUTO-GENERATED from UC-5.14.6.json — DO NOT EDIT -->

---
id: "5.14.6"
title: "HAProxy HTTP Compression Ratio Effectiveness"
status: "draft"
criticality: "low"
splunkPillar: "Observability"
---

# UC-5.14.6 · HAProxy HTTP Compression Ratio Effectiveness

> **Criticality:** Low &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance, Cost &middot; **Status:** Draft

*We watch haproxy http compression ratio effectiveness and catch issues early, before they turn into outages for the people who rely on the network.*

---

## Description

Compression reduces egress cost until misconfiguration disables it for large JSON.

## Value

Quantifies CDN and origin offload ROI.

## Implementation

Add compression byte fields per HAProxy docs; document field order for parsers.

## SPL

```spl
index=proxy sourcetype="haproxy:http"
| eval cin=tonumber(comp_in), cout=tonumber(comp_out)
| eval ratio=if(cin>0, round(100*cout/cin,1), null())
| timechart span=1h avg(ratio) by frontend
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## Known False Positives

Edge cases: multi-vendor mixes and ad hoc feeds can include lab traffic and partial visibility that mimics issues until scopes are defined. Tuning tip: match this to «HAProxy HTTP Compression Ratio Effectiveness» and exclude change windows, scans, and lab VLANs you already expect.

## References

- [Vendor documentation](https://docs.haproxy.org/2.8/configuration.html#compression)
