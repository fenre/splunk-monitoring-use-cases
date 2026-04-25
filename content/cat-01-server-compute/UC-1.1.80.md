<!-- AUTO-GENERATED from UC-1.1.80.json — DO NOT EDIT -->

---
id: "1.1.80"
title: "Systemd Unit Failures"
criticality: "high"
splunkPillar: "Observability"
---

# UC-1.1.80 · Systemd Unit Failures

## Description

Counts **systemd** log lines that mention failure, error, or missing unit files, grouped by **host** and **unit** field (when extracted) or by **host** alone if **unit** is still in `_raw`.

## Value

Service **active** state in **systemd** is the source of truth for many apps; log lines here are a quick backstop when you have not yet exported full **systemd** JSON to Splunk.

## Implementation

Add `REX` for `unit=` or the **User=** / **Subject:** lines your OS prints. Remove `not-found` if **first boot** noise is too high in your cloud image factory.

## Detailed Implementation

Prerequisites
• Forward **journal** for **systemd** units of interest, or use the **UF** `journald` input where available on your OS version.

**CIM** — Not applicable; these are **Availability** events, not **Authentication**.


Step 3 — Validate
`systemctl status unit` and `journalctl -u unit --since` on the host for the same minute you see in Splunk. Use `systemd-analyze blame` only for slow boot, not every **Failed** line.

Step 4 — Operationalize
Pair with the **D-state** and **memory** use cases when a unit failure is just a symptom of resource exhaustion.



## SPL

```spl
index=os sourcetype=syslog "systemd" ("Failed" OR "ERROR" OR "not-found")
| stats count by host, unit
| where count>0
```

## Visualization

Alert, Table

## References

- [Splunk Add-on for Unix and Linux](https://splunkbase.splunk.com/app/833)
- [Splunk Lantern — use case library](https://lantern.splunk.com/)
