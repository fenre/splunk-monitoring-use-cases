<!-- AUTO-GENERATED from UC-5.20.43.json — DO NOT EDIT -->

---
id: "5.20.43"
title: "OSPFv3 Adjacency Monitoring and IPv6 Routing Stability"
status: "verified"
criticality: "critical"
splunkPillar: "IT Operations"
---

# UC-5.20.43 · OSPFv3 Adjacency Monitoring and IPv6 Routing Stability

> **Criticality:** Critical &middot; **Difficulty:** Intermediate &middot; **Pillar:** IT Operations &middot; **Type:** Availability &middot; **Wave:** Walk &middot; **Status:** Verified

*The routers that carry IPv6 traffic need to be good neighbours — they constantly check on each other to share road maps. If a neighbour stops responding, the others have to quickly reroute traffic around the gap. We watch for these 'neighbour down' events because they mean some roads are suddenly closed and traffic might be taking a longer detour — or worse, getting lost.*

---

## Description

Monitors OSPFv3 adjacency state changes to detect IPv6 routing instability, neighbor loss, and adjacency flapping. OSPFv3 is the IPv6-native OSPF variant that uses link-local addresses for peering and IPsec for authentication. Adjacency failures in OSPFv3 cause IPv6 route withdrawals and traffic blackholing. OSPFv3-specific failure modes include IPsec authentication mismatches, Instance ID conflicts, and link-local address issues that do not have equivalents in OSPFv2.

## Value

