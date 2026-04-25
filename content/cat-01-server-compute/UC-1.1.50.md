<!-- AUTO-GENERATED from UC-1.1.50.json — DO NOT EDIT -->

---
id: "1.1.50"
title: "Transparent Hugepage Defragmentation Stalls"
criticality: "high"
splunkPillar: "Observability"
---

# UC-1.1.50 · Transparent Hugepage Defragmentation Stalls

## Description

Counts kernel log lines tied to transparent huge page defragmentation, which often shows up as latency blips for latency-sensitive services on the same host.

## Value

Knowing when a host is spending extra time in THP maintenance helps you decide whether to switch profiles (for example toward `madvise`) or to move jitter-sensitive apps.

## Implementation

Ingest the kernel or daemon logs that mention THP and khugepaged. Alert when more than a small number of lines appear in the window, then confirm on the host with THP settings and application guidance.

## Detailed Implementation

Prerequisites
• Forward security-relevant **syslog** from Linux hosts, including **kern**-priority lines where THP messages appear on your distribution.

Step 1 — Configure data collection
No extra TA feature is required beyond reliable syslog forwarding. If messages never arrive, check rsyslog/journald forwarding rules and that Splunk is not dropping **kern** facilities.

Step 2 — Create the search and alert

```spl
index=os sourcetype=syslog ("thp_defrags" OR "khugepaged" OR "thp_collapse")
| stats count by host
| where count > 5
```

Tune `>5` to your log volume. Consider adding `host=prod-*` style filters for scoped rollouts.

**Understanding this SPL** — Simple frequency count of THP-related substrings by host, alerting when the pattern appears more than a few times in the chosen lookback.


Step 3 — Validate
On a lab host, read current policy with your distribution’s ** sysfs** or ** sysctl** view of transparent hugepage settings, reproduce a low-rate pattern if safe, and confirm matching lines in Splunk. Use `top` or `htop` while testing to see user-visible latency, not to parse THP (THP is kernel-side).

Step 4 — Operationalize
Document policy choices (`always` vs `madvise` vs `never`) in the runbook and pair each alert with owners of databases or real-time apps on the node.



## SPL

```spl
index=os sourcetype=syslog ("thp_defrags" OR "khugepaged" OR "thp_collapse")
| stats count by host
| where count > 5
```

## Visualization

Alert, Table

## References

- [Splunk Add-on for Unix and Linux](https://splunkbase.splunk.com/app/833)
- [Splunk Lantern — use case library](https://lantern.splunk.com/)
