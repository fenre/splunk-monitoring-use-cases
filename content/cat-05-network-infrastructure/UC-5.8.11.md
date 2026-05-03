<!-- AUTO-GENERATED from UC-5.8.11.json — DO NOT EDIT -->

---
id: "5.8.11"
title: "API Call Rate Monitoring and Rate Limit Alerts (Meraki)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.8.11 · API Call Rate Monitoring and Rate Limit Alerts (Meraki)

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance

*We watch how hard we lean on the Meraki cloud API, so a burst of calls does not trip limits when many dashboards run at once.*

---

## Description

Monitors API usage to prevent rate limit hits and optimize automation efficiency.

## Value

Network operations teams monitor Meraki Dashboard API rate limit events and retry patterns to prevent data collection disruptions, identify competing API consumers, and maintain reliable monitoring data flow.

## Implementation

Log all API calls with timestamps. Monitor call rate by endpoint.

## Detailed Implementation

### Prerequisites
- Meraki Dashboard API rate limit monitoring. The Meraki API enforces rate limits: 10 requests per second per organization (can burst higher with API v1.1+). The TA's API calls count against this limit, as do any other API consumers (scripts, integrations, third-party tools).
- Data source: TA internal logs in `index=_internal` and/or custom API response monitoring. When the TA receives HTTP 429 (Too Many Requests), it logs retry events. Additionally, monitor Meraki API response headers: `X-RateLimit-Remaining`, `X-RateLimit-Limit`, `X-RateLimit-Reset`.
- If you have custom scripts calling the Meraki API, forward their logs to Splunk with rate limit tracking. Data in `index=meraki` (or `_internal`) with fields: `api_endpoint`, `http_status`, `rate_limit_remaining`, `retry_count`.

### Step 1 — Configure data collection
Verify API rate limit data:
```spl
index=_internal sourcetype=splunkd "meraki" ("429" OR "rate" OR "retry" OR "throttle") earliest=-24h
| stats count by log_level, message
```

### Step 2 — Create the search and alert

**Primary search — API rate limit events and retries:**
```spl
index=_internal sourcetype=splunkd "meraki" ("429" OR "rate_limit" OR "retry") earliest=-4h
| rex "(?i)(?:429|rate.?limit|throttl|retry).*?(?:endpoint|url)[=:]\s*(?P<api_endpoint>[^\s,]+)"
| rex "(?i)retry.*?(?P<retry_count>\d+)"
| bin _time span=5m
| stats count as rate_events sum(retry_count) as total_retries by _time
| eval severity=case(rate_events > 20, "CRITICAL", rate_events > 5, "WARNING", 1==1, "INFO")
| where severity!="INFO"
```

#### Understanding this SPL: Meraki API rate limiting causes the TA to retry requests, which delays data collection. If rate limits are sustained, the TA may skip data collection cycles entirely, creating monitoring gaps. The most common cause is multiple API consumers (TA + custom scripts + third-party tools) sharing the same organization's rate limit budget.

**API call volume trending:**
```spl
index=_internal sourcetype=splunkd "meraki" "api" earliest=-24h
| bin _time span=1h
| stats count as api_calls by _time
| eval calls_per_second=round(api_calls/3600, 2)
```

**Custom API consumer tracking (if applicable):**
```spl
index=meraki sourcetype="meraki:api:audit" earliest=-24h
| stats count as calls dc(api_endpoint) as endpoints by caller_ip, user_agent
| sort -calls
```

### Step 3 — Validate
(a) Intentionally make rapid API calls to the Meraki API and verify 429 responses appear in Splunk.
(b) Check Meraki Dashboard: Organization > API & Webhooks > API Usage. Compare API call counts.
(c) Verify all API consumers are identified in the tracking search.

### Step 4 — Operationalize
Dashboard ("Meraki API Health"):
- Row 1 — Single-value tiles: "Rate limit events (4h)", "Total retries", "API calls/sec (avg)", "API consumers".
- Row 2 — Rate limit event timeline.
- Row 3 — API consumer breakdown: caller IP, user agent, call volume.

Alerting:
- Critical (rate limit events > 20 per 5 minutes): data collection disrupted — reduce API consumers.
- Warning (rate limit events > 5 per 5 minutes): approaching sustained rate limiting.

### Step 5 — Troubleshooting

- **Constant rate limiting** — Identify all API consumers: the Splunk TA, custom scripts, third-party integrations (Zabbix, PRTG, etc.). Coordinate API usage or use Meraki's Action Batches for bulk operations.

- **Rate limiting only during specific hours** — A scheduled script may be making bulk API calls. Stagger API-consuming jobs to spread load.

- **TA data stops but no 429 errors** — The TA may have hit a different error (401 unauthorized, 403 forbidden, 500 server error). Check `_internal` for all Meraki-related errors, not just rate limits.

## SPL

```spl
index=cisco_network sourcetype="meraki:api:*"
| timechart count as api_calls by source, endpoint
| eval call_rate=api_calls/60
| where call_rate > 9
```

## Visualization

API call timeline; rate limit gauge; endpoint usage breakdown.

## Known False Positives

Dashboard refreshes, monitoring apps, and automation hitting the same org can add API calls; chart usage against Meraki’s published limits by product.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
