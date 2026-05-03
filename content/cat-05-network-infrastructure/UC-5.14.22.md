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

Operations teams analyze Varnish gzip compression coverage by content type, identifying uncompressed text responses that waste bandwidth and cache storage.

## Implementation

Pair with byte counters if available; sample to control volume.

## Detailed Implementation

### Prerequisites
* Varnish access logs with response size and content-type, plus `Accept-Encoding` and `Content-Encoding` headers. Key fields: `bytes_read`, `content_type`, `content_encoding`. Data in `index=proxy` with `sourcetype=varnish:access`.
* Varnish gzip compression: enabled with `set beresp.do_gzip = true;` in `vcl_backend_response`. Varnish can compress responses before storing (objects stored compressed) and decompress for clients that don't support gzip. Key benefits: reduced storage usage and bandwidth. Compression ratio = uncompressed_size / compressed_size.

### Step 1 — - Configure data collection
VCL compression:
```
sub vcl_backend_response {
    if (beresp.http.Content-Type ~ "(?i)(text/|application/json|application/javascript|application/xml)") {
        set beresp.do_gzip = true;
    }
}
```
Log format with compression info:
```
varnishncsa -F '... %{Content-Type}o %{Content-Encoding}o %b ...'
```
Verify:
```spl
index=proxy sourcetype="varnish:access" earliest=-4h
| eval is_gzipped=if(match(content_encoding, "(?i)gzip"), 1, 0)
| stats count sum(is_gzipped) as gzipped by content_type
| eval gzip_pct=round(100*gzipped/count, 1)
| sort -count
```

### Step 2 — - Create the search and alert

**Primary search -- Compression ratio by content type:**
```spl
index=proxy sourcetype="varnish:access" earliest=-4h
| eval response_bytes=tonumber(bytes_read)
| eval is_compressed=if(match(content_encoding, "(?i)gzip|br|deflate"), 1, 0)
| eval content_group=case(match(content_type, "text/html"), "text/html", match(content_type, "application/json"), "application/json", match(content_type, "application/javascript|text/javascript"), "javascript", match(content_type, "text/css"), "text/css", match(content_type, "image/"), "image (skip)", match(content_type, "video/|audio/"), "media (skip)", 1==1, "other")
| where content_group != "image (skip)" AND content_group != "media (skip)"
| stats count as responses sum(response_bytes) as total_bytes avg(response_bytes) as avg_bytes sum(is_compressed) as compressed_count by content_group
| eval compression_rate=round(100*compressed_count/responses, 1)
| eval total_mb=round(total_bytes/1048576, 1)
| eval savings_potential=if(compression_rate < 50 AND match(content_group, "text|json|javascript|css"), "HIGH -- ".content_group." should be compressed", "OK")
| sort -total_bytes
| table content_group, responses, total_mb, avg_bytes, compression_rate, savings_potential
```

### Step 3 — - Validate
(a) Request with gzip: `curl -H "Accept-Encoding: gzip" -s -o /dev/null -w "%{size_download}" https://<varnish>/page`.
(b) Request without: `curl -s -o /dev/null -w "%{size_download}" https://<varnish>/page`.
(c) Calculate ratio: uncompressed/compressed. Typical HTML ratio: 4-8x.

### Step 4 — - Operationalize
Dashboard ("Varnish -- Compression"):
* Row 1 -- Single-value: "Compression rate (%)", "Bandwidth saved (est)", "Uncompressed text types".
* Row 2 -- Compression by content type table.

### Step 5 — - Troubleshooting

* **Text content not compressed** -- Check: (1) `beresp.do_gzip = true` in VCL for the content type, (2) client sent `Accept-Encoding: gzip`, (3) content isn't already compressed by backend.

* **Images/media being compressed** -- Gzipping already-compressed formats (JPEG, PNG, MP4) wastes CPU with no benefit. Exclude: `if (beresp.http.Content-Type !~ "image|video|audio")`.

* **High CPU from compression** -- If Varnish CPU is high and compression is enabled, consider: (1) compress at the backend instead, (2) use `beresp.do_gzip` only for objects that will be served many times (high hit ratio), (3) reduce compression level.

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
