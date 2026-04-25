<!-- AUTO-GENERATED from UC-1.1.2.json — DO NOT EDIT -->

---
id: "1.1.2"
title: "Memory Pressure Detection (Linux)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-1.1.2 · Memory Pressure Detection (Linux)

## Description

Prevents OOM kills, application crashes, and unresponsive systems by detecting memory exhaustion early.

## Value

We track memory and swap pressure so you can act before the system runs out of memory, thrashes, or the kernel starts killing processes.

## Implementation

Enable `vmstat` scripted input in Splunk_TA_nix (interval=60). Key fields: `memTotalMB`, `memFreeMB`, `memUsedMB`, `memUsedPct` (memory), `swapUsedPct` (swap percentage), `loadAvg1mi` (1-min load avg). Set alert when swapUsedPct exceeds 20% or memUsedPct exceeds 95% sustained for 10 minutes.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_nix`.
• Ensure the following data sources are available: `sourcetype=vmstat`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable `vmstat` scripted input in Splunk_TA_nix (interval=60). Key fields: `memTotalMB`, `memFreeMB`, `memUsedMB`, `memUsedPct` (memory), `swapUsedPct` (swap percentage), `loadAvg1mi` (1-min load avg). Set alert when swapUsedPct exceeds 20% or memUsedPct exceeds 95% sustained for 10 minutes.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=vmstat host=*
| timechart span=5m avg(memUsedPct) as memory_pct, avg(swapUsedPct) as swap_pct by host
```

Understanding this SPL

**Memory Pressure Detection (Linux)** — Prevents OOM kills, application crashes, and unresponsive systems by detecting memory exhaustion early.

Documented **Data sources**: `sourcetype=vmstat`. **App/TA** (typical add-on context): `Splunk_TA_nix`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: vmstat. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=os, sourcetype=vmstat. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by host** — ideal for trending and alerting on this use case.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` avg(Performance.mem_used_percent) as memory_pct avg(Performance.swap_used_percent) as swap_pct
  from datamodel=Performance where nodename=Performance.Memory
  by Performance.host span=5m
```

Understanding this CIM / accelerated SPL

**Memory Pressure Detection (Linux)** — Prevents OOM kills, application crashes, and unresponsive systems by detecting memory exhaustion early.

Documented **Data sources**: `sourcetype=vmstat`. **App/TA** (typical add-on context): `Splunk_TA_nix`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Performance` — enable acceleration for that model.
• Matches the timechart’s averages and `by host` split; add mem/swap threshold filters in the alert to align with the deployment guidance in Step 1.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
On the host, compare with `top`, `htop`, `vmstat`, `iostat`, or `sar` as appropriate to this use case. For log-only detections, compare with the relevant file under `/var/log` (or `journalctl`) on a test host. Confirm that indexed event counts and field values line up with what you see on the system and that your role can search the right indexes and fields.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Area chart (memory + swap stacked), Single value panels showing current utilization, Gauge widget for threshold display.

Scripted input (generic example)
This use case relies on a scripted input. In the app's local/inputs.conf add a stanza such as:

```ini
[script://$SPLUNK_HOME/etc/apps/YourApp/bin/collect.sh]
interval = 300
sourcetype = your_sourcetype
index = main
disabled = 0
```

The script should print one event per line (e.g. key=value). Example minimal script (bash):

```bash
#!/usr/bin/env bash
# Output metrics or events, one per line
echo "metric=value timestamp=$(date +%s)"
```

For full details (paths, scheduling, permissions), see the Implementation guide: docs/implementation-guide.md

## SPL

```spl
index=os sourcetype=vmstat host=*
| timechart span=5m avg(memUsedPct) as memory_pct, avg(swapUsedPct) as swap_pct by host
```

## CIM SPL

```spl
| tstats `summariesonly` avg(Performance.mem_used_percent) as memory_pct avg(Performance.swap_used_percent) as swap_pct
  from datamodel=Performance where nodename=Performance.Memory
  by Performance.host span=5m
```

## Visualization

Area chart (memory + swap stacked), Single value panels showing current utilization, Gauge widget for threshold display.

## References

- [Splunk_TA_nix](https://splunkbase.splunk.com/app/833)
- [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)
