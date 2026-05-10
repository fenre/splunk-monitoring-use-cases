<!-- AUTO-GENERATED from UC-9.6.4.json — DO NOT EDIT -->

---
id: "9.6.4"
title: "Mobile Security Policy Violations and App Restrictions"
criticality: "high"
splunkPillar: "Security"
---

# UC-9.6.4 · Mobile Security Policy Violations and App Restrictions

> **Criticality:** High &middot; **Difficulty:** Beginner &middot; **Pillar:** Security &middot; **Type:** Security

*We use identity and sign-in data in Splunk so we can notice unusual logins, access changes, and privileged use while it still matters — Mobile Security Policy Violations and App Restrictions*

---

## Description

Detects policy violations and restricted app usage attempts.

## Value

Detects policy violations and restricted app usage attempts.

## Implementation

Meraki SM exposes app-inventory changes via webhook events. Configure either `cisco_meraki_webhook` (HEC) or `cisco_meraki_webhook_logs` (polled) input and subscribe to SM app alerts. Maintain an app allow-list lookup (`approved_mobile_apps.csv`) and join here to flag installations of unapproved apps.

## Detailed Implementation

### Prerequisites
- Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
- Ensure the following data sources are available: `index=meraki sourcetype=meraki:webhook` (HEC) or `meraki:webhooklogs:api` (polled) in `Splunk_TA_cisco_meraki` (Splunkbase 5580). Subscribe to SM app-installation / uninstall / unauthorized-app webhook events..
- For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

### Step 1 — Configure data collection
Meraki SM exposes app-inventory changes via webhook events. Configure either `cisco_meraki_webhook` (HEC) or `cisco_meraki_webhook_logs` (polled) input and subscribe to SM app alerts. Maintain an app allow-list lookup (`approved_mobile_apps.csv`) and join here to flag installations of unapproved apps.

### Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=meraki sourcetype IN ("meraki:webhook","meraki:webhooklogs:api") (alertTypeId="sm_app_install" OR alertTypeId="sm_unauthorized_app" OR like(alertType, "%app%"))
| spath
| eval app_name=coalesce('alertData.appName', 'data.appName', appName)
| eval action=case(like(alertType, "%install%"), "installed", like(alertType, "%uninstall%"), "uninstalled", like(alertType, "%unauthorized%"), "unauthorized", true(), alertType)
| where isnotnull(app_name)
| stats count as events by app_name, action, networkName
| sort - events
```

#### Understanding this SPL

**Mobile Security Policy Violations and App Restrictions** — Detects policy violations and restricted app usage attempts.

Documented **Data sources**: `index=meraki sourcetype=meraki:webhook` (HEC) or `meraki:webhooklogs:api` (polled) in `Splunk_TA_cisco_meraki` (Splunkbase 5580). Subscribe to SM app-installation / uninstall / unauthorized-app webhook events. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: meraki.

**Pipeline walkthrough**

- Scopes the data: index=meraki. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
- Extracts structured paths (JSON/XML) with `spath`.
- `eval` defines or adjusts **app_name** — often to normalize units, derive a ratio, or prepare for thresholds.
- `eval` defines or adjusts **action** — often to normalize units, derive a ratio, or prepare for thresholds.
- Filters the current rows with `where isnotnull(app_name)` — typically the threshold or rule expression for this monitoring goal.
- `stats` rolls up events into metrics; results are split **by app_name, action, networkName** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
- Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


### Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

### Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Policy violation timeline; violation type breakdown; affected device list.

## SPL

```spl
index=meraki sourcetype IN ("meraki:webhook","meraki:webhooklogs:api") (alertTypeId="sm_app_install" OR alertTypeId="sm_unauthorized_app" OR like(alertType, "%app%"))
| spath
| eval app_name=coalesce('alertData.appName', 'data.appName', appName)
| eval action=case(like(alertType, "%install%"), "installed", like(alertType, "%uninstall%"), "uninstalled", like(alertType, "%unauthorized%"), "unauthorized", true(), alertType)
| where isnotnull(app_name)
| stats count as events by app_name, action, networkName
| sort - events
```

## Visualization

Policy violation timeline; violation type breakdown; affected device list.

## Known False Positives

Planned policy rollouts, pilot tenants, and emergency relaxations for incidents; require change tickets for production changes.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
