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
• Install `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538) for shared credential and index patterns, plus a custom app (for example `TA_catalyst_swim`) that hosts the SWIM collection script and `inputs.conf`.
• Target index: `catalyst` and recommended sourcetype: `cisco:dnac:swim`.
• For Splunk app layout and passwords/credential store usage, see docs/implementation-guide.md

Step 1 — Ingestion path (not covered by a single TA sourcetype)
The Cisco Catalyst TA does not ship a native SWIM poller. Use one of:
**A) Scripted input (recommended for inventory):** Poll the Catalyst Center Intent API after obtaining a token.
- Authenticate: `POST /dna/system/api/v1/auth/token` (token in `X-Auth-Token` for subsequent calls).
- Device/update status: `GET /dna/intent/api/v1/network-device-image-updates` (running image, upgrade state).
- Image library: `GET /dna/intent/api/v1/image/importation` (imported/golden image metadata as applicable).
- Image compliance: `GET /dna/intent/api/v1/compliance/detail?complianceType=IMAGE` (compliance vs golden/baseline when modeled in Catalyst Center).

Example `inputs.conf`:

```ini
[script://$SPLUNK_HOME/etc/apps/TA_catalyst_swim/bin/collect_swim.py]
interval = 3600
sourcetype = cisco:dnac:swim
index = catalyst
disabled = 0
```

The Python (or PowerShell) script should: read controller URL and secrets from Splunk’s credential store, request a token, paginate if the API returns `response`/`total` patterns, and print one JSON line (or one multiline event) per device or per poll batch with fields such as `deviceName`, `deviceFamily`, `platformId`, `runningVersion`, `targetVersion`, `imageCompliance`, `lastUpgradeDate`.

**B) Webhook/HEC:** If Catalyst Center can emit platform events for SWIM lifecycle milestones, point the webhook destination to Splunk HEC and set `sourcetype=cisco:dnac:swim` (or a dedicated `cisco:dnac:swim:event` if you want to split poll vs event).

Step 2 — Create the search

```spl
index=catalyst sourcetype="cisco:dnac:swim" | stats dc(deviceName) as device_count values(runningVersion) as versions by deviceFamily, platformId | sort -device_count
```

Step 3 — Validate
`index=catalyst sourcetype="cisco:dnac:swim" | head 20` — confirm `deviceFamily`, `platformId`, and `runningVersion` are populated and counts match Catalyst Center UI.

Step 4 — Operationalize
Save as report/dashboard; add scheduled exports for compliance teams. Visualizations: table of platform and versions, bar chart of version distribution, single value of managed device count.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:swim" | stats dc(deviceName) as device_count values(runningVersion) as versions by deviceFamily, platformId | sort -device_count
```

## Visualization

Table (platform, version, device count), Bar chart (version distribution), Single value (total managed devices).

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
