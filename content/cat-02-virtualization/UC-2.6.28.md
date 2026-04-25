<!-- AUTO-GENERATED from UC-2.6.28.json — DO NOT EDIT -->

---
id: "2.6.28"
title: "Local Host Cache (LHC) Sync Status and Mode Transitions"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-2.6.28 · Local Host Cache (LHC) Sync Status and Mode Transitions

## Description

Local Host Cache (LHC) allows Delivery Controllers to broker sessions when the site database is unreachable. Failures in sync, unexpected mode changes (to or from LHC), or lagging replication indicate risk of logon/brokering issues and split-brain scenarios. Alerting on Citrix High Availability Service events and correlating with broker events surfaces site-database outages and recovery before users see widespread failures.

## Value

Local Host Cache (LHC) allows Delivery Controllers to broker sessions when the site database is unreachable. Failures in sync, unexpected mode changes (to or from LHC), or lagging replication indicate risk of logon/brokering issues and split-brain scenarios. Alerting on Citrix High Availability Service events and correlating with broker events surfaces site-database outages and recovery before users see widespread failures.

## Implementation

Ingest Windows Application log from all Delivery Controllers; confirm `source` and `sourcetype` for Citrix High Availability Service. Add field extractions for sync state, mode transition, and error text if Message format varies by version. Correlate with `citrix:broker:events` for registration and brokering errors. Tune noise from planned failovers. Document expected behavior during site DB maintenance so alerts can be suppressed via lookup.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk Add-on for Microsoft Windows, Template for Citrix XenDesktop 7 (TA-XD7-Broker).
• Ensure the following data sources are available: `sourcetype="WinEventLog:Application"` with `source="Citrix High Availability Service"` from Delivery Controllers; optional `index=xd` `sourcetype="citrix:broker:events"`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Forward Application logs from all Delivery Controllers. Verify the Citrix High Availability Service writes events you can key on (mode transitions, sync errors). Normalize `host` to controller identity. Add optional scheduled search to join broker-side failures when LHC is active.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range, regex, and host filters as needed):

```spl
index=windows sourcetype="WinEventLog:Application" source="Citrix High Availability Service" earliest=-24h
| rex field=Message "(?i)mode[\s:]*(?<lhc_mode>\w+)|synchroni[sz]e|sync\s+lag|Local\s*Host\s*Cache|HA\s*state"
| eval ha_event=if(match(Message, "(?i)entering|switched|transition|outage|split.?brain|sync"), 1, 0)
| where ha_event=1
| stats count, earliest(_time) as first_seen, latest(_time) as last_seen by host, EventCode, Message
| sort - count
```

Step 3 — Validate
Trigger a test in a lab (simulate database connectivity) or compare against known maintenance windows. Confirm events are parsed and that correlation searches return expected pairings with broker data.

Step 4 — Operationalize
Alert on new critical Message patterns, rising event rates per controller, or sync-related errors outside change windows. Add maintenance lookups to suppress expected transitions. Use timeline and table visualizations in the operations dashboard.

## SPL

```spl
index=windows sourcetype="WinEventLog:Application" source="Citrix High Availability Service" earliest=-24h
| rex field=Message "(?i)mode[\s:]*(?<lhc_mode>\w+)|synchroni[sz]e|sync\s+lag|Local\s*Host\s*Cache|HA\s*state"
| eval ha_event=if(match(Message, "(?i)entering|switched|transition|outage|split.?brain|sync"), 1, 0)
| where ha_event=1
| stats count, earliest(_time) as first_seen, latest(_time) as last_seen by host, EventCode, Message
| sort - count
```

## Visualization

Timeline (HA and mode events), Table (host, event text, first/last seen), Single value (count of critical HA errors).

## References

- [Local Host Cache in Citrix Virtual Apps and Desktops](https://docs.citrix.com/en-us/citrix-virtual-apps-desktops-2112/manage-deployment/broker.html)
- [Splunk Add-on for Microsoft Windows](https://splunkbase.splunk.com/app/742)
