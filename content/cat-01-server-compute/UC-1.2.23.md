---
id: "1.2.23"
title: "Non-Paged Pool Exhaustion"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-1.2.23 · Non-Paged Pool Exhaustion

## Description

Non-paged pool memory is limited kernel memory. Exhaustion causes BSOD (DRIVER_IRQL_NOT_LESS_OR_EQUAL). Often caused by driver leaks.

## Value

Non-paged pool memory is limited kernel memory. Exhaustion causes BSOD (DRIVER_IRQL_NOT_LESS_OR_EQUAL). Often caused by driver leaks.

## Implementation

Add `Pool Nonpaged Bytes` and `Pool Nonpaged Allocs` to Memory Perfmon inputs (interval=60). Default limit is ~75% of RAM or registry-defined. Alert at 256MB+ or when growth is sustained over hours. Use `poolmon.exe` or `xperf` to identify the leaking driver tag on affected hosts.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=Perfmon:Memory` (counter: Pool Nonpaged Bytes).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Add `Pool Nonpaged Bytes` and `Pool Nonpaged Allocs` to Memory Perfmon inputs (interval=60). Default limit is ~75% of RAM or registry-defined. Alert at 256MB+ or when growth is sustained over hours. Use `poolmon.exe` or `xperf` to identify the leaking driver tag on affected hosts.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=perfmon sourcetype="Perfmon:Memory" counter="Pool Nonpaged Bytes"
| eval pool_MB = Value / 1048576
| timechart span=15m avg(pool_MB) as nonpaged_pool_MB by host
| where nonpaged_pool_MB > 256
```

Understanding this SPL

**Non-Paged Pool Exhaustion** — Non-paged pool memory is limited kernel memory. Exhaustion causes BSOD (DRIVER_IRQL_NOT_LESS_OR_EQUAL). Often caused by driver leaks.

Documented **Data sources**: `sourcetype=Perfmon:Memory` (counter: Pool Nonpaged Bytes). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: perfmon; **sourcetype**: Perfmon:Memory. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=perfmon, sourcetype="Perfmon:Memory". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **pool_MB** — often to normalize units, derive a ratio, or prepare for thresholds.
• `timechart` plots the metric over time using **span=15m** buckets with a separate series **by host** — ideal for trending and alerting on this use case.
• Filters the current rows with `where nonpaged_pool_MB > 256` — typically the threshold or rule expression for this monitoring goal.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` avg(Performance.mem_used_percent) as mem_pct
                        avg(Performance.swap_used_percent) as swap_pct
  from datamodel=Performance where nodename=Performance.Memory
  by Performance.host span=5m
| where mem_pct > 95 OR swap_pct > 20
```

Understanding this CIM / accelerated SPL

**Non-Paged Pool Exhaustion** — Non-paged pool memory is limited kernel memory. Exhaustion causes BSOD (DRIVER_IRQL_NOT_LESS_OR_EQUAL). Often caused by driver leaks.

Documented **Data sources**: `sourcetype=Perfmon:Memory` (counter: Pool Nonpaged Bytes). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Performance` — enable acceleration for that model.
• Filters the current rows with `where mem_pct > 95 OR swap_pct > 20` — typically the threshold or rule expression for this monitoring goal.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (pool growth over time), Single value (current pool size), Alert threshold marker.

## SPL

```spl
index=perfmon sourcetype="Perfmon:Memory" counter="Pool Nonpaged Bytes"
| eval pool_MB = Value / 1048576
| timechart span=15m avg(pool_MB) as nonpaged_pool_MB by host
| where nonpaged_pool_MB > 256
```

## CIM SPL

```spl
| tstats `summariesonly` avg(Performance.mem_used_percent) as mem_pct
                        avg(Performance.swap_used_percent) as swap_pct
  from datamodel=Performance where nodename=Performance.Memory
  by Performance.host span=5m
| where mem_pct > 95 OR swap_pct > 20
```

## Visualization

Line chart (pool growth over time), Single value (current pool size), Alert threshold marker.

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
- [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)
