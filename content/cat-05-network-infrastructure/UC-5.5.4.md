<!-- AUTO-GENERATED from UC-5.5.4.json — DO NOT EDIT -->

---
id: "5.5.4"
title: "Path Failover Events"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.5.4 · Path Failover Events

> **Criticality:** Medium &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Availability

*We keep an eye on how our wide-area links and SD-WAN paths are behaving so we spot a bad circuit or policy issue before branch users lose voice, video, or critical apps.*

---

## Description

Tracks when traffic switches between WAN transports. Frequent failovers indicate unstable links.

## Value

Network operations teams track SD-WAN path failover events to detect transport degradation, identify flapping circuits, quantify cost impact of metered backup transports, and validate automatic failover/failback behavior.

## Implementation

Collect vManage alarm/event data. Track path changes and failover frequency. Alert on frequent failovers.

## Detailed Implementation

### Prerequisites
- Cisco Catalyst Add-on for Splunk polling vManage for application-aware routing events and control connection logs. Data in `index=sdwan` with `sourcetype=cisco:sdwan:approute` (path changes) or `sourcetype=cisco:sdwan:alarm` (tunnel/path alarms). Key fields: `site_id`, `system_ip`, `old_sla_class`, `new_sla_class`, `old_preferred_color`, `new_preferred_color`, `reason`.
- SD-WAN path failover occurs when: (1) tunnel SLA degrades below the configured SLA class threshold, (2) a tunnel goes down entirely, (3) BFD detects loss of connectivity. The SD-WAN controller (vSmart) updates the routing to use the next-best path.
- Build a `sdwan_transports.csv` lookup: `color,transport_name,provider,monthly_cost` (e.g., `mpls,MPLS-Primary,AT&T,$5000`, `biz-internet,Internet-Backup,Comcast,$500`, `lte,LTE-Failover,Verizon,metered`). This helps quantify the cost impact of failovers (e.g., traffic shifting from MPLS to metered LTE).

### Step 1 — Configure data collection
Verify path change events:
```spl
index=sdwan (sourcetype="cisco:sdwan:approute" OR sourcetype="cisco:sdwan:alarm") earliest=-24h
| search "path" OR "failover" OR "sla" OR "color"
| stats count by sourcetype, site_id
```

### Step 2 — Create the search and alert

**Primary search — Path failover events:**
```spl
index=sdwan sourcetype="cisco:sdwan:approute" earliest=-4h
| where old_preferred_color != new_preferred_color
| lookup sdwan_sites.csv site_id OUTPUT site_name tier
| lookup sdwan_transports.csv color as old_preferred_color OUTPUT transport_name as from_transport provider as from_provider
| lookup sdwan_transports.csv color as new_preferred_color OUTPUT transport_name as to_transport provider as to_provider
| eval failover_direction=from_transport." → ".to_transport
| eval cost_impact=case(new_preferred_color="lte", "HIGH (metered)", new_preferred_color="biz-internet" AND old_preferred_color="mpls", "MEDIUM (lower SLA)", 1==1, "LOW")
| stats count as failover_count latest(_time) as last_failover values(failover_direction) as paths by site_name, tier, system_ip
| eval last_failover=strftime(last_failover, "%Y-%m-%d %H:%M:%S")
| sort -failover_count
```

#### Understanding this SPL: Detects when SD-WAN changes the preferred transport path for traffic. `old_preferred_color` and `new_preferred_color` indicate the transport switch. The cost_impact evaluation is critical: failover to LTE incurs metered charges that can be expensive if sustained; failover from MPLS to internet means lower SLA guarantees.

**Flapping detection (frequent back-and-forth failovers):**
```spl
index=sdwan sourcetype="cisco:sdwan:approute" earliest=-2h
| where old_preferred_color != new_preferred_color
| bin _time span=10m
| stats count as failovers dc(new_preferred_color) as paths_used by _time, site_id, system_ip
| where failovers > 4
| lookup sdwan_sites.csv site_id OUTPUT site_name
| eval flap_severity=case(failovers > 20, "CRITICAL", failovers > 10, "HIGH", 1==1, "WARNING")
```

**Failover duration analysis:**
```spl
index=sdwan sourcetype="cisco:sdwan:approute" earliest=-24h
| where old_preferred_color != new_preferred_color
| sort system_ip, _time
| streamstats current=f window=1 last(_time) as prev_time last(new_preferred_color) as prev_color by system_ip
| eval time_on_failover=if(isnotnull(prev_time), _time - prev_time, null())
| where isnotnull(time_on_failover) AND prev_color != old_preferred_color
| eval duration_min=round(time_on_failover/60, 1)
| stats avg(duration_min) as avg_failover_min max(duration_min) as max_failover_min count as failbacks by site_id
| lookup sdwan_sites.csv site_id OUTPUT site_name
| sort -avg_failover_min
```

### Step 3 — Validate
(a) In vManage: Monitor > Application-Aware Routing > check path history for a device. Failover events should correspond.
(b) Simulate a failover: on a test device, shut down an interface and verify the failover event appears in Splunk within the polling interval.
(c) Check a known ISP outage window and verify failover events occurred for affected sites.

### Step 4 — Operationalize
Dashboard ("SD-WAN — Path Failovers"):
- Row 1 — Single-value tiles: "Failovers (4h)", "Sites with active failovers", "Flapping devices", "LTE failovers (cost alert)".
- Row 2 — Failover events table: site, device, from transport, to transport, cost impact, count.
- Row 3 — Flapping detection: devices with > 4 failovers per 10-minute window.
- Row 4 — Failover trending over 24h.

Alerting:
- Critical (flapping > 20 failovers in 10 minutes): device is oscillating between paths — investigate immediately.
- High (failover to LTE on Tier1 site): metered costs accumulating — restore primary transport.
- Warning (any path failover): informational — track for pattern analysis.

### Step 5 — Troubleshooting

- **No failover events detected** — The TA may not be collecting approute change data. Check if the vManage API endpoint `/dataservice/statistics/approute` returns path change events.

- **Excessive flapping between MPLS and Internet** — Both transports are near the SLA threshold. The solution is to: widen the SLA hysteresis (configure different thresholds for failover vs. failback), or fix the underlying transport quality issue.

- **Failover to LTE never fails back** — The primary transport recovered but AAR didn't switch back. Check the failback timer in the AAR policy. Some configurations require manual failback or have a long timer (30+ min) to avoid flapping.

## SPL

```spl
index=sdwan sourcetype="cisco:sdwan:events" ("failover" OR "path-change" OR "transport-switch")
| stats count by site, from_transport, to_transport | sort -count
```

## Visualization

Table, Sankey diagram (from/to transport), Timeline.

## Known False Positives

Tunnels may renegotiate during ISP maintenance, BFD timer changes, planned controller upgrades, or policy pushes; short blips may look like failures when the business path is still acceptable.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
