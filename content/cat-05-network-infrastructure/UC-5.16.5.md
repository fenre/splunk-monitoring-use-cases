<!-- AUTO-GENERATED from UC-5.16.5.json — DO NOT EDIT -->

---
id: "5.16.5"
title: "Appliance Pair (In-Path) Health and Redundancy"
status: "verified"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.16.5 · Appliance Pair (In-Path) Health and Redundancy

> **Criticality:** Critical &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Availability, Resilience, Operations &middot; **Wave:** Crawl &middot; **Status:** Verified

*Most offices have two boxes backing each other up so the internet helper keeps working if one gets sick. We compare notes from both boxes so we notice when only half the team is left standing.*

---

## Description

Quarter-hour Splunk bucketing counts healthy appliances sharing identical HA pair identifiers so asymmetric failover—only one surviving member online—or oscillating cluster partitions triggers paging ahead of black-holed WAN segments.

## Value

Branch resilience audits rely on automated quorum telemetry rather than quarterly manual CLI snapshots while auditors prove redundancy commitments during SOC exercises referencing Splunk-backed timelines.

## Implementation

Map orchestrator exports into deterministic `pair` keys, mute transient flap alerts using `streamstats` requiring three consecutive failing buckets.

## Detailed Implementation

### Prerequisites
- CMDB linking serial numbers to street addresses for notification routing.
- Clarified naming scheme so active/standby pairs share identical `pair` tokens.
- Maintenance playbook referencing bypass cabling steps when hardware fails.

### Step 1 — Configure data collection
Ensure failover syslog severity retained even during floods; configure persistence queues on forwarders.

### Step 2 — Create the search and alert
Save SPL as `wanopt_ha_pair_gap`; alert when `healthy_appliances==1 AND total_seen>=2` for thirty minutes.

### Step 3 — Validate
Fail lab secondary intentionally—confirm Splunk transitions align with optical bypass LED patterns.

### Step 4 — Operationalize
Glass-table style dashboard overlays vendor icons with pair clusters and embedded runbook URLs.

### Step 5 — Troubleshooting
**Split-brain:** totals mismatch across syslog duplicates—dedupe by serial.**Cloud-managed EdgeConnect:** aggregator delay—extend `_time` tolerance.**ZDX-only witnesses:** do not infer hardware HA solely from cloud probes.

## SPL

```spl
index=wanop OR index=network earliest=-8h
| eval v=lower(sourcetype)
| eval vendor=case(match(v,"riverbed|steelhead"),"Riverbed SteelHead",match(v,"silverpeak|edgeconnect"),"Silver Peak EdgeConnect",match(v,"citrix"),"Citrix SD-WAN WANOP",match(v,"zdx|zscaler"),"Zscaler Digital Experience","other")
| where vendor!="other"
| eval pair=coalesce(ha_group,inpath_pair_id,cluster_name,deployment_site,"singleton")
| eval healthy=case(match(lower(coalesce(alarm_level,severity,"")),"critical|major|down|failed"),0,match(lower(coalesce(appliance_state,health_status,opt_status,"")),"online|up|ok|healthy|nominal"),1,isnull(appliance_state) AND NOT match(_raw,"(?i)(failover|down|offline|lost peer)"),1,0)
| bin _time span=15m
| stats dc(eval(if(healthy=1,host,null()))) as healthy_appliances dc(host) as total_seen values(appliance_state) as states max(eval(if(healthy=0,1,0))) as fault_seen by pair vendor _time
| eval quorum_ratio=if(total_seen>0, round(healthy_appliances/total_seen,3), null())
| where total_seen>0 AND healthy_appliances<total_seen
| stats latest(quorum_ratio) as quorum latest(healthy_appliances) as healthy latest(total_seen) as declared_members latest(states) as raw_states by pair vendor
| sort quorum vendor pair
```

## Visualization

Chord diagram optional; pragmatic cluster matrix listing pair vs quorum_ratio plus sparkline from stacked stats.

## Known False Positives

**Rolling reboot cadence:** vendor-approved sequential upgrades mimic outages.**Telemetry gaps:** missing syslog falsely lowers totals—apply `_indextime` staleness guard.**Single-appliance pilot sites:** filter where CMDB marks `ha_expected=false`.

## References

- [Splunk Documentation — Use stats and chart commands](https://docs.splunk.com/Documentation/Splunk/latest/SearchReference/Stats)
- [Riverbed SteelHead High Availability Overview](https://support.riverbed.com/content/support/software/steelhead.html)
