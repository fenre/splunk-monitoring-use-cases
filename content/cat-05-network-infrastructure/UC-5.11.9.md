---
id: "5.11.9"
title: "Hardware Component Health (Fan, PSU, Temperature)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.11.9 · Hardware Component Health (Fan, PSU, Temperature)

## Description

Environmental monitoring via SNMP Entity-MIB polling is slow and often unreliable. gNMI streaming of `/components/component/state` provides real-time temperature, fan speed, and power supply status. A failing fan in a top-of-rack switch triggers thermal throttling within minutes — early detection prevents performance degradation and emergency hardware swaps during business hours.

## Value

Environmental monitoring via SNMP Entity-MIB polling is slow and often unreliable. gNMI streaming of `/components/component/state` provides real-time temperature, fan speed, and power supply status. A failing fan in a top-of-rack switch triggers thermal throttling within minutes — early detection prevents performance degradation and emergency hardware swaps during business hours.

## Implementation

Subscribe to `/components/component/state` at 60s intervals. Filter for component types FAN, POWER_SUPPLY, and SENSOR. Set thresholds per component type: chassis inlet >40°C warning, ASIC >85°C critical, fan speed <2000 RPM warning. Alert on PSU state changes (redundancy loss). Track temperature trends to detect environmental issues (HVAC failure, hot aisle containment breach).

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Telegraf (`inputs.gnmi` plugin) → Splunk HEC.
• Ensure the following data sources are available: gNMI path: `/components/component/state` (temperature, type=FAN/POWER_SUPPLY/SENSOR); Telegraf metric: `openconfig_platform`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Subscribe to `/components/component/state` at 60s intervals. Filter for component types FAN, POWER_SUPPLY, and SENSOR. Set thresholds per component type: chassis inlet >40°C warning, ASIC >85°C critical, fan speed <2000 RPM warning. Alert on PSU state changes (redundancy loss). Track temperature trends to detect environmental issues (HVAC failure, hot aisle containment breach).

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
| mstats latest("openconfig_platform.temperature_instant") AS temp_c WHERE index=gnmi_metrics BY host, name span=5m
| where temp_c > 65
| eval severity=case(temp_c > 85, "CRITICAL", temp_c > 75, "HIGH", temp_c > 65, "WARNING")
| table _time, host, name, temp_c, severity
| sort -temp_c
```

Understanding this SPL

**Hardware Component Health (Fan, PSU, Temperature)** — Environmental monitoring via SNMP Entity-MIB polling is slow and often unreliable. gNMI streaming of `/components/component/state` provides real-time temperature, fan speed, and power supply status. A failing fan in a top-of-rack switch triggers thermal throttling within minutes — early detection prevents performance degradation and emergency hardware swaps during business hours.

Documented **Data sources**: gNMI path: `/components/component/state` (temperature, type=FAN/POWER_SUPPLY/SENSOR); Telegraf metric: `openconfig_platform`. **App/TA** (typical add-on context): Telegraf (`inputs.gnmi` plugin) → Splunk HEC. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: gnmi_metrics.

**Pipeline walkthrough**

• Uses `mstats` to query metrics indexes (pre-aggregated metric data).
• Filters the current rows with `where temp_c > 65` — typically the threshold or rule expression for this monitoring goal.
• `eval` defines or adjusts **severity** — often to normalize units, derive a ratio, or prepare for thresholds.
• Pipeline stage (see **Hardware Component Health (Fan, PSU, Temperature)**): table _time, host, name, temp_c, severity
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t count from datamodel=Performance.CPU by Performance.host | sort - count
```

Understanding this CIM / accelerated SPL

**Hardware Component Health (Fan, PSU, Temperature)** — Environmental monitoring via SNMP Entity-MIB polling is slow and often unreliable. gNMI streaming of `/components/component/state` provides real-time temperature, fan speed, and power supply status. A failing fan in a top-of-rack switch triggers thermal throttling within minutes — early detection prevents performance degradation and emergency hardware swaps during business hours.

Documented **Data sources**: gNMI path: `/components/component/state` (temperature, type=FAN/POWER_SUPPLY/SENSOR); Telegraf metric: `openconfig_platform`. **App/TA** (typical add-on context): Telegraf (`inputs.gnmi` plugin) → Splunk HEC. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Performance.CPU` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Gauge (temperature per component), Status grid (fan/PSU status across fabric), Line chart (temperature trend), Table (components above threshold).

## SPL

```spl
| mstats latest("openconfig_platform.temperature_instant") AS temp_c WHERE index=gnmi_metrics BY host, name span=5m
| where temp_c > 65
| eval severity=case(temp_c > 85, "CRITICAL", temp_c > 75, "HIGH", temp_c > 65, "WARNING")
| table _time, host, name, temp_c, severity
| sort -temp_c
```

## CIM SPL

```spl
| tstats summariesonly=t count from datamodel=Performance.CPU by Performance.host | sort - count
```

## Visualization

Gauge (temperature per component), Status grid (fan/PSU status across fabric), Line chart (temperature trend), Table (components above threshold).

## References

- [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)
