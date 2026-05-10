<!-- AUTO-GENERATED from UC-9.6.6.json — DO NOT EDIT -->

---
id: "9.6.6"
title: "Mobile App Deployment Success Rate and Distribution Status"
criticality: "medium"
splunkPillar: "Security"
---

# UC-9.6.6 · Mobile App Deployment Success Rate and Distribution Status

> **Criticality:** Medium &middot; **Difficulty:** Beginner &middot; **Pillar:** Security &middot; **Type:** Availability

*We use identity and sign-in data in Splunk so we can notice unusual logins, access changes, and privileged use while it still matters — Mobile App Deployment Success Rate and Distribution Status*

---

## Description

Tracks app deployment success and identifies devices with failed or incomplete deployments.

## Value

Tracks app deployment success and identifies devices with failed or incomplete deployments.

## Implementation

Meraki SM app-deployment outcomes are delivered via webhook. Configure either `cisco_meraki_webhook` (HEC) or `cisco_meraki_webhook_logs` (polled) input and subscribe to SM app-deployment alerts in the Dashboard. A success_rate below 95% on a given app usually means a payload/profile/dependency issue — re-test deployment in a pilot ring before re-pushing org-wide.

## Detailed Implementation

### Prerequisites
- Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
- Ensure the following data sources are available: `index=meraki sourcetype=meraki:webhook` (HEC) or `meraki:webhooklogs:api` (polled) in `Splunk_TA_cisco_meraki` (Splunkbase 5580). Subscribe to SM app-deployment webhook events..
- For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

### Step 1 — Configure data collection
Meraki SM app-deployment outcomes are delivered via webhook. Configure either `cisco_meraki_webhook` (HEC) or `cisco_meraki_webhook_logs` (polled) input and subscribe to SM app-deployment alerts in the Dashboard. A success_rate below 95% on a given app usually means a payload/profile/dependency issue — re-test deployment in a pilot ring before re-pushing org-wide.

### Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=meraki sourcetype IN ("meraki:webhook","meraki:webhooklogs:api") (alertTypeId="sm_app_deployment" OR like(alertType, "%deploy%") OR like(alertType, "%app_install%"))
| spath
| eval app_name=coalesce('alertData.appName', 'data.appName', appName)
| eval status=coalesce('alertData.status', 'data.status', status)
| stats count as deployments, count(eval(status="success" OR status="installed")) as success_count, count(eval(status="failed" OR status="error")) as failed_count by app_name
| eval success_rate=round(success_count*100/deployments, 2)
| where success_rate < 95 OR failed_count > 0
| sort success_rate
```

#### Understanding this SPL

**Mobile App Deployment Success Rate and Distribution Status** — Tracks app deployment success and identifies devices with failed or incomplete deployments.

Documented **Data sources**: `index=meraki sourcetype=meraki:webhook` (HEC) or `meraki:webhooklogs:api` (polled) in `Splunk_TA_cisco_meraki` (Splunkbase 5580). Subscribe to SM app-deployment webhook events. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: meraki.

**Pipeline walkthrough**

- Scopes the data: index=meraki. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
- Extracts structured paths (JSON/XML) with `spath`.
- `eval` defines or adjusts **app_name** — often to normalize units, derive a ratio, or prepare for thresholds.
- `eval` defines or adjusts **status** — often to normalize units, derive a ratio, or prepare for thresholds.
- `stats` rolls up events into metrics; results are split **by app_name** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
- `eval` defines or adjusts **success_rate** — often to normalize units, derive a ratio, or prepare for thresholds.
- Filters the current rows with `where success_rate < 95 OR failed_count > 0` — typically the threshold or rule expression for this monitoring goal.
- Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


### Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

### Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Deployment success rate gauge; app deployment timeline; failure detail table.

## SPL

```spl
index=meraki sourcetype IN ("meraki:webhook","meraki:webhooklogs:api") (alertTypeId="sm_app_deployment" OR like(alertType, "%deploy%") OR like(alertType, "%app_install%"))
| spath
| eval app_name=coalesce('alertData.appName', 'data.appName', appName)
| eval status=coalesce('alertData.status', 'data.status', status)
| stats count as deployments, count(eval(status="success" OR status="installed")) as success_count, count(eval(status="failed" OR status="error")) as failed_count by app_name
| eval success_rate=round(success_count*100/deployments, 2)
| where success_rate < 95 OR failed_count > 0
| sort success_rate
```

## Visualization

Deployment success rate gauge; app deployment timeline; failure detail table.

## Known False Positives

Planned change windows, maintenance, approved automation, and known good service accounts; correlate with change tickets and identity team communication.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
