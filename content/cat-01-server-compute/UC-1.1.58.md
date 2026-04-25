<!-- AUTO-GENERATED from UC-1.1.58.json — DO NOT EDIT -->

---
id: "1.1.58"
title: "Network Bond Failover Events (Linux)"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-1.1.58 · Network Bond Failover Events (Linux)

## Description

Plots how often Linux bonding driver messages about slave or primary state changes (failed, recovering, or detected) appear, so you can see failover bursts in time across hosts.

## Value

Rapid or sustained bonding churn usually maps to a bad cable, switch port, or driver bug; catching the pattern quickly limits silent single-NIC operation that nobody noticed.

## Implementation

Kernel bonding logs to **syslog** by default on many distros. Keep `bonding` module logging at a useful level; for Dashboard Studio, convert the timechart to a thresholded alert on spikes vs baseline, or add `| where count>10` in a tstats of the underlying search in a subsearch pattern—here we keep a simple explorer **timechart** you can save as a report and clone into an alert with `anomalydetection` if you standardize on that in your org.

## Detailed Implementation

Prerequisites
• Forward **kern**-priority and driver messages to the same `syslog` path your OS index already uses.

Step 1 — Configure data collection
If nothing arrives, on-box run `dmesg -w` and confirm bonding strings while unplugging a lab cable; add **rsyslog** `imklog` or **journald** forwarding for those facilities.

Step 2 — Create the report or alert
The SPL ends at **timechart**; to alert, consider wrapping a **per-host** `bucket` in five-minute bins and `where count>threshold`, or an **anomalydetection** command on the series.

**Understanding this SPL** — String match on the bonding log lines you care about; add `bond0`-style interface filters if you multi-bond a host and only want one of them.


Step 3 — Validate
On host, `cat /proc/net/bonding/bond0` (interface name as deployed) to see live `MII Status`, then correlate timestamps with Splunk. Use `ethtool` on each slave NIC for port-level proof.

Step 4 — Operationalize
Page network operations first, then system owners; add switch port to incident tickets while links are down.



## SPL

```spl
index=os sourcetype=syslog "bonding:" ("slave" OR "primary") ("failed" OR "recovering" OR "detected")
| timechart count by host
```

## Visualization

Alert, Timechart

## References

- [Splunk Add-on for Unix and Linux](https://splunkbase.splunk.com/app/833)
- [Splunk Lantern — use case library](https://lantern.splunk.com/)
