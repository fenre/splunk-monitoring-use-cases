<!-- AUTO-GENERATED from UC-2.5.2.json — DO NOT EDIT -->

---
id: "2.5.2"
title: "IGEL Firmware Version Compliance"
criticality: "high"
splunkPillar: "Observability"
---

# UC-2.5.2 · IGEL Firmware Version Compliance

## Description

Running outdated or unapproved IGEL OS firmware exposes endpoints to known vulnerabilities and breaks standardized VDI session configurations. Tracking firmware versions across the fleet against an approved baseline ensures compliance with patch policies and simplifies troubleshooting by eliminating version drift as a variable.

## Value

Running outdated or unapproved IGEL OS firmware exposes endpoints to known vulnerabilities and breaks standardized VDI session configurations. Tracking firmware versions across the fleet against an approved baseline ensures compliance with patch policies and simplifies troubleshooting by eliminating version drift as a variable.

## Implementation

Poll `GET /v3/thinclients?facets=details` to retrieve firmware IDs per device, and `GET /v3/firmwares` to resolve firmware IDs to version strings and product names. Maintain a lookup table (`igel_approved_firmware.csv`) with columns `fw_version`, `approved`, `target_version` mapping each known firmware version to its compliance status. Run the lookup enrichment as a scheduled search daily. Alert when non-compliant device percentage exceeds 20% or when any device runs a firmware version flagged as critical-vulnerability.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom scripted input polling IGEL UMS REST API (`GET /v3/thinclients?facets=details`, `GET /v3/firmwares`).
• Ensure the following data sources are available: `index=endpoint` `sourcetype="igel:ums:inventory"` fields `device_name`, `firmware_id`, `firmware_version`, `product_name`, `directory_path`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll `GET /v3/thinclients?facets=details` to retrieve firmware IDs per device, and `GET /v3/firmwares` to resolve firmware IDs to version strings and product names. Maintain a lookup table (`igel_approved_firmware.csv`) with columns `fw_version`, `approved`, `target_version` mapping each known firmware version to its compliance status. Run the lookup enrichment as a scheduled search daily. Alert when non-compliant device percentage exceeds 20% or when any device runs a firmware version flagged a…

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=endpoint sourcetype="igel:ums:inventory"
| stats latest(firmware_id) as fw_id, latest(firmware_version) as fw_version, latest(device_name) as device_name by unit_id
| lookup igel_approved_firmware fw_version OUTPUT approved, target_version
| eval compliant=if(approved="yes", "Compliant", "Non-Compliant")
| stats count as device_count by fw_version, compliant, target_version
| sort -device_count
| table fw_version, compliant, target_version, device_count
```

Understanding this SPL

**IGEL Firmware Version Compliance** — Running outdated or unapproved IGEL OS firmware exposes endpoints to known vulnerabilities and breaks standardized VDI session configurations. Tracking firmware versions across the fleet against an approved baseline ensures compliance with patch policies and simplifies troubleshooting by eliminating version drift as a variable.

Documented **Data sources**: `index=endpoint` `sourcetype="igel:ums:inventory"` fields `device_name`, `firmware_id`, `firmware_version`, `product_name`, `directory_path`. **App/TA** (typical add-on context): Custom scripted input polling IGEL UMS REST API (`GET /v3/thinclients?facets=details`, `GET /v3/firmwares`). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: endpoint; **sourcetype**: igel:ums:inventory. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=endpoint, sourcetype="igel:ums:inventory". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by unit_id** so each row reflects one combination of those dimensions.
• Enriches events using `lookup` (lookup definition + optional OUTPUT fields).
• `eval` defines or adjusts **compliant** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by fw_version, compliant, target_version** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
• Pipeline stage (see **IGEL Firmware Version Compliance**): table fw_version, compliant, target_version, device_count

Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Pie chart (compliant vs non-compliant), Table (firmware versions with device counts), Single value (compliance %).

## SPL

```spl
index=endpoint sourcetype="igel:ums:inventory"
| stats latest(firmware_id) as fw_id, latest(firmware_version) as fw_version, latest(device_name) as device_name by unit_id
| lookup igel_approved_firmware fw_version OUTPUT approved, target_version
| eval compliant=if(approved="yes", "Compliant", "Non-Compliant")
| stats count as device_count by fw_version, compliant, target_version
| sort -device_count
| table fw_version, compliant, target_version, device_count
```

## Visualization

Pie chart (compliant vs non-compliant), Table (firmware versions with device counts), Single value (compliance %).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
