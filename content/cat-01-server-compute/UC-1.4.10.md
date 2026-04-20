---
id: "1.4.10"
title: "Disk Controller and HBA Health"
criticality: "high"
splunkPillar: "Observability"
---

# UC-1.4.10 · Disk Controller and HBA Health

## Description

RAID/HBA controller errors and degraded state often precede array failure. Early visibility enables planned maintenance and avoids data loss.

## Value

RAID/HBA controller errors and degraded state often precede array failure. Early visibility enables planned maintenance and avoids data loss.

## Implementation

Run vendor CLI (MegaCli, perccli, hpssacli) via scripted input every 15 minutes. Parse controller and virtual drive state. Alert when status is not Optimal or any array is degraded.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom scripted input (MegaRAID, perccli, hpssacli).
• Ensure the following data sources are available: Vendor CLI output (e.g. `MegaCli64 -AdpAllInfo -aAll`), `/proc/scsi/`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Run vendor CLI (MegaCli, perccli, hpssacli) via scripted input every 15 minutes. Parse controller and virtual drive state. Alert when status is not Optimal or any array is degraded.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=hardware sourcetype=raid_controller host=*
| stats latest(controller_status) as status, latest(degraded_virtual_drives) as degraded by host, controller_id
| where status != "Optimal" OR degraded > 0
| table host controller_id status degraded
```

Understanding this SPL

**Disk Controller and HBA Health** — RAID/HBA controller errors and degraded state often precede array failure. Early visibility enables planned maintenance and avoids data loss.

Documented **Data sources**: Vendor CLI output (e.g. `MegaCli64 -AdpAllInfo -aAll`), `/proc/scsi/`. **App/TA** (typical add-on context): Custom scripted input (MegaRAID, perccli, hpssacli). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: hardware; **sourcetype**: raid_controller. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=hardware, sourcetype=raid_controller. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host, controller_id** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where status != "Optimal" OR degraded > 0` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Disk Controller and HBA Health**): table host controller_id status degraded


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Status panel (Optimal/Degraded/Failed), Table of degraded arrays.

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
index=hardware sourcetype=raid_controller host=*
| stats latest(controller_status) as status, latest(degraded_virtual_drives) as degraded by host, controller_id
| where status != "Optimal" OR degraded > 0
| table host controller_id status degraded
```

## Visualization

Status panel (Optimal/Degraded/Failed), Table of degraded arrays.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
