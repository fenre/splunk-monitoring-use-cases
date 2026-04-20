---
id: "6.1.10"
title: "Storage Array Firmware Compliance"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-6.1.10 · Storage Array Firmware Compliance

## Description

Outdated firmware exposes arrays to known bugs and security vulnerabilities. Compliance tracking supports patching cadence.

## Value

Outdated firmware exposes arrays to known bugs and security vulnerabilities. Compliance tracking supports patching cadence.

## Implementation

Poll system version info periodically (daily). Maintain a lookup table of approved firmware versions per model. Alert when arrays are running non-approved versions. Report on fleet firmware distribution.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Vendor TA, scripted inventory input.
• Ensure the following data sources are available: Array system info (firmware version, model), vendor advisory feeds.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll system version info periodically (daily). Maintain a lookup table of approved firmware versions per model. Alert when arrays are running non-approved versions. Report on fleet firmware distribution.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=storage sourcetype="netapp:ontap:system"
| stats latest(version) as firmware by node, model
| lookup approved_firmware_versions model OUTPUT approved_version
| where firmware!=approved_version
| table node, model, firmware, approved_version
```

Understanding this SPL

**Storage Array Firmware Compliance** — Outdated firmware exposes arrays to known bugs and security vulnerabilities. Compliance tracking supports patching cadence.

Documented **Data sources**: Array system info (firmware version, model), vendor advisory feeds. **App/TA** (typical add-on context): Vendor TA, scripted inventory input. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: storage; **sourcetype**: netapp:ontap:system. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=storage, sourcetype="netapp:ontap:system". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by node, model** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Enriches events using `lookup` (lookup definition + optional OUTPUT fields).
• Filters the current rows with `where firmware!=approved_version` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Storage Array Firmware Compliance**): table node, model, firmware, approved_version


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (arrays with firmware status), Pie chart (firmware version distribution), Single value (% compliant).

## SPL

```spl
index=storage sourcetype="netapp:ontap:system"
| stats latest(version) as firmware by node, model
| lookup approved_firmware_versions model OUTPUT approved_version
| where firmware!=approved_version
| table node, model, firmware, approved_version
```

## Visualization

Table (arrays with firmware status), Pie chart (firmware version distribution), Single value (% compliant).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
