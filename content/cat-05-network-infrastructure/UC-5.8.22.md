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

1. Enable both API Requests History and API Requests Response Codes inputs in Splunk_TA_cisco_meraki (TA v3+). 2. The History input emits one event per individual API call with host, path (e.g. '/organizations/.../devices'), method, responseCode, sourceIp, userAgent, ts. 3. The Response Codes input gives aggregated counts per (responseCode, interval). 4. Threshold 4xx/5xx error rate >5% per endpoint to surface broken integrations or rate-limit hits (responseCode 429). 5. For client-side root-cause, the userAgent field reveals which integration (e.g. 'curl', 'python-meraki', 'TA-meraki/3.x') is misbehaving.

## Detailed Implementation

### Prerequisites
- Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
- Ensure the following data sources are available: Splunk_TA_cisco_meraki (Splunkbase #5580): API Requests History input (sourcetype=meraki:apirequestshistory, daily, TA v3+) for per-request log and API Requests Response Codes input (sourcetype=meraki:apirequestsresponsecodes, daily) for hourly response-code histograms..
- For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

### Step 1 — Configure data collection
1. Enable both API Requests History and API Requests Response Codes inputs in Splunk_TA_cisco_meraki (TA v3+). 2. The History input emits one event per individual API call with host, path (e.g. '/organizations/.../devices'), method, responseCode, sourceIp, userAgent, ts. 3. The Response Codes input gives aggregated counts per (responseCode, interval). 4. Threshold 4xx/5xx error rate >5% per endpoint to surface broken integrations or rate-limit hits (responseCode 429). 5. For client-side root-cau…

### Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=meraki sourcetype="meraki:apirequestshistory" earliest=-1h
| where responseCode >= 400
| stats count as error_count,
        values(responseCode) as response_codes,
        values(method) as http_methods
         by path, organizationId
| sort - error_count
| append [
    search index=meraki sourcetype="meraki:apirequestsresponsecodes" earliest=-24h
    | spath path=counts{} output=counts_arr
    | mvexpand counts_arr
    | spath input=counts_arr
    | where code >= 400
    | stats sum(count) as response_count by code, organizationId
    | sort - response_count
  ]
```

#### Understanding this SPL

**API Error Rate and Endpoint Health (Meraki)** — Network operations teams monitor Meraki Dashboard API error rates and response codes to detect credential failures, rate limiting, and cloud infrastructure issues that disrupt data collection.

Documented **Data sources**: Splunk_TA_cisco_meraki (Splunkbase #5580): API Requests History input (sourcetype=meraki:apirequestshistory, daily, TA v3+) for per-request log and API Requests Response Codes input (sourcetype=meraki:apirequestsresponsecodes, daily) for hourly response-code histograms. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: meraki; **sourcetype**: meraki:apirequestshistory. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

- Scopes the data: index=meraki, sourcetype="meraki:apirequestshistory", time bounds. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
- Filters the current rows with `where responseCode >= 400` — typically the threshold or rule expression for this monitoring goal.
- `stats` rolls up events into metrics; results are split **by path, organizationId** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
- Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
- Appends rows from a subsearch with `append`.


### Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

### Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: API error timeline; endpoint error breakdown; error rate gauge.

## SPL

```spl
index=meraki sourcetype="meraki:apirequestshistory" earliest=-1h
| where responseCode >= 400
| stats count as error_count,
        values(responseCode) as response_codes,
        values(method) as http_methods
         by path, organizationId
| sort - error_count
| append [
    search index=meraki sourcetype="meraki:apirequestsresponsecodes" earliest=-24h
    | spath path=counts{} output=counts_arr
    | mvexpand counts_arr
    | spath input=counts_arr
    | where code >= 400
    | stats sum(count) as response_count by code, organizationId
    | sort - response_count
  ]
```

## Visualization

API error timeline; endpoint error breakdown; error rate gauge.

## Known False Positives

Meraki 429 rate-limit responses and transient 5xx from the cloud are often environmental; back off and alert on error rate, not a single 500 line.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
