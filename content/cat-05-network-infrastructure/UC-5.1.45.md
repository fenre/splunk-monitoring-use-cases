---
id: "5.1.45"
title: "Switch CPU and Memory Utilization (Meraki MS)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.1.45 · Switch CPU and Memory Utilization (Meraki MS)

## Description

Monitors switch hardware resources to prevent performance degradation or device failure.

## Value

Monitors switch hardware resources to prevent performance degradation or device failure.

## Implementation

Query MS device API for CPU and memory metrics. Alert on threshold breaches.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
• Ensure the following data sources are available: `sourcetype=meraki:api device_type=MS`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Query MS device API for CPU and memory metrics. Alert on threshold breaches.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cisco_network sourcetype="meraki:api" device_type=MS
| stats avg(cpu_usage) as avg_cpu, max(cpu_usage) as peak_cpu, avg(memory_usage) as avg_mem by switch_name
| where avg_cpu > 75 OR avg_mem > 80
```

Understanding this SPL

**Switch CPU and Memory Utilization (Meraki MS)** — Monitors switch hardware resources to prevent performance degradation or device failure.

Documented **Data sources**: `sourcetype=meraki:api device_type=MS`. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cisco_network; **sourcetype**: meraki:api. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=cisco_network, sourcetype="meraki:api". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by switch_name** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where avg_cpu > 75 OR avg_mem > 80` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Gauge charts for CPU/memory; time-series trends; capacity planning dashboard.

## SPL

```spl
index=cisco_network sourcetype="meraki:api" device_type=MS
| stats avg(cpu_usage) as avg_cpu, max(cpu_usage) as peak_cpu, avg(memory_usage) as avg_mem by switch_name
| where avg_cpu > 75 OR avg_mem > 80
```

## Visualization

Gauge charts for CPU/memory; time-series trends; capacity planning dashboard.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
