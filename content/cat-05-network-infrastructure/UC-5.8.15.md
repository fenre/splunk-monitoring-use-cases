<!-- AUTO-GENERATED from UC-5.8.15.json — DO NOT EDIT -->

---
id: "5.8.15"
title: "Admin Privilege Changes and Permission Escalation (Meraki)"
criticality: "critical"
splunkPillar: "Security"
---

# UC-5.8.15 · Admin Privilege Changes and Permission Escalation (Meraki)

> **Criticality:** Critical &middot; **Difficulty:** Beginner &middot; **Pillar:** Security &middot; **Type:** Security

*We help you see when someone’s Meraki rights jump up in a way that should not happen, so small mistakes or misuse do not go unnoticed.*

---

## Description

Detects unauthorized privilege changes and permission escalation attempts.

## Value

Security operations teams detect Meraki administrator privilege escalation events, new admin account creation, and role changes to prevent unauthorized access and maintain least-privilege compliance across the Meraki organization.

## Implementation

1. Enable the Audit input in Splunk_TA_cisco_meraki. 2. Filter on the Administrators / Permissions pages to surface privilege escalations. 3. The audit event includes oldValue / newValue carrying the previous and new role JSON blob — useful for forensic detail. 4. Trigger a high-priority alert on every privilege change; pair with your IDM for change-control validation.

## Detailed Implementation

### Prerequisites
- Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
- Ensure the following data sources are available: Splunk_TA_cisco_meraki (Splunkbase #5580): Audit input (sourcetype=meraki:audit). Admin role / permission changes show up under page='Administrators' or page='Permissions'..
- For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

### Step 1 — Configure data collection
1. Enable the Audit input in Splunk_TA_cisco_meraki. 2. Filter on the Administrators / Permissions pages to surface privilege escalations. 3. The audit event includes oldValue / newValue carrying the previous and new role JSON blob — useful for forensic detail. 4. Trigger a high-priority alert on every privilege change; pair with your IDM for change-control validation.

### Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=meraki sourcetype="meraki:audit" earliest=-30d
    (page="Administrators" OR page="Permissions"
     OR label="*role*" OR label="*permission*" OR action="*admin*")
| stats count as priv_change_count,
        values(label) as targets,
        values(action) as actions,
        values(page) as pages,
        latest(_time) as last_change
         by adminName, organizationId
| sort - last_change
```

#### Understanding this SPL

**Admin Privilege Changes and Permission Escalation (Meraki)** — Security operations teams detect Meraki administrator privilege escalation events, new admin account creation, and role changes to prevent unauthorized access and maintain least-privilege compliance across the Meraki organization.

Documented **Data sources**: Splunk_TA_cisco_meraki (Splunkbase #5580): Audit input (sourcetype=meraki:audit). Admin role / permission changes show up under page='Administrators' or page='Permissions'. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: meraki; **sourcetype**: meraki:audit. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

- Scopes the data: index=meraki, sourcetype="meraki:audit", time bounds. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
- `stats` rolls up events into metrics; results are split **by adminName, organizationId** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
- Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


### Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

### Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Privilege change timeline; role change audit table; escalation alert dashboard.

## SPL

```spl
index=meraki sourcetype="meraki:audit" earliest=-30d
    (page="Administrators" OR page="Permissions"
     OR label="*role*" OR label="*permission*" OR action="*admin*")
| stats count as priv_change_count,
        values(label) as targets,
        values(action) as actions,
        values(page) as pages,
        latest(_time) as last_change
         by adminName, organizationId
| sort - last_change
```

## Visualization

Privilege change timeline; role change audit table; escalation alert dashboard.

## Known False Positives

Role updates during onboarding or support escalations are often correct; require ticket correlation for privilege events.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
