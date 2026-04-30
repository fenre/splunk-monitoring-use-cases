<!-- AUTO-GENERATED from UC-1.1.6.json — DO NOT EDIT -->

---
id: "1.1.6"
title: "Process Crash Detection (Linux)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-1.1.6 · Process Crash Detection (Linux)

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Fault

*Immediate awareness of unexpected process terminations — so you find out before users do when something is slowing down or breaking.*

---

## Description

Immediate awareness of unexpected process terminations. Critical for services that don't auto-restart or have no watchdog.

## Value

Immediate awareness of unexpected process terminations. Critical for services that don't auto-restart or have no watchdog.

## Implementation

Forward `/var/log/messages` and `/var/log/syslog` via UF inputs.conf. Create an alert on keywords: `segfault`, `killed process`, `core dumped`. Enrich with service/owner lookup.

## Detailed Implementation

### Prerequisites
- Install and configure the required add-on or app: `Splunk_TA_nix`, Splunk Add-on for Syslog.
- Ensure the following data sources are available: `sourcetype=syslog`, `/var/log/messages`, `/var/log/syslog`.
- For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

### Step 1 — Configure data collection
Forward `/var/log/messages` and `/var/log/syslog` via UF inputs.conf. Create an alert on keywords: `segfault`, `killed process`, `core dumped`. Enrich with service/owner lookup.

### Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=syslog ("segfault" OR "killed process" OR "core dumped" OR "terminated" OR "SIGABRT" OR "SIGSEGV")
| rex "(?<process_name>\w+)\[\d+\]"
| stats count by host, process_name, _time
| sort -count
```

#### Understanding this SPL

**Process Crash Detection (Linux)** — Immediate awareness of unexpected process terminations. Critical for services that don't auto-restart or have no watchdog.

Documented **Data sources**: `sourcetype=syslog`, `/var/log/messages`, `/var/log/syslog`. **App/TA** (typical add-on context): `Splunk_TA_nix`, Splunk Add-on for Syslog. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: syslog. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

- Scopes the data: index=os, sourcetype=syslog. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
- Extracts fields with `rex` (regular expression).
- `stats` rolls up events into metrics; results are split **by host, process_name, _time** so each row reflects one combination of those dimensions.
- Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

### Step 3 — Validate
On the host, compare with `top`, `htop`, `vmstat`, `iostat`, or `sar` as appropriate to this use case. For log-only detections, compare with the relevant file under `/var/log` (or `journalctl`) on a test host. Confirm that indexed event counts and field values line up with what you see on the system and that your role can search the right indexes and fields.

### Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Events list (timeline view), Stats table grouped by host and process, Bar chart of crash counts by process.

## SPL

```spl
index=os sourcetype=syslog ("segfault" OR "killed process" OR "core dumped" OR "terminated" OR "SIGABRT" OR "SIGSEGV")
| rex "(?<process_name>\w+)\[\d+\]"
| stats count by host, process_name, _time
| sort -count
```

## Visualization

Events list (timeline view), Stats table grouped by host and process, Bar chart of crash counts by process.

## Known False Positives

Planned restarts, package upgrades, and noisy kernel or library log lines can resemble crashes. Tune keywords and severity for your distros, and match to change records.

## References

- [Splunk_TA_nix](https://splunkbase.splunk.com/app/833)
- [CIM: Endpoint](https://docs.splunk.com/Documentation/CIM/latest/User/Endpoint)
