<!-- AUTO-GENERATED from UC-1.1.3.json — DO NOT EDIT -->

---
id: "1.1.3"
title: "Disk Capacity Forecasting (Linux)"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-1.1.3 · Disk Capacity Forecasting (Linux)

## Description

Prevents outages caused by full filesystems. A full /var or / can bring down services, databases, and logging. Enables proactive storage procurement.

## Value

Running out of space on a root or data filesystem can stop logging, databases, and applications without warning. We help you see use climbing in time to expand, clean up, or rebalance data.

## Implementation

Enable `df` scripted input (interval=300). Create a saved search that runs daily, identifying filesystems above 85%. Use `predict` command for 30-day forecasting. Set tiered alerts at 85% (warning), 90% (high), 95% (critical).

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_nix`.
• Ensure the following data sources are available: `sourcetype=df`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable `df` scripted input (interval=300). Create a saved search that runs daily, identifying filesystems above 85%. Use `predict` command for 30-day forecasting. Set tiered alerts at 85% (warning), 90% (high), 95% (critical).

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=df host=myserver Filesystem="/dev/sda1"
| timechart span=1d avg(UsePct) as disk_pct
| predict disk_pct as predicted future_timespan=30
```

Understanding this SPL

**Disk Capacity Forecasting (Linux)** — Prevents outages caused by full filesystems. A full /var or / can bring down services, databases, and logging. Enables proactive storage procurement.

Documented **Data sources**: `sourcetype=df`. **App/TA** (typical add-on context): `Splunk_TA_nix`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: df; **host** filter: myserver. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=os, sourcetype=df. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=1d** buckets — ideal for trending and alerting on this use case.
• Pipeline stage (see **Disk Capacity Forecasting (Linux)**): predict disk_pct as predicted future_timespan=30

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` avg(Performance.storage_used_percent) as disk_pct
  from datamodel=Performance where nodename=Performance.Storage
  by Performance.host Performance.mount span=1d
| where disk_pct > 85
```

Understanding this CIM / accelerated SPL

**Disk Capacity Forecasting (Linux)** — Prevents outages caused by full filesystems. A full /var or / can bring down services, databases, and logging. Enables proactive storage procurement.

Documented **Data sources**: `sourcetype=df`. **App/TA** (typical add-on context): `Splunk_TA_nix`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Performance` — enable acceleration for that model.
• Filters the current rows with `where disk_pct > 85` — typically the threshold or rule expression for this monitoring goal.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
On the host, compare with `top`, `htop`, `vmstat`, `iostat`, or `sar` as appropriate to this use case. For log-only detections, compare with the relevant file under `/var/log` (or `journalctl`) on a test host. Confirm that indexed event counts and field values line up with what you see on the system and that your role can search the right indexes and fields.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart with predict trendline, Table sorted by usage descending, Gauge per critical mount point.

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
index=os sourcetype=df host=myserver Filesystem="/dev/sda1"
| timechart span=1d avg(UsePct) as disk_pct
| predict disk_pct as predicted future_timespan=30
```

## CIM SPL

```spl
| tstats `summariesonly` avg(Performance.storage_used_percent) as disk_pct
  from datamodel=Performance where nodename=Performance.Storage
  by Performance.host Performance.mount span=1d
| where disk_pct > 85
```

## Visualization

Line chart with predict trendline, Table sorted by usage descending, Gauge per critical mount point.

## References

- [Splunk_TA_nix](https://splunkbase.splunk.com/app/833)
- [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)
