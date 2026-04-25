<!-- AUTO-GENERATED from UC-1.1.66.json — DO NOT EDIT -->

---
id: "1.1.66"
title: "SELinux Denial Monitoring"
criticality: "high"
splunkPillar: "Security"
---

# UC-1.1.66 · SELinux Denial Monitoring

## Description

Groups SELinux **denied** log lines by subject/object context so you can see where policy blocks cluster and whether a single tuple suddenly spikes.

## Value

Policy mistakes and real attacks both show up as **deny** first; a grouped view is faster for app owners to tune booleans and for security to see lateral movement in **context** space.

## Implementation

If you already ingest **linux_audit** with structured fields, switch the first line to that sourcetype; syslog-only shops should ensure **setroubleshootd** or **auditd** lines actually reach the **os** index. Parse **object** if your build leaves it in `_raw` only.

## Detailed Implementation

Prerequisites
• Kernel **audit** and SELinux in **enforcing** mode with logging you can read from `/var/log/audit/audit.log` and/or `journalctl` with **SELinux** tags.

Step 1 — Configure data collection
**Props** for **source_context** / **target_context** (or the AVC string equivalents) are critical; use the TA’s add-on for Linux props where possible.

Step 2 — Create the search and alert
`action` in `stats` is removed because many builds never extracted it—re-add when your parser supplies it. Start as a **report**; alert after two consecutive windows `>5` for the same tuple.

**CIM** — There is no clean **All_Traffic**-style field for an AVC; keep this on raw unless you also model it into a custom data model.


Step 3 — Validate
`ausearch -m avc` on the host for the same second as Splunk; `sealert` (setroubleshoot) for human-readable text if you use the GUI helper.

Step 4 — Operationalize
Send **deny** spikes to the app that owns the **target** context, not only SOC, when the pattern matches a release.



## SPL

```spl
index=os sourcetype=syslog (SELinux OR setroubleshoot) denied
| stats count by host, source_context, target_context, object
| where count>5
```

## Visualization

Table, Timechart

## References

- [Splunk Add-on for Unix and Linux](https://splunkbase.splunk.com/app/833)
- [Splunk Lantern — use case library](https://lantern.splunk.com/)
