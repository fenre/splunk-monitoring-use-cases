<!-- AUTO-GENERATED from UC-5.13.55.json — DO NOT EDIT -->

---
id: "5.13.55"
title: "Software Image Inventory and Version Summary"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.13.55 · Software Image Inventory and Version Summary

## Description

Provides a complete inventory of software images running across all managed devices, grouped by platform family and running version, using Catalyst Center's SWIM data.

## Value

Knowing exactly which software versions are running on every device is foundational for firmware compliance, vulnerability management, and upgrade planning.

## Implementation

The Cisco Catalyst TA does not poll SWIM data natively. Create a custom scripted input that authenticates to Catalyst Center and polls the SWIM endpoints.

API endpoints:
• `POST /dna/system/api/v1/auth/token` — authenticate and get a token
• `GET /dna/intent/api/v1/network-device-image-updates` — get device image update status
• `GET /dna/intent/api/v1/image/importation` — list available images
• `GET /dna/intent/api/v1/compliance/detail?complianceType=IMAGE` — image compliance

Create a scripted input in your custom app:

```ini
[script://$SPLUNK_HOME/etc/apps/TA_catalyst_swim/bin/collect_swim.py]
interval = 3600
sourcetype = cisco:dnac:swim
index = catalyst
disabled = 0
```

The script should:
1. Authenticate to Catalyst Center using `POST /dna/system/api/v1/auth/token`
2. Call `GET /dna/intent/api/v1/network-device-image-updates` to get current running versions
3. Output JSON events with fields: `deviceName`, `deviceFamily`, `platformId`, `runningVersion`, `targetVersion`, `imageCompliance`, `lastUpgradeDate`
4. Store credentials in Splunk's credential store (passwords.conf) — never hardcode

Alternatively, configure Catalyst Center Platform event notifications for SWIM events and send to Splunk via HEC webhook.

## Detailed Implementation

Prerequisites
• `Cisco Catalyst Add-on for Splunk` (7538) for index naming and, usually, the same credential patterns you use for other Intent API pollers, plus a **custom app** (for example `TA_catalyst_swim`) for SWIM that the base TA does not fully ship in every release.
• `index=catalyst` and **sourcetype** `cisco:dnac:swim` (your scripted input must emit consistent fields: `deviceName`, `deviceFamily`, `platformId`, `runningVersion` at minimum).
• `docs/implementation-guide.md` for app structure and secure credential storage (`passwords.conf` or modular input storage).

Step 1 — Ingestion (Catalyst Center SWIM)
The Cisco Catalyst TA does not replace a full SWIM inventory poll by itself; implement **one** of:
• **Scripted input:** `POST /dna/system/api/v1/auth/token`, then `GET /dna/intent/api/v1/network-device-image-updates` (and optionally `GET /dna/intent/api/v1/image/importation` or `GET /dna/intent/api/v1/compliance/detail?complianceType=IMAGE` when you need golden alignment). Paginate and normalize JSON the same way Cisco documents for your software train.
• **HEC / Platform events:** if your controller can push SWIM or deployment milestones to a webhook, land them on `cisco:dnac:swim` (or a sibling sourcetype you union in dashboards) with a stable dedup key if poll and push both run.

```ini
[script://$SPLUNK_HOME/etc/apps/TA_catalyst_swim/bin/collect_swim.py]
interval = 3600
sourcetype = cisco:dnac:swim
index = catalyst
disabled = 0
```

Step 2 — Create the report

```spl
index=catalyst sourcetype="cisco:dnac:swim" | stats dc(deviceName) as device_count values(runningVersion) as versions by deviceFamily, platformId | sort -device_count
```

Step 3 — Validate
• Run `| head 20` and compare device counts to **Catalyst Center > Software Image Management (SWIM)** and **Inventory**; differences usually mean the script is scoped to a site list or the API throttled (HTTP 429).

Step 4 — Operationalize
• Save as a **report**; export to compliance or change windows as CSV; do not over-alert on version spread by itself — this UC is a **fingerprint** for planning, not a fault detector.

Step 5 — Troubleshooting
• **Empty index:** forwarder not running the script, bad token, or wrong controller URL — check `splunkd.log` for `ERROR` in the `execprocessor` for your stanza name.
• **Partial `deviceName` set:** the API user may lack SWIM or inventory scope; confirm **SUPER-ADMIN-ROLE** or **NETWORK-ADMIN-ROLE** (or a custom role that can read software endpoints).
• **Stuck versions:** a device may show last poll only; compare `_time` to the SWIM last-contact fields in the UI when troubleshooting drift.


## SPL

```spl
index=catalyst sourcetype="cisco:dnac:swim" | stats dc(deviceName) as device_count values(runningVersion) as versions by deviceFamily, platformId | sort -device_count
```

## Visualization

Table (platform, version, device count), Bar chart (version distribution), Single value (total managed devices).

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
- [Catalyst Center Integration Guide](docs/guides/catalyst-center.md)
