<!-- AUTO-GENERATED from UC-5.14.39.json — DO NOT EDIT -->

---
id: "5.14.39"
title: "Envoy HTTP Rate Limit Filter 429 Rate"
status: "draft"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.14.39 · Envoy HTTP Rate Limit Filter 429 Rate

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Security, Performance &middot; **Status:** Draft

*We watch envoy http rate limit filter 429 rate and catch issues early, before they turn into outages for the people who rely on the network.*

---

## Description

429 spikes indicate abuse or mis-set quotas.

## Value

Operations teams track Envoy rate limit (429) responses per upstream cluster and client, evaluating whether rate limit thresholds are appropriately tuned for traffic patterns.

## Implementation

Ensure xDS pushes consistent descriptors; log external RL service errors separately.

## Detailed Implementation

### Prerequisites
* Envoy access logs with rate limit filter results. Key response flags: `RL` (rate limited). Key fields: `response_code=429`, `response_flags`. Key metrics: `envoy_http_local_rate_limit_enabled`, `envoy_http_local_rate_limit_enforced`, `envoy_http_local_rate_limit_ok`, `envoy_cluster_ratelimit_ok`, `envoy_cluster_ratelimit_over_limit`.
* Rate limiting: Envoy supports local rate limiting (in-process token bucket) and external rate limiting (via gRPC rate limit service). When rate limited, Envoy returns 429 Too Many Requests. Rate limiting prevents abuse but over-aggressive limits impact legitimate traffic.

### Step 1 — - Configure data collection
Local rate limit:
```yaml
http_filters:
- name: envoy.filters.http.local_ratelimit
  typed_config:
    "@type": type.googleapis.com/envoy.extensions.filters.http.local_ratelimit.v3.LocalRateLimit
    stat_prefix: http_local_rate_limiter
    token_bucket:
      max_tokens: 1000
      tokens_per_fill: 100
      fill_interval: 1s
    filter_enabled:
      runtime_key: local_rate_limit_enabled
      default_value: { numerator: 100, denominator: HUNDRED }
    filter_enforced:
      runtime_key: local_rate_limit_enforced
      default_value: { numerator: 100, denominator: HUNDRED }
```
Verify:
```spl
index=proxy sourcetype="envoy:access" earliest=-4h
| where response_code=429 OR match(response_flags, "RL")
| stats count by upstream_cluster
```

### Step 2 — - Create the search and alert

**Primary search -- Rate limit 429 analysis:**
```spl
index=proxy sourcetype="envoy:access" earliest=-4h
| where response_code=429 OR match(response_flags, "RL")
| eval rate_limit_type=case(match(response_flags, "RL"), "LOCAL_RATE_LIMIT", response_code=429, "429_RETURNED", 1==1, "OTHER")
| rex field=downstream_remote_address "(?<client_ip>[0-9.]+)"
| bin _time span=5m
| stats count as rate_limited dc(client_ip) as affected_clients by _time, upstream_cluster
| eval severity=case(rate_limited > 500, "HIGH -- heavy rate limiting", rate_limited > 100, "WARNING -- significant rate limiting", 1==1, "INFO")
| where severity != "INFO"
| table _time, upstream_cluster, rate_limited, affected_clients, severity
```

**Top rate-limited clients:**
```spl
index=proxy sourcetype="envoy:access" response_code=429 earliest=-4h
| rex field=downstream_remote_address "(?<client_ip>[0-9.]+)"
| stats count as limited_requests by client_ip, upstream_cluster
| sort -limited_requests | head 20
```

### Step 3 — - Validate
(a) Send rapid requests exceeding the rate limit: `for i in $(seq 1 2000); do curl -s -o /dev/null -w "%{http_code}
" http://<envoy>/; done | sort | uniq -c`.
(b) `curl http://localhost:15000/stats | grep rate_limit` -- shows rate limit counters.
(c) Verify 429 response includes appropriate `Retry-After` header.

### Step 4 — - Operationalize
Dashboard ("Envoy -- Rate Limiting"):
* Row 1 -- Single-value: "Rate limited (4h)", "Affected clients", "Top cluster".
* Row 2 -- Rate limit events timechart.
* Row 3 -- Top rate-limited clients.

Alerting:
* High (> 500 rate limits/5m): possible attack or limit too low.
* Warning (> 100 rate limits/5m): evaluate if limits are appropriate.

### Step 5 — - Troubleshooting

* **Legitimate traffic being rate limited** -- Increase token bucket: (1) raise `max_tokens` for burst capacity, (2) increase `tokens_per_fill` for sustained rate.

* **No 429s but expect rate limiting** -- Check: (1) `filter_enabled` and `filter_enforced` are both set, (2) filter is in the correct filter chain position, (3) runtime feature flags haven't disabled it.

* **External rate limit service latency** -- gRPC rate limit service adding latency. Check: (1) rate limit service health, (2) `timeout` setting in rate_limit_service config, (3) consider local rate limiting as fallback.

## SPL

```spl
index=proxy sourcetype="envoy:access"
| where response_code==429 OR match(response_flags, "RL")
| stats count by route_name, cluster_name
| sort - count
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## Known False Positives

Edge cases: multi-vendor mixes and ad hoc feeds can include lab traffic and partial visibility that mimics issues until scopes are defined. Tuning tip: match this to «Envoy HTTP Rate Limit Filter 429 Rate» and exclude change windows, scans, and lab VLANs you already expect.

## References

- [Vendor documentation](https://www.envoyproxy.io/docs/envoy/latest/configuration/http/http_filters/rate_limit_filter)
