<!-- AUTO-GENERATED from UC-5.8.14.json — DO NOT EDIT -->

---
id: "5.8.14"
title: "Admin Activity Logging and Access Control Audit (Meraki)"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.8.14 · Admin Activity Logging and Access Control Audit (Meraki)

> **Criticality:** Critical &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Compliance

*We help you see who does what in the Meraki admin console, which matters when you need to show who changed a critical setting.*

---

## Description

Tracks administrator actions and logins for compliance and security auditing.

## Value

Network operations teams audit Meraki administrator activity for compliance, detecting sensitive configuration changes, after-hours modifications, and unauthorized admin actions across all networks and organizations.

## Implementation

1. Enable the Audit input in Splunk_TA_cisco_meraki. The TA polls GET /organizations/{orgId}/configurationChanges daily (configurable to as low as 6 minutes) and emits one event per admin action with adminName, page, label, action, networkName, ssidNumber, ts, and the JSON oldValue / newValue. 2. Group by adminName for per-admin activity dashboards. 3. For privileged-admin / orphaned-admin detection, lookup adminName against your IDM and flag orphans.

## Detailed Implementation

### Prerequisites
- Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
- Ensure the following data sources are available: Splunk_TA_cisco_meraki (Splunkbase #5580): Audit input (sourcetype=meraki:audit, daily polling of GET /organizations/{orgId}/configurationChanges, OAuth scope dashboard:general:config:read). NOTE: admin activity is NOT in Meraki syslog — it is only available via the Audit input..
- For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

### Step 1 — Configure data collection
1. Enable the Audit input in Splunk_TA_cisco_meraki. The TA polls GET /organizations/{orgId}/configurationChanges daily (configurable to as low as 6 minutes) and emits one event per admin action with adminName, page, label, action, networkName, ssidNumber, ts, and the JSON oldValue / newValue. 2. Group by adminName for per-admin activity dashboards. 3. For privileged-admin / orphaned-admin detection, lookup adminName against your IDM and flag orphans.

### Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=meraki sourcetype="meraki:audit" earliest=-7d
| stats count as admin_action_count,
        values(action) as actions,
        values(page) as pages,
        values(label) as targets,
        earliest(_time) as first_action,
        latest(_time) as last_action
         by adminName, organizationId
| where admin_action_count > 0
| sort - admin_action_count
```

#### Understanding this SPL

**Admin Activity Logging and Access Control Audit (Meraki)** — Network operations teams audit Meraki administrator activity for compliance, detecting sensitive configuration changes, after-hours modifications, and unauthorized admin actions across all networks and organizations.

Documented **Data sources**: Splunk_TA_cisco_meraki (Splunkbase #5580): Audit input (sourcetype=meraki:audit, daily polling of GET /organizations/{orgId}/configurationChanges, OAuth scope dashboard:general:config:read). NOTE: admin activity is NOT in Meraki syslog — it is only available via the Audit input. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: meraki; **sourcetype**: meraki:audit. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

- Scopes the data: index=meraki, sourcetype="meraki:audit", time bounds. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
- `stats` rolls up events into metrics; results are split **by adminName, organizationId** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
- Filters the current rows with `where admin_action_count > 0` — typically the threshold or rule expression for this monitoring goal.
- Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


### Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

### Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Admin activity timeline; action type breakdown; user activity detail table.

## SPL

```spl
index=meraki sourcetype="meraki:audit" earliest=-7d
| stats count as admin_action_count,
        values(action) as actions,
        values(page) as pages,
        values(label) as targets,
        earliest(_time) as first_action,
        latest(_time) as last_action
         by adminName, organizationId
| where admin_action_count > 0
| sort - admin_action_count
```

## Visualization

Admin activity timeline; action type breakdown; user activity detail table.

## Known False Positives

Help-desk and automation accounts that log in often can look like noise; focus on new IPs, new admins, and after-hours use against policy.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
