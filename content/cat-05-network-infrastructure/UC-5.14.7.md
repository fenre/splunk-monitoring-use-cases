<!-- AUTO-GENERATED from UC-5.14.7.json — DO NOT EDIT -->

---
id: "5.14.7"
title: "HAProxy ACL-Based Traffic Routing Audit"
status: "draft"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.14.7 · HAProxy ACL-Based Traffic Routing Audit

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Audit, Security &middot; **Status:** Draft

*We watch haproxy acl-based traffic routing audit and catch issues early, before they turn into outages for the people who rely on the network.*

---

## Description

Routing audits support tenant isolation and forensic reconstruction.

## Value

Operations teams analyze HAProxy per-backend bandwidth consumption and response size distributions, detecting saturation, compression gaps, and unusually large payloads.

## Implementation

Add stable rule identifiers for regulated splits; scrub URIs with PII.

## Detailed Implementation

### Prerequisites
* HAProxy HTTP logs with response size fields. Key fields: `bytes_read` (response body bytes), `content_type`, `backend`, `request_uri`. Data in `index=proxy` with `sourcetype=haproxy:http`.
* HAProxy can compress responses when `compression algo gzip` is enabled. Large uncompressed responses indicate missing compression or naturally large payloads (file downloads, API responses).

### Step 1 — - Configure data collection
Enable compression logging:
```
# haproxy.cfg
defaults
    compression algo gzip
    compression type text/html text/plain text/css application/javascript application/json
```
Verify:
```spl
index=proxy sourcetype="haproxy:http" earliest=-4h
| eval response_kb=bytes_read/1024
| stats avg(response_kb) as avg_size_kb max(response_kb) as max_size_kb by backend
| sort -avg_size_kb
```

### Step 2 — - Create the search and alert

**Primary search -- Bandwidth and response size analysis:**
```spl
index=proxy sourcetype="haproxy:http" earliest=-4h
| eval response_kb=tonumber(bytes_read)/1024
| eval response_mb=response_kb/1024
| bin _time span=5m
| stats avg(response_kb) as avg_size_kb sum(response_kb) as total_kb count as requests p95(response_kb) as p95_size_kb by _time, backend
| eval bandwidth_mbps=round(total_kb/1024/300*8, 2)
| eval avg_size_kb=round(avg_size_kb, 1)
| eval severity=case(bandwidth_mbps > 100, "HIGH -- heavy bandwidth", p95_size_kb > 10240, "WARNING -- large responses (P95 > 10MB)", 1==1, "OK")
| where severity != "OK"
| table _time, backend, requests, avg_size_kb, p95_size_kb, bandwidth_mbps, severity
```

### Step 3 — - Validate
(a) Request a known large resource and verify size appears correctly.
(b) Compare with HAProxy stats `bout` (bytes out) counter.
(c) Verify compression is active: `curl -H "Accept-Encoding: gzip" -I https://<haproxy>/path` -- check for `Content-Encoding: gzip`.

### Step 4 — - Operationalize
Dashboard ("HAProxy -- Bandwidth & Response Size"):
* Row 1 -- Single-value: "Bandwidth (Mbps)", "Avg response size", "P95 response size".
* Row 2 -- Bandwidth timechart per backend.
* Row 3 -- Large response outliers.

Alerting:
* High (bandwidth > 100 Mbps sustained): potential bandwidth saturation.
* Warning (P95 response size > 10 MB): unusually large responses.

### Step 5 — - Troubleshooting

* **High bandwidth from specific backend** -- Identify the URIs driving large responses. Check if large API responses can be paginated.

* **Compression not working** -- Verify: (1) `compression algo` directive present, (2) `compression type` includes content types being served, (3) client sends `Accept-Encoding: gzip`.

* **Sudden bandwidth spike** -- Possible: (1) cache miss storm, (2) large file download, (3) data exfiltration. Check top URIs by bytes.

## SPL

```spl
index=proxy sourcetype="haproxy:http"
| stats count by fe_name, be_name
| sort - count
| head 40
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## Known False Positives

Edge cases: multi-vendor mixes and ad hoc feeds can include lab traffic and partial visibility that mimics issues until scopes are defined. Tuning tip: match this to «HAProxy ACL-Based Traffic Routing Audit» and exclude change windows, scans, and lab VLANs you already expect.

## References

- [Vendor documentation](https://docs.haproxy.org/2.8/configuration.html#7)
