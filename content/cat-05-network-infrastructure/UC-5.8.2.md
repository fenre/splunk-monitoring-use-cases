---
id: "5.8.2"
title: "Meraki Organization Monitoring"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.8.2 · Meraki Organization Monitoring

## Description

Tracks Meraki device status across all networks and organizations from a single pane.

## Value

Tracks Meraki device status across all networks and organizations from a single pane.

## Implementation

Configure Meraki API integration (API key + org ID). Poll device statuses. Forward syslog for events. Dashboard showing organization-wide health.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
• Ensure the following data sources are available: Meraki Dashboard API, syslog.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Configure Meraki API integration (API key + org ID). Poll device statuses. Forward syslog for events. Dashboard showing organization-wide health.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network sourcetype="meraki:api"
| stats count by network, status | eval is_offline=if(status="offline",1,0)
| where is_offline > 0
```

Understanding this SPL

**Meraki Organization Monitoring** — Tracks Meraki device status across all networks and organizations from a single pane.

Documented **Data sources**: Meraki Dashboard API, syslog. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: meraki:api. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype="meraki:api". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by network, status** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **is_offline** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where is_offline > 0` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Map (device locations), Table, Status grid, Single value (offline count).

## SPL

```spl
index=network sourcetype="meraki:api"
| stats count by network, status | eval is_offline=if(status="offline",1,0)
| where is_offline > 0
```

## Visualization

Map (device locations), Table, Status grid, Single value (offline count).

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
