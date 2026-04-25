<!-- AUTO-GENERATED from UC-5.3.41.json — DO NOT EDIT -->

---
id: "5.3.41"
title: "Citrix SD-WAN High Availability and VRRP Status"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.3.41 · Citrix SD-WAN High Availability and VRRP Status

## Description

Appliance and control-plane high availability, including VRRP and overlay tunnels, must stay stable for uninterrupted forwarding. Spurious VRRP transitions, split roles between peers, or tunnel flaps create brownouts. Monitoring role and tunnel state over time localizes a failing unit or a broadcast domain issue on the LAN side of the edge.

## Value

Appliance and control-plane high availability, including VRRP and overlay tunnels, must stay stable for uninterrupted forwarding. Spurious VRRP transitions, split roles between peers, or tunnel flaps create brownouts. Monitoring role and tunnel state over time localizes a failing unit or a broadcast domain issue on the LAN side of the edge.

## Implementation

Correlate HA and VRRP with power and link events from the same site. Set thresholds: any tunnel down over 1 minute; more than N VRRP events per 15 minutes; active role unknown for either peer. For paired appliances, a dashboard row per site should show mirror roles; mismatch triggers immediate investigation. Document flapping that maps to known firmware bugs and upgrade paths.

## Detailed Implementation

Prerequisites
• `index=sdwan` with `citrix:sdwan:ha|vrrp|tunnel` sourcetypes. Stable `site_id` and VRRP `group_id` via `REPORT-` in `props` (regex from syslog) or JSON path. Runbook: site to circuit, peer names.

Step 1 — Configure data collection
JSON preferred. Syslog: `line_breaker`, `EXTRACT-` for role strings `active/standby/master/backup`. Deduplicate dual logs: `dedup` on `_time+site+group`. Poll tunnels 1m; mark cumulative counters if applicable.

Step 2 — Create the search and alert
Sev-1: tunnel `down`>2 aligned bins. Sev-2: `vrrp_events`>4/15m or `cur_role` in unknown,init,disabled. Add dynamic threshold: 2x site’s 7d mean flap count. Correlation: if tunnel down but VRRP quiet, underlay; both noisy, split-brain risk.

Step 3 — Validate
Compare path, site, and policy state in the SD-WAN orchestrator or on-appliance health views for the same time range as the search.
Step 4 — Operationalize
Site matrix panel: A/B role, tunnel, event rate. RFO: attach chart. Escalation: on-call for Sev-1, SD-WAN TAC with serials; note version for bug DB. Maintenance windows: suppress with saved-search schedule.

## SPL

```spl
index=sdwan (sourcetype="citrix:sdwan:ha" OR sourcetype="citrix:sdwan:vrrp" OR sourcetype="citrix:sdwan:tunnel") earliest=-4h
| eval role=lower(coalesce(ha_role, vrrp_state, "")), tstate=lower(coalesce(tunnel_state, "")), vtrans=if(match(_raw, "(?i)vrrp|transition|master|backup"),1,0)
| bin _time span=1m
| stats latest(role) as cur_role, latest(tstate) as tun, sum(vtrans) as vrrp_events by _time, site_id, group_id
| where match(cur_role,"(?i)unknown|init|disabled") OR match(tun,"(?i)down|degraded|failed") OR vrrp_events>0
| table _time, site_id, group_id, cur_role, tun, vrrp_events
```

## Visualization

Timeline: HA role per site; line: VRRP event rate; state matrix: two appliances per site with color; tunnel up/down count.

## References

- [Citrix — SD-WAN high availability and redundancy](https://docs.citrix.com/en-us/citrix-sd-wan/11-4/high-availability.html)
