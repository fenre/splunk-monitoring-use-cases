<!-- AUTO-GENERATED from UC-1.1.65.json — DO NOT EDIT -->

---
id: "1.1.65"
title: "Auditd Rule Violation Detection"
criticality: "critical"
splunkPillar: "Security"
---

# UC-1.1.65 · Auditd Rule Violation Detection

## Description

Ranks SELinux or AppArmor-style **denied** access decisions seen in `linux_audit`, grouped by host, access vector class, and process name, when the count in the window is higher than a small floor.

## Value

A burst of access-vector denials often lines up with a mis-deployed build, a real probe, or policy drift; central counts let IR and platform teams start from a concrete `(host, avc_type, comm)` row instead of raw logs only.

## Implementation

Map `type`, `avc_type`, and `comm` in **props** for the sourcetype your TA actually emits (strings vary). Tighten the leading search to the rule keys you care about, and add **allow** lists for known noisy workloads once you have history.

## Detailed Implementation

Prerequisites
• `Splunk_TA_nix` with **augment**-style parsing of **linux_audit** into multi-line JSON or **key=value** (your props determine whether `type=AVC` is literally present in `_raw` or normalized differently).
• **CIM** note: a straight **tstats** on **Authentication** or **Change** only mirrors this UC after you have **eventtypes**+**tags** that project **AVC** denials into those models. Until then, keep the primary SPL on the raw sourcetype.

Step 1 — Configure data collection
Harden `auditd` rules, forward **/var/log/audit/audit.log** (or the journal path your distro uses) into the **os** index, and add **SME**-owned allow lists for build pipelines.

Step 2 — Create the search and alert
The saved SPL uses a numeric **>5**; convert to a token `$threshold$` in the saved search if you need per-environment values.

```spl
index=os sourcetype=linux_audit type=AVC
| stats count by host, avc_type, comm
| where count>5
```

**Understanding this SPL** — Counts **denied** decisions per tuple; you can add `| search avc_type=file` style clauses on day one to drop noise you already understand.

**CIM** — The `cimSpl` on this use case is the same failure-count form; it only populates after you project audit denials into **Authentication** (tags + fields).


Step 3 — Validate
On the host, `ausearch -m avc` or your distro’s `auditctl` status should show the same seconds and subjects as Splunk for a reproduced event. On non-prod, trigger a **known** policy denial in a test directory and search it back in Splunk.

Step 4 — Operationalize
Feed **host+avc_type+comm** to IR if counts spike across many machines at once; for single-host spikes, start with a recent **package** change and SELinux **boolean** diffs before assuming breach.

## SPL

```spl
index=os sourcetype=linux_audit type=AVC
| stats count by host, avc_type, comm
| where count>5
```

## CIM SPL

```spl
| tstats `summariesonly` count from datamodel=Authentication.Authentication where Authentication.action=failure by Authentication.user Authentication.dest span=1h | where count>5
```

## Visualization

Table, Alert

## References

- [Splunk Add-on for Unix and Linux](https://splunkbase.splunk.com/app/833)
- [Splunk CIM (Authentication, Change) for mapped variants](https://docs.splunk.com/Documentation/CIM/latest/User/Overview)
