<!-- AUTO-GENERATED from UC-5.14.51.json — DO NOT EDIT -->

---
id: "5.14.51"
title: "Traefik Request Content-Length Distribution"
status: "draft"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.14.51 · Traefik Request Content-Length Distribution

> **Criticality:** Medium &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Security, Performance &middot; **Status:** Draft

*We watch traefik request content-length distribution and catch issues early, before they turn into outages for the people who rely on the network.*

---

## Description

Big bodies stress buffers and may signal exfiltration.

## Value

Operations teams analyze Traefik request content-length distributions per service, detecting oversized payloads that cause timeouts, memory pressure, or potential abuse.

## Implementation

Use for large upload monitoring; pair with body size limits middleware.

## Detailed Implementation

### Prerequisites
* Traefik access logs with request body size information. Key access log fields: `RequestContentSize` (request body size in bytes), `DownstreamContentSize` (response body size), `RouterName`, `ServiceName`, `RequestMethod`, `RequestPath`. Data in `index=proxy` with `sourcetype=traefik:access`.
* Request Content-Length distribution reveals: (1) large file uploads that may timeout or cause memory pressure, (2) API request size patterns, (3) potential abuse via oversized payloads. Traefik does not limit request body size by default -- large payloads pass through to backends.

### Step 1 — - Configure data collection
JSON access log with body size:
```yaml
accessLog:
  format: json
  fields:
    names:
      RequestContentSize: keep
      DownstreamContentSize: keep
```
Verify:
```spl
index=proxy sourcetype="traefik:access" earliest=-4h
| eval req_size_kb=tonumber(RequestContentSize)/1024
| stats avg(req_size_kb) as avg_req_kb max(req_size_kb) as max_req_kb by ServiceName
| sort -max_req_kb
```

### Step 2 — - Create the search and alert

**Primary search -- Request content-length distribution:**
```spl
index=proxy sourcetype="traefik:access" earliest=-4h
| eval req_bytes=tonumber(RequestContentSize)
| where isnotnull(req_bytes) AND req_bytes > 0
| eval size_bucket=case(req_bytes < 1024, "< 1 KB", req_bytes < 10240, "1-10 KB", req_bytes < 102400, "10-100 KB", req_bytes < 1048576, "100 KB - 1 MB", req_bytes < 10485760, "1-10 MB", 1==1, "> 10 MB (LARGE)")
| stats count as requests avg(req_bytes) as avg_bytes max(req_bytes) as max_bytes by size_bucket, ServiceName
| eval avg_kb=round(avg_bytes/1024, 1)
| eval max_mb=round(max_bytes/1048576, 2)
| eval severity=case(match(size_bucket, "> 10 MB") AND requests > 10, "WARNING -- large payloads to ".ServiceName, max_bytes > 104857600, "HIGH -- >100MB request detected", 1==1, "OK")
| where severity != "OK"
| sort severity, -max_bytes
| table size_bucket, ServiceName, requests, avg_kb, max_mb, severity
```

### Step 3 — - Validate
(a) Upload a known-size file: `curl -X POST -d @10mb_file.bin http://<traefik>/upload` -- verify RequestContentSize matches.
(b) Compare with backend-side metrics for request size.
(c) Check if buffering middleware is configured (affects how Traefik handles large bodies).

### Step 4 — - Operationalize
Dashboard ("Traefik -- Request Sizes"):
* Row 1 -- Single-value: "Avg request size", "Max request size", "Large requests (>10MB)".
* Row 2 -- Size distribution per service.
* Row 3 -- Large request outliers.

Alerting:
* Warning (requests > 10 MB to non-upload service): potential abuse.
* High (request > 100 MB): very large payload -- investigate.

### Step 5 — - Troubleshooting

* **Large requests causing timeouts** -- Traefik may timeout while reading the request body. Tune: `transport.respondingTimeouts.readTimeout` in entrypoint config.

* **Memory pressure from large bodies** -- Traefik buffers the request body. For very large uploads, consider: (1) streaming the body (no buffering), (2) setting a max body size via buffering middleware: `buffering.maxRequestBodyBytes`.

* **API receiving unexpected large payloads** -- Could indicate: (1) client bug, (2) attack (denial of service via large payloads). Add buffering middleware with maxRequestBodyBytes to reject oversized requests.

## SPL

```spl
index=proxy sourcetype="traefik:access"
| eval cl=tonumber(RequestContentSize)
| where cl > 5000000
| bin cl span=1000000
| stats count by cl, RouterName
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## Known False Positives

Edge cases: multi-vendor mixes and ad hoc feeds can include lab traffic and partial visibility that mimics issues until scopes are defined. Tuning tip: match this to «Traefik Request Content-Length Distribution» and exclude change windows, scans, and lab VLANs you already expect.

## References

- [Vendor documentation](https://doc.traefik.io/traefik/observability/access-logs/#access-logs)
