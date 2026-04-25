<!-- AUTO-GENERATED from UC-1.3.1.json — DO NOT EDIT -->

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

Spotting high CPU and memory on Macs before tickets pile up helps support reroute work, add RAM or replacement, and avoid users sitting through a frozen desktop during busy meetings.

## Implementation

Install Splunk UF on macOS endpoints. Create scripted inputs for `top -l 1 -s 0`, `vm_stat`, and `df -h`. Run every 60-300 seconds. Parse key metrics.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk Universal Forwarder for macOS, custom scripted inputs.
• Ensure the following data sources are available: Custom scripted inputs (`top -l 1`, `vm_stat`, `df`).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Install the Universal Forwarder on macOS. Create scripted inputs for `top -l 1 -s 0`, `vm_stat`, and `df -h`. Run every 60–300 seconds. Parse `cpu_pct`, `mem_pct` (or equivalent) into fields your search expects.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=macos_top host=*
| stats latest(cpu_pct) as cpu, latest(mem_pct) as memory by host
| where cpu > 80 OR memory > 90
```

Understanding this SPL

**System Resource Monitoring** — Endpoint performance visibility helps IT support triage user complaints and identify machines needing replacement or upgrades.

Documented **Data sources**: Custom scripted inputs (`top -l 1`, `vm_stat`, `df`). The SPL targets **index** `os` and your macOS process/resource sourcetype; rename if your deployment differs. If you normalize the same host metrics through the add-on for Unix and Linux, you can also express this use case with the Performance data model and `tstats` (see the **cimSpl** field) once mapping is in place.

**Pipeline walkthrough**

• Scopes the data: `index=os`, `sourcetype=macos_top`. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` keeps the latest `cpu` and `memory` per **host**.
• `where` applies the high-utilization condition for alerting.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with Activity Monitor for CPU and memory on a test Mac. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table of endpoints, Gauge panels, Line chart trending.

Scripted input (generic example)
In the app’s `local/inputs.conf` add a stanza such as:

```ini
[script://$SPLUNK_HOME/etc/apps/YourApp/bin/macos_top.sh]
interval = 60
sourcetype = macos_top
index = os
disabled = 0
```

The script should emit one line per snapshot with parseable key=value fields. For full details (paths, scheduling, permissions), see the Implementation guide: docs/implementation-guide.md

## SPL

```spl
index=os sourcetype=macos_top host=*
| stats latest(cpu_pct) as cpu, latest(mem_pct) as memory by host
| where cpu > 80 OR memory > 90
```

## CIM SPL

```spl
| tstats `summariesonly` avg(Performance.cpu_load_percent) as cpu from datamodel=Performance where nodename=Performance.CPU by Performance.host span=5m
| join type=outer Performance.host [ | tstats `summariesonly` avg(Performance.mem_used_percent) as memory from datamodel=Performance where nodename=Performance.Memory by Performance.host span=5m ]
| where cpu > 80 OR memory > 90
```

## Visualization

Table of endpoints, Gauge panels, Line chart trending.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
