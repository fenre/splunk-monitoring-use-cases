---
id: "1.1.14"
title: "File Descriptor Exhaustion"
criticality: "high"
splunkPillar: "Observability"
---

# UC-1.1.14 · File Descriptor Exhaustion

## Description

File descriptor exhaustion causes "too many open files" errors, breaking network connections, log writing, and inter-process communication. Common in Java apps and databases.

## Value

File descriptor exhaustion causes "too many open files" errors, breaking network connections, log writing, and inter-process communication. Common in Java apps and databases.

## Implementation

Create scripted input: `cat /proc/sys/fs/file-nr` (system-wide) or `ls /proc/<pid>/fd | wc -l` for per-process tracking. Alert at 80% of system or per-process limit.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_nix`, custom scripted input.
• Ensure the following data sources are available: `sourcetype=openfiles` (custom) or `/proc/sys/fs/file-nr`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Create scripted input: `cat /proc/sys/fs/file-nr` (system-wide) or `ls /proc/<pid>/fd | wc -l` for per-process tracking. Alert at 80% of system or per-process limit.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=openfiles host=*
| eval usage_pct = round(open_fds / max_fds * 100, 1)
| where usage_pct > 80
| sort -usage_pct
| table host process open_fds max_fds usage_pct
```

Understanding this SPL

**File Descriptor Exhaustion** — File descriptor exhaustion causes "too many open files" errors, breaking network connections, log writing, and inter-process communication. Common in Java apps and databases.

Documented **Data sources**: `sourcetype=openfiles` (custom) or `/proc/sys/fs/file-nr`. **App/TA** (typical add-on context): `Splunk_TA_nix`, custom scripted input. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: openfiles. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=os, sourcetype=openfiles. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **usage_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where usage_pct > 80` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
• Pipeline stage (see **File Descriptor Exhaustion**): table host process open_fds max_fds usage_pct


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Gauge (system-wide), Table per process, Line chart trend.

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
index=os sourcetype=openfiles host=*
| eval usage_pct = round(open_fds / max_fds * 100, 1)
| where usage_pct > 80
| sort -usage_pct
| table host process open_fds max_fds usage_pct
```

## Visualization

Gauge (system-wide), Table per process, Line chart trend.

## References

- [Splunk_TA_nix](https://splunkbase.splunk.com/app/833)
