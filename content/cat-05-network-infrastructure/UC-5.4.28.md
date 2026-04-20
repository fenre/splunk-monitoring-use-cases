---
id: "5.4.28"
title: "AP Uptime and Availability Monitoring (Meraki MR)"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.4.28 · AP Uptime and Availability Monitoring (Meraki MR)

## Description

Ensures all access points are online and operational; alerts on unexpected AP outages.

## Value

Ensures all access points are online and operational; alerts on unexpected AP outages.

## Implementation

Monitor device status API for all MR devices. Alert on status="offline".

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
• Ensure the following data sources are available: `sourcetype=meraki:api device_type=MR`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Monitor device status API for all MR devices. Alert on status="offline".

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cisco_network sourcetype="meraki:api" device_type=MR
| stats latest(status) as ap_status, latest(last_status_change) as last_change by ap_name, ap_mac
| where ap_status="offline"
```

Understanding this SPL

**AP Uptime and Availability Monitoring (Meraki MR)** — Ensures all access points are online and operational; alerts on unexpected AP outages.

Documented **Data sources**: `sourcetype=meraki:api device_type=MR`. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cisco_network; **sourcetype**: meraki:api. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=cisco_network, sourcetype="meraki:api". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by ap_name, ap_mac** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where ap_status="offline"` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Status table with last seen time; uptime percentage gauge; event alert dashboard.

## SPL

```spl
index=cisco_network sourcetype="meraki:api" device_type=MR
| stats latest(status) as ap_status, latest(last_status_change) as last_change by ap_name, ap_mac
| where ap_status="offline"
```

## Visualization

Status table with last seen time; uptime percentage gauge; event alert dashboard.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
