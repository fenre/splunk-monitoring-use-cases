<!-- AUTO-GENERATED from UC-5.8.25.json — DO NOT EDIT -->

---
id: "5.8.25"
title: "SNMP Trap Storm Detection"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.8.25 · SNMP Trap Storm Detection

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Fault

*We help you see when one device is screaming SNMP traps in a short burst, which often means a bad link, power problem, or bad SNMP setup—not just normal day traffic.*

---

## Description

Excessive SNMP traps from a device indicating failure cascade.

## Value

Network operations teams detect and classify SNMP trap storms caused by cascading failures, device flapping, or monitoring system malfunctions, enabling rapid root-cause identification and preventing alert fatigue.

## Implementation

Configure Splunk SNMP trap input or forward traps from snmptrapd. Parse trap OID and host. Alert when trap rate from a single device exceeds 100/min or 3 standard deviations above baseline. Trap storms often indicate device failure, link flapping, or misconfiguration.

## Detailed Implementation

### Prerequisites
- SNMP trap receiver forwarding to Splunk (SC4SNMP, snmptrapd → UF, or Splunk Stream). Data in `index=snmp` with `sourcetype=snmptrapd` or `sourcetype=sc4snmp:traps`. See UC-5.8.3 for general SNMP trap setup.
- An SNMP trap storm occurs when a network event triggers a cascade of traps from many devices in a short period. Common causes: (1) a core switch failure triggers linkDown traps from every connected device, (2) a spanning tree topology change causes flapping on many ports, (3) a routing protocol reconvergence generates route change traps from all routers, (4) a monitoring system misconfiguration causes every device to send authentication failure traps simultaneously.
- Trap storms are dangerous because they: overwhelm the trap receiver, flood the network with UDP traffic, generate thousands of alerts that mask the real root cause, and consume significant Splunk indexing resources.

### Step 1 — Configure data collection
Verify trap data with volume awareness:
```spl
index=snmp (sourcetype="snmptrapd" OR sourcetype="sc4snmp:traps") earliest=-1h
| bin _time span=1m
| stats count as traps_per_minute by _time
| eventstats avg(traps_per_minute) as avg_rate
| where traps_per_minute > avg_rate * 5
```

### Step 2 — Create the search and alert

**Primary search — Trap storm detection:**
```spl
index=snmp (sourcetype="snmptrapd" OR sourcetype="sc4snmp:traps") earliest=-1h
| bin _time span=1m
| stats count as traps dc(src) as source_devices dc(trap_oid) as unique_oids values(trap_oid) as oid_list by _time
| eventstats avg(traps) as avg_rate stdev(traps) as std_rate
| eval threshold=avg_rate + (4 * std_rate)
| eval is_storm=if(traps > threshold AND traps > 50, "YES", "NO")
| where is_storm="YES"
| eval storm_type=case(source_devices > 20 AND unique_oids < 3, "CASCADE", source_devices < 5 AND traps > 500, "SINGLE_DEVICE_FLOOD", unique_oids > 10, "MIXED_STORM", 1==1, "BURST")
| eval root_cause_hint=case(storm_type="CASCADE", "Core device failure — many devices reporting linkDown/topology change", storm_type="SINGLE_DEVICE_FLOOD", "Single device generating excessive traps — hardware flapping or software bug", storm_type="MIXED_STORM", "Multiple simultaneous issues or monitoring system malfunction", 1==1, "Transient burst — verify if resolved")
| table _time, traps, source_devices, unique_oids, storm_type, root_cause_hint
```

#### Understanding this SPL: The storm classification is key. A "CASCADE" (many devices, few OID types) suggests a single root cause triggering downstream effects — find the first device that sent a trap (likely the root cause device). A "SINGLE_DEVICE_FLOOD" suggests a device with a hardware problem (flapping port, failing fan sensor) sending the same trap hundreds of times. The 4σ threshold with a minimum of 50 traps prevents false positives from normal volume variations.

**Root cause identification during storm:**
```spl
index=snmp (sourcetype="snmptrapd" OR sourcetype="sc4snmp:traps") earliest=-15m
| bin _time span=1m
| stats count as trap_count by _time, src
| where trap_count > 10
| stats earliest(_time) as first_trap sum(trap_count) as total_traps by src
| lookup snmp_device_inventory.csv src OUTPUT hostname device_type tier
| eval device_label=coalesce(hostname, src)
| sort first_trap
| head 5
```

**Post-storm impact assessment:**
```spl
index=snmp (sourcetype="snmptrapd" OR sourcetype="sc4snmp:traps") earliest=-2h
| bin _time span=5m
| stats count as traps by _time
| streamstats window=3 current=t avg(traps) as rolling_avg
| eval status=case(traps > rolling_avg * 5, "STORM", traps > rolling_avg * 2, "ELEVATED", 1==1, "NORMAL")
```

### Step 3 — Validate
(a) Generate a synthetic trap storm: use `snmptrap` to send 100 traps in 10 seconds from multiple source IPs. Verify storm detection triggers.
(b) Review historical data: identify a known network event (link flap, switch reboot) and verify the corresponding trap volume spike.
(c) Validate the storm classification: compare the detected storm type with the actual root cause.

### Step 4 — Operationalize
Dashboard ("SNMP Trap Storm Detection"):
- Row 1 — Single-value tiles: "Current trap rate (per min)", "Storm active?", "Storm type", "Devices in storm".
- Row 2 — Trap volume timeline with storm threshold line.
- Row 3 — Storm event table: time, trap count, sources, type, root cause hint.
- Row 4 — Root cause candidates: first devices to generate traps (sorted by earliest time).

Alerting:
- Critical (trap storm detected — CASCADE type): core network event — correlate with device status.
- High (trap storm — SINGLE_DEVICE_FLOOD): isolate the device generating excessive traps.
- Warning (trap volume > 2× normal for 5 minutes): elevated activity — monitor.

### Step 5 — Troubleshooting

- **Trap storms overwhelm Splunk indexing** — Configure rate limiting on the trap receiver (snmptrapd `-A` option, SC4SNMP rate limiting). Alternatively, drop duplicate traps within a 1-second window at the receiver before forwarding to Splunk.

- **Storm detected but no clear root cause** — The root cause device may not send traps itself. A power failure at a site won't generate a trap from the failed device, but all neighboring devices will send linkDown traps. Look for the absence of traps from a device that should be generating them.

- **False positive storms during maintenance windows** — Planned device reboots generate trap bursts. Implement a maintenance mode that suppresses storm alerts during scheduled windows.

## SPL

```spl
index=network sourcetype=snmptrap
| bin _time span=1m
| stats count as trap_count by host, _time
| eventstats avg(trap_count) as avg_traps, stdev(trap_count) as std_traps by host
| where trap_count > (avg_traps + 3*std_traps) OR trap_count > 100
| sort -trap_count
```

## Visualization

Line chart (traps per host over time), Table (host, count, threshold), Single value (devices in storm).

## Known False Positives

Trap storms during device reboots, link flapping, or SNMP server overload; confirm with the NMS and interface counters before a hardware swap ticket.

## References

- [Cisco ThousandEyes App for Splunk](https://splunkbase.splunk.com/app/7719)
