<!-- AUTO-GENERATED from UC-5.17.3.json — DO NOT EDIT -->

---
id: "5.17.3"
title: "TAP and SPAN Session Health"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.17.3 · TAP and SPAN Session Health

> **Criticality:** High &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Availability, Operations, Physical &middot; **Wave:** Crawl &middot; **Status:** Verified

*Think of a security camera cable: if the cable goes quiet, the recorder sees nothing even when the room is busy. We watch those cables and mirror ports so we know the feed going to our tools is alive, not silently blank.*

---

## Description

Splunk stitches TAP pair identifiers and SPAN monitor sessions with ten-minute health snapshots so dark fibers, mis-seated modules, or administrative shutdowns on visibility ingress stop masquerading as tool outages downstream.

## Value

Forensics teams retain trustworthy packet lineage because Splunk proves capture paths stayed lit during investigations while datacenter techs receive faster dispatch tickets pointing to the precise span or optical leg.

## Implementation

Tag maintenance windows in a lookup keyed by `span_id`; require dual corroboration (syslog plus SNMP) before paging passive TAP LOS alarms prone to transceiver swaps.

## Detailed Implementation

### Prerequisites
- Cable database mapping TAP/SPAN IDs to switch ports and peer racks.
- Photo baseline of optical budgets for comparison when alarms cite dB loss.
- Escalation matrix distinguishing campus networking vs visibility engineering ownership.

### Step 1 — Turn on telemetry
Export Garland link events, Gigamon blade LOS traps, Keysight TAP health JSON, and Cisco SPAN syslog into Splunk with consistent `span_id` naming aligned to CMDB.

### Step 2 — Normalize health booleans
Translate vendor-specific enumerations into `healthy` using shared macros so dashboards remain vendor-agnostic.

### Step 3 — Author saved search
Schedule `tap_span_health_offenders` every ten minutes with suppression after acknowledgement token written via KVStore.

### Step 4 — Validate
Physically break a lab TAP leg—confirm Splunk fires within two collection intervals and drilldown shows both witnesses.

### Step 5 — Operationalize
Embed QR-coded rack diagrams in dashboard drilldowns; monthly review Splunk trend of flapping interfaces to schedule fiber replacements proactively.

## SPL

```spl
index=visibility OR index=network earliest=-12h
| eval v=lower(sourcetype)
| eval path_type=case(match(v,"garland|tap"),"Passive TAP",match(v,"gigamon"),"GigaVUE Link",match(v,"keysight|ixia|vision"),"Vision TAP",match(v,"cisco|switch"),"SPAN Source","other")
| where path_type!="other"
| eval healthy=case(lower(coalesce(link_status,if_oper_status,"")) IN ("up","link_up","online","ok") AND NOT match(_raw,"(?i)(los|signal_loss|lol|down|failed)"),1,match(lower(coalesce(link_status,if_oper_status,"")),"admin.?down|disabled") AND match(_raw,"(?i)maintenance"),1,0)
| eval span_id=coalesce(span_session_id,monitor_session,tap_pair_id)
| bin _time span=10m
| stats latest(healthy) as last_ok values(signal_loss_db) as optics dc(host) as witnesses by span_id path_type source_interface
| where last_ok=0
| eval summary=coalesce(source_interface,"unknown_if") . " | " . path_type
| sort path_type span_id
```

## Visualization

Status timeline (`splunk.timeline`) per span_id; GIS-style optional rack column; red highlight table listing unhealthy paths with last optics reading.

## Known False Positives

**Scheduled SPAN rebalances:** brief admin-down states trigger alarms—honor change calendar.**Cold spare TAP ports:** remain administratively dark intentionally.**SNMP stale caches:** neighbor switch shows `up` though TAP LOS fired—prefer appliance-native telemetry.**Transceiver vendor swaps:** transient LOS during module replacement.

## References

- [Garland Technology — Network TAP resources](https://www.garlandtechnology.com/resources)
- [Splunk Documentation — Building alerts from searches](https://docs.splunk.com/Documentation/Splunk/latest/Alert/)
- [Cisco Catalyst SPAN configuration guide (mirrored sessions)](https://www.cisco.com/c/en/us/td/docs/switches/lan/catalyst9300/software/release/17-9/configuration_guide/nmgmt/b_179_nmgmt_9300_cg.pdf)
