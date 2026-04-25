<!-- AUTO-GENERATED from UC-1.1.132.json — DO NOT EDIT -->

---
id: "1.1.132"
title: "macOS Notebook Battery Health and Cycle Count Threshold"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-1.1.132 · macOS Notebook Battery Health and Cycle Count Threshold

## Description

Lithium battery wear on Mac notebooks shows up as rising cycle counts, falling maximum capacity versus design, and "Service Recommended" conditions from power management. Tracking these signals prioritizes depot battery swaps before users lose runtime or swell-risk events ground a fleet.

## Value

Reduces unexpected power loss and field failures by surfacing degraded Mac batteries before runtime collapses or Apple flags a service condition.

## Implementation

Schedule a lightweight scripted input (UF `inputs.conf`) every 6–24h: parse `pmset -g batt` for state and `ioreg -rn AppleSmartBattery` for `CycleCount`, `AppleRawMaxCapacity` vs `DesignCapacity`, and `PermanentFailureStatus`. Normalize `max_capacity_pct=100*AppleRawMaxCapacity/DesignCapacity`. Set `battery_condition` from `pmset` or ioreg `Condition` string. Route to `index=os`, `sourcetype=macos_battery`. Alert when cycles exceed policy (often 800–1200 for corporate refresh), health under 80%, or condition indicates service.

## Detailed Implementation

Prerequisites
• Splunk Universal Forwarder on macOS with a `bin/` script scheduled via `inputs.conf`.
• Python or shell access to `pmset` and `ioreg` (no root required for read-only battery queries in most builds).

Step 1 — Emit one JSON or key=value event per host per run with fields: `cycle_count`, `max_capacity_pct`, `battery_condition`, optional `is_charging`.

Step 2 — Save the SPL as a scheduled alert with a lookup allowlist for loaner/demo devices.

Step 3 — Validate against Apple System Information → Power sample values.

Step 4 — Operationalize with asset tag join on `host` for procurement.

## SPL

```spl
index=os sourcetype=macos_battery host=*
| stats latest(cycle_count) as cycles, latest(max_capacity_pct) as health_pct, latest(battery_condition) as condition by host
| where cycles > 1000 OR health_pct < 80 OR like(condition, "%Service%")
```

## Visualization

Single value (hosts below health threshold), Table (host, cycles, health_pct, condition), Histogram (cycle count distribution).

## References

- [Splunk Documentation: Install the universal forwarder on macOS](https://docs.splunk.com/Documentation/Forwarder/latest/Deployment/InstallonmacOS)
- [Splunk Add-on for Unix and Linux (Splunkbase 833)](https://splunkbase.splunk.com/app/833)