OSPFv3 adjacency loss is the immediate precursor to IPv6 route withdrawal. Detecting the adjacency change gives the operations team a head start on troubleshooting before users report connectivity loss. OSPFv3 has unique failure modes — IPsec misconfiguration is much harder to diagnose than OSPFv2 MD5 authentication failures because the symptoms are similar (adjacency won't form) but the troubleshooting is different (IPsec SA vs OSPF auth key). Monitoring adjacency state transitions provides the first diagnostic indicator and guides the troubleshooting toward the correct root cause.

## Implementation

Collect OSPFv3 ADJCHG syslog events from all routers. Track adjacency state transitions. Alert on adjacency losses and flapping. Correlate with interface events and IPsec errors.

## Detailed Implementation

### Prerequisites
- OSPFv3 deployed on IPv6-enabled interfaces.
- Syslog forwarding at severity 5 (notification) for ADJCHG events.
- Optionally, SNMP polling of ospfv3NbrState for continuous adjacency monitoring.

### Step 1 — Configure data collection

**Cisco IOS-XE — ensure OSPFv3 adjacency logging:**
```
router ospfv3 1
 address-family ipv6 unicast
  log-adjacency-changes detail
```
`detail` logs all state transitions, not just to/from FULL. This is essential for detecting stuck states.

**Juniper Junos:**
```
set protocols ospf3 traceoptions flag state
```

**Verification:**
```spl
index=network sourcetype="cisco:ios" "%OSPFv3" earliest=-7d
| stats count by host
```

### Step 2 — Create the search and alert

**Adjacency loss alert:**
```spl
index=network sourcetype="cisco:ios" "%OSPFv3" "ADJCHG" "to DOWN" earliest=-1h
| rex field=_raw "Nbr\s+(?<neighbor_id>[\d.]+)\s+on\s+(?<interface>\S+)"
| eval alert_text="OSPFv3 adjacency lost: " . host . " → " . neighbor_id . " on " . interface
| table _time, host, neighbor_id, interface, alert_text
```
Trigger: any adjacency to DOWN.

**Adjacency flapping detection:**
```spl
index=network sourcetype="cisco:ios" "%OSPFv3" "ADJCHG" earliest=-4h
| rex field=_raw "Nbr\s+(?<neighbor_id>[\d.]+)\s+on\s+(?<interface>\S+)\s+from\s+(?<from_state>\S+)\s+to\s+(?<to_state>\S+)"
| stats count as transitions dc(to_state) as distinct_states by host, neighbor_id, interface
| where transitions > 6
| eval alert="OSPFv3 flapping: " . transitions . " state changes in 4 hours for " . host . " ↔ " . neighbor_id
```

**IPsec authentication failure correlation:**
```spl
index=network sourcetype="cisco:ios" ("%OSPFv3" "ADJCHG") OR ("%CRYPTO-4" AND "ipsec" AND "fail")
  earliest=-4h
| eval event_type=case(
    match(_raw, "OSPFv3.*ADJCHG"), "OSPFv3_ADJCHG",
    match(_raw, "CRYPTO.*ipsec.*fail"), "IPsec_FAILURE",
    1=1, "OTHER")
| transaction host maxspan=5m maxpause=2m
| search event_type="OSPFv3_ADJCHG" AND event_type="IPsec_FAILURE"
| eval diagnosis="OSPFv3 adjacency failure correlated with IPsec authentication error — check IPsec SPI and keys"
```

### Step 3 — Validate
(a) **Simulate adjacency loss.** Shut down an OSPFv3 interface (`shutdown` on an OSPFv3-enabled interface). Verify the ADJCHG to DOWN appears in Splunk.

(b) **Simulate flapping.** Rapidly toggle an interface. Verify the flapping detection fires.

(c) **IPsec mismatch.** Change the IPsec key on one side of an OSPFv3 adjacency. Verify the adjacency fails and the IPsec correlation search identifies the root cause.

### Step 4 — Operationalize

**Dashboard** ("IPv6 — OSPFv3 Routing Health"):
- Row 1 — Single-value: total OSPFv3 adjacencies, current DOWN count, flapping pairs.
- Row 2 — Timechart: adjacency state changes over 24 hours.
- Row 3 — Table: current adjacency losses with host, neighbor, interface, and duration.
- Row 4 — Correlation: OSPFv3 events alongside IPsec errors and interface events.

**Scheduling:** Adjacency loss alert real-time. Flapping detection every 30 minutes.

**Runbook:**
1. Adjacency DOWN: check physical link (`show interface`), check OSPFv3 neighbor (`show ospfv3 neighbor`), check IPsec SA (`show crypto ipsec sa`).
2. Stuck in EXSTART/EXCHANGE: MTU mismatch between peers. Check interface MTU on both sides.
3. IPsec authentication failure: verify matching SPI, algorithm, and key on both sides. OSPFv3 uses Transport Mode ESP or AH.
4. Instance ID mismatch: verify `instance-id` matches on both sides of the link.

### Step 5 — Troubleshooting

- **OSPFv3 vs OSPFv2 events** — Ensure the search specifically matches `%OSPFv3` and not `%OSPF-5-ADJCHG` (which is OSPFv2). Both may exist on dual-stack routers.

- **Link-local peering complicates identification** — OSPFv3 peers using link-local addresses. The syslog shows the Router ID (IPv4 format) but the actual peering address is link-local. To identify which physical interface is affected, use the `on <interface>` field from the syslog.

- **Address Family (AF) mode** — In AF mode (RFC 5838), OSPFv3 can carry both IPv4 and IPv6 routes. An adjacency failure in AF mode affects both address families simultaneously. The syslog format may differ: `%OSPFv3-5-ADJCHG: Process 1 (address-family ipv6) Nbr ...`.

## SPL

```spl
index=network sourcetype="cisco:ios" "%OSPFv3" "ADJCHG" earliest=-24h
| rex field=_raw "Process\s+(?<ospf_pid>\d+).*Nbr\s+(?<neighbor_id>[\d.]+)\s+on\s+(?<interface>\S+)\s+from\s+(?<from_state>\S+)\s+to\s+(?<to_state>\S+)"
| eval severity=case(
    to_state="DOWN", "CRITICAL — adjacency lost",
    to_state="FULL", "INFO — adjacency established",
    match(to_state, "INIT|2WAY|EXSTART|EXCHANGE|LOADING"), "WARNING — adjacency transitioning",
    1=1, "INFO")
| eval is_down=if(to_state="DOWN", 1, 0)
| eval is_full=if(to_state="FULL", 1, 0)
| stats count as events count(eval(is_down=1)) as adjacency_losses count(eval(is_full=1)) as adjacency_ups by host, neighbor_id, interface, ospf_pid
| eval flapping=if(adjacency_losses > 3 AND adjacency_ups > 3, "FLAPPING", "stable")
| sort -adjacency_losses
```

## Visualization

(1) Table: current OSPFv3 adjacency events with state transition and severity. (2) Timechart: adjacency ups and downs over 24 hours. (3) Single-value: total active adjacency losses. (4) Network topology: OSPFv3 adjacency map (nodes=routers, edges=adjacencies, red=down).

## Known False Positives

**Planned maintenance.** Router upgrades and interface maintenance cause expected adjacency losses. Correlate with change management windows.

**OSPFv3 process restart.** A process restart (`clear ipv6 ospf process`) causes all adjacencies to drop and re-form. This is expected during troubleshooting or configuration changes.

**Dual-stack migration.** When deploying OSPFv3 on interfaces that previously ran OSPFv2 only, the initial adjacency formation generates ADJCHG events. These are expected during migration.

## References

- [RFC 5340 — OSPF for IPv6](https://www.rfc-editor.org/rfc/rfc5340)
- [RFC 5838 — Support of Address Families in OSPFv3 (dual-stack AF support)](https://www.rfc-editor.org/rfc/rfc5838)
- [RFC 4552 — Authentication/Confidentiality for OSPFv3 (IPsec for OSPFv3)](https://www.rfc-editor.org/rfc/rfc4552)
