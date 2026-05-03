<!-- AUTO-GENERATED from UC-5.1.23.json — DO NOT EDIT -->

---
id: "5.1.23"
title: "HSRP/VRRP State Changes"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.1.23 · HSRP/VRRP State Changes

> **Criticality:** Critical &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Availability

*We help you know early when something looks wrong with hsrp/vrrp state changes so the team can act before it grows into a bigger outage.*

---

## Description

Gateway redundancy state changes impact all hosts on a subnet. Detecting unexpected failovers prevents prolonged outages. VRRPv3 (RFC 5798) supports IPv4 and IPv6 in one protocol; HSRPv2 also adds IPv6 — validate both families where deployed.

## Value

NOC teams track HSRP/VRRP state changes to detect default gateway failover events and flapping, ensuring first-hop redundancy remains stable for client connectivity.

## Implementation

Enable HSRP/VRRP syslog notifications. Alert on Active/Master transitions. Correlate with interface or device failures to validate failover cause.

## Detailed Implementation

### Prerequisites
* HSRP (Hot Standby Router Protocol) and VRRP (Virtual Router Redundancy Protocol) state change syslog messages. Data in `index=network` with `sourcetype=cisco:ios` or vendor-specific sourcetypes. Key mnemonics: Cisco HSRP `%HSRP-5-STATECHANGE`; VRRP `%VRRP-6-STATECHANGE`.
* HSRP/VRRP: provides default gateway redundancy. Two routers share a virtual IP. One is Active/Master, other is Standby/Backup. State changes indicate failover events -- planned (priority change, preemption) or unplanned (active router failure).

### Step 1 — - Configure data collection
```
# Cisco IOS -- HSRP/VRRP state changes are logged automatically
# HSRP:
interface Vlan100
 standby 1 ip 10.0.100.1
 standby 1 priority 110
 standby 1 preempt
 standby 1 track GigabitEthernet0/1

# Syslog is automatic for state changes
```
Verify:
```spl
index=network earliest=-30d
| where match(_raw, "(?i)HSRP.*STATE|VRRP.*STATE|standby.*state|vrrp.*master|vrrp.*backup")
| stats count by host
```

### Step 2 — - Create the search and alert

**Primary search -- HSRP/VRRP state change tracking:**
```spl
index=network earliest=-30d
| where match(_raw, "(?i)HSRP.*STATE|VRRP.*STATE|standby.*state|vrrp.*transition")
| rex field=_raw "(?i)(?:group|Group)\s+(?<group_id>\d+)"
| rex field=_raw "(?i)(?:interface|Interface|Vlan)\s*(?<vlan_intf>\S+)"
| rex field=_raw "(?i)state\s+(?<old_state>\w+)\s+->\s+(?<new_state>\w+)"
| eval device=coalesce(host, device_name)
| eval new_state=lower(coalesce(new_state, if(match(_raw, "(?i)active|master"), "active", "standby")))
| eval protocol=if(match(_raw, "(?i)HSRP"), "HSRP", "VRRP")
| sort device, group_id, _time
| stats count as events count(eval(new_state="active" OR new_state="master")) as became_active count(eval(new_state="standby" OR new_state="backup")) as became_standby latest(new_state) as current_state by device, protocol, group_id, vlan_intf
| eval severity=case(
    events > 4, "WARNING -- ".protocol." group ".group_id." flapping",
    became_active > 0 AND became_standby > 0, "INFO -- ".protocol." failover and recovery occurred",
    1==1, "INFO")
| where severity != "INFO" OR events > 1
| sort severity, -events
```

### Step 3 — - Validate
(a) CLI: `show standby brief` (HSRP) or `show vrrp brief` (VRRP) -- current states.
(b) CLI: `show standby` -- detailed group info including priority and preempt.
(c) Verify tracking objects: `show track brief`.

### Step 4 — - Operationalize
Dashboard ("Network -- Gateway Redundancy"):
* Row 1 -- Single-value: "State changes (30d)", "Groups flapping".
* Row 2 -- HSRP/VRRP state change timeline.

Alert: Warning (HSRP/VRRP group flapping): gateway instability affecting clients.

### Step 5 — - Troubleshooting

* **Unexpected failover** -- Check tracking objects: interface tracking may have triggered priority decrease. Verify: `show track` and correlate with interface down events (UC-5.1.1).

* **Flapping between active/standby** -- Both routers have same or similar priority. Ensure clear priority difference and preempt configuration. Check: timer mismatch between peers.

* **Both routers in standby** -- Neither assumes active role. Check: group IP configuration matches on both. Verify: HSRP/VRRP multicast (224.0.0.2 / 224.0.0.18) is not blocked by ACL.

**IPv6 Coverage:** VRRPv3 (RFC 5798) supports both IPv4 and IPv6. HSRP version 2 also supports IPv6. VRRPv3 uses FF02::12 multicast and link-local VIP addressing. Validate with `show vrrp ipv6 brief`. Verify FF02::12 is not blocked by ACLs.

## SPL

```spl
index=network sourcetype="cisco:ios" "%HSRP-5-STATECHANGE" OR "%VRRP-6-STATECHANGE"
| rex "Grp (?<group>\d+) state (?<old_state>\w+) -> (?<new_state>\w+)"
| where new_state="Active" OR new_state="Master"
| stats count by host, group, old_state, new_state | sort -_time
```

## Visualization

Timeline (state changes), Table (group, host, transition), Alert panel.

## Known False Positives

Hardware sensor warnings during power redundancy testing, scheduled maintenance, or environmental swings. Lab gear often logs benign transitions.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
