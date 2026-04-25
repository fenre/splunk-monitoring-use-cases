<!-- AUTO-GENERATED from UC-1.1.1.json — DO NOT EDIT -->

---
id: "1.1.1"
title: "CPU Utilization Trending (Linux)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-1.1.1 · CPU Utilization Trending (Linux)

## Description

Detects overloaded hosts before they cause application degradation. Enables capacity planning and right-sizing.

## Value

Sustained high CPU often means a busy application, a batch window, or a host that is undersized. We surface it early so you can add capacity, move work, or track down a runaway process before service suffers.

## Implementation

Install Splunk_TA_nix on Universal Forwarders. Enable the `cpu` scripted input in `inputs.conf` (`[script://./bin/cpu.sh]`, interval=60). The cpu sourcetype provides fields: `pctUser`, `pctSystem`, `pctIowait`, `pctIdle`, etc. Create an alert for sustained >90% over 15 minutes using a rolling window.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_nix`.
• Ensure the following data sources are available: `sourcetype=cpu` (from `cpu.sh` scripted input).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Install Splunk_TA_nix on Universal Forwarders. Enable the `cpu` scripted input in `inputs.conf` (`[script://./bin/cpu.sh]`, interval=60). The cpu sourcetype provides fields: `pctUser`, `pctSystem`, `pctIowait`, `pctIdle`, etc. Create an alert for sustained >90% over 15 minutes using a rolling window.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=cpu host=*
| eval cpu_used = 100 - pctIdle
| timechart span=1h avg(cpu_used) as avg_cpu by host
| where avg_cpu > 90
```

Understanding this SPL

**CPU Utilization Trending (Linux)** — Detects overloaded hosts before they cause application degradation. Enables capacity planning and right-sizing.

Documented **Data sources**: `sourcetype=cpu` (from `cpu.sh` scripted input). **App/TA** (typical add-on context): `Splunk_TA_nix`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: cpu. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=os, sourcetype=cpu. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **cpu_used** — often to normalize units, derive a ratio, or prepare for thresholds.
• `timechart` plots the metric over time using **span=1h** buckets with a separate series **by host** — ideal for trending and alerting on this use case.
• Filters the current rows with `where avg_cpu > 90` — typically the threshold or rule expression for this monitoring goal.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` avg(Performance.cpu_load_percent) as avg_cpu
  from datamodel=Performance where nodename=Performance.CPU
  by Performance.host span=1h
| where avg_cpu > 90
```

Understanding this CIM / accelerated SPL

**CPU Utilization Trending (Linux)** — Detects overloaded hosts before they cause application degradation. Enables capacity planning and right-sizing.

Documented **Data sources**: `sourcetype=cpu` (from `cpu.sh` scripted input). **App/TA** (typical add-on context): `Splunk_TA_nix`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Performance` — enable acceleration for that model.
• Filters the current rows with `where avg_cpu > 90` — typically the threshold or rule expression for this monitoring goal.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
On the host, compare with `top`, `htop`, `vmstat`, `iostat`, or `sar` as appropriate to this use case. For log-only detections, compare with the relevant file under `/var/log` (or `journalctl`) on a test host. Confirm that indexed event counts and field values line up with what you see on the system and that your role can search the right indexes and fields.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (timechart by host), Single value panels for current/peak CPU, Table of hosts exceeding threshold.

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
index=os sourcetype=cpu host=*
| eval cpu_used = 100 - pctIdle
| timechart span=1h avg(cpu_used) as avg_cpu by host
| where avg_cpu > 90
```

## CIM SPL

```spl
| tstats `summariesonly` avg(Performance.cpu_load_percent) as avg_cpu
  from datamodel=Performance where nodename=Performance.CPU
  by Performance.host span=1h
| where avg_cpu > 90
```

## Visualization

Line chart (timechart by host), Single value panels for current/peak CPU, Table of hosts exceeding threshold.

## References

- [Splunk Add-on for Unix and Linux](https://splunkbase.splunk.com/app/833)
- [inputs.conf](https://docs.splunk.com/Documentation/Splunk/latest/Admin/Inputsconf)
