<!-- AUTO-GENERATED from UC-3.5.12.json — DO NOT EDIT -->

---
id: "3.5.12"
title: "Rate Limiting and Traffic Policy Compliance"
status: "verified"
criticality: "medium"
splunkPillar: "Security"
---

# UC-3.5.12 · Rate Limiting and Traffic Policy Compliance

## Description

Monitors Envoy proxy **429 responses** and **RL response flags** across service mesh routes to verify that Istio rate limiting policies (local rate limits and global RateLimitService) are actively enforcing traffic quotas, then compares observed throttle rates against expected policy baselines to detect **policy drift** — where misconfiguration, bypass, or disabled enforcement allows traffic that should be throttled.

## Value

Rate limiting policies are only effective when they are actually enforced. A misconfigured EnvoyFilter, a deleted RateLimitService deployment, or a VirtualService that bypasses the rate limit filter means traffic floods through unchecked. Conversely, overly aggressive rate limiting that blocks legitimate traffic degrades user experience. Monitoring the ratio of 429 responses to total requests per route and comparing against expected policy baselines detects both failure modes: absence of expected throttling (policy not enforced) and excessive throttling (policy too restrictive). This compliance monitoring turns rate limiting from a set-and-forget configuration into an observable, measurable control.

## Implementation

Collect Envoy access logs and rate limit metrics via OTel Collector into index=containers. Build two search variants: 5-minute route-level enforcement analysis with throttle classification, and hourly policy drift detection using a rate_limit_policies lookup. Alert when expected throttling is absent during high traffic or when drift exceeds 10%.

## Detailed Implementation

Prerequisites
• **Istio** 1.14+ service mesh with **rate limiting** configured via one or both mechanisms:
  — **Local rate limiting**: configured via **EnvoyFilter** resources that inject Envoy's `local_rate_limit` **HTTP filter** into sidecar or gateway proxies. Limits are enforced per-pod without coordination.
  — **Global rate limiting**: configured via **Istio**'s **RateLimitService** integration with an external **rate limit service** (typically envoyproxy/ratelimit) that maintains **shared counters** across all proxies.
• **Envoy access logging** enabled with **response_flags** included in the log format. The `RL` flag indicates rate-limited requests. The `response_code=429` indicates HTTP-level **rate limiting**. Both may be present simultaneously or independently depending on the configuration.
• **Splunk Connect for Kubernetes** or the **OTel Collector**'s **filelog receiver** for access log collection. Index as **`sourcetype=envoy:accesslog`** in **`index=containers`**.
• **OTel Collector Prometheus receiver** configured to scrape rate limit metrics:
  — From **Envoy sidecars**: `envoy_http_local_rate_limit_enabled`, `envoy_http_local_rate_limit_enforced`, `envoy_http_local_rate_limit_ok`, `envoy_http_local_rate_limit_rate_limited`
  — From the **global rate limit service**: `ratelimit_service_rate_limit_total` (labeled by domain, key, and `rate_limited=true/false`)
• **Rate limit policy lookup**: create **`rate_limit_policies.csv`** mapping `route` to `policy_name`, `max_rps`, and `expected_rl_pct`. This lookup enables **policy drift detection** by comparing observed throttle rates against expected baselines.
• **Splunk HEC** token for **`index=containers`** with appropriate sourcetype routing.
• Splunk RBAC: assign a **`security_analyst`** role with **`srchIndexesAllowed`** including `containers`.
• **License estimate**: rate limit events are a subset of all access log events. In a cluster with active rate limiting, typically 1–10% of requests are throttled. The SPL filters and aggregates efficiently.

Step 1 — Configure data collection
(1) **Envoy access log response flags**: the `response_flags` field in Envoy **access logs** contains coded flags that indicate how the request was processed. For rate limiting:
— **`RL`** — the request was **rate limited** by the local or global **rate limit filter**
— **`RLSE`** — the **rate limit service** **error** (the global rate limit service was unreachable, and the request was allowed or denied based on the `failure_mode_deny` setting)

Verify response flags are present in your access logs: `index=containers sourcetype="envoy:accesslog" earliest=-1h | stats count by **response_flags** | head 10`

