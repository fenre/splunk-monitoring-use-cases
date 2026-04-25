<!-- AUTO-GENERATED from UC-1.1.23.json — DO NOT EDIT -->

---
id: "1.1.23"
title: "Kernel Core Dump Generation"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-1.1.23 · Kernel Core Dump Generation

## Description

Core dumps indicate process crashes at kernel level, enabling root cause analysis of system stability issues.

## Value

Core dumps indicate process crashes at kernel level, enabling root cause analysis of system stability issues.

## Implementation

On the UF, enable `[monitor:///var/log/kern.log]` (Debian/Ubuntu) or `[monitor:///var/log/messages]` (RHEL/CentOS) with `sourcetype=syslog`; for journald-only distros use the `[journald://]` input. Alert on first occurrence of `segfault` or `core dumped` per host. Configure `systemd-coredump` to write dumps to `/var/lib/systemd/coredump/` and monitor the directory for new files to correlate dump metadata with syslog events.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_nix, custom scripted input`.
• Ensure the following data sources are available: `sourcetype=syslog, /var/log/kern.log`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
On the UF, enable `[monitor:///var/log/kern.log]` (Debian/Ubuntu) or `[monitor:///var/log/messages]` (RHEL/CentOS) with `sourcetype=syslog`; for journald-only distros use the `[journald://]` input. Alert on first occurrence of `segfault` or `core dumped` per host. Configure `systemd-coredump` to write dumps to `/var/lib/systemd/coredump/` and monitor the directory for new files to correlate dump metadata with syslog events.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=syslog "segfault at" OR "general protection fault" OR "double fault"
| stats count by host, message, user
| eval severity="high"
```

Understanding this SPL

**Kernel Core Dump Generation** — Core dumps indicate process crashes at kernel level, enabling root cause analysis of system stability issues.

Documented **Data sources**: `sourcetype=syslog, /var/log/kern.log`. **App/TA** (typical add-on context): `Splunk_TA_nix, custom scripted input`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: syslog. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=os, sourcetype=syslog. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host, message, user** so each row reflects one combination of those dimensions.
• `eval` defines or adjusts **severity** — often to normalize units, derive a ratio, or prepare for thresholds.


Step 3 — Validate
On the host, compare with `top`, `htop`, `vmstat`, `iostat`, or `sar` as appropriate to this use case. For log-only detections, compare with the relevant file under `/var/log` (or `journalctl`) on a test host. Confirm that indexed event counts and field values line up with what you see on the system and that your role can search the right indexes and fields.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Alert, Stats Table

## SPL

```spl
index=os sourcetype=syslog "segfault at" OR "general protection fault" OR "double fault"
| stats count by host, message, user
| eval severity="high"
```

## Visualization

Alert, Stats Table

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
