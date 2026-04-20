---
id: "5.8.14"
title: "Admin Activity Logging and Access Control Audit (Meraki)"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.8.14 · Admin Activity Logging and Access Control Audit (Meraki)

## Description

Tracks administrator actions and logins for compliance and security auditing.

## Value

Tracks administrator actions and logins for compliance and security auditing.

## Implementation

Enable admin audit logging. Ingest login and action events.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
• Ensure the following data sources are available: `sourcetype=meraki type=security_event signature="*admin*" OR signature="*login*"`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable admin audit logging. Ingest login and action events.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cisco_network sourcetype="meraki" type=security_event (signature="*admin*" OR signature="*login*")
| stats count as admin_action_count by admin_user, action_type, timestamp
| where admin_action_count > 0
```

Understanding this SPL

**Admin Activity Logging and Access Control Audit (Meraki)** — Tracks administrator actions and logins for compliance and security auditing.

Documented **Data sources**: `sourcetype=meraki type=security_event signature="*admin*" OR signature="*login*"`. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cisco_network; **sourcetype**: meraki. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=cisco_network, sourcetype="meraki". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by admin_user, action_type, timestamp** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where admin_action_count > 0` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Admin activity timeline; action type breakdown; user activity detail table.

## SPL

```spl
index=cisco_network sourcetype="meraki" type=security_event (signature="*admin*" OR signature="*login*")
| stats count as admin_action_count by admin_user, action_type, timestamp
| where admin_action_count > 0
```

## Visualization

Admin activity timeline; action type breakdown; user activity detail table.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
