<!-- AUTO-GENERATED from UC-1.1.7.json — DO NOT EDIT -->

---
id: "1.1.7"
title: "OOM Killer Events"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-1.1.7 · OOM Killer Events

## Description

OOM killer invocations mean the system ran out of memory and Linux chose to kill a process to survive. This often takes out critical services silently.

## Value

OOM killer invocations mean the system ran out of memory and Linux chose to kill a process to survive. This often takes out critical services silently.

## Implementation

Forward syslog and dmesg output. Create a real-time alert on `oom-killer` or `Out of memory` keywords. Consider setting up a triggered action to also capture current process list via scripted input when OOM occurs.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_nix`, Syslog.
• Ensure the following data sources are available: `sourcetype=syslog`, `dmesg`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Forward syslog and dmesg output. Create a real-time alert on `oom-killer` or `Out of memory` keywords. Consider setting up a triggered action to also capture current process list via scripted input when OOM occurs.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=syslog "Out of memory" OR "oom-killer" OR "Killed process"
| rex "Killed process (?<killed_pid>\d+) \((?<killed_process>[^)]+)\)"
| rex "total-vm:(?<total_vm>\d+)kB"
| table _time host killed_process killed_pid total_vm
| sort -_time
```

Understanding this SPL

**OOM Killer Events** — OOM killer invocations mean the system ran out of memory and Linux chose to kill a process to survive. This often takes out critical services silently.

Documented **Data sources**: `sourcetype=syslog`, `dmesg`. **App/TA** (typical add-on context): `Splunk_TA_nix`, Syslog. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: syslog. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=os, sourcetype=syslog. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Extracts fields with `rex` (regular expression).
• Extracts fields with `rex` (regular expression).
• Pipeline stage (see **OOM Killer Events**): table _time host killed_process killed_pid total_vm
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
On the host, compare with `top`, `htop`, `vmstat`, `iostat`, or `sar` as appropriate to this use case. For log-only detections, compare with the relevant file under `/var/log` (or `journalctl`) on a test host. Confirm that indexed event counts and field values line up with what you see on the system and that your role can search the right indexes and fields.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Events timeline, Single value panel (count of OOM events last 24h), Table with affected hosts and processes.

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
index=os sourcetype=syslog "Out of memory" OR "oom-killer" OR "Killed process"
| rex "Killed process (?<killed_pid>\d+) \((?<killed_process>[^)]+)\)"
| rex "total-vm:(?<total_vm>\d+)kB"
| table _time host killed_process killed_pid total_vm
| sort -_time
```

## Visualization

Events timeline, Single value panel (count of OOM events last 24h), Table with affected hosts and processes.

## References

- [Splunk_TA_nix](https://splunkbase.splunk.com/app/833)
