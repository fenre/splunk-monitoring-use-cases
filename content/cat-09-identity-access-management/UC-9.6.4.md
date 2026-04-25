<!-- AUTO-GENERATED from UC-9.6.4.json — DO NOT EDIT -->

---
id: "9.6.4"
title: "Mobile Security Policy Violations and App Restrictions"
criticality: "high"
splunkPillar: "Security"
---

# UC-9.6.4 · Mobile Security Policy Violations and App Restrictions

## Description

Detects policy violations and restricted app usage attempts.

## Value

Detects policy violations and restricted app usage attempts.

## Implementation

Monitor security policy violation events. Alert on repeated violations.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
• Ensure the following data sources are available: `sourcetype=meraki type=security_event signature="*policy*" OR signature="*app*"`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Monitor security policy violation events. Alert on repeated violations.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cisco_network sourcetype="meraki" type=security_event (signature="*policy*" OR signature="*app*") violation="true"
| stats count as violation_count by device_id, policy_name, violation_type
| where violation_count > 5
```

Understanding this SPL

**Mobile Security Policy Violations and App Restrictions** — Detects policy violations and restricted app usage attempts.

Documented **Data sources**: `sourcetype=meraki type=security_event signature="*policy*" OR signature="*app*"`. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cisco_network; **sourcetype**: meraki. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=cisco_network, sourcetype="meraki". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by device_id, policy_name, violation_type** so each row reflects one combination of those dimensions.
• Filters the current rows with `where violation_count > 5` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Compare with the Meraki Systems Manager or device inventory UI for the same devices and policy state.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Policy violation timeline; violation type breakdown; affected device list.

## SPL

```spl
index=cisco_network sourcetype="meraki" type=security_event (signature="*policy*" OR signature="*app*") violation="true"
| stats count as violation_count by device_id, policy_name, violation_type
| where violation_count > 5
```

## Visualization

Policy violation timeline; violation type breakdown; affected device list.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
