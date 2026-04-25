<!-- AUTO-GENERATED from UC-2.6.70.json — DO NOT EDIT -->

---
id: "2.6.70"
title: "Citrix ShareFile Storage Zone Controller Health"
criticality: "high"
splunkPillar: "Observability"
---

# UC-2.6.70 · Citrix ShareFile Storage Zone Controller Health

## Description

ShareFile content collaboration depends on healthy Storage Zone Controllers and connectors. Monitoring zone online state, synchronization backlog, split between on-premises and cloud-hosted zones, and connector health early exposes outages, replication stalls, and hybrid path failures that block file access, uploads, and business workflows.

## Value

ShareFile content collaboration depends on healthy Storage Zone Controllers and connectors. Monitoring zone online state, synchronization backlog, split between on-premises and cloud-hosted zones, and connector health early exposes outages, replication stalls, and hybrid path failures that block file access, uploads, and business workflows.

## Implementation

Ingest Storage Zone Controller and Storage Zone Connector logs (syslog, file, or API export) with consistent timestamps and time zones. Tag each zone with `hosting_mode` to separate on-prem vs customer-managed cloud. Define backlog thresholds from your baseline; alert when a zone is not online, backlog grows beyond an agreed cap, or any connector is unhealthy. Pair with Citrix Cloud status and network path tests for the control plane if applicable.

## Detailed Implementation

Prerequisites
• Storage Zone Controller and connector logs (or API export) available to Splunk with field extraction for `zone_state`, `sync_backlog` or equivalent, and `hosting_mode`.
• Reference architecture doc listing zone IDs, on-prem vs cloud, and which connectors serve each site.

Step 1 — Configure data collection
Send controller and connector output to a dedicated index. Normalize time to UTC. Map vendor-specific status strings to `zone_state` and `connector_health` for consistent `eval` rules.

Step 2 — Create the search and alert
Run the base SPL, tune `max_backlog` and health string patterns to your build. Create alerts: any zone not online for 10 minutes, backlog over threshold for two consecutive 5m buckets, or any connector not healthy for 15 minutes.

Step 3 — Validate
Compare panel counts to the admin console. Inject or replay a test event where backlog spikes in a non-production zone.

Step 4 — Operationalize
Add the panels to a ShareFile operations dashboard, route alerts to the collaboration and storage teams, and document escalation when cloud-hosted vs on-prem path differs.

## SPL

```spl
index=sharefile (sourcetype="citrix:sharefile:storagezone" OR sourcetype="citrix:sharefile:connector")
| eval zone_ok=if(match(lower(zone_state),"(?i)online|healthy|up"),1,0), backlog=tonumber(coalesce(sync_backlog, queue_depth, 0)), conn_ok=if(match(lower(connector_health),"(?i)ok|up|connected") OR isnull(connector_health),1,0)
| bin _time span=5m
| stats min(zone_ok) as min_zone, max(backlog) as max_backlog, min(conn_ok) as min_connector, values(hosting_mode) as hosting by zone_id, _time
| where min_zone=0 OR max_backlog>10000 OR min_connector=0
| table _time, zone_id, hosting, min_zone, max_backlog, min_connector
```

## Visualization

Single-value: zones unhealthy count; timechart: max sync backlog by zone; table: zone_id, hosting_mode, min zone state, max backlog, connector health; pie or bar: on-prem vs cloud event volume (sanity for split reporting).

## References

- [Citrix — StorageZones Controller](https://docs.citrix.com/en-us/citrix-content-collaboration/storage-zones-controller/4-storage-zones-controllers.html)
