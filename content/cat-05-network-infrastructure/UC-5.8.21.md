---
id: "5.8.21"
title: "Webhook Delivery Failure Tracking (Meraki)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.8.21 · Webhook Delivery Failure Tracking (Meraki)

## Description

Ensures webhook notifications reach integrations and alerts don't get lost.

## Value

Ensures webhook notifications reach integrations and alerts don't get lost.

## Implementation

Log webhook delivery attempts. Alert on sustained failures.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580, webhooks).
• Ensure the following data sources are available: `sourcetype=meraki:webhook status="failure" OR status="error"`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Log webhook delivery attempts. Alert on sustained failures.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cisco_network sourcetype="meraki:webhook" (status="failure" OR status="error")
| stats count as failure_count, latest(error_message) as last_error by webhook_id, organization
| where failure_count > 5
```

Understanding this SPL

**Webhook Delivery Failure Tracking (Meraki)** — Ensures webhook notifications reach integrations and alerts don't get lost.

Documented **Data sources**: `sourcetype=meraki:webhook status="failure" OR status="error"`. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580, webhooks). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cisco_network; **sourcetype**: meraki:webhook. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=cisco_network, sourcetype="meraki:webhook". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by webhook_id, organization** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where failure_count > 5` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Webhook failure timeline; failure cause breakdown; affected org list.

## SPL

```spl
index=cisco_network sourcetype="meraki:webhook" (status="failure" OR status="error")
| stats count as failure_count, latest(error_message) as last_error by webhook_id, organization
| where failure_count > 5
```

## Visualization

Webhook failure timeline; failure cause breakdown; affected org list.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
