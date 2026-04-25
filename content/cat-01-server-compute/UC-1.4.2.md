<!-- AUTO-GENERATED from UC-1.4.2.json — DO NOT EDIT -->

---
id: "1.4.2"
title: "RAID Degradation Alerts"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-1.4.2 · RAID Degradation Alerts

## Description

A degraded RAID has lost redundancy — another disk failure means data loss. Requires immediate attention.

## Value

The moment a mirror or parity group drops out of a healthy state, you need to know so you can replace a disk or fix a backplane while data is still protected.

## Implementation

Create scripted input for the RAID controller CLI tool: `storcli /c0/v0 show` or `megacli -LDInfo -Lall -aAll`. Run every 300 seconds. Alert immediately on any non-Optimal state.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom scripted input (`megacli`, `storcli`, `ssacli`).
• Ensure the following data sources are available: Custom sourcetype (RAID controller output).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
On the host OS (typically Linux with vendor CLI), create a scripted input for the RAID tool: e.g. `storcli` or `megacli`. Run every 300 seconds. Parse virtual disk name, state, and failed disk count. Alert on any non-Optimal or policy-defined state.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=hardware sourcetype=raid_status
| where state!="Optimal" AND state!="Online"
| table _time host vd_name state disks_failed
| sort -_time
```

Understanding this SPL

**RAID Degradation Alerts** — A degraded RAID has lost redundancy — another disk failure means data loss. Requires immediate attention.

**Pipeline walkthrough**

• Scopes the data: `index=hardware`, `sourcetype=raid_status`.
• `where` keeps rows that are not in your healthy set.
• `table` and `sort` list recent problem arrays.


Step 3 — Validate
On a test host, run the vendor CLI and compare to indexed fields. If your vendor never emits `Optimal` but uses a different “OK” string, change the **where** clause accordingly.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions as required. See the Implementation guide: docs/implementation-guide.md

## SPL

```spl
index=hardware sourcetype=raid_status
| where state!="Optimal" AND state!="Online"
| table _time host vd_name state disks_failed
| sort -_time
```

## CIM SPL

```spl
N/A — RAID array state is not a standard CIM data model object; use controller CLI output in a custom sourcetype or vendor extension.
```

## Visualization

Status indicator per array, Table, Alert panel (critical).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
