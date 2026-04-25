<!-- AUTO-GENERATED from UC-1.1.131.json — DO NOT EDIT -->

---
id: "1.1.131"
title: "Linux OOM Killer Invocation Tracking"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-1.1.131 · Linux OOM Killer Invocation Tracking

## Description

Track which processes were killed by the OOM killer and how often. OOM events indicate severe memory pressure and often precede application outages.

## Value

Track which processes were killed by the OOM killer and how often. OOM events indicate severe memory pressure and often precede application outages.

## Implementation

Ensure kernel messages are forwarded via syslog or Splunk_TA_nix. The OOM killer logs to the kernel ring buffer; rsyslog typically captures to kern.log. Use `dmesg -T` or `journalctl -k` on the host for immediate capture. Create alert on any OOM event. Parse process name and PID for context. Correlate with memory metrics before the event.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_nix`.
• Ensure the following data sources are available: `/var/log/kern.log`, `dmesg`, `sourcetype=syslog`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Ensure kernel messages are forwarded via syslog or Splunk_TA_nix. The OOM killer logs to the kernel ring buffer; rsyslog typically captures to kern.log. Use `dmesg -T` or `journalctl -k` for immediate capture. Create alert on any OOM event. Parse process name and PID for context. Correlate with memory metrics before the event.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os (sourcetype=syslog OR sourcetype=linux_secure) host=*
| search ("oom-kill" OR "Out of memory" OR "Killed process" OR "invoked oom-killer")
| stats count by host
| where count > 0
```

Understanding this SPL

**Linux OOM Killer Invocation Tracking** — Track which processes were killed by the OOM killer and how often. OOM events indicate severe memory pressure and often precede application outages.

Documented **Data sources**: `/var/log/kern.log`, `dmesg`, `sourcetype=syslog`. **App/TA** (typical add-on context): `Splunk_TA_nix`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: syslog, linux_secure. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=os, sourcetype=syslog, linux_secure. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Applies an explicit `search` filter for kernel OOM phrases.
• `stats` rolls up events into metrics; results are split **by host** so each row reflects one combination of those dimensions.
• Filters the current rows with `where count > 0` — typically the threshold or rule expression for this monitoring goal.

Kernel OOM text does not map to a CIM data model; keep this on syslog/kernel sources.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Alert (immediate on OOM), Table (host, process, count), Timeline of OOM events.

## SPL

```spl
index=os (sourcetype=syslog OR sourcetype=linux_secure) host=*
| search ("oom-kill" OR "Out of memory" OR "Killed process" OR "invoked oom-killer")
| stats count by host
| where count > 0
```

## Visualization

Alert (immediate on OOM), Table (host, process, count), Timeline of OOM events.

## References

- [Splunk_TA_nix](https://splunkbase.splunk.com/app/833)
