<!-- AUTO-GENERATED from UC-1.1.81.json — DO NOT EDIT -->

---
id: "1.1.81"
title: "Systemd Timer Missed Triggers"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-1.1.81 · Systemd Timer Missed Triggers

## Description

Finds **systemd** timer messages that say a trigger could not run or was skipped, grouped by **host** and **timer_unit** when parsed.

## Value

Missed backups, **SLA** batch jobs, and security **rotate** tasks often first show up as timer journal lines, not as an app-level error code.

## Implementation

Some distros log these at **notice** not **err**—verify your **syslog** facility filter is not dropping them. Add `| where count>1` to avoid one-off clock skew noise.

## Detailed Implementation

Prerequisites
• Timers defined in `/etc/systemd/system` or **vendor** trees, with **Persistent=true** where you need catch-up after downtime.


Step 3 — Validate
`systemctl list-timers --all` and `journalctl -u mytimer.timer` on the host; compare **NEXT** / **LEFT** with the Splunk timestamp.

Step 4 — Operationalize
When a timer is **missed**, check **OnCalendar=** vs actual host load first, not only the app.



## SPL

```spl
index=os sourcetype=syslog "systemd" "timer" ("cannot run" OR "Skipping")
| stats count by host, timer_unit
| where count>0
```

## Visualization

Alert, Table

## References

- [Splunk Add-on for Unix and Linux](https://splunkbase.splunk.com/app/833)
- [Splunk Lantern — use case library](https://lantern.splunk.com/)
