---
id: "1.4.5"
title: "Firmware Version Compliance"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-1.4.5 · Firmware Version Compliance

## Description

Outdated firmware may have security vulnerabilities or known bugs. Fleet-wide firmware tracking supports patch management.

## Value

Outdated firmware may have security vulnerabilities or known bugs. Fleet-wide firmware tracking supports patch management.

## Implementation

Create scripted input: `ipmitool mc info` or `dmidecode -t bios`. Run daily. Maintain a lookup table of expected firmware versions per server model. Dashboard showing compliance.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom scripted input (`ipmitool`, `dmidecode`), vendor APIs.
• Ensure the following data sources are available: BMC/BIOS version data via scripted input.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Create scripted input: `ipmitool mc info` or `dmidecode -t bios`. Run daily. Maintain a lookup table of expected firmware versions per server model. Dashboard showing compliance.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=hardware sourcetype=firmware_inventory
| stats latest(bios_version) as bios, latest(bmc_version) as bmc by host, model
| lookup current_firmware model OUTPUT expected_bios, expected_bmc
| eval bios_current = if(bios=expected_bios, "Yes", "No")
| where bios_current="No"
```

Understanding this SPL

**Firmware Version Compliance** — Outdated firmware may have security vulnerabilities or known bugs. Fleet-wide firmware tracking supports patch management.

Documented **Data sources**: BMC/BIOS version data via scripted input. **App/TA** (typical add-on context): Custom scripted input (`ipmitool`, `dmidecode`), vendor APIs. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: hardware; **sourcetype**: firmware_inventory. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=hardware, sourcetype=firmware_inventory. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host, model** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Enriches events using `lookup` (lookup definition + optional OUTPUT fields).
• `eval` defines or adjusts **bios_current** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where bios_current="No"` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (host, model, current vs. expected), Pie chart (compliant %), Bar chart by model.

Scripted input (generic example)
This use case relies on a scripted input. In the app's local/inputs.conf add a stanza such as:

```ini
[script://$SPLUNK_HOME/etc/apps/YourApp/bin/collect.sh]
interval = 300
sourcetype = your_sourcetype
index = main
disabled = 0
```

The script should print one event per line (e.g. key=value). Example minimal script (bash):

```bash
#!/usr/bin/env bash
# Output metrics or events, one per line
echo "metric=value timestamp=$(date +%s)"
```

For full details (paths, scheduling, permissions), see the Implementation guide: docs/implementation-guide.md

## SPL

```spl
index=hardware sourcetype=firmware_inventory
| stats latest(bios_version) as bios, latest(bmc_version) as bmc by host, model
| lookup current_firmware model OUTPUT expected_bios, expected_bmc
| eval bios_current = if(bios=expected_bios, "Yes", "No")
| where bios_current="No"
```

## Visualization

Table (host, model, current vs. expected), Pie chart (compliant %), Bar chart by model.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
