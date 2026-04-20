---
id: "1.1.49"
title: "Memory Cgroup Limit Enforcement"
criticality: "high"
splunkPillar: "Observability"
---

# UC-1.1.49 · Memory Cgroup Limit Enforcement

## Description

Cgroup limits prevent runaway processes but enforcement indicates containers at memory limits need scaling.

## Value

Cgroup limits prevent runaway processes but enforcement indicates containers at memory limits need scaling.

## Implementation

Create a scripted input that tracks /sys/fs/cgroup/memory/* metrics. Monitor max_usage_in_bytes vs. limit_in_bytes ratio. Alert when usage exceeds 90% of limit, indicating need for more memory allocation or right-sizing.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_nix, custom scripted input`.
• Ensure the following data sources are available: `sourcetype=syslog, custom:cgroup_memory`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Create a scripted input that tracks /sys/fs/cgroup/memory/* metrics. Monitor max_usage_in_bytes vs. limit_in_bytes ratio. Alert when usage exceeds 90% of limit, indicating need for more memory allocation or right-sizing.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=syslog "memory.max_usage_in_bytes" OR "Out of memory" AND cgroup
| stats count by host, cgroup_id
| where count > 0
```

Understanding this SPL

**Memory Cgroup Limit Enforcement** — Cgroup limits prevent runaway processes but enforcement indicates containers at memory limits need scaling.

Documented **Data sources**: `sourcetype=syslog, custom:cgroup_memory`. **App/TA** (typical add-on context): `Splunk_TA_nix, custom scripted input`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: syslog. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=os, sourcetype=syslog. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host, cgroup_id** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where count > 0` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table, Gauge

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
index=os sourcetype=syslog "memory.max_usage_in_bytes" OR "Out of memory" AND cgroup
| stats count by host, cgroup_id
| where count > 0
```

## Visualization

Table, Gauge

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
