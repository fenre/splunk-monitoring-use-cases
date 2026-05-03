<!-- AUTO-GENERATED from UC-5.16.2.json — DO NOT EDIT -->

---
id: "5.16.2"
title: "Connection Table Exhaustion and Session Limits"
status: "verified"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.16.2 · Connection Table Exhaustion and Session Limits

> **Criticality:** Critical &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Availability, Capacity, Fault &middot; **Wave:** Crawl &middot; **Status:** Verified

*We keep an eye on how many conversations each middle box is juggling versus how many it can handle. When the box runs out of room for those conversations, we raise the alarm before calls and apps start dropping.*

---

## Description

Five-minute Splunk rollups compare active optimized flows against platform ceilings per appliance so connection-table pressure nearing exhaustion triggers before TCP resets and tunnel tears degrade branch productivity.

## Value

Incident teams shorten outages by catching finite hardware flow limits early while architects justify upgrades or split pairs using utilization evidence instead of anecdotal complaints about intermittent disconnects.

## Implementation

Emit periodic SNMP/syslog counters with stable field names, schedule alert when peak_util>=85 for two consecutive buckets or worst_pct>=95 instantaneous.

## Detailed Implementation

### Prerequisites
- Known licensed/session limits per model captured in `wanopt_capacity.csv` lookup (`host,capacity_notes`).
- Clock sync and polling interval ≤5 minutes so peaks are not aliased away.
- Change window awareness—software upgrades briefly spike session counts.

### Step 1 — Configure data collection
Enable SNMP OID sets or structured syslog streams exposing active vs maximum flows; avoid proprietary blobs without extraction.

### Step 2 — Create the search and alert
Save SPL as `wanopt_conn_table_pressure`; alert triggers after `worst_pct>=90` for 10 minutes or immediate when syslog severity ERROR matches regex `(?i)htable|flow table full`.

### Step 3 — Validate
During maintenance, artificially raise synthetic flows in lab appliance if permitted—confirm pct_full calculation tracks CLI counters.

### Step 4 — Operationalize
Dashboard pairs utilization thermometers with neighbor HA status; send pager payloads including recommended mitigation (bypass rules, increase timeouts).

### Step 5 — Troubleshooting
**Null limits:** appliances omit gauge until licensed—join lookup.**Short spikes:** microbursts from scans—require sustained predicate.**Asymmetric paths:** ensure both directions polled per serial/cluster.

## SPL

```spl
index=wanop OR index=network earliest=-4h
| eval v=lower(sourcetype)
| eval vendor=case(match(v,"riverbed|steelhead"),"Riverbed SteelHead",match(v,"silverpeak|edgeconnect"),"Silver Peak EdgeConnect",match(v,"citrix"),"Citrix SD-WAN WANOP",match(v,"zdx|zscaler"),"Zscaler Digital Experience","other")
| where vendor!="other"
| eval used=tonumber(coalesce(active_connections,conn_table_used,sessions_in_use,flows_active,n_conn))
| eval limit=tonumber(coalesce(max_connections,session_capacity,max_flows,conn_table_max))
| eval pct_full=if(limit>0 AND isnotnull(used), round(100*used/limit,2), null())
| where isnotnull(pct_full)
| bin _time span=5m
| stats max(pct_full) as peak_util latest(used) as sessions latest(limit) as cap by host vendor _time
| where peak_util>=85
| stats max(peak_util) as worst_pct latest(sessions) as latest_sessions latest(cap) as capacity by host vendor
| sort - worst_pct
```

## Visualization

Heatmap host × vendor with peak_util color scale; adjacent drilldown raw events filtered `htable OR "connection table"`.

## Known False Positives

**Backup windows:** simultaneous DFS synchronizations legitimately fill tables.**Mis-sized defaults:** licenses artificially low vs hardware capacity yield chronic warnings.**SNMP timeouts:** missed polls mimic flat utilization—watch missing-data detectors.**IPv6 transition labs:** dual-stack duplication doubles logical flows briefly.

## References

- [Splunk Documentation — Alert on statistics thresholds](https://docs.splunk.com/Documentation/Splunk/latest/Alert/Definealerts)
- [Citrix SD-WAN WAN Optimization Product Documentation](https://docs.citrix.com/en-us/citrix-sd-wan/)