(2) **Local rate limit metrics**: when an **EnvoyFilter** configures the `local_rate_limit` filter, Envoy exposes per-**listener** metrics:
— `envoy_http_local_rate_limit_enabled` (counter — requests processed by the filter)
— `envoy_http_local_rate_limit_ok` (counter — requests allowed)
— `envoy_http_local_rate_limit_rate_limited` (counter — requests denied)
— `envoy_http_local_rate_limit_enforced` (counter — denials enforced vs **shadow mode**)

These metrics provide **precise** rate limit counts without parsing access logs, but lack the **per-client** and **per-path** detail that access logs provide.

(3) **Global rate limit service**: if using envoyproxy/ratelimit as the global rate limit service, scrape its `/metrics` endpoint:
— `ratelimit_service_rate_limit_total{rate_limited="true"}` — requests denied by the global service
— `ratelimit_service_rate_limit_total{rate_limited="false"}` — requests allowed
— `ratelimit_service_total_hits` — total **descriptor evaluations**

(4) **Rate limit service health**: the global rate limit service is a **critical dependency** — if it goes down and `failure_mode_deny=true`, all requests are blocked; if `failure_mode_deny=false`, all rate limits are bypassed. Collect **`sourcetype=kube:events`** and **`sourcetype=kube:container:logs`** for the rate limit service pods to detect outages.

(5) **Policy lookup maintenance**: the `rate_limit_policies.csv` lookup should be updated whenever rate limit policies change. A scheduled search can extract current policies from **EnvoyFilter** resources collected via `kube:objects` and update the lookup automatically.

Step 2 — Create the search and alert
The primary SPL computes 5-minute rate limit enforcement per route from access logs. The **`enforcement_status`** classification:
— **HEAVY_THROTTLE** (>20% requests limited): aggressive throttling that may affect legitimate users — investigate whether the limit is too low or traffic is genuinely abusive
— **ACTIVE_THROTTLE** (>5%): moderate throttling — the policy is actively enforcing
— **LIGHT_THROTTLE** (>0%): occasional throttling — may be edge cases or bursty clients
— **NO_THROTTLE** (0%): no rate limiting observed — may be expected (low traffic) or concerning (policy not enforced)

The policy drift variant compares **observed hourly throttle rates** against **expected baselines** from the lookup:
— **SIGNIFICANT_DRIFT** (>10% deviation): the observed rate differs significantly from the **policy baseline** — investigate
— **MINOR_DRIFT** (>5%): notable but not urgent deviation
— **COMPLIANT**: within expected bounds
— **NO_POLICY**: route has no rate limit policy in the lookup — may be intentionally unprotected or missing from documentation

Schedule the enforcement search every **5 minutes** and alert on HEAVY_THROTTLE (may indicate **DDoS** or misconfigured policy). Schedule the drift search hourly and alert on SIGNIFICANT_DRIFT or NO_POLICY for routes that should be protected.

Step 3 — Validate
(a) Verify rate limit enforcement: generate traffic exceeding the rate limit threshold for a test route using a **load testing** tool or `hey` command and verify 429 responses appear: `index=containers sourcetype="envoy:accesslog" response_code=429 earliest=-5m | stats count by route_name`.
(b) Verify response flags: `index=containers sourcetype="envoy:accesslog" response_flags="*RL*" earliest=-1h | stats count`. Should show non-zero if rate limiting is active.
(c) Verify metric collection: `index=containers sourcetype="otel:metrics" metric_name="envoy_http_local_rate_limit_rate_limited" earliest=-1h | stats sum(metric_value)`.
(d) Populate and verify the policy lookup: `| inputlookup rate_limit_policies.csv | table route policy_name max_rps expected_rl_pct`.
(e) Test **policy drift detection**: temporarily lower a rate limit to trigger more 429s, then verify the drift search shows SIGNIFICANT_DRIFT.

