<!-- AUTO-GENERATED from UC-5.3.36.json — DO NOT EDIT -->

---
id: "5.3.36"
title: "Citrix ADC API Gateway Policy Evaluation"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.3.36 · Citrix ADC API Gateway Policy Evaluation

## Description

API gateway policies on Citrix ADC enforce OpenAPI shapes, XML/JSON validation, authentication, and rate limits. Mis-specified definitions cause load failures; validation errors may reflect attack traffic; 429 storms show mis-tuned quotas or abuse. Monitoring policy evaluation alongside latency keeps both security and user experience within SLO.

## Value

API gateway policies on Citrix ADC enforce OpenAPI shapes, XML/JSON validation, authentication, and rate limits. Mis-specified definitions cause load failures; validation errors may reflect attack traffic; 429 storms show mis-tuned quotas or abuse. Monitoring policy evaluation alongside latency keeps both security and user experience within SLO.

## Implementation

Send AppFlow or security logs with status, vserver, and response time to `index=netscaler`. Map each API product to a vserver name. Extract policy name and error class from syslog for definition load issues. Alert on definition load failure, sustained 429 above baseline, or validation error spikes uncorrelated with version rollouts.

## Detailed Implementation

Prerequisites: API gateway feature enabled; OpenAPI bundle in change control; AppFlow with resp_time_ms and HTTP status. Step 1: Configure data collection — Structure logs or use HEC with acks; props [citrix:netscaler:appflow] for status, resp_time_ms, vserver; redact request bodies in syslog lines. Step 2: Create the search and alert — Split alerts: definition load/parse errors, validation spikes, and performance (start p95>1000ms, begin tuning at >500ms and raise only with baseline noise data). Step 3: Validate — In lab deploy a bad OpenAPI, send malformed JSON, and rate-test to 429; confirm throttled/val_fail fields in the index with `index=netscaler earliest=-1h vserver="*api*" | stats count by status`. Step 4: Operationalize — Playbook for WAF-style blocks vs client fixes vs quota changes vs spec rollback; if the same vserver repeats, escalate to Citrix ADC and API product owners after two consecutive alert windows.

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

## References

- [Splunk Documentation: Splunk Add-on for Citrix NetScaler](https://docs.splunk.com/Documentation/AddOns/released/CitrixNetScaler/CitrixNetScaler)
- [CIM: Web](https://docs.splunk.com/Documentation/CIM/latest/User/Web)
- [Citrix ADC — API gateway](https://docs.citrix.com/en-us/citrix-adc/current-release/api-gateway.html)
