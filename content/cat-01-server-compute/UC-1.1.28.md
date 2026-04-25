<!-- AUTO-GENERATED from UC-1.1.28.json — DO NOT EDIT -->

---
id: "1.1.28"
title: "IRQ Imbalance Across CPU Cores"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-1.1.28 · IRQ Imbalance Across CPU Cores

## Description

Imbalanced IRQ handling causes uneven CPU utilization and can bottleneck network or storage throughput.

## Value

Imbalanced IRQ handling causes uneven CPU utilization and can bottleneck network or storage throughput.

## Implementation

Create a scripted input that parses /proc/interrupts and calculates the coefficient of variation (stdev/mean) of IRQ distribution across CPUs. Alert when imbalance is detected; use irqbalance daemon or kernel parameters to correct.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_nix, custom scripted input`.
• Ensure the following data sources are available: `sourcetype=custom:irq_stats, /proc/interrupts`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Create a scripted input that parses /proc/interrupts and calculates the coefficient of variation (stdev/mean) of IRQ distribution across CPUs. Alert when imbalance is detected; use irqbalance daemon or kernel parameters to correct.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=custom:irq_stats
| stats avg(count) as avg_irq, stdev(count) as stddev_irq by host, irq_type
| eval cv=stddev_irq/avg_irq
| where cv > 0.5
```

Understanding this SPL

**IRQ Imbalance Across CPU Cores** — Imbalanced IRQ handling causes uneven CPU utilization and can bottleneck network or storage throughput.

Documented **Data sources**: `sourcetype=custom:irq_stats, /proc/interrupts`. **App/TA** (typical add-on context): `Splunk_TA_nix, custom scripted input`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: custom:irq_stats. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=os, sourcetype=custom:irq_stats. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host, irq_type** so each row reflects one combination of those dimensions.
• `eval` defines or adjusts **cv** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where cv > 0.5` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
On the host, compare with `top`, `htop`, `vmstat`, `iostat`, or `sar` as appropriate to this use case. For log-only detections, compare with the relevant file under `/var/log` (or `journalctl`) on a test host. Confirm that indexed event counts and field values line up with what you see on the system and that your role can search the right indexes and fields.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Heatmap, Table

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
index=os sourcetype=custom:irq_stats
| stats avg(count) as avg_irq, stdev(count) as stddev_irq by host, irq_type
| eval cv=stddev_irq/avg_irq
| where cv > 0.5
```

## Visualization

Heatmap, Table

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
