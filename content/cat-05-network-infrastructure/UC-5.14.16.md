<!-- AUTO-GENERATED from UC-5.14.16.json — DO NOT EDIT -->

---
id: "5.14.16"
title: "Varnish Workspace Client Overflow Detection"
status: "draft"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.14.16 · Varnish Workspace Client Overflow Detection

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Fault, Performance &middot; **Status:** Draft

*We watch varnish workspace client overflow detection and catch issues early, before they turn into outages for the people who rely on the network.*

---

## Description

Workspace overflows drop transactions abruptly.

## Value

Prevents mysterious 503s during marketing campaigns with huge headers.

## Implementation

Raise `workspace_client` and hunt oversized cookies or headers.

## SPL

```spl
index=proxy sourcetype="varnish:log"
| regex _raw="(?i)workspace.*overflow|WS.*overflow"
| stats count by host
| where count >= 1
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## Known False Positives

Edge cases: multi-vendor mixes and ad hoc feeds can include lab traffic and partial visibility that mimics issues until scopes are defined. Tuning tip: match this to «Varnish Workspace Client Overflow Detection» and exclude change windows, scans, and lab VLANs you already expect.

## References

- [Vendor documentation](https://varnish-cache.org/docs/trunk/reference/varnishd.html)
