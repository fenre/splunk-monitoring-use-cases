<!-- AUTO-GENERATED from UC-1.1.5.json — DO NOT EDIT -->

---
id: "1.1.5"
title: "System Load Anomalies"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-1.1.5 · System Load Anomalies

> **Criticality:** Medium &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Performance &middot; **Wave:** Run

*Load average exceeding CPU core count indicates process queuing — so you find out before users do when something is slowing down or breaking.*

---

## Description

Load average exceeding CPU core count indicates process queuing. Useful as an early warning for runaway processes or unexpected workloads.

## Value

Load average exceeding CPU core count indicates process queuing. Useful as an early warning for runaway processes or unexpected workloads.

## Implementation

The `vmstat` sourcetype provides `loadAvg1mi` (1-minute load average). For CPU core count, use either the `hardware` sourcetype (`CPU_COUNT` field) or a server inventory lookup. Alternatively, create a custom `uptime` scripted input parsing all three load averages. Alert when load ratio exceeds 1.5 for 15+ minutes.

## Detailed Implementation

### Prerequisites
- Install and configure the required add-on or app: `Splunk_TA_nix`.
- Ensure the following data sources are available: `sourcetype=vmstat` (includes `loadAvg1mi`) or custom `uptime` scripted input.
- For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

### Step 1 — Configure data collection
The `vmstat` sourcetype provides `loadAvg1mi` (1-minute load average). For CPU core count, use either the `hardware` sourcetype (`CPU_COUNT` field) or a server inventory lookup. Alternatively, create a custom `uptime` scripted input parsing all three load averages. Alert when load ratio exceeds 1.5 for 15+ minutes.

### Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=vmstat host=*
| stats latest(loadAvg1mi) as load1 by host
| lookup server_inventory host OUTPUT cpu_count
| eval load_ratio = round(load1 / cpu_count, 2)
| where load_ratio > 1.5
| sort -load_ratio
| table host load1 cpu_count load_ratio
```

#### Understanding this SPL

**System Load Anomalies** — Load average exceeding CPU core count indicates process queuing. Useful as an early warning for runaway processes or unexpected workloads.

Documented **Data sources**: `sourcetype=vmstat` (includes `loadAvg1mi`) or custom `uptime` scripted input. **App/TA** (typical add-on context): `Splunk_TA_nix`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: vmstat. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

- Scopes the data: index=os, sourcetype=vmstat. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
- `stats` rolls up events into metrics; results are split **by host** so each row reflects one combination of those dimensions.
- Enriches events using `lookup` (lookup definition + optional OUTPUT fields).
- `eval` defines or adjusts **load_ratio** — often to normalize units, derive a ratio, or prepare for thresholds.
- Filters the current rows with `where load_ratio > 1.5` — typically the threshold or rule expression for this monitoring goal.
- Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
- Pipeline stage (see **System Load Anomalies**): table host load1 cpu_count load_ratio

### Step 3 — Validate
On the host, compare with `top`, `htop`, `vmstat`, `iostat`, or `sar` as appropriate to this use case. For log-only detections, compare with the relevant file under `/var/log` (or `journalctl`) on a test host. Confirm that indexed event counts and field values line up with what you see on the system and that your role can search the right indexes and fields.

### Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (load1/5/15 over time), Table of high-load hosts with core count context.

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
| stats latest(loadAvg1mi) as load1 by host
| lookup server_inventory host OUTPUT cpu_count
| eval load_ratio = round(load1 / cpu_count, 2)
| where load_ratio > 1.5
| sort -load_ratio
| table host load1 cpu_count load_ratio
```

## Visualization

Line chart (load1/5/15 over time), Table of high-load hosts with core count context.

## Known False Positives

Load can exceed core count during short traffic bursts, build or backup jobs, or when the CPU count in your lookup is wrong. Verify `cpu_count` from inventory or the `hardware` feed.

## References

- [Splunk_TA_nix](https://splunkbase.splunk.com/app/833)
- [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)