Step 4 — Operationalize dashboards and runbooks
• Row A: **single-value tiles** — total 429s last 1h, rate-limited percentage (cluster-wide), routes with active throttling, drift alerts (SIGNIFICANT_DRIFT count), rate limit service status.
• Row B: **stacked bar chart** of allowed vs rate-limited requests per route over 24h — immediately shows which routes bear the most throttling.
• Row C: **policy drift table** — route, policy_name, hourly_requests, hourly_rl_pct, expected_rl_pct, drift, drift_status. Red rows for SIGNIFICANT_DRIFT.
• Row D: **client analysis** for heavily throttled routes — client IP, request count, 429 count, rl_pct. Identifies **abusive clients**.
• **Alerting**: HEAVY_THROTTLE on any route → **Slack** `#security-ops`; SIGNIFICANT_DRIFT → Slack `#mesh-ops`; rate limit service pod restart → **PagerDuty** P3; rate limit service down → PagerDuty P2 (all limits may be bypassed).
• **Runbook**: (1) for unexpected NO_THROTTLE: verify EnvoyFilter is applied: `kubectl get envoyfilter -A | grep rate`, (2) for HEAVY_THROTTLE: check top clients and block abusive IPs, (3) for SIGNIFICANT_DRIFT: compare current policy config with the lookup baseline, (4) for rate limit service outage: check `failure_mode_deny` setting to understand the impact.

Step 5 — Visualization, alert design, and troubleshooting
• **Visualization**: use a **traffic light matrix** showing each route as a row with columns for enforcement_status, drift_status, and RLS service health — green/amber/red coloring provides instant policy compliance overview. Pair with a **time series** of 429 rate per route.
• **Alert design**: include `route`, `total_requests`, `rate_limited`, `rl_pct`, `enforcement_status`, `drift_status`, `policy_name`, and top 3 throttled clients in the alert payload.
• **No 429 responses despite configured rate limits** — the EnvoyFilter may not be targeting the correct **workload selector** or listener. Verify: `istioctl proxy-config listener <pod> | grep rate_limit`.
• **Rate limit service RLSE errors** — the global rate limit service is unreachable. Check `failure_mode_deny` to determine if requests are being allowed or blocked during the outage.
• **Drift shows negative values** — the observed throttle rate is lower than expected, meaning fewer requests are being limited than the policy intended. This may indicate traffic volume is below the rate limit threshold (expected) or the **rate limit counter** is not being incremented (bug).
• **Per-descriptor hit analysis** — the global rate limit service evaluates **descriptor keys** (e.g., client IP, API key, route) against configured limits. Monitor the `ratelimit_service_total_hits` metric labeled by descriptor to identify which descriptors trigger the most evaluations.
• **Inconsistent enforcement across pods** — local rate limits are enforced per-pod, so total enforcement across the deployment is proportional to **replica count**. A deployment with 10 replicas each limiting at 100 RPS effectively allows 1000 RPS total. Scale-aware policies require the global rate limit service.

## SPL

```spl
`comment("--- Rate Limit Enforcement — 429 Response and RL Flag Analysis by Route ---")`
index=containers sourcetype="envoy:accesslog"
| eval route=coalesce(route_name, authority, host, "unknown")
| eval client=coalesce(downstream_remote_address, client_ip, "unknown")
| eval is_rate_limited=if(response_code=429 OR match(coalesce(response_flags,""), "RL"), 1, 0)
| eval request_path=coalesce(path, uri, request_uri)
| bin _time span=5m
| stats count as total_requests,
    sum(is_rate_limited) as rate_limited,
    dc(client) as unique_clients,
    dc(request_path) as unique_paths
    by _time, route
| eval rl_pct=round(100 * rate_limited / max(total_requests, 1), 2)
| eval enforcement_status=case(
    rl_pct > 20, "HEAVY_THROTTLE",
    rl_pct > 5, "ACTIVE_THROTTLE",
    rl_pct > 0, "LIGHT_THROTTLE",
    1=1, "NO_THROTTLE")
| table _time route total_requests rate_limited rl_pct unique_clients unique_paths enforcement_status

`comment("--- Rate Limit Policy Drift — Expected vs Observed Throttle Rates ---")`
index=containers sourcetype="envoy:accesslog"
| eval route=coalesce(route_name, authority, host, "unknown")
| eval is_rate_limited=if(response_code=429 OR match(coalesce(response_flags,""), "RL"), 1, 0)
| bin _time span=1h
| stats count as hourly_requests,
    sum(is_rate_limited) as hourly_limited
    by _time, route
| eval hourly_rl_pct=round(100 * hourly_limited / max(hourly_requests, 1), 2)
| lookup rate_limit_policies.csv route OUTPUT expected_rl_pct, max_rps, policy_name
| eval drift=if(isnotnull(expected_rl_pct), round(hourly_rl_pct - expected_rl_pct, 2), null())
| eval drift_status=case(
    isnull(drift), "NO_POLICY",
    abs(drift) > 10, "SIGNIFICANT_DRIFT",
    abs(drift) > 5, "MINOR_DRIFT",
    1=1, "COMPLIANT")
| where drift_status IN ("SIGNIFICANT_DRIFT", "NO_POLICY") OR hourly_limited > 100
| sort -hourly_limited
| table _time route policy_name hourly_requests hourly_limited hourly_rl_pct expected_rl_pct drift drift_status

`comment("--- Rate Limit Service Health — Global RLS Availability ---")`
index=containers sourcetype="otel:metrics" metric_name IN ("ratelimit_service_rate_limit_total", "envoy_http_local_rate_limit_rate_limited", "envoy_http_local_rate_limit_ok")
| eval metric=coalesce(metric_name, _metric_name)
| eval is_limited=if(match(metric, "rate_limited"), metric_value, 0)
| eval is_ok=if(match(metric, "_ok$"), metric_value, 0)
| bin _time span=5m
| stats sum(is_limited) as total_limited,
    sum(is_ok) as total_allowed
    by _time
| eval total=total_limited + total_allowed
| eval enforcement_pct=if(total > 0, round(100 * total_limited / total, 2), 0)
| eval rls_status=case(
    total=0, "NO_DATA",
    enforcement_pct > 30, "HEAVY",
    enforcement_pct > 0, "ACTIVE",
    1=1, "IDLE")
| table _time total_allowed total_limited enforcement_pct rls_status
```

