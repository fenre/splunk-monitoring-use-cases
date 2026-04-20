---
id: "1.1.45"
title: "Swap Thrashing Detection"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-1.1.45 · Swap Thrashing Detection

## Description

Swap thrashing causes severe performance degradation and can make systems unresponsive.

## Value

Swap thrashing causes severe performance degradation and can make systems unresponsive.

## Implementation

Monitor vmstat si (swap in) and so (swap out) rates. Alert when both exceed 100 pages/sec simultaneously for 10+ consecutive samples. Include memory pressure metrics and process identification in alert context.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_nix`.
• Ensure the following data sources are available: `sourcetype=vmstat`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Monitor vmstat si (swap in) and so (swap out) rates. Alert when both exceed 100 pages/sec simultaneously for 10+ consecutive samples. Include memory pressure metrics and process identification in alert context.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=vmstat host=*
| where si > 100 AND so > 100
| stats count by host
| eval swap_thrash="YES"
| where count > 10
```

Understanding this SPL

**Swap Thrashing Detection** — Swap thrashing causes severe performance degradation and can make systems unresponsive.

Documented **Data sources**: `sourcetype=vmstat`. **App/TA** (typical add-on context): `Splunk_TA_nix`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: vmstat. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=os, sourcetype=vmstat. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where si > 100 AND so > 100` — typically the threshold or rule expression for this monitoring goal.
• `stats` rolls up events into metrics; results are split **by host** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **swap_thrash** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where count > 10` — typically the threshold or rule expression for this monitoring goal.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` avg(Performance.mem_used_percent) as mem_pct
                        avg(Performance.swap_used_percent) as swap_pct
  from datamodel=Performance where nodename=Performance.Memory
  by Performance.host span=5m
| where mem_pct > 95 OR swap_pct > 20
```

Understanding this CIM / accelerated SPL

**Swap Thrashing Detection** — Swap thrashing causes severe performance degradation and can make systems unresponsive.

Documented **Data sources**: `sourcetype=vmstat`. **App/TA** (typical add-on context): `Splunk_TA_nix`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Performance` — enable acceleration for that model.
• Filters the current rows with `where mem_pct > 95 OR swap_pct > 20` — typically the threshold or rule expression for this monitoring goal.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Alert, Timechart

## SPL

```spl
index=os sourcetype=vmstat host=*
| where si > 100 AND so > 100
| stats count by host
| eval swap_thrash="YES"
| where count > 10
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

Alert, Timechart

## References

- [Splunk_TA_nix](https://splunkbase.splunk.com/app/833)
- [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)
