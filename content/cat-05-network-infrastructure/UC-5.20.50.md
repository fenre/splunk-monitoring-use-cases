<!-- AUTO-GENERATED from UC-5.20.50.json — DO NOT EDIT -->

---
id: "5.20.50"
title: "VRRPv3/HSRPv3 IPv6 Gateway Redundancy Monitoring"
status: "verified"
criticality: "high"
splunkPillar: "IT Operations"
---

# UC-5.20.50 · VRRPv3/HSRPv3 IPv6 Gateway Redundancy Monitoring

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** IT Operations &middot; **Type:** Availability &middot; **Wave:** Walk &middot; **Status:** Verified

*The main router that serves as the front door of each floor needs a backup. If the main door breaks, the backup door opens instantly. We watch for these door switches — each one means something went wrong with the main door. If the doors keep swapping back and forth rapidly, something is seriously wrong. And the worst situation is when both doors are closed and nobody can get out.*

---

## Description

Monitors VRRPv3 and HSRPv3 state transitions for IPv6 virtual gateway redundancy, detecting failovers, split-brain conditions, and gateway loss. IPv6 FHRP behaviour differs from IPv4: the virtual gateway uses a link-local address, hosts discover it via Router Advertisements, and NDP resolves the virtual MAC. A VRRPv3/HSRPv3 failover causes a brief interruption as NDP caches update with the new MAC-to-link-local binding. Frequent failovers (flapping) cause persistent connectivity issues as NDP caches oscillate between the two routers' MACs.

## Value

The default gateway is the single most critical piece of network infrastructure for end users. A missing or flapping default gateway disconnects the entire VLAN from the network. VRRPv3/HSRPv3 provides redundancy, but failover events still cause brief interruptions and — more importantly — indicate an underlying problem with the primary router that needs investigation. Monitoring FHRP state changes catches both the failover itself and the recovery, ensuring the operations team is aware of every gateway disruption. Detecting split-brain (both routers in Master/Active state) catches the most dangerous failure mode, where two routers respond to NDP for the same virtual IP with different MACs.

## Implementation

Collect VRRPv3/HSRPv3 state change syslog events. Track state transitions by group and interface. Alert on failovers, group with no Master/Active, and flapping.

## Detailed Implementation

### Prerequisites
- VRRPv3 or HSRPv3 configured for IPv6 on distribution/core routers.
- Syslog forwarding at severity 5 (notification) for FHRP state changes.
- Understanding of the FHRP group-to-VLAN-to-gateway mapping.

### Step 1 — Configure data collection

**Cisco IOS-XE — VRRPv3 for IPv6:**
```
interface GigabitEthernet0/0/0
 vrrp 10 address-family ipv6
  address FE80::CAFE:1 primary
  address 2001:db8:100::1/64
  priority 110
  preempt delay minimum 60
  track 1 decrement 20
```

**Cisco IOS-XE — HSRPv3 for IPv6:**
```
interface GigabitEthernet0/0/0
 standby version 2
 standby 10 ipv6 autoconfig
 standby 10 priority 110
 standby 10 preempt delay minimum 60
 standby 10 track 1 decrement 20
```

**Syslog messages:**
```
%VRRP-6-STATECHANGE: Gi0/0/0 Grp 10 AF IPv6 state Backup -> Master
%HSRP-5-STATECHANGE: Gi0/0/0 Grp 10 state Standby -> Active
```

**Verification:**
```spl
index=network sourcetype="cisco:ios" ("%VRRP" OR "%HSRP") ("IPv6" OR "AF 2") earliest=-7d
| stats count by host
```

### Step 2 — Create the search and alert

**Failover detection:**
```spl
index=network sourcetype="cisco:ios" ("%VRRP" OR "%HSRP") "STATECHANGE" ("IPv6" OR "AF 2") earliest=-1h
| rex field=_raw "(?<interface>\S+)\s+Grp\s+(?<group>\d+).*state\s+(?<from>\S+)\s*->?\s*(?<to>\S+)"
| eval is_failover=if((from="Backup" AND to="Master") OR (from="Standby" AND to="Active"), 1, 0)
| where is_failover=1
| eval alert="IPv6 gateway failover: " . host . " group " . group . " on " . interface . " became primary"
| table _time, host, interface, group, from, to, alert
```

**Flapping detection:**
```spl
index=network sourcetype="cisco:ios" ("%VRRP" OR "%HSRP") "STATECHANGE" ("IPv6" OR "AF 2") earliest=-4h
| rex field=_raw "(?<interface>\S+)\s+Grp\s+(?<group>\d+)"
| stats count as transitions by host, interface, group
| where transitions > 4
| eval alert="IPv6 gateway flapping: " . transitions . " state changes in 4 hours for group " . group . " on " . host
```

