---
id: "6.3.24"
title: "Tape Library Slot Utilization"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-6.3.24 · Tape Library Slot Utilization

## Description

Tape library capacity and media expiration tracking prevent backup failures when slots are exhausted or tapes expire. Supports capacity planning and media lifecycle management.

## Value

Tape library capacity and media expiration tracking prevent backup failures when slots are exhausted or tapes expire. Supports capacity planning and media lifecycle management.

## Implementation

Poll tape library via SNMP (MIB-II, vendor-specific MIBs for slot counts) or vendor REST/CLI API. Collect total_slots, slots_used, and optionally media expiration dates. Run scripted input every 1–4 hours. Index to Splunk. Alert when slot utilization exceeds 85% or when media expiring within 30 days is detected. Maintain lookup of media barcodes and expiration for lifecycle tracking.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom scripted input (tape library SNMP, vendor API).
• Ensure the following data sources are available: Tape library management interface (SNMP/API).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll tape library via SNMP (MIB-II, vendor-specific MIBs for slot counts) or vendor REST/CLI API. Collect total_slots, slots_used, and optionally media expiration dates. Run scripted input every 1–4 hours. Index to Splunk. Alert when slot utilization exceeds 85% or when media expiring within 30 days is detected. Maintain lookup of media barcodes and expiration for lifecycle tracking.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=backup sourcetype="tape_library:capacity"
| eval slot_util_pct=round(slots_used/total_slots*100, 1)
| eval media_expiring_30d=if(media_expiration_days<=30, 1, 0)
| stats latest(slot_util_pct) as pct_used, latest(slots_used) as used, latest(total_slots) as total, sum(media_expiring_30d) as expiring_soon by library_name
| where pct_used > 85 OR expiring_soon > 0
| table library_name, used, total, pct_used, expiring_soon
```

Understanding this SPL

**Tape Library Slot Utilization** — Tape library capacity and media expiration tracking prevent backup failures when slots are exhausted or tapes expire. Supports capacity planning and media lifecycle management.

Documented **Data sources**: Tape library management interface (SNMP/API). **App/TA** (typical add-on context): Custom scripted input (tape library SNMP, vendor API). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: backup; **sourcetype**: tape_library:capacity. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=backup, sourcetype="tape_library:capacity". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **slot_util_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• `eval` defines or adjusts **media_expiring_30d** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by library_name** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where pct_used > 85 OR expiring_soon > 0` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Tape Library Slot Utilization**): table library_name, used, total, pct_used, expiring_soon


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Gauge (slot utilization % per library), Table (libraries with slot counts and expiring media), Line chart (slot usage trend), Single value (libraries near capacity).

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
index=backup sourcetype="tape_library:capacity"
| eval slot_util_pct=round(slots_used/total_slots*100, 1)
| eval media_expiring_30d=if(media_expiration_days<=30, 1, 0)
| stats latest(slot_util_pct) as pct_used, latest(slots_used) as used, latest(total_slots) as total, sum(media_expiring_30d) as expiring_soon by library_name
| where pct_used > 85 OR expiring_soon > 0
| table library_name, used, total, pct_used, expiring_soon
```

## Visualization

Gauge (slot utilization % per library), Table (libraries with slot counts and expiring media), Line chart (slot usage trend), Single value (libraries near capacity).

## References

- [Splunk Add-on for Microsoft Windows](https://splunkbase.splunk.com/app/742)
