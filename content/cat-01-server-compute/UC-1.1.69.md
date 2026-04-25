<!-- AUTO-GENERATED from UC-1.1.69.json — DO NOT EDIT -->

---
id: "1.1.69"
title: "SUID/SGID Binary Changes"
criticality: "critical"
splunkPillar: "Security"
---

# UC-1.1.69 · SUID/SGID Binary Changes

## Description

Collects `linux_audit` events that look like setuid/setgid or privilege-changing syscalls, grouped by path and command, as a first pass before you refine to `chmod` rule keys for your build.

## Value

Unplanned **setuid** roots on a server are a classic persistence move; a narrow audit feed cuts mean-time-to-detect for mis-builds and attackers alike when paired with a weekly `find` inventory.

## Implementation

**auditd** rules must log **chmod**/**fchmod** on executables and watch critical directories. Your fields may be `nametype`, `name`, or `file`—retarget the `search` to your parser. Drop in your standard `suid` hunting search from the OS baseline doc when ready to replace the starter string.

## Detailed Implementation

Prerequisites
• Hardened **auditd** with writable rules in `/etc/audit/rules.d` for permission bits on binaries, not only **exec**.

**SPL** — The starter `spl` is intentionally broad. Replace with the exact `key=` filters your org standardizes on, for example `key=priv_esc` on **execve**+**chmod** pairs from your reference architecture.

**CIM** — `cimSpl` is a generic **object**+**user**+**dest** count for anything mapped to **All_Changes**; tune `object` to your field name (often `file_name`).


Step 3 — Validate
`ausearch -k priv_esc` (or your key) on the node and `ls -l` the binary. Use `find / -xdev -perm /6000` during maintenance windows to rebuild an inventory baseline, not for minute-by-minute Splunk match.

Step 4 — Operationalize
Any truly new SUID in `/tmp` or `/var/tmp` is usually **sev-1** until proven otherwise.



## SPL

```spl
index=os sourcetype=linux_audit (suid=1 OR sgid=1 OR auid=0) (type=PATH OR type=SYSCALL name=chmod*)
| stats count by host, name, comm
| where count>0
```

## CIM SPL

```spl
| tstats `summariesonly` count from datamodel=Change.All_Changes where All_Changes.action=modified by All_Changes.user All_Changes.object All_Changes.dest span=1d | where count>0
```

## Visualization

Alert, Table

## References

- [Splunk Add-on for Unix and Linux](https://splunkbase.splunk.com/app/833)
- [CIM: Change](https://docs.splunk.com/Documentation/CIM/latest/User/Change)
