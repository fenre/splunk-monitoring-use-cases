---
id: "6.1.4"
title: "Disk Failure Alerts"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-6.1.4 · Disk Failure Alerts

## Description

Immediate awareness of disk failures allows replacement before RAID degradation leads to data loss.

## Value

Immediate awareness of disk failures allows replacement before RAID degradation leads to data loss.

## Implementation

Enable SNMP traps or syslog forwarding for disk failure events. Create high-priority alert with PagerDuty/ServiceNow integration. Track spare disk inventory to ensure replacements are available.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Vendor TA, SNMP traps.
• Ensure the following data sources are available: Array event/alert logs, SNMP traps.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable SNMP traps or syslog forwarding for disk failure events. Create high-priority alert with PagerDuty/ServiceNow integration. Track spare disk inventory to ensure replacements are available.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=storage sourcetype="netapp:ontap:ems" severity="EMERGENCY" OR severity="ALERT"
| search disk_fail* OR disk_broken OR disk_error
| table _time, node, disk, severity, message
```

Understanding this SPL

**Disk Failure Alerts** — Immediate awareness of disk failures allows replacement before RAID degradation leads to data loss.

Documented **Data sources**: Array event/alert logs, SNMP traps. **App/TA** (typical add-on context): Vendor TA, SNMP traps. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: storage; **sourcetype**: netapp:ontap:ems. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=storage, sourcetype="netapp:ontap:ems". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Applies an explicit `search` filter to narrow the current result set.
• Pipeline stage (see **Disk Failure Alerts**): table _time, node, disk, severity, message


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Single value (failed disk count), Table (failed disks with details), Timeline (failure events).

## SPL

```spl
index=storage sourcetype="netapp:ontap:ems" severity="EMERGENCY" OR severity="ALERT"
| search disk_fail* OR disk_broken OR disk_error
| table _time, node, disk, severity, message
```

## Visualization

Single value (failed disk count), Table (failed disks with details), Timeline (failure events).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
