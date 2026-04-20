---
id: "3.5.12"
title: "Rate Limiting and Traffic Policy Compliance"
criticality: "medium"
splunkPillar: "Security"
---

# UC-3.5.12 · Rate Limiting and Traffic Policy Compliance

## Description

Confirms quotas and Istio `RateLimitService`/Local rate limit configs actually throttle abuse; drift between policy and observed denials indicates misconfiguration or bypass attempts.

## Value

Confirms quotas and Istio `RateLimitService`/Local rate limit configs actually throttle abuse; drift between policy and observed denials indicates misconfiguration or bypass attempts.

## Implementation

Ensure access logs include `response_code` 429 and Envoy `response_flags` (e.g. `RL` for rate limited). For global RLS, scrape `ratelimit_service_*` or service metrics. Dashboard expected 429 share per route against policy (e.g. per-API key). Alert on unexpected absence of throttling during attacks or sudden spikes in 429s indicating config errors.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk OTel Collector (Envoy local rate limit / RLS metrics), Envoy access logs.
• Ensure the following data sources are available: `sourcetype=envoy:access` or `sourcetype=otel:metrics`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Ensure access logs include `response_code` 429 and Envoy `response_flags` (e.g. `RL` for rate limited). For global RLS, scrape `ratelimit_service_*` or service metrics. Dashboard expected 429 share per route against policy (e.g. per-API key). Alert on unexpected absence of throttling during attacks or sudden spikes in 429s indicating config errors.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=containers sourcetype="envoy:access"
| eval denied=if(response_code=429 OR match(response_flags, "RL"), 1, 0)
| stats count as total, sum(denied) as rate_limited by route_name, cluster_name
| eval rl_pct=round(100*rate_limited/total, 3)
| where rate_limited>0
| sort -rate_limited
```

Understanding this SPL

**Rate Limiting and Traffic Policy Compliance** — Confirms quotas and Istio `RateLimitService`/Local rate limit configs actually throttle abuse; drift between policy and observed denials indicates misconfiguration or bypass attempts.

Documented **Data sources**: `sourcetype=envoy:access` or `sourcetype=otel:metrics`. **App/TA** (typical add-on context): Splunk OTel Collector (Envoy local rate limit / RLS metrics), Envoy access logs. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: containers; **sourcetype**: envoy:access. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=containers, sourcetype="envoy:access". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **denied** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by route_name, cluster_name** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **rl_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where rate_limited>0` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Time chart (429 rate by route), Table (routes with throttle events), Stacked bar (allowed vs rate-limited volume).

## SPL

```spl
index=containers sourcetype="envoy:access"
| eval denied=if(response_code=429 OR match(response_flags, "RL"), 1, 0)
| stats count as total, sum(denied) as rate_limited by route_name, cluster_name
| eval rl_pct=round(100*rate_limited/total, 3)
| where rate_limited>0
| sort -rate_limited
```

## Visualization

Time chart (429 rate by route), Table (routes with throttle events), Stacked bar (allowed vs rate-limited volume).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
