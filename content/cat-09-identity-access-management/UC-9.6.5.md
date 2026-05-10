<!-- AUTO-GENERATED from UC-9.6.5.json — DO NOT EDIT -->

---
id: "9.6.5"
title: "Lost Mode Device Activation and Recovery Tracking"
criticality: "high"
splunkPillar: "Security"
---

# UC-9.6.5 · Lost Mode Device Activation and Recovery Tracking

> **Criticality:** High &middot; **Difficulty:** Beginner &middot; **Pillar:** Security &middot; **Type:** Performance

*We use identity and sign-in data in Splunk so we can notice unusual logins, access changes, and privileged use while it still matters — Lost Mode Device Activation and Recovery Tracking*

---

## Description

Tracks activation of lost mode on devices to ensure recovery protocols are working.

## Value

Tracks activation of lost mode on devices to ensure recovery protocols are working.

## Implementation

All Meraki SM remote actions (lock, wipe, retire) are admin-initiated and emit webhook events. Configure either `cisco_meraki_webhook` (HEC) or `cisco_meraki_webhook_logs` (polled) input and subscribe in the Dashboard. Cross-reference with `meraki:audit` (admin login source/IP) for full attribution. A burst of wipes from a single admin is a strong account-compromise signal.

## Detailed Implementation

### Prerequisites
- Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
- Ensure the following data sources are available: `index=meraki sourcetype=meraki:webhook` (HEC) or `meraki:webhooklogs:api` (polled) in `Splunk_TA_cisco_meraki` (Splunkbase 5580). Subscribe to SM remote-action webhook events (lock, wipe, retire)..
- For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

### Step 1 — Configure data collection
All Meraki SM remote actions (lock, wipe, retire) are admin-initiated and emit webhook events. Configure either `cisco_meraki_webhook` (HEC) or `cisco_meraki_webhook_logs` (polled) input and subscribe in the Dashboard. Cross-reference with `meraki:audit` (admin login source/IP) for full attribution. A burst of wipes from a single admin is a strong account-compromise signal.

### Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=meraki sourcetype IN ("meraki:webhook","meraki:webhooklogs:api") (alertTypeId="sm_remote_action" OR like(alertType, "%lock%") OR like(alertType, "%wipe%") OR like(alertType, "%retire%"))
| spath
| eval action=case(like(alertType, "%wipe%"), "wiped", like(alertType, "%lock%"), "locked", like(alertType, "%retire%"), "retired", true(), alertType)
| eval device_name=coalesce('alertData.deviceName', 'data.deviceName', deviceName)
| eval admin=coalesce('alertData.adminName', 'data.adminName', adminName)
| stats count as actions, latest(_time) as last_action by admin, action, device_name
| eval last_action_human=strftime(last_action, "%Y-%m-%d %H:%M:%S")
| sort - last_action
```

#### Understanding this SPL

**Lost Mode Device Activation and Recovery Tracking** — Tracks activation of lost mode on devices to ensure recovery protocols are working.

Documented **Data sources**: `index=meraki sourcetype=meraki:webhook` (HEC) or `meraki:webhooklogs:api` (polled) in `Splunk_TA_cisco_meraki` (Splunkbase 5580). Subscribe to SM remote-action webhook events (lock, wipe, retire). **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: meraki.

**Pipeline walkthrough**

- Scopes the data: index=meraki. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
- Extracts structured paths (JSON/XML) with `spath`.
- `eval` defines or adjusts **action** — often to normalize units, derive a ratio, or prepare for thresholds.
- `eval` defines or adjusts **device_name** — often to normalize units, derive a ratio, or prepare for thresholds.
- `eval` defines or adjusts **admin** — often to normalize units, derive a ratio, or prepare for thresholds.
- `stats` rolls up events into metrics; results are split **by admin, action, device_name** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
- `eval` defines or adjusts **last_action_human** — often to normalize units, derive a ratio, or prepare for thresholds.
- Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


### Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

### Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Lost mode event timeline; affected device table; recovery status dashboard.

## SPL

```spl
index=meraki sourcetype IN ("meraki:webhook","meraki:webhooklogs:api") (alertTypeId="sm_remote_action" OR like(alertType, "%lock%") OR like(alertType, "%wipe%") OR like(alertType, "%retire%"))
| spath
| eval action=case(like(alertType, "%wipe%"), "wiped", like(alertType, "%lock%"), "locked", like(alertType, "%retire%"), "retired", true(), alertType)
| eval device_name=coalesce('alertData.deviceName', 'data.deviceName', deviceName)
| eval admin=coalesce('alertData.adminName', 'data.adminName', adminName)
| stats count as actions, latest(_time) as last_action by admin, action, device_name
| eval last_action_human=strftime(last_action, "%Y-%m-%d %H:%M:%S")
| sort - last_action
```

## Visualization

Lost mode event timeline; affected device table; recovery status dashboard.

## Known False Positives

Planned change windows, maintenance, approved automation, and known good service accounts; correlate with change tickets and identity team communication.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
