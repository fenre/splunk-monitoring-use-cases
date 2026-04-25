<!-- AUTO-GENERATED from UC-1.1.68.json — DO NOT EDIT -->

---
id: "1.1.68"
title: "Rootkit Detection via File Integrity"
criticality: "critical"
splunkPillar: "Security"
---

# UC-1.1.68 · Rootkit Detection via File Integrity

## Description

Surfaces AIDE file-integrity **added/changed/removed** rows for review. **count>0** is a guard so empty buckets drop out once you add windowing; most teams alert on the first new **file_path** not in a lookup.

## Value

Unexpected changes in **/bin**, **/sbin**, or other protected trees are a fast path to find dropped binaries or config drift before you rely on slower AV-only signals on servers.

## Implementation

Have AIDE print stable **change_type** and **file_path** fields. In production, add `| lookup aide_expected_changes file_path OUTPUT reason | where isnull(reason)` to suppress packager noise.

## Detailed Implementation

Prerequisites
• Nightly AIDE and a non-interactive way to **scp** or **HEC** results to Splunk. Large outputs should be one **event** per file change, not a giant **multiline** event without **LINE_BREAKER** help.

**CIM** — File integrity to **Change** is possible after CIM add-on + tags; until then, **N/A**.


Step 3 — Validate
`aide --check` exit status and the local AIDE log should match the rows Splunk shows for the run id / timestamp. Use `rpm -V` / `dpkg` verify selectively for a second opinion on a hot path.

Step 4 — Operationalize
For each hit, first ask **change management**; only then run deeper host forensics.



## SPL

```spl
index=os sourcetype=custom:aide host=*
| where change_type IN ("added", "changed", "removed")
| stats count by host, file_path, change_type
| where count>0
```

## Visualization

Alert, Table

## References

- [Splunk Add-on for Unix and Linux](https://splunkbase.splunk.com/app/833)
- [Splunk Lantern — use case library](https://lantern.splunk.com/)
