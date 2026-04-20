---
id: "1.1.105"
title: "Fan Speed Anomalies"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-1.1.105 · Fan Speed Anomalies

## Description

Fan speed anomalies indicate cooling system degradation potentially leading to thermal overload.

## Value

Fan speed anomalies indicate cooling system degradation potentially leading to thermal overload.

## Implementation

Monitor fan speed readings via IPMI. Alert on anomalously low fan speeds (< 20%) even when speed is non-zero. Correlate with temperature readings to assess thermal risk.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_nix, custom scripted input`.
• Ensure the following data sources are available: `sourcetype=custom:ipmi, ipmitool reading`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Monitor fan speed readings via IPMI. Alert on anomalously low fan speeds (< 20%) even when speed is non-zero. Correlate with temperature readings to assess thermal risk.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=custom:ipmi host=* sensor_type=fan
| stats latest(reading_pct) as fan_speed by host, fan_name
| where fan_speed < 20 AND fan_speed > 0
```

Understanding this SPL

**Fan Speed Anomalies** — Fan speed anomalies indicate cooling system degradation potentially leading to thermal overload.

Documented **Data sources**: `sourcetype=custom:ipmi, ipmitool reading`. **App/TA** (typical add-on context): `Splunk_TA_nix, custom scripted input`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: custom:ipmi. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=os, sourcetype=custom:ipmi. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host, fan_name** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where fan_speed < 20 AND fan_speed > 0` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Gauge, Table

## SPL

```spl
index=os sourcetype=custom:ipmi host=* sensor_type=fan
| stats latest(reading_pct) as fan_speed by host, fan_name
| where fan_speed < 20 AND fan_speed > 0
```

## Visualization

Gauge, Table

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
