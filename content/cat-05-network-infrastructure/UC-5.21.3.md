<!-- AUTO-GENERATED from UC-5.21.3.json — DO NOT EDIT -->

---
id: "5.21.3"
title: "PTP (IEEE 1588) Grandmaster and Boundary Clock Health"
status: "verified"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.21.3 · PTP (IEEE 1588) Grandmaster and Boundary Clock Health

> **Criticality:** Critical &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Availability, Performance &middot; **Wave:** Run &middot; **Status:** Verified

*Some systems need clocks so precise they measure time in millionths of a second — things like cell phone towers, TV broadcasts, and stock exchanges. We watch the master clock and all the clocks that sync to it, alerting if any clock loses its connection to the master and starts drifting.*

---

## Description

Monitors IEEE 1588 PTP grandmaster clock health, boundary clock synchronization, and port state changes. PTP provides sub-microsecond timing accuracy required by 5G fronthaul, financial trading platforms, broadcast TV, and industrial automation. Grandmaster failures or holdover conditions degrade timing accuracy from nanoseconds to milliseconds within minutes, causing frame drops in 5G, trade timestamping violations, or production line synchronization failures.

## Value

PTP-dependent systems have zero tolerance for timing failures. A 5G fronthaul network losing PTP sync causes dropped calls and degraded service within seconds. Financial exchanges require sub-microsecond timestamps for regulatory compliance (MiFID II). Broadcast networks lose frame sync causing visible artifacts. This UC catches grandmaster changes, holdover conditions, and accuracy degradation before downstream systems are affected — the difference between a planned failover and a service outage.

## Implementation

Monitor PTP syslog events from network devices. Track grandmaster changes, holdover/freerun transitions, and port state changes. Alert immediately on freerun or sustained holdover.

## Detailed Implementation

### Prerequisites
- PTP configured on network devices with `ptp mode boundary` (boundary clocks) or `ptp mode e2etransparent` (transparent clocks). Grandmaster typically GPS-synced.
- Cisco IOS-XE: PTP syslog events enabled by default at severity 3-6.
- For SNMP-based monitoring: IEEE 1588 MIB objects accessible. Cisco-specific OIDs under `1.3.6.1.4.1.9.9.760`.

### Step 1 — Configure PTP event collection
Verify PTP events are arriving:
```spl
index=network sourcetype="cisco:ios" PTP earliest=-24h | stats count by host
```

If no events, verify PTP is configured:
```
show ptp clock
show ptp port
show ptp parent
```

### Step 2 — Create monitoring search
The primary search (above) classifies PTP events by severity.

**SNMP-based offset monitoring (sub-microsecond precision):**
```spl
index=network sourcetype="sc4snmp:metric" metric_name="ptpClockCurrentDSOffsetFromMaster" earliest=-4h
| eval offset_ns=abs(metric_value)
| eval offset_us=round(offset_ns/1000, 3)
| where offset_us > 1
| stats latest(offset_us) as current_offset_us by host
| eval status=case(
    current_offset_us > 1000, "CRITICAL — " . current_offset_us . "us offset (> 1ms)",
    current_offset_us > 100, "HIGH — " . current_offset_us . "us offset",
    current_offset_us > 10, "WARNING — " . current_offset_us . "us offset",
    1=1, null())
| where isnotnull(status)
| sort -current_offset_us
```

**Grandmaster change tracking:**
```spl
index=network sourcetype="cisco:ios" PTP "GM_CHANGE" earliest=-7d
| rex field=_raw "from.*(?<old_gm>[0-9a-fA-F:]+).*to.*(?<new_gm>[0-9a-fA-F:]+)"
| table _time host old_gm new_gm
| sort _time
```

### Step 3 — Validate
(a) On a boundary clock, run `show ptp clock` and note the offset from grandmaster. Compare with SNMP data.
(b) Run `show ptp parent` to identify the current grandmaster. Verify it matches expected GPS-synced source.
(c) Simulate grandmaster failover (if dual grandmaster). Verify GM_CHANGE event appears.

### Step 4 — Operationalize
Dashboard ("PTP Timing Infrastructure"):
- Row 1 — Single-value: devices in freerun/holdover (red if >0), grandmaster changes in 24h.
- Row 2 — Table: boundary clocks with current offset, grandmaster ID, port state.
- Row 3 — Timechart: offset trend over 24h per boundary clock.
- Row 4 — Grandmaster change history (timeline).

Alerting:
- FREERUN or HOLDOVER >5 minutes: Critical page — timing accuracy degrading rapidly.
- Grandmaster change: High priority — verify the new grandmaster is a valid GPS-synced source.
- Offset >100us sustained >10 minutes: High priority — check physical layer (fiber, SFP).

### Step 5 — Troubleshooting
- **Device entered FREERUN.** Lost all PTP sources. Check grandmaster status, network path, and physical connectivity. The device's oscillator will drift at ~1us/sec (OCXO) or ~11us/sec (TCXO).
- **Frequent grandmaster changes.** BMCA (Best Master Clock Algorithm) is selecting different grandmasters. This indicates either multiple grandmasters with similar priority or flapping connectivity. Set explicit priority values.
- **Large offset despite PTP running.** Asymmetric network delay (different forward/reverse path latency) causes systematic offset errors. PTP assumes symmetric paths — use TC (transparent clocks) to correct for switch delay.
- **PTP port FAULTY.** Physical layer issue on the PTP-enabled port. Check SFP, fiber, and CRC errors.

## SPL

```spl
index=network (sourcetype="cisco:ios" OR sourcetype="cisco:iosxe") earliest=-4h
  ("PTP" AND ("GM_CHANGE" OR "STATE_CHANGE" OR "CLOCK_ACCURACY" OR "PORT_STATE" OR "HOLDOVER" OR "FREERUN" OR "grandmaster"))
| rex field=_raw "(?<ptp_event>GM_CHANGE|STATE_CHANGE|CLOCK_ACCURACY|PORT_STATE|HOLDOVER|FREERUN)"
| eval severity=case(
    match(_raw, "FREERUN|holdover"), "CRITICAL — device in freerun/holdover (no PTP source)",
    match(_raw, "GM_CHANGE|grandmaster.*change"), "HIGH — grandmaster changed",
    match(_raw, "CLOCK_ACCURACY"), "HIGH — clock accuracy threshold exceeded",
    match(_raw, "PORT_STATE.*FAULTY"), "HIGH — PTP port faulty",
    1=1, "INFO")
| stats count as events latest(severity) as last_severity latest(_time) as last_event by host
| where last_severity != "INFO"
| sort -events
```

## Visualization

(1) Single-value: freerun/holdover count. (2) Table: boundary clock status. (3) Timechart: offset trend. (4) GM change timeline.

## Known False Positives

**Planned grandmaster maintenance.** Scheduled GPS antenna or grandmaster maintenance causes expected GM_CHANGE and brief holdover. Correlate with maintenance windows.

**BMCA convergence after topology change.** After a link failure/recovery, BMCA re-evaluates best grandmaster. Brief (< 30 second) holdover during reconvergence is normal.

**Leap second events.** UTC leap seconds can cause brief PTP offset spikes as grandmasters and boundary clocks absorb the correction. This is a known, predictable event.

## References

- [IEEE 1588-2019 — Precision Time Protocol](https://standards.ieee.org/standard/1588-2019.html)
- [Cisco — PTP Configuration Guide IOS-XE](https://www.cisco.com/c/en/us/)
