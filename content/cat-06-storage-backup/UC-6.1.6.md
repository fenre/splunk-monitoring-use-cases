---
id: "6.1.6"
title: "Controller Failover Events"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-6.1.6 · Controller Failover Events

## Description

Controller failovers indicate hardware problems and may cause transient performance impact. Quick detection ensures rapid root cause analysis.

## Value

Controller failovers indicate hardware problems and may cause transient performance impact. Quick detection ensures rapid root cause analysis.

## Implementation

For NetApp ONTAP: ingest EMS events via syslog (UDP/TCP) or use `TA-netapp_ontap` for REST-based EMS polling. Key EMS message families: `cf.takeover`, `cf.giveback`, `ha.interconnect`. Alert on any takeover outside a scheduled change window, or any giveback failure. Include `cluster`, `node`, and `partner` fields in the alert for storage operations handoff.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Vendor TA, syslog.
• Ensure the following data sources are available: Array event logs, cluster status.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
For NetApp ONTAP: ingest EMS events via syslog (UDP/TCP) or use `TA-netapp_ontap` for REST-based EMS polling. Key EMS message families: `cf.takeover`, `cf.giveback`, `ha.interconnect`. Alert on any takeover outside a scheduled change window, or any giveback failure. Include `cluster`, `node`, and `partner` fields in the alert for storage operations handoff.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=storage sourcetype="netapp:ontap:ems"
| search "cf.takeover*" OR "cf.giveback*" OR failover
| table _time, node, event, message
```

Understanding this SPL

**Controller Failover Events** — Controller failovers indicate hardware problems and may cause transient performance impact. Quick detection ensures rapid root cause analysis.

Documented **Data sources**: Array event logs, cluster status. **App/TA** (typical add-on context): Vendor TA, syslog. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: storage; **sourcetype**: netapp:ontap:ems. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=storage, sourcetype="netapp:ontap:ems". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Applies an explicit `search` filter to narrow the current result set.
• Pipeline stage (see **Controller Failover Events**): table _time, node, event, message


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Timeline (failover events), Single value (days since last failover), Table (event details).

## SPL

```spl
index=storage sourcetype="netapp:ontap:ems"
| search "cf.takeover*" OR "cf.giveback*" OR failover
| table _time, node, event, message
```

## Visualization

Timeline (failover events), Single value (days since last failover), Table (event details).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
