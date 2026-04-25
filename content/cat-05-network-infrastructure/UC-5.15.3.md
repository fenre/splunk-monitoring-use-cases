<!-- AUTO-GENERATED from UC-5.15.3.json — DO NOT EDIT -->

---
id: "5.15.3"
title: "Infoblox Grid Replication Lag and Member Sync Status (Infoblox)"
criticality: "critical"
splunkPillar: "IT Operations"
---

# UC-5.15.3 · Infoblox Grid Replication Lag and Member Sync Status (Infoblox)

## Description

When Grid replication falls behind, DNS and DHCP views diverge between members—leading to intermittent resolution failures or stale RPZ data. Audit events are often the earliest observable signal before user impact.

## Value

DNS architects detect split-brain or lagging members quickly, schedule controlled Grid restarts, and avoid prolonged inconsistency across sites.

## Implementation

Forward all Grid and member audit categories. Create correlation searches for keywords such as replication, serial mismatch, disconnected member, or database join failure. Track event rate per member pair and alert on absence of healthy heartbeat logs.

## Detailed Implementation

Prerequisites
• Ingest `infoblox:audit` for Grid, replication, and member state into `index=dns` or a dedicated index.
• Map severity so truly critical strings can drive paging.

Step 1 — Configure data collection
Forward all audit categories that mention serial mismatch, join failure, or disconnected members; keep Grid Manager time in sync (NTP).

Step 2 — Create the search and alert
```spl
index=dns sourcetype="infoblox:audit" earliest=-4h
| search replication OR "grid" OR "database" OR "serial" OR "out of sync" OR "disconnected" OR "member"
| rex field=_raw "(?i)member[\s:]+(?<member>[^\s,]+)"
| stats count values(message) as notes latest(_time) as last by member, host
| where count>=1
| sort -last
```

Understanding this SPL
We key off replication, grid, and member keywords, then list recent text per member so operators see lag or split conditions.

Step 3 — Validate
In Grid Manager, open the member or replication status for the time of the event and read the same messages Splunk received. Confirm serial numbers, member hostnames, and last sync time match; use `show network` or the Infoblox CLI on a lab member to compare a sample message if needed.

Step 4 — Operationalize
Route sustained replication loss to the DNS and DHCP owners; include member pairs in the ticket.

Step 5 — Troubleshooting
If noise is high, add explicit phrases from your NIOS version to the search; if too quiet, confirm audit filters are not dropping replication events.

## SPL

```spl
index=dns sourcetype="infoblox:audit" earliest=-4h
| search replication OR "grid" OR "database" OR "serial" OR "out of sync" OR "disconnected" OR "member"
| rex field=_raw "(?i)member[\s:]+(?<member>[^\s,]+)"
| stats count values(message) as notes latest(_time) as last by member, host
| where count>=1
| sort -last
```

## Visualization

Timeline (audit severity), table (member, last sync message, object), map (site/member status).

## References

- [Splunk Documentation — Sourcetypes for the Splunk Add-on for Infoblox](https://docs.splunk.com/Documentation/AddOns/released/Infoblox/Sourcetypes)
- [Splunkbase — Splunk Add-on for Infoblox](https://splunkbase.splunk.com/app/2934)
- [Infoblox NIOS — Grid and replication concepts](https://docs.infoblox.com/)
