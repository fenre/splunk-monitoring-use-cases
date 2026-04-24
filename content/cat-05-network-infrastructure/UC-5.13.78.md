---
id: "5.13.78"
title: "Catalyst Center License Utilization Tracking"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.13.78 · Catalyst Center License Utilization Tracking

## Description

Tracks Catalyst Center license utilization by type, alerting when license consumption approaches capacity limits.

## Value

Running out of licenses prevents onboarding new devices. Proactive tracking ensures license procurement happens before capacity is exhausted.

## Implementation

Catalyst Center license data requires polling the Intent API.

API endpoint:
• `GET /dna/intent/api/v1/licenses/summary` — license counts by type
• `GET /dna/intent/api/v1/licenses/device/count` — per-device license usage

Create a custom scripted input:

```ini
[script://$SPLUNK_HOME/etc/apps/TA_catalyst_license/bin/collect_licenses.py]
interval = 86400
sourcetype = cisco:dnac:license
index = catalyst
disabled = 0
```

The script polls license summary data daily and outputs fields: `licenseType`, `totalLicenses`, `consumedLicenses`, `availableLicenses`, `expirationDate`.

## Detailed Implementation

Prerequisites
• UC-5.13.1 complete (Catalyst API token, connectivity).
• Ability to install a small **custom app** or **add-on** on the same tier as other scripted inputs (often Heavy Forwarder). Python 3 with `requests` to call DNAC with OAuth2 client credentials or existing TA token if exposed to script (prefer separate least-privilege API user for license reads).

Step 1 — API calls
- **Summary:** `GET https://<dnac>/dna/intent/api/v1/licenses/summary` — parse JSON for each license type and counts.
- **Device count (optional):** `GET /dna/intent/api/v1/licenses/device/count` for enforcement vs inventory reconciliation.
- Auth: `X-Auth-Token` from Catalyst Center auth API per Cisco documentation; refresh before expiry in the script.

Step 2 — Script output
- One **Splunk** event per license type (or one JSON with `multikv` expansion in parsing) with fields: `licenseType`, `totalLicenses`, `consumedLicenses`, `availableLicenses`, `expirationDate` (ISO-8601 string).
- Sourcetype: `cisco:dnac:license` — add **props.conf** for line-breaking if one event is multi-line JSON.

Step 3 — inputs.conf (example path)
- Place the script under `$SPLUNK_HOME/etc/apps/<your_app>/bin/collect_licenses.py` and reference it from `inputs.conf` as in the short implementation. Set `interval = 86400` (daily) or `3600` for faster burn-down visibility.
- Set `index = catalyst` and `sourcetype = cisco:dnac:license`.

Step 4 — Baseline SPL

```spl
index=catalyst sourcetype="cisco:dnac:license" | stats latest(totalLicenses) as total latest(consumedLicenses) as consumed latest(availableLicenses) as available by licenseType | eval utilization_pct=round(consumed*100/total,1) | eval status=case(utilization_pct>90,"Critical",utilization_pct>75,"Warning",1==1,"Healthy") | sort -utilization_pct
```

Step 5 — Alerting
- Alert when `status` is `Warning` or `Critical` or when `availableLicenses` is below procurement lead-time threshold (eval via lookup of SKU lead time).

Step 6 — Security
- Store API credentials in **passwords.conf** (storage endpoint) or OS keychain — never in cleartext in the script; integrate with **splunklib** binding if using modular input pattern.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:license" | stats latest(totalLicenses) as total latest(consumedLicenses) as consumed latest(availableLicenses) as available by licenseType | eval utilization_pct=round(consumed*100/total,1) | eval status=case(utilization_pct>90,"Critical",utilization_pct>75,"Warning",1==1,"Healthy") | sort -utilization_pct
```

## Visualization

Table: licenseType, total, consumed, available, utilization_pct, status; gauge or single value per license type; trend of utilization_pct over 90 days if stored in summary or indexed daily snapshots.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