**No primary gateway detection (both routers in Backup/Standby):**
```spl
index=network sourcetype="cisco:ios" ("%VRRP" OR "%HSRP") "STATECHANGE" ("IPv6" OR "AF 2") ("Init" OR "Listen") earliest=-15m
| rex field=_raw "(?<interface>\S+)\s+Grp\s+(?<group>\d+)"
| eval alert="CRITICAL — no primary IPv6 gateway for group " . group . " on " . interface . " — all hosts on this VLAN have lost their default gateway"
| table _time, host, interface, group, alert
```
Trigger: any group where both routers are in Init/Listen/Backup state means no Master — hosts have no gateway.

### Step 3 — Validate
(a) **Controlled failover.** Lower the VRRPv3 priority on the primary router below the standby. Verify the failover is detected in Splunk.

(b) **Recovery.** Restore the priority. With preemption enabled, verify the Master transition back is detected.

(c) **Split-brain test (lab).** Block VRRPv3/HSRPv3 hello messages between two routers (e.g., ACL blocking FF02::12 or FF02::66). Both should become Master/Active. Verify the split-brain alert fires.

### Step 4 — Operationalize

**Dashboard** ("IPv6 — Gateway Redundancy"):
- Row 1 — Single-value: total FHRP groups, groups in normal state, recent failovers.
- Row 2 — Status table: per-group FHRP state with primary router identity.
- Row 3 — Timechart: state changes over 7 days.
- Row 4 — Alerts: active flapping and no-primary conditions.

**Scheduling:** Failover detection continuous. Flapping detection every 30 minutes. No-primary detection every 5 minutes.

**Runbook:**
1. Failover occurred: check the former primary router for hardware, link, or software issues. Check tracked objects.
2. Flapping: check for intermittent link issues (CRC errors, duplex mismatch) or hello timer mismatch between routers.
3. No primary: immediate — both routers are not seeing each other's hellos. Check L2 connectivity between them (VLAN trunking, STP).

### Step 5 — Troubleshooting

- **VRRPv3 vs HSRPv3 event format** — VRRPv3 uses `AF IPv6` in the syslog. HSRPv3 uses group numbering. The search regex must account for both formats.

- **RA interaction** — VRRPv3 Master sends Router Advertisements with the virtual link-local address. When a failover occurs, the new Master starts sending RAs. Hosts update their default gateway based on the new RA. The NDP cache update delay (up to 30 seconds in some implementations) causes a brief connectivity gap during failover.

- **HSRPv3 IPv6 autoconfig** — When using `standby <group> ipv6 autoconfig`, HSRPv3 automatically generates a link-local virtual address. This simplifies configuration but makes manual identification harder. Use `show standby` to see the actual virtual link-local address.

## SPL

```spl
index=network sourcetype="cisco:ios" ("%VRRP" OR "%HSRP") ("STATECHANGE" OR "state") ("IPv6" OR "AF 2") earliest=-24h
| rex field=_raw "(?<interface>\S+)\s+Grp\s+(?<group_id>\d+).*state\s+(?<from_state>\S+)\s*->?\s*(?<to_state>\S+)"
| eval protocol=case(
    match(_raw, "VRRP"), "VRRPv3",
    match(_raw, "HSRP"), "HSRPv3",
    1=1, "unknown")
| eval severity=case(
    to_state="Master" OR to_state="Active", "WARNING — failover occurred (this router is now primary)",
    to_state="Backup" OR to_state="Standby", "WARNING — this router is no longer primary",
    to_state="Init" OR to_state="Listen", "CRITICAL — no primary router",
    1=1, "INFO")
| table _time, host, protocol, interface, group_id, from_state, to_state, severity
| sort -_time
```

## Visualization

(1) Status table: per-group FHRP state (green=stable Master/Active, yellow=recent failover, red=no primary). (2) Timechart: state changes over 7 days. (3) Single-value: current failover count. (4) Drilldown: state transition history per group.

## Known False Positives

**Planned maintenance.** Taking the primary router offline for maintenance causes an expected failover to the standby. Correlate with change management.

**Preemption after recovery.** When the primary router recovers from a failure, VRRPv3 preemption causes a state change from Backup to Master. This is a second state change event for the same incident and is expected.

**Interface tracking triggers.** VRRPv3/HSRPv3 can track upstream interface or route status. If a tracked interface goes down (e.g., WAN link), the FHRP priority is decremented, causing a failover to the standby — even though the primary router itself is healthy. This is by design for upstream failure detection.

## References

- [RFC 5798 — Virtual Router Redundancy Protocol (VRRP) Version 3 for IPv4 and IPv6](https://www.rfc-editor.org/rfc/rfc5798)
- [Cisco HSRPv3 and VRRPv3 Configuration Guide for IPv6](https://www.cisco.com/c/en/us/td/docs/ios-xml/ios/ipapp_fhrp/configuration/xe-17/fhp-xe-17-book.html)
