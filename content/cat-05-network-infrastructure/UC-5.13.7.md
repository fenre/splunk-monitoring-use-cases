<!-- AUTO-GENERATED from UC-5.13.7.json — DO NOT EDIT -->

---
id: "5.13.7"
title: "Device Health Score Degradation (Anomaly Detection)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.13.7 · Device Health Score Degradation (Anomaly Detection)

## Description

Uses statistical anomaly detection to identify devices whose health scores have dropped significantly below their own historical baseline, catching degradation that fixed thresholds miss.

## Value

Fixed thresholds cannot account for devices that normally run at different health levels. Anomaly detection catches relative degradation specific to each device's baseline.

## Implementation

Build on UC-5.13.1 and UC-5.13.2 with at least several weeks of retained hourly buckets. This search needs stable history per `deviceName`; deprioritize lab or frequently reloaded devices in a `lookup` if they skew baselines. Start with 2-sigma, then tune; consider seasonality in a later iteration.

## Detailed Implementation

Prerequisites
• UC-5.13.1 and UC-5.13.2 in production; retain at least 30 days of `cisco:dnac:devicehealth` (60–90+ days is better for stable stdev on hourly buckets).
• Cisco Catalyst Add-on (7538); `devicehealth` input at the default 15-minute poll; this search bins to one hour.
• Exclusion or flag lab and frequently reloaded devices in a lookup, or their baselines and sigma will be meaningless.
• See `docs/implementation-guide.md`.

Step 1 — Configure data collection
• Intent API: `GET /dna/intent/api/v1/device-health`.
• `eventstats` needs enough hourly points per `deviceName` in the chosen time range; a 7-day window is often too short for nonzero stdev on very stable platforms.
• Confirm `overallHealth` is numeric in events where Assurance reports health; all-null devices should be fixed in ingest or excluded from this search.

Step 2 — Create the search and alert
```spl
index=catalyst sourcetype="cisco:dnac:devicehealth" | bin _time span=1h | stats avg(overallHealth) as avg_health by deviceName, _time | eventstats avg(avg_health) as baseline stdev(avg_health) as stdev_health by deviceName | where avg_health < (baseline - 2*stdev_health) AND stdev_health > 0 | eval deviation=round((baseline-avg_health)/stdev_health,1) | sort -deviation
```

Understanding this SPL
• `span=1h` smooths 15-minute polls. Two-sigma below each device’s mean of hourly averages is a simple self-baseline, not a full ML model.
• `stdev_health > 0` filters out devices with flat health history (no variation), which would never meaningfully fire.
• Tune to 2.5–3 sigma, or add `where baseline > 50` to avoid noisy rows for devices that already sit chronically low.

**Pipeline walkthrough**
• `bin` and first `stats` produce one row per device per hour.
• `eventstats` by `deviceName` yields mean and stdev of those hourly means across the current search window (wider time range = different baseline).
• `where` and `eval` produce sigma deviation; `sort` shows worst hours first, then use UC-5.13.1 for same-device context.

Step 3 — Validate
• During a known change window, confirm devices show large `deviation` and decide whether to exclude change hours via lookup or increase sigma to reduce change-driven noise.
• If the network is unhealthy but the search returns nothing, stdev may be zero on many devices—widen the time range or re-check field extraction.
• Spot-check one anomalous hour in Catalyst Center Assurance for that device the same day.

Step 4 — Operationalize
• Dashboard table: deviceName, hour, avg_health, deviation. Do not use as a P1 page alone: pair with UC-5.13.3; seasonal or backup windows can look anomalous without triage rules.
• Optional alert: daily or 4-hour digest, throttle per device, require two consecutive bad hours (summary index or `streamstats`) before paging.

Step 5 — Troubleshooting
• Too many rows: longer window, higher sigma, or `where baseline >= 60` to ignore chronic low-health devices already tracked elsewhere.
• Baseline shift around holidays: maintain a lookup of excluded dates or a separate off-hours search.
• Missing or null `overallHealth`: fix data collection before trusting anomaly output.


## SPL

```spl
index=catalyst sourcetype="cisco:dnac:devicehealth" | bin _time span=1h | stats avg(overallHealth) as avg_health by deviceName, _time | eventstats avg(avg_health) as baseline stdev(avg_health) as stdev_health by deviceName | where avg_health < (baseline - 2*stdev_health) AND stdev_health > 0 | eval deviation=round((baseline-avg_health)/stdev_health,1) | sort -deviation
```

## Visualization

Table of anomalous hours with deviation score, timechart of avg_health for drilldown, combined with a baseline reference line from eventstats in a subsearch (optional).

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
- [Catalyst Center Integration Guide](docs/guides/catalyst-center.md)
