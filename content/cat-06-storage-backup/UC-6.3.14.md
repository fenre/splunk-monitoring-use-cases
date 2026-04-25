<!-- AUTO-GENERATED from UC-6.3.14.json — DO NOT EDIT -->

---
id: "6.3.14"
title: "Tape Library Robotics and Drive Health"
criticality: "high"
splunkPillar: "Observability"
---

# UC-6.3.14 · Tape Library Robotics and Drive Health

## Description

Mechanical faults, barcode read errors, and drive cleaning states cause failed backups before media errors. Dedicated robotics metrics reduce MTTR for tape operations.

## Value

Mechanical faults, barcode read errors, and drive cleaning states cause failed backups before media errors. Dedicated robotics metrics reduce MTTR for tape operations.

## Implementation

Augment generic tape syslog with SNMP polls for robotics status. Alert on inventory failures or slot errors. Schedule cleaning when `cleaning_required` is set.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Vendor SNMP, backup software tape events.
• Ensure the following data sources are available: Library element status, picker errors, drive cleaning required flags.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Augment generic tape syslog with SNMP polls for robotics status. Alert on inventory failures or slot errors. Schedule cleaning when `cleaning_required` is set.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=backup sourcetype="tape_library:robot"
| search (robot_error OR slot_unavailable OR "inventory failed" OR cleaning_required="true")
| stats count by library_name, component, error_code
| where count > 0
```

Understanding this SPL

**Tape Library Robotics and Drive Health** — Mechanical faults, barcode read errors, and drive cleaning states cause failed backups before media errors. Dedicated robotics metrics reduce MTTR for tape operations.

Documented **Data sources**: Library element status, picker errors, drive cleaning required flags. **App/TA** (typical add-on context): Vendor SNMP, backup software tape events. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: backup; **sourcetype**: tape_library:robot. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=backup, sourcetype="tape_library:robot". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Applies an explicit `search` filter to narrow the current result set.
• `stats` rolls up events into metrics; results are split **by library_name, component, error_code** so each row reflects one combination of those dimensions.
• Filters the current rows with `where count > 0` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Compare the same metric, object name, and interval in the vendor or cloud console (array, backup, or object store) that is the source of truth for this feed.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. List media server, proxy, and repository names in the runbook, and when to open a ticket with the application team versus the backup team. Consider visualizations: Table (library, component, errors), Timeline (robotics faults), Single value (libraries with open faults).

## SPL

```spl
index=backup sourcetype="tape_library:robot"
| search (robot_error OR slot_unavailable OR "inventory failed" OR cleaning_required="true")
| stats count by library_name, component, error_code
| where count > 0
```

## Visualization

Table (library, component, errors), Timeline (robotics faults), Single value (libraries with open faults).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
