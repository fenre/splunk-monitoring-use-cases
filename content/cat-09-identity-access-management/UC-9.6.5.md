<!-- AUTO-GENERATED from UC-9.6.5.json — DO NOT EDIT -->

---
id: "9.6.5"
title: "Lost Mode Device Activation and Recovery Tracking"
criticality: "high"
splunkPillar: "Security"
---

# UC-9.6.5 · Lost Mode Device Activation and Recovery Tracking

## Description

Tracks activation of lost mode on devices to ensure recovery protocols are working.

## Value

Tracks activation of lost mode on devices to ensure recovery protocols are working.

## Implementation

Monitor lost mode activation events. Track recovery time.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
• Ensure the following data sources are available: `sourcetype=meraki type=security_event signature="*lost mode*"`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Monitor lost mode activation events. Track recovery time.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cisco_network sourcetype="meraki" type=security_event signature="*lost mode*"
| stats count as lost_mode_count, latest(timestamp) as last_activation by device_id, activation_reason
```

Understanding this SPL

**Lost Mode Device Activation and Recovery Tracking** — Tracks activation of lost mode on devices to ensure recovery protocols are working.

Documented **Data sources**: `sourcetype=meraki type=security_event signature="*lost mode*"`. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cisco_network; **sourcetype**: meraki. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=cisco_network, sourcetype="meraki". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by device_id, activation_reason** so each row reflects one combination of those dimensions.


Step 3 — Validate
Compare with the Meraki Systems Manager or device inventory UI for the same devices and policy state.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Lost mode event timeline; affected device table; recovery status dashboard.

## SPL

```spl
index=cisco_network sourcetype="meraki" type=security_event signature="*lost mode*"
| stats count as lost_mode_count, latest(timestamp) as last_activation by device_id, activation_reason
```

## Visualization

Lost mode event timeline; affected device table; recovery status dashboard.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
