<!-- AUTO-GENERATED from UC-1.1.133.json — DO NOT EDIT -->

---
id: "1.1.133"
title: "macOS CPU Thermal Pressure and Throttle Events"
status: "draft"
criticality: "high"
splunkPillar: "Observability"
---

# UC-1.1.133 · macOS CPU Thermal Pressure and Throttle Events

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance, Fault &middot; **Status:** Draft

*We notice when a Mac is getting too hot and has to slow itself down, so IT can fix cooling problems instead of blaming the wrong app.*

---

## Description

When macOS reports non-nominal thermal pressure or forces a low CPU speed limit, interactive and build workloads slow sharply even if average CPU utilization looks healthy. Ingesting thermal state explains user-perceived slowness tied to fan failures, dust, ambient heat, or sustained AV/backup jobs.

## Value

Cuts mean-time-to-diagnose for "slow Mac" tickets by proving hardware thermal throttling versus application inefficiency.

## Implementation

Run a controlled `powermetrics` sample (requires admin) on an interval that matches your compliance posture—often 5–15 minutes—or parse `log show --predicate 'subsystem == "com.apple.powermanagement"'` / thermal-related messages into `thermal_pressure` (nominal|moderate|heavy|trapping) and `cpu_speed_limit_pct` (0–100). For fleet scripts without root, map best-effort proxies from `pmset -g therm`. Use `index=os`, `sourcetype=macos_thermal`. Alert on sustained non-nominal pressure or `cpu_speed_limit_pct` under 70% for more than two consecutive samples.

## Detailed Implementation

### Prerequisites
- Decide whether elevated `powermetrics` sampling is acceptable; if not, use log-based thermal strings only.
- Standardize enums: `thermal_pressure` lowercase nominal|moderate|heavy|trapping|unknown.

### Step 1 — Scripted input prints one event per interval with `cpu_speed_limit_pct` as integer percent.

### Step 2 — Correlate with `sourcetype=macos_top` or `cpu` from TA nix if co-deployed.

### Step 3 — Validate on a known thermally loaded test unit (video encode + CPU burn).

### Step 4 — Tune alert to ignore single-sample spikes during macOS updates.

## SPL

```spl
index=os sourcetype=macos_thermal host=*
| stats latest(thermal_pressure) as pressure, latest(cpu_speed_limit_pct) as speed_limit by host
| where (isnull(pressure) OR lower(pressure)!="nominal") OR speed_limit < 70
```

## Visualization

Timeline (thermal_pressure by host), Line chart (cpu_speed_limit_pct), Table (worst hosts last hour).

## Known False Positives

A single heavy encode or index rebuild can trip non-nominal pressure briefly with no hardware fault. `powermetrics` sampling itself adds load—stagger runs and avoid back-to-back samples. On Intel vs Apple Silicon, `cpu_speed_limit_pct` availability differs; null `pressure` with low `speed_limit` still needs platform-specific interpretation.

## References

- [Apple Platform Security — macOS power and thermal management (overview)](https://support.apple.com/guide/security/welcome/web)
- [Splunk Add-on for Unix and Linux (Splunkbase 833)](https://splunkbase.splunk.com/app/833)
