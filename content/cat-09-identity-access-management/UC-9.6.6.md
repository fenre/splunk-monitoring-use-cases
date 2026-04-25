<!-- AUTO-GENERATED from UC-9.6.6.json — DO NOT EDIT -->

---
id: "9.6.6"
title: "Mobile App Deployment Success Rate and Distribution Status"
criticality: "medium"
splunkPillar: "Security"
---

# UC-9.6.6 · Mobile App Deployment Success Rate and Distribution Status

## Description

Tracks app deployment success and identifies devices with failed or incomplete deployments.

## Value

Tracks app deployment success and identifies devices with failed or incomplete deployments.

## Implementation

Monitor app deployment status events. Alert on low success rates.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
• Ensure the following data sources are available: `sourcetype=meraki type=security_event signature="*app*deployment*"`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Monitor app deployment status events. Alert on low success rates.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cisco_network sourcetype="meraki" type=security_event signature="*app*deployment*"
| stats count as deployment_count, count(eval(status="success")) as success_count, count(eval(status="failed")) as failed_count by app_name
| eval success_rate=round(success_count*100/deployment_count, 2)
| where success_rate < 95
```

Understanding this SPL

**Mobile App Deployment Success Rate and Distribution Status** — Tracks app deployment success and identifies devices with failed or incomplete deployments.

Documented **Data sources**: `sourcetype=meraki type=security_event signature="*app*deployment*"`. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cisco_network; **sourcetype**: meraki. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=cisco_network, sourcetype="meraki". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by app_name** so each row reflects one combination of those dimensions.
• `eval` defines or adjusts **success_rate** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where success_rate < 95` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Compare with the Meraki Systems Manager or device inventory UI for the same devices and policy state.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Deployment success rate gauge; app deployment timeline; failure detail table.

## SPL

```spl
index=cisco_network sourcetype="meraki" type=security_event signature="*app*deployment*"
| stats count as deployment_count, count(eval(status="success")) as success_count, count(eval(status="failed")) as failed_count by app_name
| eval success_rate=round(success_count*100/deployment_count, 2)
| where success_rate < 95
```

## Visualization

Deployment success rate gauge; app deployment timeline; failure detail table.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
