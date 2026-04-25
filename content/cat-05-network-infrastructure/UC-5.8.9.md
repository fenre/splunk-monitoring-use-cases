<!-- AUTO-GENERATED from UC-5.8.9.json — DO NOT EDIT -->

---
id: "5.8.9"
title: "SSL/TLS Certificate Expiration Tracking (Meraki)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.8.9 · SSL/TLS Certificate Expiration Tracking (Meraki)

## Description

Monitors SSL certificate expiration dates on all network devices to prevent outages.

## Value

Monitors SSL certificate expiration dates on all network devices to prevent outages.

## Implementation

Query device API for certificate expiry dates. Alert on <30 days.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
• Ensure the following data sources are available: `sourcetype=meraki:api`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Query device API for certificate expiry dates. Alert on <30 days.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cisco_network sourcetype="meraki:api" certificate_expiry=*
| eval days_until_expiry=round((strptime(certificate_expiry, "%Y-%m-%d")-now())/86400, 0)
| where days_until_expiry < 30
| stats latest(days_until_expiry) as days_left by device_name, device_type
| sort days_left
```

Understanding this SPL

**SSL/TLS Certificate Expiration Tracking (Meraki)** — Monitors SSL certificate expiration dates on all network devices to prevent outages.

Documented **Data sources**: `sourcetype=meraki:api`. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cisco_network; **sourcetype**: meraki:api. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=cisco_network, sourcetype="meraki:api". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **days_until_expiry** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where days_until_expiry < 30` — typically the threshold or rule expression for this monitoring goal.
• `stats` rolls up events into metrics; results are split **by device_name, device_type** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
In Meraki Dashboard, open the same organization or network, compare the metric (status, event feed, or admin log) to the Splunk result, and confirm the TA’s API key, org ID, and optional syslog reach the same index and sourcetype you used in the search.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Expiration countdown gauge; timeline of expiring certs; alert table.

## SPL

```spl
index=cisco_network sourcetype="meraki:api" certificate_expiry=*
| eval days_until_expiry=round((strptime(certificate_expiry, "%Y-%m-%d")-now())/86400, 0)
| where days_until_expiry < 30
| stats latest(days_until_expiry) as days_left by device_name, device_type
| sort days_left
```

## Visualization

Expiration countdown gauge; timeline of expiring certs; alert table.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
