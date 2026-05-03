<!-- AUTO-GENERATED from UC-5.10.8.json — DO NOT EDIT -->

---
id: "5.10.8"
title: "Circuit and Last-Mile Link Utilization Monitoring"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.10.8 · Circuit and Last-Mile Link Utilization Monitoring

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Capacity, Performance &middot; **Wave:** Crawl &middot; **Status:** Verified

*We watch how full the pipe is between us and the phone company so we upgrade or reshuffle traffic before everything slows to a crawl at rush hour.*

---

## Description

Turns IF-MIB counter deltas into sustained bits-per-second utilization on carrier-facing interfaces and overlays contractual CIR utilization so operations sees both physical port saturation and committed-rate overrun risk on tail circuits.

## Value

Capacity planners receive empirical trending ahead of billable overage or congestion-driven SLA breaches—especially valuable where uplinks remain physically uncapped but billing meters enforce CIR envelopes enforced only on carrier side.

## Implementation

Poll five-minute intervals minimum; align clocks via NTP; maintain lookup tying Splunk `host`/SNMP index to commercial circuit metadata; alert dual thresholds—SNMP physical utilization above seventy-five percent and CIR utilization above eighty-five percent.

## Detailed Implementation

### Prerequisites
- Reliable IF-MIB polling every five minutes (or faster for bursty tails) using `ifHCInOctets`/`ifHCOutOctets` on carrier-facing interfaces; legacy 32-bit counters require exclusion.
- Verified `ifSpeed` plus optional `ifHighSpeed` when ports exceed four-gigabit semantic limits—maintain override CSV when optics negotiate unexpected speeds.
- Carrier contract artifacts defining CIR in bits per second per VLAN or physical interface; finance-approved conversions when framing overhead differs.
- Network Time Protocol discipline across SNMP agents and Splunk indexers to prevent negative deltas.

### Step 1 — Land telemetry as `sourcetype=snmp:interface` inside `index=network`, ensuring hosts resolve to the same identifiers used in inventory tools.

### Step 2 — Chronologically sort per `host`/`ifDescr`, then apply `streamstats` deltas transforming octet growth into sustained throughput (multiply by eight, divide by elapsed seconds).

### Step 3 — Compose `host_interface` keys (`host|ifDescr`) feeding `carrier_circuits.csv` so Splunk enriches circuits with carrier names, POP/site codes, billing IDs, and CIR.

### Step 4 — Dashboard row displays SNMP-derived physical utilization beside CIR-relative utilization; schedule alerts crossing seventy-five percent physical or eighty-five percent CIR with staggered severities.

### Step 5 — Troubleshooting: SNMP timeouts yield bogus spikes—drop intervals lacking sequential samples; EtherChannel members may need aggregated counters via vendor-specific MIB supplements; DSL tails remain asymmetric—consider direction-specific thresholds instead of `max()`.

## SPL

```spl
index=network sourcetype="snmp:interface" ifSpeed>0 ifDescr=*
| sort 0 host, ifDescr, _time
| streamstats current=f global=f last(ifHCInOctets) as prev_in last(ifHCOutOctets) as prev_out last(_time) as prev_ts by host, ifDescr
| eval dt=_time-prev_ts
| eval in_bps=if(dt>0 AND dt<900,(ifHCInOctets-prev_in)*8/dt,null())
| eval out_bps=if(dt>0 AND dt<900,(ifHCOutOctets-prev_out)*8/dt,null())
| eval speed_bps=case(ifSpeed>=4294967295 AND isnotnull(ifHighSpeed), ifHighSpeed*1000000, ifSpeed>=4294967295, null(), true(), ifSpeed)
| eval util_peak=if(isnotnull(speed_bps) AND speed_bps>0, round(100*max(in_bps,out_bps)/speed_bps,2), null())
| eval host_interface=host."|".ifDescr
| lookup carrier_circuits.csv host_interface OUTPUT cir_bps carrier circuit_id site_code
| eval cir_util=if(isnotnull(cir_bps) AND cir_bps>0, round(100*max(in_bps,out_bps)/cir_bps,2), null())
| where util_peak>75 OR cir_util>85
| stats latest(util_peak) as snmp_util_pct latest(cir_util) as cir_util_pct latest(ifOperStatus) as oper latest(ifDescr) as interface by host, carrier, circuit_id
| sort -cir_util_pct
```

## Visualization

Gauge tiles per circuit for instantaneous utilization; dual-axis timechart comparing SNMP utilization vs CIR utilization; map panel keyed by site_code with color thresholds.

## Known False Positives

Brief backup replication bursts crossing a fifteen-minute spike filter may page despite healthy sustained utilization; SNMP gaps emit null deltas—ignore windows without two sequential samples; LLDP renames can duplicate `ifDescr` rows until caches refresh.

## References

- [Splunk Lantern — SNMP polling guidance](https://lantern.splunk.com/)
- [IF-MIB (RFC 2863)](https://www.rfc-editor.org/rfc/rfc2863)
