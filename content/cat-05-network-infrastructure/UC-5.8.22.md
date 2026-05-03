<!-- AUTO-GENERATED from UC-5.8.22.json — DO NOT EDIT -->

---
id: "5.8.22"
title: "API Error Rate and Endpoint Health (Meraki)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.8.22 · API Error Rate and Endpoint Health (Meraki)

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Availability

*We help you see when the Meraki cloud API is returning errors, before dashboards and scripts quietly break.*

---

## Description

Monitors API endpoint health and error rates to ensure automation reliability.

## Value

Network operations teams monitor Meraki Dashboard API error rates and response codes to detect credential failures, rate limiting, and cloud infrastructure issues that disrupt data collection.

## Implementation

Log API responses with status codes. Alert on error rate threshold.

## Detailed Implementation

### Prerequisites
- Meraki Dashboard API error monitoring via TA internal logs and custom API health checks. The Meraki API returns standard HTTP status codes: 200 (success), 400 (bad request), 401 (unauthorized), 403 (forbidden), 404 (not found), 429 (rate limited), 500 (server error).
- Data sources: (1) `index=_internal` for TA HTTP response errors, (2) `index=meraki sourcetype=meraki:api:audit` for custom API monitoring scripts, (3) Meraki Dashboard: Organization > API & Webhooks > API Usage for reference.

### Step 1 — Configure data collection
Verify API error visibility:
```spl
index=_internal sourcetype=splunkd "meraki" ("error" OR "failed" OR "4[0-9][0-9]" OR "5[0-9][0-9]") earliest=-24h
| stats count by log_level
```

### Step 2 — Create the search and alert

**Primary search — API error rate by endpoint:**
```spl
index=_internal sourcetype=splunkd "meraki" earliest=-4h
| rex "(?:status|response|http)[_=:\s]*(?P<http_status>\d{3})"
| rex "(?:endpoint|url|path)[_=:\s]*(?P<api_endpoint>[^\s,"]+)"
| where isnotnull(http_status) AND http_status >= 400
| eval error_category=case(http_status="401" OR http_status="403", "AUTH_ERROR", http_status="404", "NOT_FOUND", http_status="429", "RATE_LIMITED", http_status >= "500", "SERVER_ERROR", 1==1, "CLIENT_ERROR")
| stats count as errors by http_status, error_category, api_endpoint
| sort -errors
```

#### Understanding this SPL: API errors indicate different failure modes: 401/403 = credential or permission issue (data collection stops); 404 = endpoint changed (API version mismatch); 429 = rate limiting (data delayed); 500+ = Meraki cloud issue (temporary or sustained). Each requires a different remediation approach.

**API health trending:**
```spl
index=_internal sourcetype=splunkd "meraki" earliest=-24h
| rex "(?:status|response|http)[_=:\s]*(?P<http_status>\d{3})"
| where isnotnull(http_status)
| eval is_error=if(http_status >= 400, 1, 0)
| bin _time span=1h
| stats count as total_calls sum(is_error) as error_calls by _time
| eval error_rate_pct=round(100*error_calls/total_calls, 1)
```

### Step 3 — Validate
(a) Intentionally use an invalid API key and verify 401 errors appear in Splunk.
(b) Compare API usage statistics with Meraki Dashboard: Organization > API & Webhooks.
(c) During a Meraki cloud maintenance window, verify 5xx errors are captured.

### Step 4 — Operationalize
Dashboard ("Meraki API Health"):
- Row 1 — Single-value tiles: "API error rate %", "Auth errors", "Rate limit events", "Server errors".
- Row 2 — Error breakdown by status code and endpoint.
- Row 3 — API health trending (error rate % over 24h).

Alerting:
- Critical (401/403 errors sustained > 15 minutes): data collection stopped — credential issue.
- Warning (error rate > 5%): API issues impacting data quality.

### Step 5 — Troubleshooting

- **Sustained 401 errors** — API key was revoked, expired, or the admin account was deactivated. Generate a new API key in Meraki Dashboard and update the TA configuration.

- **Intermittent 500 errors** — Meraki cloud infrastructure issue. Check status.meraki.com for ongoing incidents. These typically self-resolve.

- **429 errors increasing** — Too many API consumers sharing the rate limit. See UC-5.8.11 for detailed rate limit troubleshooting.

## SPL

```spl
index=cisco_network sourcetype="meraki:api:*" (http_status_code=4* OR http_status_code=5*)
| stats count as error_count, values(http_status_code) as status_codes by endpoint, method
| eval error_rate=round(error_count*100/total_requests, 2)
| where error_rate > 5
```

## Visualization

API error timeline; endpoint error breakdown; error rate gauge.

## Known False Positives

Meraki 429 rate-limit responses and transient 5xx from the cloud are often environmental; back off and alert on error rate, not a single 500 line.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
