<!-- AUTO-GENERATED from UC-5.3.41.json — DO NOT EDIT -->

---
id: "5.3.41"
title: "Citrix SD-WAN High Availability and VRRP Status"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.3.41 · Citrix SD-WAN High Availability and VRRP Status

> **Criticality:** Critical &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Availability

*We read high-availability and router redundancy style events on the same path so a rehearsed switch and a real fault are both time-stamped in data.*

---

## Description

Appliance and control-plane high availability, including VRRP and overlay tunnels, must stay stable for uninterrupted forwarding. Spurious VRRP transitions, split roles between peers, or tunnel flaps create brownouts. Monitoring role and tunnel state over time localizes a failing unit or a broadcast domain issue on the LAN side of the edge.

## Value

Network operations teams monitor Citrix SD-WAN high availability and VRRP status per site, detecting failovers, peer failures, and split-brain conditions that impact site redundancy.

## Implementation

Correlate HA and VRRP with power and link events from the same site. Set thresholds: any tunnel down over 1 minute; more than N VRRP events per 15 minutes; active role unknown for either peer. For paired appliances, a dashboard row per site should show mirror roles; mismatch triggers immediate investigation. Document flapping that maps to known firmware bugs and upgrade paths.

## Detailed Implementation

### Prerequisites
* Citrix SD-WAN syslog. Key fields: `ha_state` (ACTIVE/STANDBY), `vrrp_state`, `peer_state`, `failover_reason`, `site_name`.
* Citrix SD-WAN HA: two appliances per site in active-standby. VRRP (Virtual Router Redundancy Protocol) manages the virtual IP. Failover should be seamless, but split-brain or delayed failover causes traffic disruption.

### Step 1 — - Configure data collection
Verify HA events:
```spl
index=netscaler sourcetype="citrix:sdwan:syslog" ("HA" OR "VRRP" OR "failover" OR "standby" OR "active" OR "peer") earliest=-7d
| stats count by host
```

### Step 2 — - Create the search and alert

**Primary search -- HA and VRRP status:**
```spl
index=netscaler sourcetype="citrix:sdwan:syslog" ("HA" OR "VRRP" OR "failover" OR "peer") earliest=-24h
| eval ha_event=case(match(_raw, "(?i)active.*to.*standby|demoted"), "DEMOTED", match(_raw, "(?i)standby.*to.*active|promoted"), "PROMOTED", match(_raw, "(?i)peer.*down|peer.*unreachable"), "PEER_DOWN", match(_raw, "(?i)split.?brain"), "SPLIT_BRAIN", match(_raw, "(?i)vrrp.*master"), "VRRP_MASTER", 1==1, null())
| where isnotnull(ha_event)
| eval site=coalesce(site_name, site)
| eval severity=case(ha_event="SPLIT_BRAIN", "CRITICAL -- both active", ha_event="PEER_DOWN", "HIGH -- HA protection lost", ha_event IN ("PROMOTED", "DEMOTED"), "WARNING -- failover occurred", 1==1, "INFO")
| stats count as events latest(_time) as last_event by site, ha_event, severity
| sort severity
```

### Step 3 — - Validate
(a) Check HA status on the SD-WAN appliance management console.
(b) Verify both nodes are reporting to Splunk.
(c) Check VRRP state: both appliances should not be MASTER simultaneously.

### Step 4 — - Operationalize
Dashboard ("Citrix SD-WAN -- HA"):
* Row 1 -- Single-value: "HA pairs", "Failovers (24h)", "Peer down", "Split-brain alerts".
* Row 2 -- HA event history.

Alerting:
* Critical (split-brain): both nodes active -- immediate intervention.
* High (peer down): HA protection lost at site.
* Warning (failover occurred): investigate cause.

### Step 5 — - Troubleshooting

* **Split-brain** -- HA heartbeat link between appliances has failed but both are still operational. Immediate action: determine which should be active, force the other to standby. Fix the HA link.

* **Frequent failovers** -- Check: (1) HA heartbeat link health, (2) appliance resource utilization (CPU/memory), (3) power supply stability.

* **Peer down** -- Check: (1) physical connectivity between appliances, (2) standby appliance power/boot status, (3) management interface.

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

## Known False Positives

Rehearsals, firmware, and line cards can make HA or VRRP messages loud while traffic still fails over as designed.

## References

- [Citrix — SD-WAN high availability and redundancy](https://docs.citrix.com/en-us/citrix-sd-wan/11-4/high-availability.html)
