<!-- AUTO-GENERATED from UC-6.3.8.json — DO NOT EDIT -->

---
id: "6.3.8"
title: "Tape Library Health"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-6.3.8 · Tape Library Health

## Description

Tape media and drive failures can silently corrupt backups. Monitoring ensures long-term archival reliability.

## Value

Tape media and drive failures can silently corrupt backups. Monitoring ensures long-term archival reliability.

## Implementation

Forward tape library syslog to Splunk. Poll SNMP for drive error counters and media faults. Alert on drive errors, media faults, or cleaning cartridge expiration. Track tape media lifecycle.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: SNMP TA, vendor syslog.
• Ensure the following data sources are available: Tape library logs, SNMP traps, drive error counters.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Forward tape library syslog to Splunk. Poll SNMP for drive error counters and media faults. Alert on drive errors, media faults, or cleaning cartridge expiration. Track tape media lifecycle.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=backup sourcetype="tape_library"
| search media_error OR drive_error OR cleaning_required
| stats count by library, drive_id, error_type
| where count > 0
```

Understanding this SPL

**Tape Library Health** — Tape media and drive failures can silently corrupt backups. Monitoring ensures long-term archival reliability.

Documented **Data sources**: Tape library logs, SNMP traps, drive error counters. **App/TA** (typical add-on context): SNMP TA, vendor syslog. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: backup; **sourcetype**: tape_library. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=backup, sourcetype="tape_library". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Applies an explicit `search` filter to narrow the current result set.
• `stats` rolls up events into metrics; results are split **by library, drive_id, error_type** so each row reflects one combination of those dimensions.
• Filters the current rows with `where count > 0` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Compare the same metric, object name, and interval in the vendor or cloud console (array, backup, or object store) that is the source of truth for this feed.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. List media server, proxy, and repository names in the runbook, and when to open a ticket with the application team versus the backup team. Consider visualizations: Table (drive/media errors), Single value (drives needing attention), Timeline (error events).

## SPL

```spl
index=backup sourcetype="tape_library"
| search media_error OR drive_error OR cleaning_required
| stats count by library, drive_id, error_type
| where count > 0
```

## Visualization

Table (drive/media errors), Single value (drives needing attention), Timeline (error events).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
