<!-- AUTO-GENERATED from UC-1.1.67.json — DO NOT EDIT -->

---
id: "1.1.67"
title: "AppArmor Profile Violation Detection"
criticality: "high"
splunkPillar: "Security"
---

# UC-1.1.67 · AppArmor Profile Violation Detection

## Description

Counts AppArmor log lines for **DENIED** actions (and optional **ALLOW** lines that still show an enforcing profile) per **host**, **profile**, and **operation** to highlight noisy policies or abuse.

## Value

A sudden climb on a **profile**+**operation** pair is often the first place teams look when a new build reaches production under AppArmor **enforce** mode.

## Implementation

The exact `mode=enforce` string varies—adjust to your `dmesg` or **journal** phrasing. Prefer extractions of **profile** and **operation**; if your logs only have `_raw`, add two `REX` lines in **props** before you alert.

## Detailed Implementation

Prerequisites
• **AppArmor** with logging to `kern` **syslog** or **journald** that Splunk can read. Enable forwarding for **audit**-style **AppArmor** events.

Step 1 — Configure data collection
Harden the **search** string for your version of AppArmor: some builds say “audit” in every line, others are terse.

**CIM** — Not modelled; keep **N/A** unless you add an internal **security**-style CIM extension.


Step 3 — Validate
`aa-status` and `dmesg | grep -i apparmor` (or `journalctl -k` as appropriate) on the host, then the same line in **Search** in Splunk.

Step 4 — Operationalize
Tie the **profile** field to a CMDB owner for apps; route generic **unknown** profile buckets to a platform queue.



## SPL

```spl
index=os sourcetype=syslog "apparmor" ("DENIED" OR "DENY" OR ("ALLOWED" AND "enforce"))
| stats count by host, profile, operation
| where count>5
```

## Visualization

Table, Alert

## References

- [Splunk Add-on for Unix and Linux](https://splunkbase.splunk.com/app/833)
- [Splunk Lantern — use case library](https://lantern.splunk.com/)
