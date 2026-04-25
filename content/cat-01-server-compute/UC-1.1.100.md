<!-- AUTO-GENERATED from UC-1.1.100.json — DO NOT EDIT -->

---
id: "1.1.100"
title: "Vmstat swap-in (si) rate"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-1.1.100 · Vmstat swap-in (si) rate

## Description

In standard vmstat(8) output, `si` is kilobytes swapped in from disk per interval (memory pressure), not softirq. A sustained high `si` rate usually means the system is actively paging or thrashing swap.

## Value

Spotting heavy swap-in activity early helps us add memory, tune workloads, or fix leaks before latency and timeouts spread to users and services.

## Implementation

Enable vmstat collection in Splunk_TA_nix. Track the `si` field (swap-in) per host. Alert when the average swap-in rate exceeds your threshold; correlate with `so` (swap-out) and `vmstat` free/buff/cache fields.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_nix`.
• Ensure the following data sources are available: `sourcetype=vmstat`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable the `vmstat` scripted input on Linux. Confirm field names in Search: `si` is swap-in pages/kB per sample (per `vmstat` man page for your distro). If you need softirq rates, ingest `/proc/softirqs` or `mpstat` with a separate scripted input—do not map `si` to softirq.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=vmstat host=*
| stats avg(si) as avg_swap_in by host
| where avg_swap_in > 1000
```

Understanding this SPL

**Vmstat swap-in (si) rate** — In standard vmstat(8) output, `si` is kilobytes swapped in from disk per interval (memory pressure), not softirq.

Documented **Data sources**: `sourcetype=vmstat`. **App/TA** (typical add-on context): `Splunk_TA_nix`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: vmstat. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=os, sourcetype=vmstat. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host** so each row reflects one combination of those dimensions.
• Filters the current rows with `where avg_swap_in > 1000` — tune the threshold to your environment and vmstat interval.

Optional CIM / accelerated variant (related memory-pressure view via Common Information Model):

```spl
| tstats `summariesonly` avg(Performance.mem_used_percent) as mem_pct avg(Performance.swap_used_percent) as swap_pct
  from datamodel=Performance where nodename=Performance.Memory
  by Performance.host span=5m
| where mem_pct > 90 OR swap_pct > 15
```

Understanding this CIM / accelerated SPL

This **CIM** block approximates memory pressure using **Performance.Memory** (`mem_used_percent`, `swap_used_percent`). It does not reproduce `vmstat` `si` exactly—use it when the data model is accelerated and normalized to the same hosts.

Enable **acceleration** on **Performance.Memory** (and correct CIM knowledge objects) or the search may return nothing from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Timechart, Alert

## SPL

```spl
index=os sourcetype=vmstat host=*
| stats avg(si) as avg_swap_in by host
| where avg_swap_in > 1000
```

## CIM SPL

```spl
| tstats `summariesonly` avg(Performance.mem_used_percent) as mem_pct avg(Performance.swap_used_percent) as swap_pct
  from datamodel=Performance where nodename=Performance.Memory
  by Performance.host span=5m
| where mem_pct > 90 OR swap_pct > 15
```

## Visualization

Timechart, Alert

## References

- [Splunk_TA_nix](https://splunkbase.splunk.com/app/833)
- [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)
