---
id: "5.6.14"
title: "DNS Resolution Performance and Failures (Meraki)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.6.14 · DNS Resolution Performance and Failures (Meraki)

## Description

Monitors DNS query resolution times and failures to identify misconfiguration or server issues affecting user experience.

## Value

Monitors DNS query resolution times and failures to identify misconfiguration or server issues affecting user experience.

## Implementation

Extract DNS query timing from syslog events. Set SLA thresholds (e.g., <100ms average).

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
• Ensure the following data sources are available: `sourcetype=meraki type=security_event signature="*DNS*"`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Extract DNS query timing from syslog events. Set SLA thresholds (e.g., <100ms average).

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cisco_network sourcetype="meraki" type=security_event signature="*DNS*" resolution_time=*
| stats avg(resolution_time) as avg_dns_time, max(resolution_time) as max_dns_time, count by ap_name
| where avg_dns_time > 100
```

Understanding this SPL

**DNS Resolution Performance and Failures (Meraki)** — Monitors DNS query resolution times and failures to identify misconfiguration or server issues affecting user experience.

Documented **Data sources**: `sourcetype=meraki type=security_event signature="*DNS*"`. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cisco_network; **sourcetype**: meraki. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=cisco_network, sourcetype="meraki". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by ap_name** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where avg_dns_time > 100` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Gauge showing average DNS time; histogram of query times; slow query detail table.

## SPL

```spl
index=cisco_network sourcetype="meraki" type=security_event signature="*DNS*" resolution_time=*
| stats avg(resolution_time) as avg_dns_time, max(resolution_time) as max_dns_time, count by ap_name
| where avg_dns_time > 100
```

## Visualization

Gauge showing average DNS time; histogram of query times; slow query detail table.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
