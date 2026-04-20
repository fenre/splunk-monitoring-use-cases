---
id: "5.8.12"
title: "License Expiration Tracking and Renewal Alerts (Meraki)"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.8.12 · License Expiration Tracking and Renewal Alerts (Meraki)

## Description

Ensures licenses don't expire unexpectedly and features remain available.

## Value

Ensures licenses don't expire unexpectedly and features remain available.

## Implementation

Query organization API for license expiry. Alert on <90 days.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
• Ensure the following data sources are available: `sourcetype=meraki:api`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Query organization API for license expiry. Alert on <90 days.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cisco_network sourcetype="meraki:api" license_expiry=*
| eval days_until_expire=round((strptime(license_expiry, "%Y-%m-%d")-now())/86400, 0)
| stats latest(days_until_expire) as days_left, latest(license_expiry) as expiry_date by license_type, organization
| where days_left < 90
| sort days_left
```

Understanding this SPL

**License Expiration Tracking and Renewal Alerts (Meraki)** — Ensures licenses don't expire unexpectedly and features remain available.

Documented **Data sources**: `sourcetype=meraki:api`. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cisco_network; **sourcetype**: meraki:api. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=cisco_network, sourcetype="meraki:api". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **days_until_expire** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by license_type, organization** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where days_left < 90` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: License expiration countdown; renewal timeline; license detail table.

## SPL

```spl
index=cisco_network sourcetype="meraki:api" license_expiry=*
| eval days_until_expire=round((strptime(license_expiry, "%Y-%m-%d")-now())/86400, 0)
| stats latest(days_until_expire) as days_left, latest(license_expiry) as expiry_date by license_type, organization
| where days_left < 90
| sort days_left
```

## Visualization

License expiration countdown; renewal timeline; license detail table.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
