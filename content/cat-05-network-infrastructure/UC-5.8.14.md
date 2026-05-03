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

Enable admin audit logging. Ingest login and action events.

## Detailed Implementation

### Prerequisites
- Meraki Dashboard API providing admin activity logs via the organization change log endpoint. Data in `index=meraki` with `sourcetype=meraki:api:changelog` or `sourcetype=meraki:events`. The Meraki Change Log API (`GET /organizations/{orgId}/actionBatches` and `GET /organizations/{orgId}/configurationChanges`) returns all admin actions.
- Key fields: `adminName`/`adminEmail`, `networkName`, `ts` (timestamp), `page` (Meraki Dashboard page), `label` (action description), `oldValue`, `newValue`.

### Step 1 — Configure data collection
Verify admin activity log:
```spl
index=meraki (sourcetype="meraki:api:changelog" OR sourcetype="meraki:events") earliest=-24h
| stats count by adminName, page
| sort -count
```

### Step 2 — Create the search and alert

**Primary search — Admin activity audit:**
```spl
index=meraki (sourcetype="meraki:api:changelog" OR sourcetype="meraki:events") earliest=-24h
| eval admin=coalesce(adminName, adminEmail)
| stats count as actions dc(networkName) as networks_touched dc(page) as pages_touched values(page) as activity_areas first(_time) as first_action latest(_time) as last_action by admin
| eval active_hours=round((last_action - first_action)/3600, 1)
| sort -actions
```

#### Understanding this SPL: The Meraki change log captures every configuration change made through the dashboard or API. This provides complete audit visibility: who changed what, when, and what the old/new values were. Tracking actions per admin helps identify: (1) rogue changes (unauthorized admin), (2) bulk errors (admin making many changes quickly — possible mistake), (3) automation activity (API key making systematic changes).

**Sensitive configuration changes:**
```spl
index=meraki (sourcetype="meraki:api:changelog" OR sourcetype="meraki:events") earliest=-24h
| where match(page, "(?i)(firewall|security|vpn|admin|saml|snmp|syslog|api)")
| eval admin=coalesce(adminName, adminEmail)
| table _time, admin, networkName, page, label, oldValue, newValue
| sort -_time
```

**After-hours admin activity:**
```spl
index=meraki (sourcetype="meraki:api:changelog" OR sourcetype="meraki:events") earliest=-7d
| eval hour=strftime(_time, "%H")
| eval is_after_hours=if(hour < 7 OR hour > 19, 1, 0)
| where is_after_hours=1
| eval admin=coalesce(adminName, adminEmail)
| stats count as after_hours_actions by admin, networkName
| sort -after_hours_actions
```

### Step 3 — Validate
(a) Make a configuration change in Meraki Dashboard and verify it appears in Splunk within minutes.
(b) Compare admin activity in Splunk with Meraki Dashboard: Organization > Change log.
(c) Verify all admin accounts are accounted for in the activity audit.

### Step 4 — Operationalize
Dashboard ("Meraki Admin Activity"):
- Row 1 — Single-value tiles: "Active admins (24h)", "Total changes", "Security changes", "After-hours changes".
- Row 2 — Admin activity table: admin, actions, networks touched, activity areas.
- Row 3 — Sensitive change log: firewall, VPN, admin, security changes with old/new values.
- Row 4 — After-hours activity: admin, network, change count.

Alerting:
- High (security-related change outside change window): investigate immediately.
- Warning (after-hours admin activity > 5 changes): verify legitimacy.
- Info (new admin account activity): first-time admin making changes.

### Step 5 — Troubleshooting

- **Change log data gaps** — The Meraki change log API has pagination limits. Ensure the TA polls frequently enough to capture all changes. Increase polling frequency for large organizations.

- **adminName shows as email** — Some Meraki API versions return email instead of display name. Use both fields with `coalesce`.

- **API-driven changes show generic admin** — Changes made via API show the API key owner, not the script that invoked it. Tag API keys with descriptive names in Meraki Dashboard.

## SPL

```spl
index=cisco_network sourcetype="meraki" type=security_event (signature="*admin*" OR signature="*login*")
| stats count as admin_action_count by admin_user, action_type, timestamp
| where admin_action_count > 0
```

## Visualization

Admin activity timeline; action type breakdown; user activity detail table.

## Known False Positives

Help-desk and automation accounts that log in often can look like noise; focus on new IPs, new admins, and after-hours use against policy.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
