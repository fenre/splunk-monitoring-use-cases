<!-- AUTO-GENERATED from UC-2.1.6.json — DO NOT EDIT -->

---
id: "2.1.6"
title: "vMotion Tracking"
criticality: "low"
splunkPillar: "Observability"
---

# UC-2.1.6 · vMotion Tracking

## Description

Tracks VM migrations for troubleshooting and change management. Excessive vMotion can indicate DRS instability or resource contention.

## Value

Tracks VM migrations for troubleshooting and change management. Excessive vMotion can indicate DRS instability or resource contention.

## Implementation

Splunk_TA_vmware collects vCenter events. Create a report for audit/change tracking. Alert on excessive vMotion frequency (>10 migrations per host per hour may indicate DRS instability).

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_vmware`.
• Ensure the following data sources are available: `sourcetype=vmware:events`, vCenter event data.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Splunk_TA_vmware collects vCenter events. Create a report for audit/change tracking. Alert on excessive vMotion frequency (>10 migrations per host per hour may indicate DRS instability).

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=vmware sourcetype="vmware:events" event_type="VmMigratedEvent" OR event_type="DrsVmMigratedEvent"
| table _time vm_name source_host dest_host user event_type
| sort -_time
```

Understanding this SPL

**vMotion Tracking** — Tracks VM migrations for troubleshooting and change management. Excessive vMotion can indicate DRS instability or resource contention.

Documented **Data sources**: `sourcetype=vmware:events`, vCenter event data. **App/TA** (typical add-on context): `Splunk_TA_vmware`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: vmware; **sourcetype**: vmware:events. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=vmware, sourcetype="vmware:events". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Pipeline stage (see **vMotion Tracking**): table _time vm_name source_host dest_host user event_type
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (timeline), Sankey diagram (source to destination host), Count by host/hour.

## SPL

```spl
index=vmware sourcetype="vmware:events" event_type="VmMigratedEvent" OR event_type="DrsVmMigratedEvent"
| table _time vm_name source_host dest_host user event_type
| sort -_time
```

## Visualization

Table (timeline), Sankey diagram (source to destination host), Count by host/hour.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
