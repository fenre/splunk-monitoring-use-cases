<!-- AUTO-GENERATED from UC-5.14.38.json — DO NOT EDIT -->

---
id: "5.14.38"
title: "Envoy HTTP/2 RST_STREAM and Protocol Errors"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.14.38 · Envoy HTTP/2 RST_STREAM and Protocol Errors

## Description

Protocol errors masquerade as application timeouts.

## Value

Shortens mesh-wide incident resolution.

## Implementation

Align `http2` settings with language runtimes; log `%RESPONSE_CODE_DETAILS%`.

## SPL

```spl
index=proxy sourcetype="envoy:access"
| regex _raw="(?i)(RST_STREAM|GOAWAY|protocol_error)"
| bin _time span=5m
| stats count by cluster_name, _time
| where count > 15
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## References

- [Vendor documentation](https://www.envoyproxy.io/docs/envoy/latest/api-v3/config/core/v3/protocol.proto)
