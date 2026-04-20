---
id: "5.11.4"
title: "System CPU and Memory Utilization Streaming"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.11.4 · System CPU and Memory Utilization Streaming

## Description

Network device control planes running hot indicate routing churn, excessive logging, or a control-plane DoS. gNMI streaming at 30-second intervals catches transient CPU spikes that 5-minute SNMP polls miss entirely. A Nexus spine hitting 90% CPU during a BGP convergence event could start dropping BFD keepalives, cascading into a fabric-wide outage.

## Value

Network device control planes running hot indicate routing churn, excessive logging, or a control-plane DoS. gNMI streaming at 30-second intervals catches transient CPU spikes that 5-minute SNMP polls miss entirely. A Nexus spine hitting 90% CPU during a BGP convergence event could start dropping BFD keepalives, cascading into a fabric-wide outage.

## Implementation

Subscribe to `/system/cpus/cpu/state` at 30s intervals. For Cisco IOS XR, use native YANG `system-monitoring/cpu-utilization/total-cpu-one-minute`. Alert at 80% sustained for 5 minutes. Correlate with BGP update storms (UC-5.11.8) and interface flaps. Track per-process CPU if platform supports `/system/processes/process/state`.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Telegraf (`inputs.gnmi` plugin) → Splunk HEC.
• Ensure the following data sources are available: gNMI path: `/system/cpus/cpu/state` (OpenConfig), Cisco native: `Cisco-IOS-XR-wdsysmon-fd-oper:system-monitoring/cpu-utilization`; Telegraf metric: `openconfig_system`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Subscribe to `/system/cpus/cpu/state` at 30s intervals. For Cisco IOS XR, use native YANG `system-monitoring/cpu-utilization/total-cpu-one-minute`. Alert at 80% sustained for 5 minutes. Correlate with BGP update storms (UC-5.11.8) and interface flaps. Track per-process CPU if platform supports `/system/processes/process/state`.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
| mstats avg("openconfig_system.cpu_total_instant") AS cpu_pct WHERE index=gnmi_metrics BY host span=1m
| where cpu_pct > 80
| table _time, host, cpu_pct
| sort -cpu_pct
```

Understanding this SPL

**System CPU and Memory Utilization Streaming** — Network device control planes running hot indicate routing churn, excessive logging, or a control-plane DoS. gNMI streaming at 30-second intervals catches transient CPU spikes that 5-minute SNMP polls miss entirely. A Nexus spine hitting 90% CPU during a BGP convergence event could start dropping BFD keepalives, cascading into a fabric-wide outage.

Documented **Data sources**: gNMI path: `/system/cpus/cpu/state` (OpenConfig), Cisco native: `Cisco-IOS-XR-wdsysmon-fd-oper:system-monitoring/cpu-utilization`; Telegraf metric: `openconfig_system`. **App/TA** (typical add-on context): Telegraf (`inputs.gnmi` plugin) → Splunk HEC. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: gnmi_metrics.

**Pipeline walkthrough**

• Uses `mstats` to query metrics indexes (pre-aggregated metric data).
• Filters the current rows with `where cpu_pct > 80` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **System CPU and Memory Utilization Streaming**): table _time, host, cpu_pct
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t count from datamodel=Performance.CPU by Performance.host | sort - count
```

Understanding this CIM / accelerated SPL

**System CPU and Memory Utilization Streaming** — Network device control planes running hot indicate routing churn, excessive logging, or a control-plane DoS. gNMI streaming at 30-second intervals catches transient CPU spikes that 5-minute SNMP polls miss entirely. A Nexus spine hitting 90% CPU during a BGP convergence event could start dropping BFD keepalives, cascading into a fabric-wide outage.

Documented **Data sources**: gNMI path: `/system/cpus/cpu/state` (OpenConfig), Cisco native: `Cisco-IOS-XR-wdsysmon-fd-oper:system-monitoring/cpu-utilization`; Telegraf metric: `openconfig_system`. **App/TA** (typical add-on context): Telegraf (`inputs.gnmi` plugin) → Splunk HEC. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Performance.CPU` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Gauge (current CPU per device), Line chart (CPU trend), Table (devices above threshold).

## SPL

```spl
| mstats avg("openconfig_system.cpu_total_instant") AS cpu_pct WHERE index=gnmi_metrics BY host span=1m
| where cpu_pct > 80
| table _time, host, cpu_pct
| sort -cpu_pct
```

## CIM SPL

```spl
| tstats summariesonly=t count from datamodel=Performance.CPU by Performance.host | sort - count
```

## Visualization

Gauge (current CPU per device), Line chart (CPU trend), Table (devices above threshold).

## References

- [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)
