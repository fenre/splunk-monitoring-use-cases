<!-- AUTO-GENERATED from UC-1.1.60.json — DO NOT EDIT -->

---
id: "1.1.60"
title: "MTU Mismatch Detection"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-1.1.60 · MTU Mismatch Detection

## Description

Flags a host on which at least two interfaces in the last snapshot use different MTU values, a situation that can cause hidden fragmentation or black-holed jumbo traffic across mixed networks.

## Value

Mixed-MTU boxes often sit on edges between 1500- and 9000-byte networks; making the mismatch visible prevents long hunts when apps see retransmission storms only on certain paths.

## Implementation

Snapshot `ip link` output into key=value lines with **host**, **interface**, **mtu**. The search dedupes to latest per interface, then looks for more than one distinct MTU on the same host, which is not automatically bad but always worth confirming against design documents.

## Detailed Implementation

Prerequisites
• A script the forwarder can run (often with **sudo -n** to **ip** if needed) to dump MTU in a single pass across interfaces you care about.

Step 1 — Configure data collection
Run every 15–30 minutes; MTU does not need per-second resolution. Index as `custom:mtu` under the **os** index.

Step 2 — Create the search and alert
SPL as written finds **any** mixed MTU on a host; scope with `| search interface!=lo*` if loopback mis-sized values are normal in your build.

**Understanding this SPL** — `values()` of MTU with `where mvcount(mtus) > 1` marks heterogeneity, not a specific “wrong” value.


Step 3 — Validate
On host, `ip -4 link` / `ip -6 link` to compare, and your switch `show interface` for native MTU. Use `ping -M do` / `ping -s` path tests for path MTU; **traceroute** is optional in complex MPLS cases.

Step 4 — Operationalize
Store intended MTU in CMDB, auto-close alerts when a lookup says the host is an approved mixed-MTU border.



## SPL

```spl
index=os sourcetype=custom:mtu host=*
| stats latest(mtu) as interface_mtu by host, interface
| stats values(interface_mtu) as mtus by host
| where mvcount(mtus) > 1
```

## Visualization

Table, Alert

## References

- [Splunk Add-on for Unix and Linux](https://splunkbase.splunk.com/app/833)
- [Splunk Lantern — use case library](https://lantern.splunk.com/)
