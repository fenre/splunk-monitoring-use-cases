---
id: "1.1.6"
title: "Process Crash Detection (Linux)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-1.1.6 · Process Crash Detection (Linux)

## Description

Immediate awareness of unexpected process terminations. Critical for services that don't auto-restart or have no watchdog.

## Value

Immediate awareness of unexpected process terminations. Critical for services that don't auto-restart or have no watchdog.

## Implementation

Forward `/var/log/messages` and `/var/log/syslog` via UF inputs.conf. Create an alert on keywords: `segfault`, `killed process`, `core dumped`. Enrich with service/owner lookup.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_nix`, Splunk Add-on for Syslog.
• Ensure the following data sources are available: `sourcetype=syslog`, `/var/log/messages`, `/var/log/syslog`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Forward `/var/log/messages` and `/var/log/syslog` via UF inputs.conf. Create an alert on keywords: `segfault`, `killed process`, `core dumped`. Enrich with service/owner lookup.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=syslog ("segfault" OR "killed process" OR "core dumped" OR "terminated" OR "SIGABRT" OR "SIGSEGV")
| rex "(?<process_name>\w+)\[\d+\]"
| stats count by host, process_name, _time
| sort -count
```

Understanding this SPL

**Process Crash Detection (Linux)** — Immediate awareness of unexpected process terminations. Critical for services that don't auto-restart or have no watchdog.

Documented **Data sources**: `sourcetype=syslog`, `/var/log/messages`, `/var/log/syslog`. **App/TA** (typical add-on context): `Splunk_TA_nix`, Splunk Add-on for Syslog. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: syslog. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=os, sourcetype=syslog. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Extracts fields with `rex` (regular expression).
• `stats` rolls up events into metrics; results are split **by host, process_name, _time** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Endpoint.Processes
  by Processes.dest Processes.process_name Processes.user span=1h
| sort -count
```

Understanding this CIM / accelerated SPL

**Process Crash Detection (Linux)** — Immediate awareness of unexpected process terminations. Critical for services that don't auto-restart or have no watchdog.

Documented **Data sources**: `sourcetype=syslog`, `/var/log/messages`, `/var/log/syslog`. **App/TA** (typical add-on context): `Splunk_TA_nix`, Splunk Add-on for Syslog. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Endpoint.Processes` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Events list (timeline view), Stats table grouped by host and process, Bar chart of crash counts by process.

## SPL

```spl
index=os sourcetype=syslog ("segfault" OR "killed process" OR "core dumped" OR "terminated" OR "SIGABRT" OR "SIGSEGV")
| rex "(?<process_name>\w+)\[\d+\]"
| stats count by host, process_name, _time
| sort -count
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Endpoint.Processes
  by Processes.dest Processes.process_name Processes.user span=1h
| sort -count
```

## Visualization

Events list (timeline view), Stats table grouped by host and process, Bar chart of crash counts by process.

## References

- [Splunk_TA_nix](https://splunkbase.splunk.com/app/833)
- [CIM: Endpoint](https://docs.splunk.com/Documentation/CIM/latest/User/Endpoint)
