<!-- AUTO-GENERATED from UC-5.1.1.json — DO NOT EDIT -->

---
id: "5.1.1"
title: "Interface Up/Down Events"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.1.1 · Interface Up/Down Events

> **Criticality:** Critical &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Availability

*We watch when network ports go up and down so we can tell if a link is flapping or a whole site is at risk before users flood the help desk.*

---

## Description

A hard-down uplink or WAN port can isolate an entire site or VLAN; flapping often manifests as application timeouts and VoIP drops before a ticket names 'the network.' Treat each DOWN on a trunk or uplink as a potential SEV-1 for that site; treat more than 3 transitions in 10 minutes as a stability risk requiring immediate investigation of optics, cabling, or port configuration.

## Value

NOC teams detect network interface up/down events and link flapping across routers and switches, enabling rapid identification of cabling failures, optics issues, and unstable links.

## Implementation

Configure syslog forwarding on all network devices (UDP/TCP 514). Install TA for field extraction. Alert on down events for uplinks/trunks. Track flapping (>3 transitions in 10 min).

## Detailed Implementation

### Prerequisites
* Network device syslog forwarded to Splunk. Data in `index=network` or `index=infrastructure` with `sourcetype=syslog`, `sourcetype=cisco:ios`, or vendor-specific sourcetypes. Key syslog mnemonics: Cisco `%LINK-3-UPDOWN`, `%LINEPROTO-5-UPDOWN`; Juniper `SNMP_TRAP_LINK_DOWN/UP`; Arista `LINEPROTO-5-UPDOWN`.
* Interface up/down events indicate physical link changes (cable pull, optics failure, remote device reboot) or administrative shutdowns. High-frequency flapping indicates unstable links requiring immediate investigation.

### Step 1 — - Configure data collection
```
# Cisco IOS/IOS-XE -- ensure syslog is forwarded
logging host <splunk-syslog-ip>
logging trap informational
logging source-interface Loopback0

# Splunk inputs.conf
[udp://514]
sourcetype = cisco:ios
index = network
```
Verify:
```spl
index=network sourcetype="cisco:ios" earliest=-4h
| where match(_raw, "(?i)UPDOWN|LINK.*(UP|DOWN)|LINEPROTO.*(UP|DOWN)")
| stats count by host
```

### Step 2 — - Create the search and alert

**Primary search -- Interface up/down event tracking:**
```spl
index=network earliest=-4h
| where match(_raw, "(?i)UPDOWN|LINK.*(UP|DOWN)|LINEPROTO.*(UP|DOWN)|link.state|ifOperStatus")
| rex field=_raw "(?i)Interface\s+(?<interface>\S+).*(?<state>up|down)"
| eval interface=coalesce(interface, ifName, port)
| eval state=lower(coalesce(state, if(match(_raw, "(?i)down"), "down", "up")))
| eval device=coalesce(host, device_name)
| sort device, interface, _time
| streamstats count as event_num window=10 time_window=3600 by device, interface
| stats count as events count(eval(state="down")) as downs count(eval(state="up")) as ups latest(state) as current_state latest(_time) as last_event by device, interface
| eval flapping=if(events > 4, "YES", "NO")
| eval severity=case(
    current_state="down" AND flapping="YES", "CRITICAL -- interface DOWN and flapping",
    current_state="down", "WARNING -- interface DOWN",
    flapping="YES", "WARNING -- interface flapping (currently up)",
    1==1, "OK")
| where severity != "OK"
| eval last_event_time=strftime(last_event, "%Y-%m-%d %H:%M:%S")
| sort severity, -events
```

### Step 3 — - Validate
(a) CLI: `show interface status` (Cisco) or `show interfaces terse` (Juniper) -- verify current states.
(b) Compare event count with SNMP ifOperStatus traps.
(c) Correlate with CDP/LLDP neighbor changes to identify cascading failures.

### Step 4 — - Operationalize
Dashboard ("Network -- Interface Status"):
* Row 1 -- Single-value: "Interfaces DOWN", "Flapping interfaces", "Events (4h)".
* Row 2 -- Interface event timeline.
* Row 3 -- Currently down interfaces table.

Alert: Critical (critical interface DOWN, e.g., uplink, trunk): page NOC.

### Step 5 — - Troubleshooting

* **Interface flapping** -- Check: (1) cable/optics (SFP light levels), (2) remote device port status, (3) auto-negotiation issues, (4) power supply on PoE. CLI: `show interface <intf> | include flap`.

* **Admin shutdown vs physical failure** -- Differentiate by syslog message: `administratively down` = intentional. `down` without admin = physical/protocol failure.

* **Trunk link down** -- Cascading impact. Check spanning tree reconvergence (UC-5.1.6), routing adjacency (UC-5.1.4/5.1.5), and downstream devices.

## SPL

```spl
index=network sourcetype="cisco:ios" "%LINEPROTO-5-UPDOWN" OR "%LINK-3-UPDOWN"
| rex "Interface (?<interface>\S+), changed state to (?<state>\w+)"
| stats count by host, interface, state | where count > 3 | sort -count
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.dvc All_Traffic.action span=10m
| where count>3
| sort -count
```

## Visualization

Status grid (green/red per interface), Table, Timeline.

## Known False Positives

Interfaces flap during scheduled cable replacements, port channel rebalancing, or PoE device power cycling. Some test and lab ports flap routinely.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
