---
id: "1.1.129"
title: "Linux Softirq / Hardirq Time"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-1.1.129 · Linux Softirq / Hardirq Time

## Description

Detect interrupt storms (softirq/hardirq) that degrade system performance. High IRQ time indicates network, block I/O, or timer storms.

## Value

Detect interrupt storms (softirq/hardirq) that degrade system performance. High IRQ time indicates network, block I/O, or timer storms.

## Implementation

Create a scripted input that parses `/proc/softirqs` and `/proc/interrupts` (or use `mpstat -I SUM` for softirq/hardirq percentages). Calculate softirq and hardirq as percentage of CPU time. Run every 60 seconds. Alert when combined IRQ time exceeds 20% sustained for 10 minutes. Correlate with network/block device activity.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_nix` (scripted input).
• Ensure the following data sources are available: `/proc/interrupts`, `/proc/softirqs`, `mpstat` output.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Create a scripted input that parses `/proc/softirqs` and `/proc/interrupts` (or use `mpstat -I SUM` for softirq/hardirq percentages). Calculate softirq and hardirq as percentage of CPU time. Run every 60 seconds. Alert when combined IRQ time exceeds 20% sustained for 10 minutes. Correlate with network/block device activity.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=irq_stats host=* cpu=*
| stats latest(softirq_pct) as softirq, latest(hardirq_pct) as hardirq by host, cpu
| where softirq > 30 OR hardirq > 15
```

Understanding this SPL

**Linux Softirq / Hardirq Time** — Detect interrupt storms (softirq/hardirq) that degrade system performance. High IRQ time indicates network, block I/O, or timer storms.

Documented **Data sources**: `/proc/interrupts`, `/proc/softirqs`, `mpstat` output. **App/TA** (typical add-on context): `Splunk_TA_nix` (scripted input). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: irq_stats. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=os, sourcetype=irq_stats. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host, cpu** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where softirq > 30 OR hardirq > 15` — typically the threshold or rule expression for this monitoring goal.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t count from datamodel=Performance.CPU by Performance.host span=5m | sort - count
```

Understanding this CIM / accelerated SPL

**Linux Softirq / Hardirq Time** — Detect interrupt storms (softirq/hardirq) that degrade system performance. High IRQ time indicates network, block I/O, or timer storms.

Documented **Data sources**: `/proc/interrupts`, `/proc/softirqs`, `mpstat` output. **App/TA** (typical add-on context): `Splunk_TA_nix` (scripted input). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Performance.CPU` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (softirq/hardirq % over time), Table of hosts with elevated IRQ, Stacked area chart by IRQ type.

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
index=os sourcetype=irq_stats host=* cpu=*
| stats latest(softirq_pct) as softirq, latest(hardirq_pct) as hardirq by host, cpu
| where softirq > 30 OR hardirq > 15
```

## CIM SPL

```spl
| tstats summariesonly=t count from datamodel=Performance.CPU by Performance.host span=5m | sort - count
```

## Visualization

Line chart (softirq/hardirq % over time), Table of hosts with elevated IRQ, Stacked area chart by IRQ type.

## References

- [Splunk_TA_nix](https://splunkbase.splunk.com/app/833)
- [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)
