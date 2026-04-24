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
• Install and configure the required add-on or app: `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538).
• Ensure the following data sources are available: index=catalyst, sourcetype cisco:dnac:devicehealth (Catalyst Center /dna/intent/api/v1/device-health).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Build on UC-5.13.1 and UC-5.13.2 with at least several weeks of retained hourly buckets. This search needs stable history per `deviceName`; deprioritize lab or frequently reloaded devices in a `lookup` if they skew baselines. Start with 2-sigma, then tune; consider seasonality in a later iteration.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=catalyst sourcetype="cisco:dnac:devicehealth" | bin _time span=1h | stats avg(overallHealth) as avg_health by deviceName, _time | eventstats avg(avg_health) as baseline stdev(avg_health) as stdev_health by deviceName | where avg_health < (baseline - 2*stdev_health) AND stdev_health > 0 | eval deviation=round((baseline-avg_health)/stdev_health,1) | sort -deviation
```

Understanding this SPL

**Device Health Score Degradation (Anomaly Detection)** — Fixed thresholds cannot account for devices that normally run at different health levels. Anomaly detection catches relative degradation specific to each device's baseline.

Documented **Data sources**: index=catalyst, sourcetype cisco:dnac:devicehealth (Catalyst Center /dna/intent/api/v1/device-health). **App/TA** (typical add-on context): `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: catalyst; **sourcetype**: cisco:dnac:devicehealth. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• `bin` and first `stats` build one hourly average of `overallHealth` per `deviceName` to smooth poll jitter.
• `eventstats` over the result set (wide time range) creates per-device mean and standard deviation of those hourly means as a rolling self-baseline in the same window as the search.
• `where` flags hours more than two standard deviations under the per-device mean; `eval` quantifies the gap in sigma units, then `sort` prioritizes the largest deteriorations for triage with UC-5.13.1 context.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table of anomalous hours with deviation score, timechart of avg_health for drilldown, combined with a baseline reference line from eventstats in a subsearch (optional).

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:devicehealth" | bin _time span=1h | stats avg(overallHealth) as avg_health by deviceName, _time | eventstats avg(avg_health) as baseline stdev(avg_health) as stdev_health by deviceName | where avg_health < (baseline - 2*stdev_health) AND stdev_health > 0 | eval deviation=round((baseline-avg_health)/stdev_health,1) | sort -deviation
```

## Visualization

Table of anomalous hours with deviation score, timechart of avg_health for drilldown, combined with a baseline reference line from eventstats in a subsearch (optional).

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
