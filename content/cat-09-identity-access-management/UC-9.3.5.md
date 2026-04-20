---
id: "9.3.5"
title: "IdP Availability Monitoring"
criticality: "critical"
splunkPillar: "Security"
---

# UC-9.3.5 · IdP Availability Monitoring

## Description

IdP outage blocks all SSO authentication across the organization. Rapid detection enables failover and communication.

## Value

IdP outage blocks all SSO authentication across the organization. Rapid detection enables failover and communication.

## Implementation

Set up synthetic HTTP checks against IdP login endpoints every minute. Track response time and availability. Alert on response time >5 seconds or any 5xx errors. Subscribe to vendor status page updates as secondary source.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Scripted input (HTTP check), `Splunk_TA_okta`.
• Ensure the following data sources are available: IdP status API, synthetic monitoring, Okta system health.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Set up synthetic HTTP checks against IdP login endpoints every minute. Track response time and availability. Alert on response time >5 seconds or any 5xx errors. Subscribe to vendor status page updates as secondary source.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=synthetic sourcetype="http_check" target="*.okta.com"
| timechart span=1m avg(response_time_ms) as rt, count(eval(status_code>=500)) as errors
| where rt > 5000 OR errors > 0
```

Understanding this SPL

**IdP Availability Monitoring** — IdP outage blocks all SSO authentication across the organization. Rapid detection enables failover and communication.

Documented **Data sources**: IdP status API, synthetic monitoring, Okta system health. **App/TA** (typical add-on context): Scripted input (HTTP check), `Splunk_TA_okta`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: synthetic; **sourcetype**: http_check. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=synthetic, sourcetype="http_check". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=1m** buckets — ideal for trending and alerting on this use case.
• Filters the current rows with `where rt > 5000 OR errors > 0` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Single value (IdP uptime %), Line chart (response time), Status indicator (available/degraded/down).

## SPL

```spl
index=synthetic sourcetype="http_check" target="*.okta.com"
| timechart span=1m avg(response_time_ms) as rt, count(eval(status_code>=500)) as errors
| where rt > 5000 OR errors > 0
```

## Visualization

Single value (IdP uptime %), Line chart (response time), Status indicator (available/degraded/down).

## Known False Positives

Administrative tasks, scheduled jobs or platform updates can match this pattern — correlate with change management, maintenance windows and user role before raising severity.

## References

- [Splunk_TA_okta](https://splunkbase.splunk.com/app/6553)
