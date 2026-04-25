<!-- AUTO-GENERATED from UC-5.14.16.json — DO NOT EDIT -->

---
id: "5.14.16"
title: "Varnish Workspace Client Overflow Detection"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.14.16 · Varnish Workspace Client Overflow Detection

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

## References

- [Vendor documentation](https://varnish-cache.org/docs/trunk/reference/varnishd.html)
