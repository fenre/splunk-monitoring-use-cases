---
id: "5.8.22"
title: "API Error Rate and Endpoint Health (Meraki)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.8.22 · API Error Rate and Endpoint Health (Meraki)

## Description

Monitors API endpoint health and error rates to ensure automation reliability.

## Value

Monitors API endpoint health and error rates to ensure automation reliability.

## Implementation

Log API responses with status codes. Alert on error rate threshold.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
• Ensure the following data sources are available: `sourcetype=meraki:api (http_status_code=4* OR http_status_code=5*)`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Log API responses with status codes. Alert on error rate threshold.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cisco_network sourcetype="meraki:api:*" (http_status_code=4* OR http_status_code=5*)
| stats count as error_count, values(http_status_code) as status_codes by endpoint, method
| eval error_rate=round(error_count*100/total_requests, 2)
| where error_rate > 5
```

Understanding this SPL

**API Error Rate and Endpoint Health (Meraki)** — Monitors API endpoint health and error rates to ensure automation reliability.

Documented **Data sources**: `sourcetype=meraki:api (http_status_code=4* OR http_status_code=5*)`. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cisco_network; **sourcetype**: meraki:api:*. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=cisco_network, sourcetype="meraki:api:*". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by endpoint, method** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **error_rate** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where error_rate > 5` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: API error timeline; endpoint error breakdown; error rate gauge.

## SPL

```spl
index=cisco_network sourcetype="meraki:api:*" (http_status_code=4* OR http_status_code=5*)
| stats count as error_count, values(http_status_code) as status_codes by endpoint, method
| eval error_rate=round(error_count*100/total_requests, 2)
| where error_rate > 5
```

## Visualization

API error timeline; endpoint error breakdown; error rate gauge.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
