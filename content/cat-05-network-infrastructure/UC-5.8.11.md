---
id: "5.8.11"
title: "API Call Rate Monitoring and Rate Limit Alerts (Meraki)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.8.11 · API Call Rate Monitoring and Rate Limit Alerts (Meraki)

## Description

Monitors API usage to prevent rate limit hits and optimize automation efficiency.

## Value

Monitors API usage to prevent rate limit hits and optimize automation efficiency.

## Implementation

Log all API calls with timestamps. Monitor call rate by endpoint.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
• Ensure the following data sources are available: `sourcetype=meraki:api`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Log all API calls with timestamps. Monitor call rate by endpoint.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cisco_network sourcetype="meraki:api:*"
| timechart count as api_calls by source, endpoint
| eval call_rate=api_calls/60
| where call_rate > 9
```

Understanding this SPL

**API Call Rate Monitoring and Rate Limit Alerts (Meraki)** — Monitors API usage to prevent rate limit hits and optimize automation efficiency.

Documented **Data sources**: `sourcetype=meraki:api`. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cisco_network; **sourcetype**: meraki:api:*. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=cisco_network, sourcetype="meraki:api:*". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time with a separate series **by source, endpoint** — ideal for trending and alerting on this use case.
• `eval` defines or adjusts **call_rate** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where call_rate > 9` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: API call timeline; rate limit gauge; endpoint usage breakdown.

## SPL

```spl
index=cisco_network sourcetype="meraki:api:*"
| timechart count as api_calls by source, endpoint
| eval call_rate=api_calls/60
| where call_rate > 9
```

## Visualization

API call timeline; rate limit gauge; endpoint usage breakdown.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
