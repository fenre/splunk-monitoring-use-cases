---
id: "5.5.13"
title: "Edge Device Resource Utilization"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.5.13 · Edge Device Resource Utilization

## Description

SD-WAN edge routers running high CPU or memory can drop packets, fail to establish tunnels, or crash. Monitoring device resources prevents silent performance degradation at remote sites where physical access is limited.

## Value

SD-WAN edge routers running high CPU or memory can drop packets, fail to establish tunnels, or crash. Monitoring device resources prevents silent performance degradation at remote sites where physical access is limited.

## Implementation

Poll vManage device statistics API for CPU, memory, and disk usage. Alert when CPU exceeds 80% or memory exceeds 85% sustained over 15 minutes. Trend over time to identify sites that need hardware upgrades. Pay special attention to devices running UTD (Unified Threat Defense) or DPI, which consume significantly more resources.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538), vManage API.
• Ensure the following data sources are available: vManage device statistics, `sourcetype=cisco:sdwan:device`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll vManage device statistics API for CPU, memory, and disk usage. Alert when CPU exceeds 80% or memory exceeds 85% sustained over 15 minutes. Trend over time to identify sites that need hardware upgrades. Pay special attention to devices running UTD (Unified Threat Defense) or DPI, which consume significantly more resources.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=sdwan sourcetype="cisco:sdwan:device"
| stats latest(cpu_user) as cpu_user, latest(cpu_system) as cpu_system, latest(mem_used) as mem_used, latest(mem_total) as mem_total by hostname, system_ip, site_id
| eval cpu_pct=cpu_user+cpu_system, mem_pct=round(mem_used/mem_total*100,1)
| where cpu_pct > 80 OR mem_pct > 85
| table hostname system_ip site_id cpu_pct mem_pct
| sort -cpu_pct
```

Understanding this SPL

**Edge Device Resource Utilization** — SD-WAN edge routers running high CPU or memory can drop packets, fail to establish tunnels, or crash. Monitoring device resources prevents silent performance degradation at remote sites where physical access is limited.

Documented **Data sources**: vManage device statistics, `sourcetype=cisco:sdwan:device`. **App/TA** (typical add-on context): `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538), vManage API. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: sdwan; **sourcetype**: cisco:sdwan:device. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=sdwan, sourcetype="cisco:sdwan:device". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by hostname, system_ip, site_id** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **cpu_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where cpu_pct > 80 OR mem_pct > 85` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Edge Device Resource Utilization**): table hostname system_ip site_id cpu_pct mem_pct
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` avg(Performance.cpu_load_percent) as cpu_pct
  from datamodel=Performance where nodename=Performance.CPU
  by Performance.host span=1h
| where cpu_pct > 80
```

Understanding this CIM / accelerated SPL

**Edge Device Resource Utilization** — SD-WAN edge routers running high CPU or memory can drop packets, fail to establish tunnels, or crash. Monitoring device resources prevents silent performance degradation at remote sites where physical access is limited.

Documented **Data sources**: vManage device statistics, `sourcetype=cisco:sdwan:device`. **App/TA** (typical add-on context): `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538), vManage API. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Performance` — enable acceleration for that model.
• Filters the current rows with `where cpu_pct > 80` — typically the threshold or rule expression for this monitoring goal.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (CPU/memory trending per device), Table (devices above threshold), Gauge (fleet-wide average).

## SPL

```spl
index=sdwan sourcetype="cisco:sdwan:device"
| stats latest(cpu_user) as cpu_user, latest(cpu_system) as cpu_system, latest(mem_used) as mem_used, latest(mem_total) as mem_total by hostname, system_ip, site_id
| eval cpu_pct=cpu_user+cpu_system, mem_pct=round(mem_used/mem_total*100,1)
| where cpu_pct > 80 OR mem_pct > 85
| table hostname system_ip site_id cpu_pct mem_pct
| sort -cpu_pct
```

## CIM SPL

```spl
| tstats `summariesonly` avg(Performance.cpu_load_percent) as cpu_pct
  from datamodel=Performance where nodename=Performance.CPU
  by Performance.host span=1h
| where cpu_pct > 80
```

## Visualization

Line chart (CPU/memory trending per device), Table (devices above threshold), Gauge (fleet-wide average).

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)
