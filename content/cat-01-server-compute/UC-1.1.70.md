<!-- AUTO-GENERATED from UC-1.1.70.json — DO NOT EDIT -->

---
id: "1.1.70"
title: "/etc/passwd Modifications"
criticality: "critical"
splunkPillar: "Security"
---

# UC-1.1.70 · /etc/passwd Modifications

## Description

Lists audit events that reference **/etc/passwd** with a modification-style action so you can prove who changed local account metadata and from which binary.

## Value

Account creation and lock/unlock events should flow through **change** management; unexpected **passwd** writers are a first-class signal for insider and external abuse on shared servers.

## Implementation

Requires an **auditd** rule such as `-w /etc/passwd -p wa -k passwd_changes` (exact key is your choice). Map `auid`, `exe`, and `path` for the TA; drop `nametype=normal` if your distro only logs `PATH` parts.

## Detailed Implementation

Prerequisites
• **auditd** on every production host, with logs shipped and **FIM**-style retention in your org’s secure index as required by policy.

**CIM** — The `object` string match mirrors file-path monitoring once your **props**+**eventtypes** map these events to **All_Changes**.


Step 3 — Validate
`ausearch -f /etc/passwd` on the host for the same epoch; `lastlog` / `getent` for the users you expect. Keep **PAM** logs (`linux_secure`) in a correlated search for the same **auid** when triaging.

Step 4 — Operationalize
Auto-ticket the owning application when **exe** is not **useradd**-class; send straight to **IR** for **exe** in world-writable paths.



## SPL

```spl
index=os sourcetype=linux_audit path="/etc/passwd" (action=modified OR nametype=normal)
| stats count by host, auid, exe
| where count>0
```

## CIM SPL

```spl
| tstats `summariesonly` count from datamodel=Change.All_Changes where All_Changes.action=modified AND All_Changes.object="*passwd*" by All_Changes.user All_Changes.dest span=1h | where count>0
```

## Visualization

Alert, Table

## References

- [Splunk Add-on for Unix and Linux](https://splunkbase.splunk.com/app/833)
- [CIM: Change](https://docs.splunk.com/Documentation/CIM/latest/User/Change)
