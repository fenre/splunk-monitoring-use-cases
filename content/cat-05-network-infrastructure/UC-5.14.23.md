<!-- AUTO-GENERATED from UC-5.14.23.json — DO NOT EDIT -->

---
id: "5.14.23"
title: "Squid Cache Hit Ratio by Request Method"
status: "draft"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.14.23 · Squid Cache Hit Ratio by Request Method

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance &middot; **Status:** Draft

*We watch squid cache hit ratio by request method and catch issues early, before they turn into outages for the people who rely on the network.*

---

## Description

CONNECT-heavy networks behave differently in hit ratio than browser traffic.

## Value

Operations teams trend Squid cache hit ratios by request method and domain, identifying cache effectiveness degradation and high-miss-rate origins.

## Implementation

Use `cache_access_log` with Splunk-friendly format; map `%>hs` status and `%rm` method in `props.conf`.

## Detailed Implementation

### Prerequisites
* Squid access logs in `index=proxy` with `sourcetype=squid:access`. Default Squid log format: `time elapsed remotehost code/status bytes method URL rfc931 peerstatus/peerhost type`. Key fields: `squid_request_status` (TCP_HIT, TCP_MISS, TCP_MEM_HIT, TCP_DENIED, etc.), `http_method`, `http_status_code`, `request_url`.
* Cache hit results: TCP_HIT (served from disk cache), TCP_MEM_HIT (served from memory cache), TCP_MISS (fetched from origin), TCP_REFRESH_HIT (revalidated, still valid), TCP_REFRESH_MISS (revalidated, stale -- re-fetched), TCP_DENIED (access denied by ACL). Hit ratio = (TCP_HIT + TCP_MEM_HIT + TCP_REFRESH_HIT) / total.
* Create `squid_config.csv` lookup: `proxy_host`, `site`, `max_cache_size_gb`, `expected_hit_ratio`.

### Step 1 — - Configure data collection
Squid access log format (default is sufficient):
```
# squid.conf
access_log daemon:/var/log/squid/access.log squid
```
Verify:
```spl
index=proxy sourcetype="squid:access" earliest=-4h
| stats count by squid_request_status
```

### Step 2 — - Create the search and alert

**Primary search -- Cache hit ratio by request method:**
```spl
index=proxy sourcetype="squid:access" earliest=-24h
| eval cache_result=upper(coalesce(squid_request_status, "UNKNOWN"))
| eval is_hit=if(match(cache_result, "TCP_HIT|TCP_MEM_HIT|TCP_REFRESH_HIT|TCP_IMS_HIT|TCP_OFFLINE_HIT"), 1, 0)
| eval is_miss=if(match(cache_result, "TCP_MISS|TCP_REFRESH_MISS|TCP_CLIENT_REFRESH_MISS"), 1, 0)
| eval is_denied=if(match(cache_result, "TCP_DENIED"), 1, 0)
| bin _time span=15m
| stats sum(is_hit) as hits sum(is_miss) as misses sum(is_denied) as denied count as total by _time, http_method
| eval hit_ratio=round(100*hits/(hits+misses), 2)
| where http_method="GET"
| eval severity=case(hit_ratio < 30, "CRITICAL -- hit ratio below 30%", hit_ratio < 50, "WARNING -- hit ratio below 50%", 1==1, "OK")
| where severity != "OK"
| table _time, http_method, total, hits, misses, hit_ratio, denied, severity
```

**Per-domain cache effectiveness:**
```spl
index=proxy sourcetype="squid:access" http_method=GET earliest=-4h
| eval is_miss=if(match(squid_request_status, "(?i)MISS"), 1, 0)
| rex field=request_url "https?://(?<domain>[^/]+)"
| stats count as requests sum(is_miss) as misses by domain
| eval miss_pct=round(100*misses/requests, 1)
| where requests > 50
| sort -miss_pct | head 20
```

### Step 3 — - Validate
(a) `squidclient mgr:info` -- shows cache hit ratios.
(b) Request a known cacheable URL twice and verify TCP_HIT on second request.
(c) Compare GET hit ratio with `squidclient mgr:5min` for recent performance.

### Step 4 — - Operationalize
Dashboard ("Squid -- Cache Hit Ratio"):
* Row 1 -- Single-value: "GET hit ratio", "Total hits", "Total misses", "Denied".
* Row 2 -- Hit ratio timechart.
* Row 3 -- Top miss domains.

Alerting:
* Critical (GET hit ratio < 30%): cache is largely ineffective.
* Warning (GET hit ratio < 50%): investigate cache configuration.

### Step 5 — - Troubleshooting

* **Low hit ratio** -- Common causes: (1) `Cache-Control: no-cache/no-store` from origins, (2) `maximum_object_size` too small -- large objects bypass cache, (3) cache storage too small for working set, (4) too many unique URLs (query strings).

* **TCP_REFRESH_MISS high** -- Objects are being revalidated but found stale. Origins are changing content frequently. Consider: `refresh_pattern` tuning in squid.conf.

* **All requests showing TCP_MISS** -- Verify caching is enabled. Check: `cache_dir` is configured, `cache deny` rules aren't overly broad, and `minimum_object_size`/`maximum_object_size` are reasonable.

## SPL

```spl
index=proxy sourcetype="squid:access"
| eval meth=coalesce(request_method, cs_method)
| eval is_hit=if(match(code, "TCP_(HIT|MEM_HIT|REFRESH_HIT)"),1,0)
| stats sum(is_hit) as hits count as total by meth
| eval hit_pct=round(100*hits/total,2)
| table meth, hits, total, hit_pct
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## Known False Positives

Edge cases: multi-vendor mixes and ad hoc feeds can include lab traffic and partial visibility that mimics issues until scopes are defined. Tuning tip: match this to «Squid Cache Hit Ratio by Request Method» and exclude change windows, scans, and lab VLANs you already expect.

## References

- [Vendor documentation](http://www.squid-cache.org/Doc/config/access_log/)
