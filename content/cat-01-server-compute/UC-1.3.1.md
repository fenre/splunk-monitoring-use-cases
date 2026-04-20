---
id: "1.3.1"
title: "System Resource Monitoring"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-1.3.1 · System Resource Monitoring

## Description

Endpoint performance visibility helps IT support triage user complaints and identify machines needing replacement or upgrades.

## Value

Endpoint performance visibility helps IT support triage user complaints and identify machines needing replacement or upgrades.

## Implementation

Install Splunk UF on macOS endpoints. Create scripted inputs for `top -l 1 -s 0`, `vm_stat`, and `df -h`. Run every 60-300 seconds. Parse key metrics.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk UF for macOS, custom scripted inputs.
• Ensure the following data sources are available: Custom scripted inputs (`top -l 1`, `vm_stat`, `df`).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Install Splunk UF on macOS endpoints. Create scripted inputs for `top -l 1 -s 0`, `vm_stat`, and `df -h`. Run every 60-300 seconds. Parse key metrics.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=macos_top host=*
| stats latest(cpu_pct) as cpu, latest(mem_pct) as memory by host
| where cpu > 80 OR memory > 90
```

Understanding this SPL

**System Resource Monitoring** — Endpoint performance visibility helps IT support triage user complaints and identify machines needing replacement or upgrades.

Documented **Data sources**: Custom scripted inputs (`top -l 1`, `vm_stat`, `df`). **App/TA** (typical add-on context): Splunk UF for macOS, custom scripted inputs. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: macos_top. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=os, sourcetype=macos_top. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where cpu > 80 OR memory > 90` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table of endpoints, Gauge panels, Line chart trending.

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
index=os sourcetype=macos_top host=*
| stats latest(cpu_pct) as cpu, latest(mem_pct) as memory by host
| where cpu > 80 OR memory > 90
```

## Visualization

Table of endpoints, Gauge panels, Line chart trending.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
