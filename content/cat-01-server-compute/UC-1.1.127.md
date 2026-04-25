<!-- AUTO-GENERATED from UC-1.1.127.json — DO NOT EDIT -->

---
id: "1.1.127"
title: "Swap Activity Rate Trending"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-1.1.127 · Swap Activity Rate Trending

## Description

Pages swapped in/out per second (distinct from swap usage %) indicates memory pressure and I/O load. High swap I/O rate degrades performance even before swap usage is critical.

## Value

Pages swapped in/out per second (distinct from swap usage %) indicates memory pressure and I/O load. High swap I/O rate degrades performance even before swap usage is critical.

## Implementation

Enable vmstat scripted input in Splunk_TA_nix (interval=60). Fields `si` (swap in) and `so` (swap out) represent pages per interval. Create baseline of normal swap rate per host; alert when swap I/O rate exceeds 2x baseline or exceeds 100 pages/sec sustained for 10 minutes.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_nix`.
• Ensure the following data sources are available: `sourcetype=vmstat`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable vmstat scripted input in Splunk_TA_nix (interval=60). Fields `si` (swap in) and `so` (swap out) represent pages per interval. Create baseline of normal swap rate per host; alert when swap I/O rate exceeds 2x baseline or exceeds 100 pages/sec sustained for 10 minutes.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=vmstat host=*
| eval swap_rate = si + so
| bin _time span=1h
| stats avg(swap_rate) as avg_rate, stdev(swap_rate) as std_rate by host, _time
| eventstats avg(avg_rate) as baseline stdev(avg_rate) as baseline_std by host
| eval threshold = baseline + (2 * coalesce(baseline_std, 50))
| where avg_rate > threshold
```

Understanding this SPL

**Swap Activity Rate Trending** — Pages swapped in/out per second (distinct from swap usage %) indicates memory pressure and I/O load. High swap I/O rate degrades performance even before swap usage is critical.

Documented **Data sources**: `sourcetype=vmstat`. **App/TA** (typical add-on context): `Splunk_TA_nix`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: vmstat. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=os, sourcetype=vmstat. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **swap_rate** — often to normalize units, derive a ratio, or prepare for thresholds.
• Discretizes time or numeric ranges with `bin`/`bucket`.
• `stats` rolls up events into metrics; results are split **by host, _time** so each row reflects one combination of those dimensions.
• `eventstats` rolls up events into metrics; results are split **by host** so each row reflects one combination of those dimensions.
• `eval` defines or adjusts **threshold** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where avg_rate > threshold` — typically the threshold or rule expression for this monitoring goal.

Optional CIM / accelerated variant (memory pressure view aligned to **Performance.Memory** — complements but does not replace `si`/`so` from vmstat):

```spl
| tstats `summariesonly` avg(Performance.mem_used_percent) as mem_pct avg(Performance.swap_used_percent) as swap_pct
  from datamodel=Performance where nodename=Performance.Memory
  by Performance.host span=5m
| where mem_pct > 85 OR swap_pct > 10
```

Understanding this CIM / accelerated SPL

**Swap Activity Rate Trending** — The CIM view surfaces normalized RAM and **swap space utilization**; tune thresholds alongside your vmstat swap I/O search.

Enable **Data Model Acceleration** on **Performance.Memory**; otherwise `tstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (swap in/out rates by host), Table of hosts with elevated swap I/O, Single value (current swap rate).

## SPL

```spl
index=os sourcetype=vmstat host=*
| eval swap_rate = si + so
| bin _time span=1h
| stats avg(swap_rate) as avg_rate, stdev(swap_rate) as std_rate by host, _time
| eventstats avg(avg_rate) as baseline stdev(avg_rate) as baseline_std by host
| eval threshold = baseline + (2 * coalesce(baseline_std, 50))
| where avg_rate > threshold
```

## CIM SPL

```spl
| tstats `summariesonly` avg(Performance.mem_used_percent) as mem_pct avg(Performance.swap_used_percent) as swap_pct
  from datamodel=Performance where nodename=Performance.Memory
  by Performance.host span=5m
| where mem_pct > 85 OR swap_pct > 10
```

## Visualization

Line chart (swap in/out rates by host), Table of hosts with elevated swap I/O, Single value (current swap rate).

## References

- [Splunk_TA_nix](https://splunkbase.splunk.com/app/833)
- [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)
