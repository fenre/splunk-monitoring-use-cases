<!-- AUTO-GENERATED from UC-5.3.40.json — DO NOT EDIT -->

---
id: "5.3.40"
title: "Citrix SD-WAN WAN Link Health and Standby Failover"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.3.40 · Citrix SD-WAN WAN Link Health and Standby Failover

> **Criticality:** Critical &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Availability

*We follow physical link and standby use on the same edge so a quiet line on purpose and a real cable fault are not the same in hindsight.*

---

## Description

SD-WAN sites often bond multiple WAN links with a defined active and standby plan. Health checks, utilization, and failover events show when the primary is saturated, when a standby unexpectedly carries traffic, and when a metered link risks billing overages. Early visibility shortens repair time and controls cost.

## Value

Network operations teams monitor Citrix SD-WAN WAN link availability and failover events, detecting link failures, standby activations, and bandwidth saturation per site.

## Implementation

Tag each link with `metered` in a lookup for finance alerts. Alert on failover, sustained high utilization, or standby link carrying production traffic (possible mis-balance). Roll up to site level for a single on-call view. For meter overages, daily sums against monthly caps from procurement.

## Detailed Implementation

### Prerequisites
* Citrix SD-WAN syslog or Orchestrator API. Key fields: `wan_link`, `link_state` (UP/DOWN/STANDBY), `bandwidth_total`, `bandwidth_used`, `failover_events`, `site_name`.
* Citrix SD-WAN WAN link states: Active (carrying traffic), Standby (available but not preferred), Down (failed), Metered (LTE/cellular -- usage-limited). Failover from primary to standby should be automatic and fast.

### Step 1 — - Configure data collection
Verify WAN link data:
```spl
index=netscaler (sourcetype="citrix:sdwan:syslog" OR sourcetype="citrix:sdwan:perf") earliest=-4h
| where isnotnull(wan_link) OR isnotnull(link_state)
| stats count by wan_link, link_state
```

### Step 2 — - Create the search and alert

**Primary search -- WAN link health and failover:**
```spl
index=netscaler (sourcetype="citrix:sdwan:syslog" OR sourcetype="citrix:sdwan:perf") earliest=-4h
| eval link=coalesce(wan_link, link_name)
| eval state=coalesce(link_state, link_status)
| eval site=coalesce(site_name, site)
| eval bw_total=coalesce(bandwidth_total, link_bandwidth)
| eval bw_used=coalesce(bandwidth_used, throughput)
| stats latest(state) as current_state latest(bw_used) as current_bw latest(bw_total) as max_bw count(eval(match(_raw, "(?i)(failover|standby.*active|backup.*active)"))) as failover_events by site, link
| eval utilization_pct=if(max_bw > 0, round(100*current_bw/max_bw, 1), null())
| eval status=case(match(lower(current_state), "down"), "CRITICAL -- link DOWN", failover_events > 0, "WARNING -- failover occurred", utilization_pct > 90, "WARNING -- link near capacity", match(lower(current_state), "standby") AND failover_events=0, "INFO -- standby", 1==1, "OK")
| where status != "OK"
| sort status
```

### Step 3 — - Validate
(a) Compare link states with Citrix SD-WAN Orchestrator: Monitor > WAN Links.
(b) Simulate a link failure (if test environment) and verify failover event appears.
(c) Check bandwidth utilization against ISP circuit capacity.

### Step 4 — - Operationalize
Dashboard ("Citrix SD-WAN -- WAN Links"):
* Row 1 -- Single-value: "WAN links", "Links DOWN", "Failovers (4h)", "Highest utilization link".
* Row 2 -- WAN link status table.

Alerting:
* Critical (WAN link DOWN at any site): check ISP circuit.
* Warning (failover to standby occurred): investigate primary link.

### Step 5 — - Troubleshooting

* **Link DOWN** -- Check: (1) ISP circuit status, (2) router interface, (3) SD-WAN appliance interface.

* **Frequent failovers** -- Unstable primary link. Contact ISP for circuit testing. Consider adding a second primary link.

* **Link near capacity** -- Consider bandwidth upgrade or traffic shaping to prioritize critical applications.

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

## Known False Positives

Planned work, long repair windows, and standby links can make link-state logs busy without missing service class.

## References

- [Citrix — SD-WAN high availability and links](https://docs.citrix.com/en-us/citrix-sd-wan/11-4/)
