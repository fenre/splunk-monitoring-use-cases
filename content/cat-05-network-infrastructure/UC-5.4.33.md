<!-- AUTO-GENERATED from UC-5.4.33.json — DO NOT EDIT -->

---
id: "5.4.33"
title: "AP Health and Radio Status Monitoring (HPE Aruba)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.4.33 · AP Health and Radio Status Monitoring (HPE Aruba)

## Description

Aruba APs report radio status (up/down per band), CPU/memory utilization, and uptime via controller syslog and Aruba Central API. A radio stuck in "down" state creates a coverage hole on that band. Monitor per-radio health across the fleet to proactively address failing hardware and capacity issues.

## Value

Aruba APs report radio status (up/down per band), CPU/memory utilization, and uptime via controller syslog and Aruba Central API. A radio stuck in "down" state creates a coverage hole on that band. Monitor per-radio health across the fleet to proactively address failing hardware and capacity issues.

## Implementation

Forward Mobility Controller / gateway syslog to Splunk with the Aruba TA (field aliases for `ap_name`, per-radio operational state, CPU/memory, uptime). Optionally poll Aruba Central for AP inventory and merge with syslog for sites without local controllers. Alert on any radio not `up`, sustained high CPU/memory, or APs with abnormal uptime resets.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Aruba Networks Add-on for Splunk` (Splunkbase 4668), Aruba Central API (scripted input or HEC).
• Ensure the following data sources are available: `sourcetype=aruba:syslog`, Aruba Central API (AP/radio inventory and health).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Forward Mobility Controller / gateway syslog to Splunk with the Aruba TA (field aliases for `ap_name`, per-radio operational state, CPU/memory, uptime). Optionally poll Aruba Central for AP inventory and merge with syslog for sites without local controllers. Alert on any radio not `up`, sustained high CPU/memory, or APs with abnormal uptime resets.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network sourcetype="aruba:syslog"
| eval ap=coalesce(ap_name, caller_ap_name, device_name, ap_mac)
| eval radio_st=coalesce(radio_oper_status, radio_status, oper_status)
| eval band=coalesce(radio_band, freq_band, band)
| bin _time span=5m
| stats latest(radio_st) as radio_state, latest(cpu_utilization_pct) as cpu_pct, latest(memory_utilization_pct) as mem_pct, latest(uptime_seconds) as uptime_sec by ap, band, ap_group, controller_name
| where like(lower(radio_state), "%down%") OR like(lower(radio_state), "%off%") OR cpu_pct>85 OR mem_pct>85
| sort ap_group ap band
```

Understanding this SPL

**AP Health and Radio Status Monitoring (HPE Aruba)** — Aruba APs report radio status (up/down per band), CPU/memory utilization, and uptime via controller syslog and Aruba Central API. A radio stuck in "down" state creates a coverage hole on that band. Monitor per-radio health across the fleet to proactively address failing hardware and capacity issues.

Documented **Data sources**: `sourcetype=aruba:syslog`, Aruba Central API (AP/radio inventory and health). **App/TA** (typical add-on context): `Aruba Networks Add-on for Splunk` (Splunkbase 4668), Aruba Central API (scripted input or HEC). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: aruba:syslog. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype="aruba:syslog". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **ap** — often to normalize units, derive a ratio, or prepare for thresholds.
• `eval` defines or adjusts **radio_st** — often to normalize units, derive a ratio, or prepare for thresholds.
• `eval` defines or adjusts **band** — often to normalize units, derive a ratio, or prepare for thresholds.
• Discretizes time or numeric ranges with `bin`/`bucket`.
• `stats` rolls up events into metrics; results are split **by ap, band, ap_group, controller_name** so each row reflects one combination of those dimensions.
• Filters the current rows with `where like(lower(radio_state), "%down%") OR like(lower(radio_state), "%off%") OR cpu_pct>85 OR mem_pct>85` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
In Aruba Central, the mobility controller UI, or ClearPass Policy Manager (Access Tracker / policy views), compare authentication and health events with the search for the same timeframe.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (AP, band, radio state, CPU, memory, uptime), Single value (APs with down radios), Timechart (unhealthy AP count), Map or site breakdown (by `ap_group` / zone).

## SPL

```spl
index=network sourcetype="aruba:syslog"
| eval ap=coalesce(ap_name, caller_ap_name, device_name, ap_mac)
| eval radio_st=coalesce(radio_oper_status, radio_status, oper_status)
| eval band=coalesce(radio_band, freq_band, band)
| bin _time span=5m
| stats latest(radio_st) as radio_state, latest(cpu_utilization_pct) as cpu_pct, latest(memory_utilization_pct) as mem_pct, latest(uptime_seconds) as uptime_sec by ap, band, ap_group, controller_name
| where like(lower(radio_state), "%down%") OR like(lower(radio_state), "%off%") OR cpu_pct>85 OR mem_pct>85
| sort ap_group ap band
```

## Visualization

Table (AP, band, radio state, CPU, memory, uptime), Single value (APs with down radios), Timechart (unhealthy AP count), Map or site breakdown (by `ap_group` / zone).

## References

- [Splunkbase app 4668](https://splunkbase.splunk.com/app/4668)
