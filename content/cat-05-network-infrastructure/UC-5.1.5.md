<!-- AUTO-GENERATED from UC-5.1.5.json — DO NOT EDIT -->

---
id: "5.1.5"
title: "OSPF Neighbor Adjacency"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.1.5 · OSPF Neighbor Adjacency

> **Criticality:** Critical &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Availability

*We follow OSPF neighbor health so you know if routing in an area is unstable before it shows up as slow or broken application traffic.*

---

## Description

OSPF neighbor loss triggers SPF recalculation, disrupting traffic.

## Value

NOC teams track OSPF neighbor adjacency state changes, detecting lost adjacencies and flapping that cause routing reconvergence and potential traffic disruption.

## Implementation

Forward syslog from all OSPF routers. Alert on adjacency changes to/from FULL. Track frequency for instability.

## Detailed Implementation

### Prerequisites
* OSPF neighbor adjacency syslog messages. Data in `index=network` with `sourcetype=cisco:ios` or vendor-specific sourcetypes. Key mnemonics: Cisco `%OSPF-5-ADJCHG`; Juniper `RPD_OSPF_NBRSTATE`; Arista `OSPF-5-ADJCHG`.
* OSPF adjacency: routers form neighbor relationships (states: Down → Init → 2-Way → ExStart → Exchange → Loading → Full). Loss of Full adjacency causes routing reconvergence and potential traffic disruption. Flapping adjacencies indicate underlying issues (MTU mismatch, authentication, timer mismatch, interface instability).

### Step 1 — - Configure data collection
```
# Cisco IOS/IOS-XE
router ospf 1
 log-adjacency-changes detail

logging host <splunk-syslog-ip>
logging trap informational
```
Verify:
```spl
index=network earliest=-24h
| where match(_raw, "(?i)OSPF.*ADJ|OSPF.*NBRSTATE|ospf.*neighbor|ospf.*full|ospf.*down")
| stats count by host
```

### Step 2 — - Create the search and alert

**Primary search -- OSPF neighbor adjacency changes:**
```spl
index=network earliest=-24h
| where match(_raw, "(?i)OSPF.*ADJ|OSPF.*NBRSTATE|ospf.*neighbor.*state|ospf.*full|ospf.*down")
| rex field=_raw "(?i)(?:neighbor|Nbr)\s+(?<neighbor_ip>\d+\.\d+\.\d+\.\d+)"
| rex field=_raw "(?i)(?:area|Area)\s+(?<ospf_area>[\d\.]+)"
| rex field=_raw "(?i)(?:state|State).*?(?:to|:)\s*(?<ospf_state>\w+)"
| eval neighbor=coalesce(neighbor_ip, ospf_neighbor)
| eval state=lower(coalesce(ospf_state, new_state))
| eval device=coalesce(host, device_name)
| sort device, neighbor, _time
| stats count as events count(eval(state="down" OR state="init")) as down_events count(eval(state="full")) as full_events latest(state) as current_state latest(_time) as last_event by device, neighbor, ospf_area
| eval flapping=if(events > 4, "YES", "NO")
| eval severity=case(
    current_state!="full" AND flapping="YES", "CRITICAL -- OSPF adjacency DOWN and flapping",
    current_state!="full", "WARNING -- OSPF adjacency not FULL (state: ".current_state.")",
    flapping="YES", "WARNING -- OSPF adjacency flapping (currently full)",
    1==1, "OK")
| where severity != "OK"
| sort severity, -events
```

### Step 3 — - Validate
(a) CLI: `show ip ospf neighbor` -- verify current neighbor states.
(b) CLI: `show ip ospf interface` -- check hello/dead timers match.
(c) CLI: `debug ip ospf adj` (brief, remove after) -- verify hello exchange.

### Step 4 — - Operationalize
Dashboard ("Network -- OSPF Adjacency"):
* Row 1 -- Single-value: "Adjacencies DOWN", "Flapping adjacencies", "Events (24h)".
* Row 2 -- OSPF adjacency event timeline.

Alert: Critical (core OSPF adjacency lost): routing reconvergence, page NOC.

### Step 5 — - Troubleshooting

* **Stuck in ExStart/Exchange** -- MTU mismatch between neighbors. Check: `show ip ospf interface` on both sides. Match MTU or use `ip ospf mtu-ignore`.

* **Dead timer expired** -- Hellos not received. Check: interface up/down, ACLs blocking OSPF multicast (224.0.0.5/6), timer mismatch.

* **Authentication failure** -- Check OSPF authentication configuration matches on both sides. CLI: `show ip ospf interface <intf> | include Auth`.

**IPv6 Coverage:** OSPFv3 (RFC 5340) uses link-local addresses for adjacency, multicast FF02::5 (AllSPFRouters) and FF02::6 (AllDRRouters) instead of 224.0.0.5/6. Validate with `show ospfv3 neighbor`. ACLs blocking ICMPv6 or OSPFv3 multicast can silently break adjacency.

## SPL

```spl
index=network ((sourcetype="cisco:ios" ("%OSPF-5-ADJCHG" OR "%OSPFv3-5-ADJCHG")) OR "RPD_OSPF3_NBRSTATE")
| rex "Nbr (?<neighbor_ip>\S+) on (?<interface>\S+) from (?<from_state>\S+) to (?<to_state>\S+)"
| table _time host neighbor_ip interface from_state to_state
```

## Visualization

Events timeline, Table (router, neighbor, states).

## Known False Positives

OSPF neighbors may transition during interface MTU changes, DR and BDR elections, or area type changes.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
