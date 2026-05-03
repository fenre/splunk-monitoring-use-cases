<!-- AUTO-GENERATED from UC-5.14.38.json — DO NOT EDIT -->

---
id: "5.14.38"
title: "Envoy HTTP/2 RST_STREAM and Protocol Errors"
status: "draft"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.14.38 · Envoy HTTP/2 RST_STREAM and Protocol Errors

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Fault, Performance &middot; **Status:** Draft

*We watch envoy http/2 rst_stream and protocol errors and catch issues early, before they turn into outages for the people who rely on the network.*

---

## Description

Protocol errors masquerade as application timeouts.

## Value

Operations teams analyze Envoy HTTP/2 RST_STREAM errors and protocol violations, distinguishing flow control issues from client incompatibilities and stream refusals.

## Implementation

Align `http2` settings with language runtimes; log `%RESPONSE_CODE_DETAILS%`.

## Detailed Implementation

### Prerequisites
* Envoy access logs with HTTP/2 protocol details. Key response flags: `IH` (invalid HTTP header), `SI` (stream idle timeout), `DPE` (downstream protocol error). Key metrics: `envoy_http_downstream_rq_rx_reset`, `envoy_http_downstream_rq_tx_reset`, `envoy_http2_stream_refused_errors`.
* HTTP/2 RST_STREAM: sent when either side aborts a stream. Error codes: PROTOCOL_ERROR, INTERNAL_ERROR, FLOW_CONTROL_ERROR, CANCEL, REFUSED_STREAM, ENHANCE_YOUR_CALM (rate limiting). High RST_STREAM rates indicate protocol incompatibility, client/server bugs, or resource exhaustion.

### Step 1 — - Configure data collection
Envoy access log with protocol info:
```yaml
log_format:
  json_format:
    protocol: "%PROTOCOL%"
    response_flags: "%RESPONSE_FLAGS%"
    response_code_details: "%RESPONSE_CODE_DETAILS%"
    upstream_cluster: "%UPSTREAM_CLUSTER%"
```
Verify:
```spl
index=proxy sourcetype="envoy:access" earliest=-4h
| where protocol="HTTP/2" AND (match(response_flags, "DPE|IH|SI") OR match(response_code_details, "(?i)rst_stream|protocol_error"))
| stats count
```

### Step 2 — - Create the search and alert

**Primary search -- HTTP/2 RST_STREAM and protocol error analysis:**
```spl
index=proxy sourcetype="envoy:access" earliest=-4h
| where (match(response_flags, "DPE|IH|SI|DC") OR match(response_code_details, "(?i)rst_stream|protocol_error|flow_control|stream_refused")) AND protocol="HTTP/2"
| eval error_type=case(match(response_flags, "DPE"), "DOWNSTREAM_PROTOCOL_ERROR", match(response_flags, "IH"), "INVALID_HTTP_HEADER", match(response_flags, "SI"), "STREAM_IDLE_TIMEOUT", match(response_flags, "DC"), "DOWNSTREAM_DISCONNECT", match(response_code_details, "(?i)flow_control"), "FLOW_CONTROL_ERROR", match(response_code_details, "(?i)stream_refused"), "STREAM_REFUSED", 1==1, "RST_STREAM")
| bin _time span=5m
| stats count as errors dc(upstream_cluster) as affected_clusters by _time, error_type
| eval severity=case(error_type="FLOW_CONTROL_ERROR" AND errors > 50, "HIGH -- flow control issues", error_type="STREAM_REFUSED" AND errors > 100, "HIGH -- streams being refused", errors > 200, "WARNING -- elevated protocol errors", 1==1, "INFO")
| where severity != "INFO"
| table _time, error_type, errors, affected_clusters, severity
```

### Step 3 — - Validate
(a) `curl http://localhost:15000/stats | grep http2` -- shows HTTP/2 specific counters.
(b) Send a malformed HTTP/2 request using h2spec: `h2spec -h <envoy_host> -p 8080`.
(c) Check for `ENHANCE_YOUR_CALM` -- indicates Envoy is rate limiting the client.

### Step 4 — - Operationalize
Dashboard ("Envoy -- HTTP/2 Health"):
* Row 1 -- Single-value: "RST_STREAM events", "Protocol errors", "Flow control errors".
* Row 2 -- Error type breakdown timechart.

Alerting:
* High (flow control or stream refused > 50/5m): HTTP/2 protocol issues.
* Warning (DPE > 200/5m): downstream client protocol errors.

### Step 5 — - Troubleshooting

* **FLOW_CONTROL_ERROR** -- Client or server is sending data faster than the peer's receive window allows. Check: `initial_stream_window_size` and `initial_connection_window_size` in Envoy config. Increase if legitimate traffic.

* **STREAM_REFUSED (ENHANCE_YOUR_CALM)** -- Envoy is rate-limiting streams. Check: `max_concurrent_streams` setting (default 100). Increase if clients legitimately need more concurrent streams.

* **DPE (Downstream Protocol Error)** -- Client is sending invalid HTTP/2 frames. Common with broken client libraries or proxies that don't fully support HTTP/2. Consider falling back to HTTP/1.1 for problematic clients.

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

## Known False Positives

Edge cases: multi-vendor mixes and ad hoc feeds can include lab traffic and partial visibility that mimics issues until scopes are defined. Tuning tip: match this to «Envoy HTTP/2 RST_STREAM and Protocol Errors» and exclude change windows, scans, and lab VLANs you already expect.

## References

- [Vendor documentation](https://www.envoyproxy.io/docs/envoy/latest/api-v3/config/core/v3/protocol.proto)