## Visualization

Stacked bar of allowed vs rate-limited requests by route, policy drift table, enforcement status timeline, single-value tiles (total 429s, heaviest throttled route, drift count), client breakdown for throttled routes.

## Known False Positives

**legitimate_burst_traffic** — Legitimate traffic bursts (e.g., batch API calls, webhook retries, cron-triggered bulk operations) trigger rate limits that are correctly enforced but do not represent abuse. These bursts appear as ACTIVE_THROTTLE or HEAVY_THROTTLE without any malicious intent. Correlate with known batch processing schedules and application behavior patterns.

**rate_limit_service_cold_start** — After a global rate limit service restart, the in-memory counters reset to zero. Traffic that was previously at the limit is temporarily allowed through until counters rebuild. This appears as a brief NO_THROTTLE period followed by normal enforcement. Correlate with RLS pod restart events.

**local_rate_limit_per_pod_variance** — Local rate limits enforce per-pod, so the effective cluster-wide limit scales with replica count. During HPA scaling events, the effective limit changes. A scale-down concentrates traffic onto fewer pods, potentially triggering more throttling. Correlate enforcement changes with HPA scaling events.

**shadow_mode_enforcement** — Envoy's rate limit filter can operate in shadow mode where it logs rate limit decisions without actually enforcing them. Shadow mode generates metrics and log entries but never returns 429 to clients. The enforcement search may show NO_THROTTLE even though rate limits are configured. Check the `envoy_http_local_rate_limit_enforced` vs `envoy_http_local_rate_limit_rate_limited` ratio.

**client_retry_amplification** — When a client receives a 429 response, many HTTP client libraries automatically retry the request. Each retry generates another 429, inflating the rate-limited count. A single rate-limited client may appear to generate dozens of 429s from retry loops. Analyze by client IP to identify retry-driven inflation.

## References

- [Istio — Local Rate Limiting](https://istio.io/latest/docs/tasks/policy-enforcement/rate-limit/)
- [Envoy — Rate Limit Configuration](https://www.envoyproxy.io/docs/envoy/latest/configuration/http/http_filters/rate_limit_filter)
- [Envoy — Local Rate Limit Filter](https://www.envoyproxy.io/docs/envoy/latest/configuration/http/http_filters/local_rate_limit_filter)
- [Envoy — Response Flags Reference](https://www.envoyproxy.io/docs/envoy/latest/configuration/observability/access_log/usage#command-operators)
- [Splunk lookup Command Reference](https://docs.splunk.com/Documentation/Splunk/latest/SearchReference/Lookup)
