<!-- AUTO-GENERATED from UC-5.2.14.json — DO NOT EDIT -->

---
id: "5.2.14"
title: "Firewall HA Failover Events"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.2.14 · Firewall HA Failover Events

> **Criticality:** Critical &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Availability

*We catch failover and high-availability events so the team knows which box was live, and whether a handover was clean or a surprise.*

---

## Description

HA failovers cause brief traffic disruption and can indicate underlying hardware or link failures. Tracking failover frequency detects instability.

## Value

Operations teams track firewall HA failover events, heartbeat losses, and state transitions, detecting loss of redundancy and investigating root causes of failovers.

## Implementation

Forward firewall system logs to Splunk. Alert on any active/passive transition. Correlate with link down events. Track failover frequency — more than 1 per week indicates instability.

## Detailed Implementation

### Prerequisites
* Firewall HA (High Availability) logs. Palo Alto: `sourcetype=pan:system` (HA events), Fortinet: `sourcetype=fgt_event` (HA events), Cisco FTD: HA syslog events, Juniper SRX: chassis cluster events. Key events: failover trigger, state change (active/passive/active-active), heartbeat loss, link monitoring failure.

### Step 1 — - Configure data collection
Verify HA events:
```spl
index=firewall earliest=-7d
| where match(_raw, "(?i)failover|HA.*(state|change|transition|active|passive|standby)|heartbeat|cluster|redundancy|preempt")
| stats count by host, sourcetype
```

### Step 2 — - Create the search and alert

**Primary search -- HA failover event detection:**
```spl
index=firewall earliest=-7d
| where match(_raw, "(?i)failover|HA.*(state|change|transition)|heartbeat.*(lost|fail)|cluster.*(failover|switchover|transition)|active.*to.*passive|passive.*to.*active|standby.*to.*active")
| eval ha_event=case(match(_raw, "(?i)failover.*trigger|switchover"), "FAILOVER_TRIGGERED", match(_raw, "(?i)heartbeat.*(lost|fail|miss)"), "HEARTBEAT_LOST", match(_raw, "(?i)link.*monitor.*(fail|down)"), "LINK_MONITOR_FAIL", match(_raw, "(?i)preempt"), "PREEMPTION", match(_raw, "(?i)passive.*to.*active|standby.*to.*active|became.*active"), "BECAME_ACTIVE", match(_raw, "(?i)active.*to.*passive|became.*passive|became.*standby"), "BECAME_PASSIVE", 1==1, "HA_EVENT")
| eval node=coalesce(host, device_name)
| stats count as events latest(_time) as last_event by node, ha_event
| eval severity=case(ha_event="HEARTBEAT_LOST", "CRITICAL -- HA peer unreachable", ha_event="FAILOVER_TRIGGERED", "HIGH -- failover occurred", ha_event="LINK_MONITOR_FAIL", "HIGH -- link failure triggered failover", ha_event="PREEMPTION", "WARNING -- preemption event", 1==1, "INFO")
| where severity != "INFO"
| sort severity, -events
```

### Step 3 — - Validate
(a) Palo Alto: `show high-availability all` -- shows HA state and peer status.
(b) Fortinet: `get system ha status` -- shows cluster status and role.
(c) Simulate failover (if in maintenance window) and verify events appear.

### Step 4 — - Operationalize
Dashboard ("Firewall -- HA Status"):
* Row 1 -- Single-value: "Failovers (7d)", "Heartbeat losses", "Current HA state".
* Row 2 -- HA event timeline.

Alerting:
* Critical (heartbeat lost): HA peer may be down -- single point of failure.
* High (failover triggered): investigate root cause.

### Step 5 — - Troubleshooting

* **Frequent failovers (flapping)** -- Check: (1) HA heartbeat link stability (dedicated link recommended), (2) link monitoring thresholds too sensitive, (3) hardware issue on one node causing intermittent failures.

* **Heartbeat lost but peer is up** -- HA heartbeat link may have a physical issue. Check: (1) cable/SFP on HA ports, (2) switch port configuration for HA VLAN, (3) latency between HA peers.

* **Sessions lost during failover** -- Verify session synchronization: Palo Alto: `show high-availability state-synchronization`, Fortinet: `get system ha status` -- check session pickup. Active-Active requires session sync to be enabled.

## SPL

```spl
index=firewall (sourcetype="pan:system" "HA state change") OR (sourcetype="fgt_event" subtype="ha")
| rex "state change.*from (?<old_state>\w+) to (?<new_state>\w+)"
| table _time, dvc, old_state, new_state | sort -_time
```

## Visualization

Timeline (failover events), Single value (failovers this month), Table (history).

## Known False Positives

Test failovers, maintenance failovers, and power events trigger HA messages even when the network is under control.

## References

- [Splunk_TA_paloalto](https://splunkbase.splunk.com/app/2757)
