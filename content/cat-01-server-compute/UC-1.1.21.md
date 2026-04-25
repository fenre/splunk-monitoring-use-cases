<!-- AUTO-GENERATED from UC-1.1.21.json — DO NOT EDIT -->

---
id: "1.1.21"
title: "Kernel Module Loading Tracking"
criticality: "high"
splunkPillar: "Security"
---

# UC-1.1.21 · Kernel Module Loading Tracking

## Description

Detects unauthorized kernel module insertions which can indicate rootkits or malware persistence.

## Value

Detects unauthorized kernel module insertions which can indicate rootkits or malware persistence.

## Implementation

Configure auditctl rules to monitor syscalls for module loading (init_module, finit_module). Create a search that alerts on any unexpected module loads outside maintenance windows. Correlate against a whitelist of approved modules per host.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_nix, custom scripted input`.
• Ensure the following data sources are available: `sourcetype=linux_audit, auditctl syscall logs`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Configure auditctl rules to monitor syscalls for module loading (init_module, finit_module). Create a search that alerts on any unexpected module loads outside maintenance windows. Correlate against a whitelist of approved modules per host.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=linux_audit action=* syscall=init_module OR syscall=finit_module
| stats count by host, name, exe
| where count > 0
```

Understanding this SPL

**Kernel Module Loading Tracking** — Detects unauthorized kernel module insertions which can indicate rootkits or malware persistence.

Documented **Data sources**: `sourcetype=linux_audit, auditctl syscall logs`. **App/TA** (typical add-on context): `Splunk_TA_nix, custom scripted input`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: linux_audit. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=os, sourcetype=linux_audit. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host, name, exe** so each row reflects one combination of those dimensions.
• Filters the current rows with `where count > 0` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
On the host, compare with `top`, `htop`, `vmstat`, `iostat`, or `sar` as appropriate to this use case. For log-only detections, compare with the relevant file under `/var/log` (or `journalctl`) on a test host. Confirm that indexed event counts and field values line up with what you see on the system and that your role can search the right indexes and fields.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table of module name, executable path, and loading user sorted by time; timechart of module load counts per host to spot anomalous spikes; single-value panel showing new (first-seen) modules in the last 24 hours for SOC triage.

## SPL

```spl
index=os sourcetype=linux_audit action=* syscall=init_module OR syscall=finit_module
| stats count by host, name, exe
| where count > 0
```

## Visualization

Table of module name, executable path, and loading user sorted by time; timechart of module load counts per host to spot anomalous spikes; single-value panel showing new (first-seen) modules in the last 24 hours for SOC triage.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
