---
id: "1.4.11"
title: "Boot Order and UEFI/BIOS Configuration Drift"
criticality: "medium"
splunkPillar: "Security"
---

# UC-1.4.11 · Boot Order and UEFI/BIOS Configuration Drift

## Description

Unauthorized or accidental boot order changes can prevent systems from booting from the correct disk or PXE. Tracking supports change audit and recovery.

## Value

Unauthorized or accidental boot order changes can prevent systems from booting from the correct disk or PXE. Tracking supports change audit and recovery.

## Implementation

Use vendor APIs or scripts to export boot order and Secure Boot state. Compare to a lookup of expected configuration. Alert on drift. Run after changes or daily.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom scripted input (vendor tools, dmidecode).
• Ensure the following data sources are available: `dmidecode -t bios`, vendor REST/CLI (iDRAC, iLO) for boot order.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Use vendor APIs or scripts to export boot order and Secure Boot state. Compare to a lookup of expected configuration. Alert on drift. Run after changes or daily.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=hardware sourcetype=boot_config host=*
| stats latest(boot_order) as current_order, latest(secure_boot) as secure_boot by host
| inputlookup expected_boot_config append=t
| eval match=if('current_order'='expected_order', "Match", "Drift")
| where match="Drift"
| table host current_order expected_order secure_boot
```

Understanding this SPL

**Boot Order and UEFI/BIOS Configuration Drift** — Unauthorized or accidental boot order changes can prevent systems from booting from the correct disk or PXE. Tracking supports change audit and recovery.

Documented **Data sources**: `dmidecode -t bios`, vendor REST/CLI (iDRAC, iLO) for boot order. **App/TA** (typical add-on context): Custom scripted input (vendor tools, dmidecode). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: hardware; **sourcetype**: boot_config. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=hardware, sourcetype=boot_config. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Loads rows via `inputlookup` (KV store or CSV lookup) for enrichment or reporting.
• `eval` defines or adjusts **match** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where match="Drift"` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Boot Order and UEFI/BIOS Configuration Drift**): table host current_order expected_order secure_boot


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (host, current vs. expected boot order), Compliance percentage.

## SPL

```spl
index=hardware sourcetype=boot_config host=*
| stats latest(boot_order) as current_order, latest(secure_boot) as secure_boot by host
| inputlookup expected_boot_config append=t
| eval match=if('current_order'='expected_order', "Match", "Drift")
| where match="Drift"
| table host current_order expected_order secure_boot
```

## Visualization

Table (host, current vs. expected boot order), Compliance percentage.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
