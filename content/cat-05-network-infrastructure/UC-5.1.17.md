<!-- AUTO-GENERATED from UC-5.1.17.json — DO NOT EDIT -->

---
id: "5.1.17"
title: "Duplex Mismatch Detection"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.1.17 · Duplex Mismatch Detection

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance, Fault

*We help you know early when something looks wrong with duplex mismatch detection so the team can act before it grows into a bigger outage.*

---

## Description

Duplex mismatches degrade link performance silently. They cause late collisions, CRC errors, and reduced throughput that are hard to diagnose.

## Value

Network engineers detect duplex mismatches across switch and router interfaces, a common cause of intermittent packet loss, CRC errors, and degraded link performance.

## Implementation

Enable CDP/LLDP on all interfaces. Monitor syslog for duplex mismatch messages. Cross-reference with SNMP interface counters showing late collisions.

## Detailed Implementation

### Prerequisites
* Interface speed/duplex syslog and SNMP data. Data in `index=network` with `sourcetype=cisco:ios` or SNMP data. Key fields: `ifSpeed`, `ifDuplex`, syslog messages about auto-negotiation results.
* Duplex mismatch: one side of a link is full-duplex, the other half-duplex. Causes late collisions, CRC errors, and degraded throughput. Typically occurs when one side has auto-negotiation disabled (hardcoded) and the other auto-negotiates. Very common cause of intermittent packet loss.

### Step 1 — - Configure data collection
```
# SNMP polling for interface speed/duplex
# OID: dot3StatsDuplexStatus (.1.3.6.1.2.1.10.7.2.1.19)
# Values: 1=unknown, 2=halfDuplex, 3=fullDuplex

# Cisco syslog: %LINK-3-UPDOWN includes speed/duplex info
# %CDP-4-DUPLEX_MISMATCH is key indicator
```
Verify:
```spl
index=network earliest=-24h
| where match(_raw, "(?i)duplex.*mismatch|DUPLEX_MISMATCH|half.?duplex|auto.*negot")
| stats count by host
```

### Step 2 — - Create the search and alert

**Primary search -- Duplex mismatch detection:**
```spl
index=network earliest=-24h
| where match(_raw, "(?i)DUPLEX_MISMATCH|duplex.*mismatch|half.?duplex|a-half|auto.*negot.*half")
| rex field=_raw "(?i)(?:port|interface|Port)\s+(?<interface>\S+)"
| rex field=_raw "(?i)(?:neighbor|peer|remote).*?(?<neighbor_port>\S+)"
| eval device=coalesce(host, device_name)
| eval iface=coalesce(interface, port)
| stats count as events latest(_time) as last_seen by device, iface, neighbor_port
| eval severity="WARNING -- duplex mismatch detected on ".iface
| eval last_seen_time=strftime(last_seen, "%Y-%m-%d %H:%M:%S")
| table device, iface, neighbor_port, events, last_seen_time, severity
| sort -events
```

**Secondary search -- Half-duplex interface inventory:**
```spl
index=network earliest=-4h
| eval duplex=coalesce(dot3StatsDuplexStatus, duplex, if(match(_raw, "(?i)half"), "half", if(match(_raw, "(?i)full"), "full", null())))
| where duplex="half" OR duplex="2"
| eval device=coalesce(host, device_name)
| eval interface=coalesce(ifName, interface, port)
| stats count latest(_time) as last_seen by device, interface
| eval severity="INFO -- interface running half-duplex"
| table device, interface, last_seen, severity
```

### Step 3 — - Validate
(a) CLI: `show interface status` -- check speed/duplex for all ports.
(b) CLI: `show cdp neighbors detail` -- check CDP duplex mismatch warnings.
(c) Correlate with CRC/input error trending (UC-5.1.2, UC-5.1.21).

### Step 4 — - Operationalize
Dashboard ("Network -- Duplex Status"):
* Row 1 -- Single-value: "Duplex mismatches", "Half-duplex interfaces".
* Row 2 -- Duplex mismatch table with interface details.

Alert: Warning (duplex mismatch detected): fix immediately to prevent packet loss.

### Step 5 — - Troubleshooting

* **Fix duplex mismatch** -- Best practice: set both ends to auto-negotiate OR both ends to hardcoded same speed/duplex. Never mix auto and hardcoded. CLI: `interface <intf>` then `speed auto` and `duplex auto`.

* **Correlate with errors** -- Duplex mismatch causes: late collisions (on full-duplex side), FCS/CRC errors, runts. Check `show interface <intf>` error counters.

* **Why auto-negotiation fails** -- Some older devices or specific cabling (crossover vs straight-through) may not auto-negotiate correctly. Hardcode both ends to match.

## SPL

```spl
index=network sourcetype="cisco:ios" "%CDP-4-DUPLEX_MISMATCH"
| rex "duplex mismatch discovered on (?<local_intf>\S+).*with (?<remote_device>\S+) (?<remote_intf>\S+)"
| stats count latest(_time) as last_seen by host, local_intf, remote_device, remote_intf
| sort -last_seen
```

## Visualization

Table (local device/interface → remote device/interface), Alert list.

## Known False Positives

Intermittent autonegotiation blips and cable wiggles during moves can look like a mismatch—verify with a sustained port test.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
