<!-- AUTO-GENERATED from UC-5.14.4.json — DO NOT EDIT -->

---
id: "5.14.4"
title: "HAProxy SSL/TLS Handshake Failure Rate"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.14.4 · HAProxy SSL/TLS Handshake Failure Rate

## Description

TLS failures block whole cohorts of clients and often precede major incidents after renewals.

## Value

Protects partner and mobile traffic that is sensitive to cipher and chain changes.

## Implementation

Enable sufficient TLS logging without secrets. Join failure spikes with certificate inventory expiry.

## SPL

```spl
index=proxy sourcetype="haproxy:http"
| regex _raw="(?i)(SSL handshake failure|verify error|alert unknown ca|alert certificate)"
| bin _time span=5m
| stats count by frontend, _time
| where count > 20
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## References

- [Vendor documentation](https://docs.haproxy.org/2.8/configuration.html#5.1)
