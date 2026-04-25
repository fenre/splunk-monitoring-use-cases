<!-- AUTO-GENERATED from UC-1.1.13.json — DO NOT EDIT -->

---
id: "1.1.13"
title: "Zombie Process Accumulation"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-1.1.13 · Zombie Process Accumulation

## Description

Zombie processes indicate parent processes not properly reaping children. Accumulation can exhaust PID space and indicates application bugs.

## Value

Zombie processes indicate parent processes not properly reaping children. Accumulation can exhaust PID space and indicates application bugs.

## Implementation

Enable `ps` scripted input (interval=300). The `ps` sourcetype includes a `S` (state) field where `Z` = zombie. This is more reliable than parsing the `top` header. Alert when zombie count exceeds 5. Investigate parent PIDs with `PPID` field to identify the root cause process.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_nix`.
• Ensure the following data sources are available: `sourcetype=ps` (process listing from Splunk_TA_nix).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable `ps` scripted input (interval=300). The `ps` sourcetype includes a `S` (state) field where `Z` = zombie. This is more reliable than parsing the `top` header. Alert when zombie count exceeds 5. Investigate parent PIDs with `PPID` field to identify the root cause process.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=ps host=*
| search S="Z"
| stats count as zombie_count, values(COMMAND) as zombie_processes by host
| where zombie_count > 5
| sort -zombie_count
| table host zombie_count zombie_processes
```

Understanding this SPL

**Zombie Process Accumulation** — Zombie processes indicate parent processes not properly reaping children. Accumulation can exhaust PID space and indicates application bugs.

Documented **Data sources**: `sourcetype=ps` (process listing from Splunk_TA_nix). **App/TA** (typical add-on context): `Splunk_TA_nix`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: ps. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=os, sourcetype=ps. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Applies an explicit `search` filter to narrow the current result set.
• `stats` rolls up events into metrics; results are split **by host** so each row reflects one combination of those dimensions.
• Filters the current rows with `where zombie_count > 5` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
• Pipeline stage (see **Zombie Process Accumulation**): table host zombie_count zombie_processes


Step 3 — Validate
On the host, compare with `top`, `htop`, `vmstat`, `iostat`, or `sar` as appropriate to this use case. For log-only detections, compare with the relevant file under `/var/log` (or `journalctl`) on a test host. Confirm that indexed event counts and field values line up with what you see on the system and that your role can search the right indexes and fields.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Single value panel, Table of hosts with zombie counts.

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
index=os sourcetype=ps host=*
| search S="Z"
| stats count as zombie_count, values(COMMAND) as zombie_processes by host
| where zombie_count > 5
| sort -zombie_count
| table host zombie_count zombie_processes
```

## Visualization

Single value panel, Table of hosts with zombie counts.

## References

- [Splunk_TA_nix](https://splunkbase.splunk.com/app/833)
