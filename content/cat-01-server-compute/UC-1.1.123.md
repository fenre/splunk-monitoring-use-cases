---
id: "1.1.123"
title: "Linux Cgroup Resource Pressure (PSI)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-1.1.123 · Linux Cgroup Resource Pressure (PSI)

## Description

Monitor Pressure Stall Information (PSI) for CPU, memory, and I/O at cgroup level to detect resource contention before it causes application latency.

## Value

Monitor Pressure Stall Information (PSI) for CPU, memory, and I/O at cgroup level to detect resource contention before it causes application latency.

## Implementation

Create a scripted input that reads `/proc/pressure/cpu`, `/proc/pressure/memory`, and `/proc/pressure/io`. Parse avg10, avg60, avg300, and total fields (format: `avg10=0.00 avg60=0.00 avg300=0.00 total=12345`). Optionally collect per-cgroup PSI from `/sys/fs/cgroup/<cgroup>/cpu.pressure` etc. Run every 60 seconds. Alert when avg10 exceeds 10% or avg60 exceeds 5% for any resource.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_nix` (scripted input).
• Ensure the following data sources are available: `/proc/pressure/cpu`, `/proc/pressure/memory`, `/proc/pressure/io`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Create a scripted input that reads `/proc/pressure/cpu`, `/proc/pressure/memory`, and `/proc/pressure/io`. Parse avg10, avg60, avg300, and total fields (format: `avg10=0.00 avg60=0.00 avg300=0.00 total=12345`). Optionally collect per-cgroup PSI from `/sys/fs/cgroup/<cgroup>/cpu.pressure` etc. Run every 60 seconds. Alert when avg10 exceeds 10% or avg60 exceeds 5% for any resource.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=psi host=* cgroup=*
| stats latest(avg10) as pressure by host, cgroup, resource
| where pressure > 20
| sort -pressure
```

Understanding this SPL

**Linux Cgroup Resource Pressure (PSI)** — Monitor Pressure Stall Information (PSI) for CPU, memory, and I/O at cgroup level to detect resource contention before it causes application latency.

Documented **Data sources**: `/proc/pressure/cpu`, `/proc/pressure/memory`, `/proc/pressure/io`. **App/TA** (typical add-on context): `Splunk_TA_nix` (scripted input). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: psi. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=os, sourcetype=psi. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host, cgroup, resource** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where pressure > 20` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (pressure over time by resource), Table of hosts with elevated pressure, Gauge per resource type.

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
index=os sourcetype=psi host=* cgroup=*
| stats latest(avg10) as pressure by host, cgroup, resource
| where pressure > 20
| sort -pressure
```

## Visualization

Line chart (pressure over time by resource), Table of hosts with elevated pressure, Gauge per resource type.

## References

- [Splunk_TA_nix](https://splunkbase.splunk.com/app/833)
