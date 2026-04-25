<!-- AUTO-GENERATED from UC-2.4.4.json — DO NOT EDIT -->

---
id: "2.4.4"
title: "VM Provisioning Time Tracking"
criticality: "low"
splunkPillar: "Observability"
---

# UC-2.4.4 · VM Provisioning Time Tracking

## Description

Measures the time from VM creation request to operational state. Long provisioning times indicate process bottlenecks — slow template deployment, manual approval delays, storage provisioning issues, or network configuration problems. Supports ITSM service level tracking and infrastructure automation improvement.

## Value

Measures the time from VM creation request to operational state. Long provisioning times indicate process bottlenecks — slow template deployment, manual approval delays, storage provisioning issues, or network configuration problems. Supports ITSM service level tracking and infrastructure automation improvement.

## Implementation

Correlate VM creation events with first power-on events from vCenter. For full lifecycle tracking, also correlate with ITSM ticket creation time (when the request was submitted). Calculate time from request → approval → creation → power-on. Set SLA targets and alert when provisioning exceeds them.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_vmware`, ITSM TA.
• Ensure the following data sources are available: vCenter events, ITSM request logs.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Correlate VM creation events with first power-on events from vCenter. For full lifecycle tracking, also correlate with ITSM ticket creation time (when the request was submitted). Calculate time from request → approval → creation → power-on. Set SLA targets and alert when provisioning exceeds them.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=vmware sourcetype="vmware:events" event_type="VmCreatedEvent"
| eval create_time=_time
| join max=1 vm_name [search index=vmware sourcetype="vmware:events" event_type="VmPoweredOnEvent" | eval poweron_time=_time | table vm_name, poweron_time]
| eval provision_minutes=round((poweron_time-create_time)/60, 1)
| where provision_minutes > 0
| stats avg(provision_minutes) as avg_min, median(provision_minutes) as median_min, max(provision_minutes) as max_min by datacenter
| table datacenter, avg_min, median_min, max_min
```

Understanding this SPL

**VM Provisioning Time Tracking** — Measures the time from VM creation request to operational state. Long provisioning times indicate process bottlenecks — slow template deployment, manual approval delays, storage provisioning issues, or network configuration problems. Supports ITSM service level tracking and infrastructure automation improvement.

Documented **Data sources**: vCenter events, ITSM request logs. **App/TA** (typical add-on context): `Splunk_TA_vmware`, ITSM TA. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: vmware; **sourcetype**: vmware:events. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=vmware, sourcetype="vmware:events". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **create_time** — often to normalize units, derive a ratio, or prepare for thresholds.
• Joins to a subsearch with `join` — set `max=` to match cardinality and avoid silent truncation.
• `eval` defines or adjusts **provision_minutes** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where provision_minutes > 0` — typically the threshold or rule expression for this monitoring goal.
• `stats` rolls up events into metrics; results are split **by datacenter** so each row reflects one combination of those dimensions.
• Pipeline stage (see **VM Provisioning Time Tracking**): table datacenter, avg_min, median_min, max_min

Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Bar chart (average provisioning time by DC), Line chart (trend over time), Table (slowest provisions).

## SPL

```spl
index=vmware sourcetype="vmware:events" event_type="VmCreatedEvent"
| eval create_time=_time
| join max=1 vm_name [search index=vmware sourcetype="vmware:events" event_type="VmPoweredOnEvent" | eval poweron_time=_time | table vm_name, poweron_time]
| eval provision_minutes=round((poweron_time-create_time)/60, 1)
| where provision_minutes > 0
| stats avg(provision_minutes) as avg_min, median(provision_minutes) as median_min, max(provision_minutes) as max_min by datacenter
| table datacenter, avg_min, median_min, max_min
```

## Visualization

Bar chart (average provisioning time by DC), Line chart (trend over time), Table (slowest provisions).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
