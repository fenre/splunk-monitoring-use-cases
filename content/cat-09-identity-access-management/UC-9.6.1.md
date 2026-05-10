<!-- AUTO-GENERATED from UC-9.6.1.json — DO NOT EDIT -->

---
id: "9.6.1"
title: "Device Compliance Status and Policy Enforcement"
criticality: "high"
splunkPillar: "Security"
---

# UC-9.6.1 · Device Compliance Status and Policy Enforcement

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Security &middot; **Type:** Security, Compliance

*We use identity and sign-in data in Splunk so we can notice unusual logins, access changes, and privileged use while it still matters — Device Compliance Status and Policy Enforcement*

---

## Description

Ensures all managed devices comply with security policies and configuration standards.

## Value

Ensures all managed devices comply with security policies and configuration standards.

## Implementation

Meraki Systems Manager (SM) data is NOT polled by the standard `Splunk_TA_cisco_meraki` device modular inputs. To monitor SM device compliance: (1) configure `cisco_meraki_webhook` (HEC, real-time, sourcetype `meraki:webhook`) OR `cisco_meraki_webhook_logs` (polled, sourcetype `meraki:webhooklogs:api`) and subscribe to SM compliance alerts in the Meraki Dashboard, OR (2) write a custom modular input that polls `GET /networks/{networkId}/sm/devices` and `GET /networks/{networkId}/sm/devices/{deviceId}/securityCenters` and writes results to `index=meraki sourcetype=meraki:sm:devices`. This UC uses the webhook path (works with either input).

## Detailed Implementation

### Prerequisites
- Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
- Ensure the following data sources are available: `index=meraki sourcetype=meraki:webhook` (HEC) or `meraki:webhooklogs:api` (polled) in `Splunk_TA_cisco_meraki` (Splunkbase 5580). The polled device inputs do NOT cover Meraki Systems Manager (SM/MDM); compliance status arrives via SM webhook events. For richer SM detail, write a custom modular input that polls `GET /networks/{networkId}/sm/devices`..
- For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

### Step 1 — Configure data collection
Meraki Systems Manager (SM) data is NOT polled by the standard `Splunk_TA_cisco_meraki` device modular inputs. To monitor SM device compliance: (1) configure `cisco_meraki_webhook` (HEC, real-time, sourcetype `meraki:webhook`) OR `cisco_meraki_webhook_logs` (polled, sourcetype `meraki:webhooklogs:api`) and subscribe to SM compliance alerts in the Meraki Dashboard, OR (2) write a custom modular input that polls `GET /networks/{networkId}/sm/devices` and `GET /networks/{networkId}/sm/devices/{devi…

### Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=meraki sourcetype IN ("meraki:webhook","meraki:webhooklogs:api") (alertTypeId="sm_device_compliance" OR like(alertType, "%compliance%") OR like(alertType, "%mdm%"))
| spath
| eval compliance_status=coalesce('alertData.complianceStatus', 'data.complianceStatus', complianceStatus)
| eval os_type=coalesce('alertData.osName', 'data.osName', osName, "unknown")
| stats count as total_devices, count(eval(compliance_status IN ("noncompliant","unknown"))) as noncompliant_count by os_type
| eval compliance_pct=round((total_devices-noncompliant_count)*100/total_devices, 2)
| where noncompliant_count > 0
| sort - noncompliant_count
```

#### Understanding this SPL

**Device Compliance Status and Policy Enforcement** — Ensures all managed devices comply with security policies and configuration standards.

Documented **Data sources**: `index=meraki sourcetype=meraki:webhook` (HEC) or `meraki:webhooklogs:api` (polled) in `Splunk_TA_cisco_meraki` (Splunkbase 5580). The polled device inputs do NOT cover Meraki Systems Manager (SM/MDM); compliance status arrives via SM webhook events. For richer SM detail, write a custom modular input that polls `GET /networks/{networkId}/sm/devices`. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: meraki.

**Pipeline walkthrough**

- Scopes the data: index=meraki. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
- Extracts structured paths (JSON/XML) with `spath`.
- `eval` defines or adjusts **compliance_status** — often to normalize units, derive a ratio, or prepare for thresholds.
- `eval` defines or adjusts **os_type** — often to normalize units, derive a ratio, or prepare for thresholds.
- `stats` rolls up events into metrics; results are split **by os_type** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
- `eval` defines or adjusts **compliance_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
- Filters the current rows with `where noncompliant_count > 0` — typically the threshold or rule expression for this monitoring goal.
- Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


### Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

### Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Compliance status table; compliance percentage gauge; noncompliant device list.

## SPL

```spl
index=meraki sourcetype IN ("meraki:webhook","meraki:webhooklogs:api") (alertTypeId="sm_device_compliance" OR like(alertType, "%compliance%") OR like(alertType, "%mdm%"))
| spath
| eval compliance_status=coalesce('alertData.complianceStatus', 'data.complianceStatus', complianceStatus)
| eval os_type=coalesce('alertData.osName', 'data.osName', osName, "unknown")
| stats count as total_devices, count(eval(compliance_status IN ("noncompliant","unknown"))) as noncompliant_count by os_type
| eval compliance_pct=round((total_devices-noncompliant_count)*100/total_devices, 2)
| where noncompliant_count > 0
| sort - noncompliant_count
```

## Visualization

Compliance status table; compliance percentage gauge; noncompliant device list.

## Known False Positives

Planned policy rollouts, pilot tenants, and emergency relaxations for incidents; require change tickets for production changes.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
