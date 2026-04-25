<!-- AUTO-GENERATED from UC-5.3.40.json — DO NOT EDIT -->

---
id: "5.3.40"
title: "Citrix SD-WAN WAN Link Health and Standby Failover"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.3.40 · Citrix SD-WAN WAN Link Health and Standby Failover

## Description

SD-WAN sites often bond multiple WAN links with a defined active and standby plan. Health checks, utilization, and failover events show when the primary is saturated, when a standby unexpectedly carries traffic, and when a metered link risks billing overages. Early visibility shortens repair time and controls cost.

## Value

SD-WAN sites often bond multiple WAN links with a defined active and standby plan. Health checks, utilization, and failover events show when the primary is saturated, when a standby unexpectedly carries traffic, and when a metered link risks billing overages. Early visibility shortens repair time and controls cost.

## Implementation

Tag each link with `metered` in a lookup for finance alerts. Alert on failover, sustained high utilization, or standby link carrying production traffic (possible mis-balance). Roll up to site level for a single on-call view. For meter overages, daily sums against monthly caps from procurement.

## Detailed Implementation

Prerequisites: citrix:sdwan:wan_link with link_id, role, state, utilization; optional lookup metered_wan_links.csv for caps. Step 1: Configure data collection — Join metered/billing data via lookup if not in the feed; props for failover_event, util_in_pct, util_out_pct, metered_bytes. Step 2: Create the search and alert — Severe: any failover; warning: 90% utilization for three consecutive 5m on active; finance alert at 80% of monthly cap with two weeks left; if alerts fire on standby links, treat as path imbalance. Step 3: Validate — After controlled lab failover, run `index=sdwan sourcetype="citrix:sdwan:wan_link" | stats latest(state) max(failover) by site_id, link_id` and match appliance UI. Step 4: Operationalize — Map to carrier SLAs, archive monthly meters; if unexpected standby load or failovers continue, escalate to SD-WAN operations and providers; on-call: loop carrier first for last-mile, platform second.

## SPL

```spl
index=sdwan sourcetype="citrix:sdwan:wan_link" earliest=-24h
| eval uin=tonumber(util_in_pct), uout=tonumber(util_out_pct), mbytes=tonumber(metered_bytes), fo=if(match(lower(failover_event),"(?i)yes|true|1|fail"),1,0)
| bin _time span=5m
| stats max(uin) as max_in, max(uout) as max_out, max(mbytes) as max_meter, sum(fo) as failover by _time, site_id, link_id, role, state
| where max_in>90 OR max_out>90 OR failover>0 OR match(lower(state),"(?i)down|failed") OR (role="standby" AND max_in>1 AND max_out>1)
| table _time, site_id, link_id, role, state, max_in, max_out, max_meter, failover
```

## Visualization

Gauge: active link utilization; timeline: failovers; table: top sites for metered bytes; state timeline per link.

## References

- [Citrix — SD-WAN high availability and links](https://docs.citrix.com/en-us/citrix-sd-wan/11-4/high-availability.html)
