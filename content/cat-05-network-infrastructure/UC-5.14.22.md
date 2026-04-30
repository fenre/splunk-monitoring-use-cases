<!-- AUTO-GENERATED from UC-5.14.22.json — DO NOT EDIT -->

---
id: "5.14.22"
title: "Varnish Gzip Compression Ratio by Content Type"
status: "draft"
criticality: "low"
splunkPillar: "Observability"
---

# UC-5.14.22 · Varnish Gzip Compression Ratio by Content Type

> **Criticality:** Low &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance, Cost &middot; **Status:** Draft

*We watch varnish gzip compression ratio by content type and catch issues early, before they turn into outages for the people who rely on the network.*

---

## Description

JSON and text compress better than images; mis-tuned filters waste CPU.

## Value

Optimizes CPU spend versus egress savings.

## Implementation

Pair with byte counters if available; sample to control volume.

## SPL

```spl
index=proxy sourcetype="varnish:vsl"
| rex field=_raw "Content-Type:\s+(?<ctype>[^\s;]+)"
| stats count by ctype
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## Known False Positives

Edge cases: multi-vendor mixes and ad hoc feeds can include lab traffic and partial visibility that mimics issues until scopes are defined. Tuning tip: match this to «Varnish Gzip Compression Ratio by Content Type» and exclude change windows, scans, and lab VLANs you already expect.

## References

- [Vendor documentation](https://varnish-cache.org/docs/trunk/users-guide/compression.html)
