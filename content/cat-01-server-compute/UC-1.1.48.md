---
id: "1.1.48"
title: "NUMA Memory Imbalance Per Node"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-1.1.48 · NUMA Memory Imbalance Per Node

## Description

NUMA memory imbalance causes remote memory access latency affecting NUMA-aware applications.

## Value

NUMA memory imbalance causes remote memory access latency affecting NUMA-aware applications.

## Implementation

Create a scripted input parsing /sys/devices/system/node/node*/meminfo. Calculate free memory per NUMA node monthly. Alert when free memory distribution becomes imbalanced, indicating suboptimal memory allocation.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_nix, custom scripted input`.
• Ensure the following data sources are available: `sourcetype=custom:numa_meminfo`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Create a scripted input parsing /sys/devices/system/node/node*/meminfo. Calculate free memory per NUMA node monthly. Alert when free memory distribution becomes imbalanced, indicating suboptimal memory allocation.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=custom:numa_meminfo host=*
| stats avg(node_free) as avg_free by host, numa_node
| stats max(avg_free) as max_free, min(avg_free) as min_free by host
| eval imbalance_ratio=max_free/min_free
| where imbalance_ratio > 1.5
```

Understanding this SPL

**NUMA Memory Imbalance Per Node** — NUMA memory imbalance causes remote memory access latency affecting NUMA-aware applications.

Documented **Data sources**: `sourcetype=custom:numa_meminfo`. **App/TA** (typical add-on context): `Splunk_TA_nix, custom scripted input`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: custom:numa_meminfo. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=os, sourcetype=custom:numa_meminfo. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host, numa_node** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `stats` rolls up events into metrics; results are split **by host** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **imbalance_ratio** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where imbalance_ratio > 1.5` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Gauge, Heatmap

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
index=os sourcetype=custom:numa_meminfo host=*
| stats avg(node_free) as avg_free by host, numa_node
| stats max(avg_free) as max_free, min(avg_free) as min_free by host
| eval imbalance_ratio=max_free/min_free
| where imbalance_ratio > 1.5
```

## Visualization

Gauge, Heatmap

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
