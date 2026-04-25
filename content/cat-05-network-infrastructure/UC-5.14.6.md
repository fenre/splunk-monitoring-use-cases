<!-- AUTO-GENERATED from UC-5.14.6.json — DO NOT EDIT -->

---
id: "5.14.6"
title: "HAProxy HTTP Compression Ratio Effectiveness"
criticality: "low"
splunkPillar: "Observability"
---

# UC-5.14.6 · HAProxy HTTP Compression Ratio Effectiveness

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

## References

- [Vendor documentation](https://docs.haproxy.org/2.8/configuration.html#compression)
