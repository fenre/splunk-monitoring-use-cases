<!-- AUTO-GENERATED from UC-5.12.12.json — DO NOT EDIT -->

---
id: "5.12.12"
title: "Trunk Group Utilization and All-Trunks-Busy Detection"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.12.12 · Trunk Group Utilization and All-Trunks-Busy Detection

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Capacity, Availability &middot; **Wave:** Crawl &middot; **Status:** Verified

*We count how many phone lines are in use at once so nobody hits a busy signal across the whole pool before your team adds more lines or opens a backup route.*

---

## Description

Combines active-call counts, peg-limit ratios, and congestion-oriented release causes per trunk group to reveal exhaustion before subscribers hear reorder tones or automated reroutes fail silently.

## Value

Capacity planners catch creeping utilization on PRI/SIP trunks, justify augment orders with trending evidence, and trigger preemptive overflow routing when groups approach all-trunks-busy—protecting revenue-critical contact centers and PSTN egress SLAs.

## Implementation

Primary signal should be SNMP curr/max channels from SBC; supplement with CDR cause spikes and five-minute occupancy rollups; alert at 85–90% sustained peg with hysteresis.

## Detailed Implementation

### Prerequisites
- Authoritative trunk inventory: CSV `trunk_groups.csv` mapping `trunk_group`, `carrier`, `licensed_channels`, `site`, `overflow_peer`.
- Either SNMP walks exposing concurrent usage or CDR with reliable start/stop timestamps per call_id.
- Baseline busy-hour curves per group (seasonal retail, Monday openings).

### Step 1 — Instrument peg counts
Enable SNMP on SBC/CUBE for concurrent voice sessions; normalize into `index=network` or unified `index=voip` sourcetype.

### Step 2 — Correlate failures
Join fifteen-minute windows where utilization >85% with spikes in Q.850 causes 34/42 from CDR.

### Step 3 — Alerts
Fire warning at fifteen-minute average >80% licensed channels; critical when equals licensed max for two consecutive polls or when congestion causes exceed SLA.

### Step 4 — Dashboards
Stacked area of utilization per trunk_group; single-value ATB events (zero idle circuits); table of top overflow destinations.

### Step 5 — Runbook actions
Engage carrier for additional SIP sessions; enable geographic redundancy; validate licensing on SBC after firmware upgrades because silent cap reductions mimic ATB.

Extended troubleshooting
Batch CDR delays under-report concurrency—prefer SNMP for real-time pegging. Maintenance windows that seize circuits should be tagged to suppress alerts.

## SPL

```spl
index=voip sourcetype="cdr:voip" earliest=-15m
| where isnotnull(trunk_group)
| stats count as attempts sum(eval(if(match(release_cause,"^(34|42|503)$"),1,0))) as congestion_events dc(call_id) as unique_sessions by trunk_group
| eval congestion_pct=if(attempts>0, round(100*congestion_events/attempts, 2), 0)
| where congestion_events>10 OR congestion_pct>3
| sort -congestion_events
```

## Visualization

Gauge row per trunk_group (curr/max); timeline of utilization vs. congestion causes; map/table of sites nearing exhaustion.

## Known False Positives

SNMP counter resets during failover briefly show zero utilization; fax/modem long holds inflate concurrency without voice faults; mis-labeled trunk_group strings split aggregates; scheduled carrier tests that seize every channel appear as artificial ATB unless calendar suppressed.

## References

- [Cisco IOS Voice Troubleshooting — Resource Exhaustion Signatures](https://www.cisco.com/c/en/us/)
- [Splunk Lantern — use case library](https://lantern.splunk.com/)
