<!-- AUTO-GENERATED from UC-5.8.10.json — DO NOT EDIT -->

---
id: "5.8.10"
title: "Firmware Update Compliance and Version Tracking (Meraki)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.8.10 · Firmware Update Compliance and Version Tracking (Meraki)

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Compliance

*We track whether Meraki devices run current safe firmware, so you are not running known bugs or missing fixes across offices.*

---

## Description

Ensures all network devices run supported firmware versions and patches.

## Value

Network operations teams track Meraki device firmware versions against compliance targets, identifying devices running below minimum required firmware and monitoring upgrade rollout progress across the organization.

## Implementation

1. Enable the Devices and Firmware Upgrades inputs in Splunk_TA_cisco_meraki. The Devices input emits one event per device with the firmware field already populated (e.g. 'wireless-29-7'). 2. Create a lookup file recommended_meraki_firmware.csv with columns (model, target_firmware) reflecting the Meraki Dashboard recommendations under Organization -> Firmware upgrades. 3. The TA reads the Firmware Upgrades input from GET /organizations/{orgId}/firmware/upgrades and carries upgrade.toVersion.shortName for each scheduled upgrade — pair with the Devices output to detect drift after a wave.

## Detailed Implementation

### Prerequisites
- Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
- Ensure the following data sources are available: Splunk_TA_cisco_meraki (Splunkbase #5580): Devices input (sourcetype=meraki:devices) for current firmware version per device, and Firmware Upgrades input (sourcetype=meraki:firmwareupgrades, daily) for upgrade history. The recommended_meraki_firmware.csv is a customer-maintained lookup; populate it with the firmware version Meraki currently recommends per model..
- For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

### Step 1 — Configure data collection
1. Enable the Devices and Firmware Upgrades inputs in Splunk_TA_cisco_meraki. The Devices input emits one event per device with the firmware field already populated (e.g. 'wireless-29-7'). 2. Create a lookup file recommended_meraki_firmware.csv with columns (model, target_firmware) reflecting the Meraki Dashboard recommendations under Organization -> Firmware upgrades. 3. The TA reads the Firmware Upgrades input from GET /organizations/{orgId}/firmware/upgrades and carries upgrade.toVersion.shor…

### Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=meraki sourcetype="meraki:devices" earliest=-1h
| stats latest(firmware) as current_fw,
        dc(serial) as device_count,
        values(network.name) as networks
         by productType, model
| join type=left model [
    | inputlookup recommended_meraki_firmware.csv
    | rename target_firmware as recommended_fw
  ]
| eval compliant = if(current_fw==recommended_fw, "Yes", "No")
| where compliant="No" OR isnull(recommended_fw)
| sort productType model
```

#### Understanding this SPL

**Firmware Update Compliance and Version Tracking (Meraki)** — Network operations teams track Meraki device firmware versions against compliance targets, identifying devices running below minimum required firmware and monitoring upgrade rollout progress across the organization.

Documented **Data sources**: Splunk_TA_cisco_meraki (Splunkbase #5580): Devices input (sourcetype=meraki:devices) for current firmware version per device, and Firmware Upgrades input (sourcetype=meraki:firmwareupgrades, daily) for upgrade history. The recommended_meraki_firmware.csv is a customer-maintained lookup; populate it with the firmware version Meraki currently recommends per model. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: meraki; **sourcetype**: meraki:devices. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

- Scopes the data: index=meraki, sourcetype="meraki:devices", time bounds. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
- `stats` rolls up events into metrics; results are split **by productType, model** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
- Joins to a subsearch with `join` — set `max=` to match cardinality and avoid silent truncation.
- `eval` defines or adjusts **compliant** — often to normalize units, derive a ratio, or prepare for thresholds.
- Filters the current rows with `where compliant="No" OR isnull(recommended_fw)` — typically the threshold or rule expression for this monitoring goal.
- Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


### Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

### Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Firmware version table by device type; compliance percentage gauge; outdated device list.

## SPL

```spl
index=meraki sourcetype="meraki:devices" earliest=-1h
| stats latest(firmware) as current_fw,
        dc(serial) as device_count,
        values(network.name) as networks
         by productType, model
| join type=left model [
    | inputlookup recommended_meraki_firmware.csv
    | rename target_firmware as recommended_fw
  ]
| eval compliant = if(current_fw==recommended_fw, "Yes", "No")
| where compliant="No" OR isnull(recommended_fw)
| sort productType model
```

## Visualization

Firmware version table by device type; compliance percentage gauge; outdated device list.

## Known False Positives

Staged rollouts, deferred upgrades for stability, and lab networks often stay on older versions on purpose; policy by site tag, not a single version everywhere.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
