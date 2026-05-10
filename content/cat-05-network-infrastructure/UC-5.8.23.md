<!-- AUTO-GENERATED from UC-5.8.23.json — DO NOT EDIT -->

---
id: "5.8.23"
title: "Dashboard Configuration and Export Backup (Meraki)"
criticality: "low"
splunkPillar: "Observability"
---

# UC-5.8.23 · Dashboard Configuration and Export Backup (Meraki)

> **Criticality:** Low &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Compliance

*We help you back up and track Meraki dashboard exports, so a bad change does not erase a good layout when you need it most.*

---

## Description

Tracks dashboard configuration backups to enable disaster recovery and configuration review.

## Value

Network operations teams maintain indexed Meraki configuration backups in Splunk for disaster recovery, audit compliance, and configuration drift detection across all networks and configuration sections.

## Implementation

1. Enable the Audit input in Splunk_TA_cisco_meraki. 2. Filter audit entries for configuration export / template backup activity. 3. The query identifies organizations or networks where no backup-related admin action has happened in the last 30 days. 4. For an automated backup, run a scheduled script that calls GET /networks/{networkId}/appliance/firewall/l3FirewallRules, /wireless/ssids, /switch/accessPolicies etc. and stores the output in version control. The Audit input gives you visibility into manual exports performed via the Meraki Dashboard UI.

## Detailed Implementation

### Prerequisites
- Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
- Ensure the following data sources are available: Splunk_TA_cisco_meraki (Splunkbase #5580): Audit input (sourcetype=meraki:audit, daily). NOTE: the Meraki Dashboard does not provide a native 'config backup' API endpoint; backups are typically performed by exporting GET /networks/{networkId}/configTemplates and per-product config endpoints via a custom script. The audit log records when an admin performs these actions..
- For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

### Step 1 — Configure data collection
1. Enable the Audit input in Splunk_TA_cisco_meraki. 2. Filter audit entries for configuration export / template backup activity. 3. The query identifies organizations or networks where no backup-related admin action has happened in the last 30 days. 4. For an automated backup, run a scheduled script that calls GET /networks/{networkId}/appliance/firewall/l3FirewallRules, /wireless/ssids, /switch/accessPolicies etc. and stores the output in version control. The Audit input gives you visibility i…

### Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=meraki sourcetype="meraki:audit" earliest=-30d
    (page="Backup" OR label="*backup*" OR action="*backup*"
     OR page="Configuration sync" OR label="*export*")
| stats latest(_time) as last_action,
        values(adminName) as performed_by,
        values(label) as actions
         by organizationName, networkName
| eval days_since_last = round((now() - last_action)/86400, 0)
| where isnull(last_action) OR days_since_last > 30
| sort - days_since_last
```

#### Understanding this SPL

**Dashboard Configuration and Export Backup (Meraki)** — Network operations teams maintain indexed Meraki configuration backups in Splunk for disaster recovery, audit compliance, and configuration drift detection across all networks and configuration sections.

Documented **Data sources**: Splunk_TA_cisco_meraki (Splunkbase #5580): Audit input (sourcetype=meraki:audit, daily). NOTE: the Meraki Dashboard does not provide a native 'config backup' API endpoint; backups are typically performed by exporting GET /networks/{networkId}/configTemplates and per-product config endpoints via a custom script. The audit log records when an admin performs these actions. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: meraki; **sourcetype**: meraki:audit. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

- Scopes the data: index=meraki, sourcetype="meraki:audit", time bounds. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
- `stats` rolls up events into metrics; results are split **by organizationName, networkName** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
- `eval` defines or adjusts **days_since_last** — often to normalize units, derive a ratio, or prepare for thresholds.
- Filters the current rows with `where isnull(last_action) OR days_since_last > 30` — typically the threshold or rule expression for this monitoring goal.
- Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


### Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

### Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Last backup timestamp by org; backup recency gauge; backup history timeline.

## SPL

```spl
index=meraki sourcetype="meraki:audit" earliest=-30d
    (page="Backup" OR label="*backup*" OR action="*backup*"
     OR page="Configuration sync" OR label="*export*")
| stats latest(_time) as last_action,
        values(adminName) as performed_by,
        values(label) as actions
         by organizationName, networkName
| eval days_since_last = round((now() - last_action)/86400, 0)
| where isnull(last_action) OR days_since_last > 30
| sort - days_since_last
```

## Visualization

Last backup timestamp by org; backup recency gauge; backup history timeline.

## Known False Positives

Exports before big dashboard edits look like noise; only alert when backup is missing for longer than the scheduled export interval.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
