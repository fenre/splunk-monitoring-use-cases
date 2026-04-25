<!-- AUTO-GENERATED from UC-5.14.26.json — DO NOT EDIT -->

---
id: "5.14.26"
title: "Squid CONNECT Tunnel Duration and Volume"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.14.26 · Squid CONNECT Tunnel Duration and Volume

## Description

CONNECT dominates bandwidth on many enterprise proxies.

## Value

Supports fair sharing and DLP placement decisions.

## Implementation

Ensure log format includes duration; never log decrypted payload. Comply with local interception law.

## SPL

```spl
index=proxy sourcetype="squid:access"
| where request_method=="CONNECT"
| eval dur_ms=tonumber(time_taken_ms)
| eval bytes=tonumber(bytes_sent)+tonumber(bytes_received)
| timechart span=5m perc95(dur_ms) as p95_tunnel_ms sum(bytes) as tunnel_bytes
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## References

- [Vendor documentation](http://www.squid-cache.org/Doc/config/access_log/)
