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

Query device API for firmware versions. Compare to recommended baseline.

## Detailed Implementation

### Prerequisites
- Cisco Meraki Add-on for Splunk (Splunkbase 5580) polling Meraki Dashboard API for device inventory including firmware versions. Data in `index=meraki` with `sourcetype=meraki:api:devices`. Key fields: `serial`, `name`, `model`, `firmware`, `network`, `productType` (appliance/switch/wireless/camera/sensor).
- Meraki firmware is managed centrally through the Meraki Dashboard. Firmware upgrades can be: (1) automatic (Meraki schedules), (2) scheduled by admin, or (3) pinned to a specific version. Key events appear in `sourcetype=meraki:events` with type "firmware upgrade".
- Build `meraki_firmware_policy.csv` lookup: `productType,target_firmware,min_firmware,notes` (e.g., `appliance,MX 18.2,MX 17.0,Required for WPA3`). Meraki firmware versions follow a product-specific naming convention (e.g., MX 18.2, MR 30.7, MS 15.21).

### Step 1 — Configure data collection
Verify firmware data:
```spl
index=meraki sourcetype="meraki:api:devices" earliest=-1h
| dedup serial
| stats count by firmware, productType
| sort productType, firmware
```

### Step 2 — Create the search and alert

**Primary search — Firmware compliance assessment:**
```spl
index=meraki sourcetype="meraki:api:devices" earliest=-1h
| dedup serial sortby -_time
| lookup meraki_firmware_policy.csv productType OUTPUT target_firmware min_firmware
| eval on_target=if(firmware=target_firmware, "YES", "NO")
| eval above_minimum=if(firmware >= min_firmware, "YES", "NO")
| eval compliance=case(firmware=target_firmware, "COMPLIANT", above_minimum="NO", "BELOW_MINIMUM", 1==1, "NEEDS_UPGRADE")
| lookup meraki_networks.csv network OUTPUT site_name tier
| stats count by compliance, productType, firmware
| sort compliance, productType
```

**Devices below minimum firmware:**
```spl
index=meraki sourcetype="meraki:api:devices" earliest=-1h
| dedup serial sortby -_time
| lookup meraki_firmware_policy.csv productType OUTPUT min_firmware
| where isnotnull(min_firmware) AND firmware < min_firmware
| lookup meraki_networks.csv network OUTPUT site_name tier
| table name, serial, model, network, site_name, firmware, min_firmware
| sort tier, productType
```

**Firmware upgrade event tracking:**
```spl
index=meraki sourcetype="meraki:events" "firmware" earliest=-30d
| stats count by network, deviceName, firmware
| sort -_time
```

### Step 3 — Validate
(a) In Meraki Dashboard: Organization > Firmware Upgrades. Compare scheduled/completed upgrades with Splunk firmware data.
(b) Spot-check 10 devices: verify firmware version in Splunk matches Meraki Dashboard > Network > device detail.
(c) Verify firmware policy lookup against Meraki's current recommended firmware for each product type.

### Step 4 — Operationalize
Dashboard ("Meraki Firmware Compliance"):
- Row 1 — Single-value tiles: "Compliant devices", "Below minimum", "Needs upgrade", "Total devices".
- Row 2 — Compliance by product type: stacked bar chart.
- Row 3 — Below-minimum devices table with site context.
- Row 4 — Firmware upgrade event history (30 days).

Alerting:
- High (device below minimum firmware): may have known vulnerabilities or missing features.
- Warning (weekly): compliance report — % of fleet on target firmware per product type.

### Step 5 — Troubleshooting

- **Firmware field empty** — Some device types may not report firmware through the inventory API. Check the raw API response for the specific device model.

- **Firmware version format varies** — Meraki uses product-specific version strings (MX 18.2 vs. MR 30.7). Comparison must be done within the same product type, never across product types.

- **Automatic upgrades not applying** — Check the network's firmware upgrade schedule in Meraki Dashboard: Network > Firmware upgrades. Some networks may have upgrades paused or pinned.

## SPL

```spl
index=cisco_network sourcetype="meraki:api"
| stats latest(firmware_version) as current_fw, count as device_count by device_type
| lookup recommended_firmware.csv device_type OUTPUTNEW recommended_fw
| where current_fw != recommended_fw
```

## Visualization

Firmware version table by device type; compliance percentage gauge; outdated device list.

## Known False Positives

Staged rollouts, deferred upgrades for stability, and lab networks often stay on older versions on purpose; policy by site tag, not a single version everywhere.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
