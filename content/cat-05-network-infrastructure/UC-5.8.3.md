<!-- AUTO-GENERATED from UC-5.8.3.json — DO NOT EDIT -->

---
id: "5.8.3"
title: "SNMP Trap Consolidation"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.8.3 · SNMP Trap Consolidation

> **Criticality:** Medium &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Fault

*We pull all SNMP traps into one place so we can look up what broke without jumping between old tools.*

---

## Description

Centralizing SNMP traps from all sources enables cross-tool correlation and reduces monitoring tool sprawl.

## Value

Network operations teams consolidate SNMP traps from all network devices into a single, enriched, prioritized view that transforms cryptic OIDs into actionable alerts with device context and severity classification.

## Implementation

Configure Splunk SNMP trap receiver (UDP 162). Map trap OIDs to human-readable names via lookup. Correlate with syslog events from the same device.

## Detailed Implementation

### Prerequisites
- SNMP trap receiver configured to forward traps to Splunk. Common approaches: (1) Splunk Connect for SNMP (SC4SNMP) receives traps and forwards via HEC, (2) snmptrapd on a Linux host forwards to a Splunk Universal Forwarder, (3) Splunk Stream captures SNMP trap packets. Data in `index=snmp` (or `index=network`) with `sourcetype=snmptrapd` or `sourcetype=sc4snmp:traps`.
- Key fields: `trap_oid` (enterprise-specific OID), `trap_name` (resolved MIB name), `src` (sending device IP), `severity`, `message`, `community` (SNMPv2c) or `context_name` (SNMPv3).
- SNMP traps are the oldest and most universal network monitoring mechanism. Every network device (router, switch, firewall, UPS, PDU, server) can send traps. Common trap types: linkDown/linkUp, coldStart/warmStart, authenticationFailure, BGP state changes, fan/temperature alerts, configuration changes.
- Build `snmp_device_inventory.csv` lookup: `src,hostname,device_type,location,tier` (e.g., `10.1.1.1,core-sw-01,switch,DC-East,Tier1`). Build `snmp_trap_severity.csv` lookup: `trap_oid,trap_name,severity,category,runbook_url` to map OIDs to human-readable names and severity levels.

### Step 1 — Configure data collection
Verify trap data arrival:
```spl
index=snmp (sourcetype="snmptrapd" OR sourcetype="sc4snmp:traps") earliest=-1h
| stats count by sourcetype, src
| sort -count
```

### Step 2 — Create the search and alert

**Primary search — Consolidated trap view with enrichment:**
```spl
index=snmp (sourcetype="snmptrapd" OR sourcetype="sc4snmp:traps") earliest=-4h
| lookup snmp_device_inventory.csv src OUTPUT hostname device_type location tier
| lookup snmp_trap_severity.csv trap_oid OUTPUT trap_name as resolved_name severity category
| eval display_name=coalesce(resolved_name, trap_name, trap_oid)
| eval device_label=coalesce(hostname, src)
| stats count as trap_count dc(src) as source_devices first(_time) as first_seen latest(_time) as last_seen by display_name, severity, category
| eval duration_min=round((last_seen - first_seen)/60, 1)
| sort severity, -trap_count
```

#### Understanding this SPL: SNMP traps are notoriously noisy and cryptic (raw OIDs like `1.3.6.1.6.3.1.1.5.3` mean nothing to most operators). The lookup-based enrichment translates OIDs to human-readable names, assigns severity, and categorizes traps. This transforms a flood of raw traps into an actionable, prioritized event table. Grouping by `display_name` aggregates duplicate traps (e.g., 500 linkDown traps from a switch stack during a firmware upgrade).

**Top trap sources (noisy devices):**
```spl
index=snmp (sourcetype="snmptrapd" OR sourcetype="sc4snmp:traps") earliest=-24h
| lookup snmp_device_inventory.csv src OUTPUT hostname device_type location
| eval device_label=coalesce(hostname, src)
| stats count as traps dc(trap_oid) as unique_trap_types by device_label, device_type, location
| sort -traps
| head 20
```

**Link state change tracking:**
```spl
index=snmp (sourcetype="snmptrapd" OR sourcetype="sc4snmp:traps") earliest=-4h
| where match(trap_oid, "1\.3\.6\.1\.6\.3\.1\.1\.5\.(3|4)") OR match(trap_name, "link(Down|Up)")
| lookup snmp_device_inventory.csv src OUTPUT hostname location
| eval event_type=if(match(trap_oid, "\.3$") OR match(trap_name, "linkDown"), "LINK_DOWN", "LINK_UP")
| stats count by hostname, event_type, _time
| sort -_time
```

### Step 3 — Validate
(a) Generate a test trap: `snmptrap -v 2c -c public <receiver_ip> '' .1.3.6.1.6.3.1.1.5.3` (linkDown). Verify it appears in Splunk.
(b) Cross-check trap counts with your SNMP manager (e.g., SolarWinds, PRTG, LibreNMS) for the same time window.
(c) Verify OID resolution: check that 10 common trap OIDs resolve correctly in the `snmp_trap_severity.csv` lookup.

### Step 4 — Operationalize
Dashboard ("SNMP Trap Console"):
- Row 1 — Single-value tiles: "Traps (4h)", "Critical traps", "Unique sources", "Link state changes".
- Row 2 — Consolidated trap table: trap name, severity, category, count, source devices, duration.
- Row 3 — Top noisy devices table (for tuning/suppression).
- Row 4 — Link state change timeline.

Alerting:
- Critical (specific high-severity trap OIDs — e.g., BGP peer down, power supply failure): page NOC.
- Warning (trap volume > 2× baseline in 15 minutes): possible trap storm — investigate root cause.

### Step 5 — Troubleshooting

- **Traps not arriving in Splunk** — Check: (1) trap receiver process running (snmptrapd/SC4SNMP), (2) firewall allows UDP 162 from network devices to receiver, (3) community string matches (SNMPv2c) or USM credentials match (SNMPv3), (4) receiver forwarding to Splunk (HEC or UF).

- **Traps arrive but OIDs not resolved** — The `snmp_trap_severity.csv` lookup needs to be populated with your environment's trap OIDs. Export MIBs from your devices and map enterprise-specific OIDs. Alternatively, use `snmptranslate` to resolve OIDs on the receiver before forwarding.

- **Trap timestamps don't match event times** — SNMP traps don't carry a timestamp; the receiver timestamps them on arrival. If there's network delay between the device and receiver, the timestamp may be slightly off. For precision, use SNMP Inform (acknowledged) instead of Trap (fire-and-forget).

## SPL

```spl
index=network sourcetype="snmp:trap"
| stats count by trap_oid, host, severity | sort -count
```

## Visualization

Table (device, trap, severity), Bar chart, Timeline.

## Known False Positives

Trap storms during device reboots, link flapping, or SNMP server overload can dwarf normal traps; use host and OID baselines and storm detection (UC-5.8.25) together.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
