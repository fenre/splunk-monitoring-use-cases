<!-- AUTO-GENERATED from UC-5.14.22.json — DO NOT EDIT -->

---
id: "5.14.22"
title: "Varnish Gzip Compression Ratio by Content Type"
criticality: "low"
splunkPillar: "Observability"
---

# UC-5.14.22 · Varnish Gzip Compression Ratio by Content Type

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

## References

- [Vendor documentation](https://varnish-cache.org/docs/trunk/users-guide/compression.html)
