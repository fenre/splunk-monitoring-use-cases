<!-- AUTO-GENERATED from UC-5.3.36.json — DO NOT EDIT -->

---
id: "5.3.36"
title: "Citrix ADC API Gateway Policy Evaluation"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.3.36 · Citrix ADC API Gateway Policy Evaluation

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Security &middot; **Type:** Security, Performance

*We see how often gateway policies are used so a new route, a rate cap, and a test client are all visible in the same counter story.*

---

## Description

API gateway policies on Citrix ADC enforce OpenAPI shapes, XML/JSON validation, authentication, and rate limits. Mis-specified definitions cause load failures; validation errors may reflect attack traffic; 429 storms show mis-tuned quotas or abuse. Monitoring policy evaluation alongside latency keeps both security and user experience within SLO.

## Value

API operations teams monitor Citrix ADC API Gateway policy evaluation including rate limiting, OAuth validation failures, and schema violations per API endpoint for API reliability.

## Implementation

Send AppFlow or security logs with status, vserver, and response time to `index=netscaler`. Map each API product to a vserver name. Extract policy name and error class from syslog for definition load issues. Alert on definition load failure, sustained 429 above baseline, or validation error spikes uncorrelated with version rollouts.

## Detailed Implementation

### Prerequisites
* Splunk Add-on for Citrix NetScaler (`Splunk_TA_citrix-netscaler`, Splunkbase 2770). Citrix ADC API Gateway logs. Key fields: `api_name`, `method`, `path`, `status_code`, `response_time_ms`, `policy_name`, `rate_limit_action`, `oauth_status`, `client_id`.
* Citrix ADC as API Gateway: (1) API rate limiting, (2) OAuth/JWT validation, (3) request/response transformation, (4) API schema validation, (5) traffic management per API endpoint.

### Step 1 — - Configure data collection
Enable API Gateway logging via AppFlow or syslog. Verify:
```spl
index=netscaler (sourcetype="citrix:netscaler:syslog" OR sourcetype="citrix:netscaler:appflow") ("API" OR "api_" OR "oauth" OR "jwt" OR "rate.limit") earliest=-4h
| stats count by host
```

### Step 2 — - Create the search and alert

**Primary search -- API Gateway policy evaluation:**
```spl
index=netscaler (sourcetype="citrix:netscaler:syslog" OR sourcetype="citrix:netscaler:appflow") ("API" OR "api_" OR "oauth" OR "jwt" OR "rate.limit") earliest=-4h
| eval api=coalesce(api_name, api_endpoint, path)
| eval policy_result=coalesce(policy_action, rate_limit_action, oauth_status)
| eval status=coalesce(status_code, http_status)
| eval rt=coalesce(response_time_ms, latency)
| eval issue=case(match(policy_result, "(?i)rate.limit|throttle"), "RATE_LIMITED", match(policy_result, "(?i)oauth.*fail|jwt.*invalid|401"), "AUTH_FAILURE", match(policy_result, "(?i)schema.*fail|validation.*error"), "SCHEMA_VIOLATION", tonumber(status) >= 500, "BACKEND_ERROR", 1==1, null())
| where isnotnull(issue)
| stats count as events dc(client_id) as affected_clients by api, issue
| eval severity=case(issue="AUTH_FAILURE" AND events > 50, "HIGH -- mass auth failures", issue="RATE_LIMITED" AND events > 100, "WARNING -- heavy throttling", issue="BACKEND_ERROR", "WARNING -- backend issues", 1==1, "INFO")
| sort severity, -events
```

### Step 3 — - Validate
(a) Send an API request with invalid OAuth token and verify AUTH_FAILURE appears.
(b) Exceed rate limit and verify RATE_LIMITED events.
(c) Compare with ADC API stats.

### Step 4 — - Operationalize
Dashboard ("Citrix ADC -- API Gateway"):
* Row 1 -- Single-value: "API requests (4h)", "Rate limited", "Auth failures", "Backend errors".
* Row 2 -- API policy evaluation issue table.

Alerting:
* High (mass auth failures > 50 in 15 min): potential API key compromise or misconfiguration.
* Warning (rate limiting > 100 events): clients exceeding limits.

### Step 5 — - Troubleshooting

* **High rate limiting** -- Clients may need higher limits. Review: API rate limit policy on the ADC. Consider per-client or per-API tier limits.

* **OAuth failures** -- Check: (1) OAuth token endpoint, (2) JWT signing key rotation, (3) clock skew between ADC and OAuth provider.

* **Schema validation errors** -- API request payload doesn't match expected schema. Check the API definition and client implementation.

## SPL

```spl
index=netscaler (sourcetype="citrix:netscaler:syslog" OR sourcetype="citrix:netscaler:appflow") ("API" OR "openapi" OR swagger OR "json" OR "xml" OR throttle OR "rate" OR "429" OR validation OR xss OR "schema")
| eval is_block=if(status=429 OR match(_raw,"(?i)429|throttl|deny"),1,0)
| eval val_err=if(match(_raw,"(?i)(invalid|schema|validation|malform)"),1,0)
| bin _time span=5m
| stats count as hits, sum(is_block) as throttled, sum(val_err) as val_fail, p95(resp_time_ms) as p95_lat by _time, host, vserver
| where throttled>10 OR val_fail>0 OR p95_lat>1000
| table _time, host, vserver, hits, throttled, val_fail, p95_lat
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Web.Web
  by Web.status Web.url Web.http_method Web.dest span=1h
| sort -count
```

## Visualization

Time chart: throttles vs successes, bar: validation failure types, table: top API paths by error (hashed if needed).

## Known False Positives

Rate limits, bad clients, and new API routes can all raise policy hit counts during healthy rollouts.

## References

- [Splunk Documentation: Splunk Add-on for Citrix NetScaler](https://docs.splunk.com/Documentation/AddOns/released/CitrixNetScaler/CitrixNetScaler)
- [CIM: Web](https://docs.splunk.com/Documentation/CIM/latest/User/Web)
- [Citrix ADC — API gateway](https://docs.citrix.com/en-us/citrix-adc/current-release/api-gateway.html)
