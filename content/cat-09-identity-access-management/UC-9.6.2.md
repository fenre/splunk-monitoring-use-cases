<!-- AUTO-GENERATED from UC-9.6.2.json — DO NOT EDIT -->

---
id: "9.6.2"
title: "Mobile Device Enrollment and MDM Status Tracking"
criticality: "medium"
splunkPillar: "Security"
---

# UC-9.6.2 · Mobile Device Enrollment and MDM Status Tracking

> **Criticality:** Medium &middot; **Difficulty:** Beginner &middot; **Pillar:** Security &middot; **Type:** Security, Availability

*We use identity and sign-in data in Splunk so we can notice unusual logins, access changes, and privileged use while it still matters — Mobile Device Enrollment and MDM Status Tracking*

---

## Description

Tracks device enrollment status to ensure mobile device management coverage.

## Value

Tracks device enrollment status to ensure mobile device management coverage.

## Implementation

Meraki SM enrollment events are delivered via Meraki Dashboard webhooks. Configure either `cisco_meraki_webhook` (HEC, real-time) or `cisco_meraki_webhook_logs` (polled) input in `Splunk_TA_cisco_meraki` and add a webhook URL in the Dashboard. Subscribe to SM device enrollment alerts. Track unexpected un-enrollment as a potential MDM-evasion signal.

## Detailed Implementation

### Prerequisites
- Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
- Ensure the following data sources are available: `index=meraki sourcetype=meraki:webhook` (HEC) or `meraki:webhooklogs:api` (polled) in `Splunk_TA_cisco_meraki` (Splunkbase 5580). Subscribe to SM enrollment / un-enrollment webhook events..
- For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

### Step 1 — Configure data collection
Meraki SM enrollment events are delivered via Meraki Dashboard webhooks. Configure either `cisco_meraki_webhook` (HEC, real-time) or `cisco_meraki_webhook_logs` (polled) input in `Splunk_TA_cisco_meraki` and add a webhook URL in the Dashboard. Subscribe to SM device enrollment alerts. Track unexpected un-enrollment as a potential MDM-evasion signal.

### Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=meraki sourcetype IN ("meraki:webhook","meraki:webhooklogs:api") (alertTypeId="sm_enrollment" OR like(alertType, "%enrollment%") OR like(alertType, "%sm_device_added%") OR like(alertType, "%sm_device_removed%"))
| spath
| eval action=case(like(alertType, "%added%") OR like(alertType, "%enroll%"), "enrolled", like(alertType, "%removed%") OR like(alertType, "%unenroll%"), "unenrolled", true(), alertType)
| stats count as events, latest(_time) as last_event by networkName, action, alertType
| eval last_event_human=strftime(last_event, "%Y-%m-%d %H:%M:%S")
| sort - events
```

#### Understanding this SPL

**Mobile Device Enrollment and MDM Status Tracking** — Tracks device enrollment status to ensure mobile device management coverage.

Documented **Data sources**: `index=meraki sourcetype=meraki:webhook` (HEC) or `meraki:webhooklogs:api` (polled) in `Splunk_TA_cisco_meraki` (Splunkbase 5580). Subscribe to SM enrollment / un-enrollment webhook events. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: meraki.

**Pipeline walkthrough**

- Scopes the data: index=meraki. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
- Extracts structured paths (JSON/XML) with `spath`.
- `eval` defines or adjusts **action** — often to normalize units, derive a ratio, or prepare for thresholds.
- `stats` rolls up events into metrics; results are split **by networkName, action, alertType** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
- `eval` defines or adjusts **last_event_human** — often to normalize units, derive a ratio, or prepare for thresholds.
- Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


### Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

### Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Enrollment status pie chart; pending enrollment timeline; device count by OS.

## SPL

```spl
index=meraki sourcetype IN ("meraki:webhook","meraki:webhooklogs:api") (alertTypeId="sm_enrollment" OR like(alertType, "%enrollment%") OR like(alertType, "%sm_device_added%") OR like(alertType, "%sm_device_removed%"))
| spath
| eval action=case(like(alertType, "%added%") OR like(alertType, "%enroll%"), "enrolled", like(alertType, "%removed%") OR like(alertType, "%unenroll%"), "unenrolled", true(), alertType)
| stats count as events, latest(_time) as last_event by networkName, action, alertType
| eval last_event_human=strftime(last_event, "%Y-%m-%d %H:%M:%S")
| sort - events
```

## Visualization

Enrollment status pie chart; pending enrollment timeline; device count by OS.

## Known False Positives

New devices from BYOD enrollment, replaced laptops, browser cache clears, re-enrollment after OS updates, or lab devices joining the org.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
