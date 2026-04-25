<!-- AUTO-GENERATED from UC-1.1.72.json — DO NOT EDIT -->

---
id: "1.1.72"
title: "SSH Public Key Changes"
criticality: "critical"
splunkPillar: "Security"
---

# UC-1.1.72 · SSH Public Key Changes

## Description

Rolls up **auditd** file events for any `authorized_keys` path, showing who ( **auid** / **user** ) and which **host** had a create or content change, for a classic persistence check.

## Value

A new key in **authorized_keys** is a silent, durable way back in; many breaches stop here for months if you only watch password auth.

## Implementation

Add recursive watches on `/home` and `/root` `.ssh/authorized_keys` (pattern depends on `auditd` version). Use a **CIM**-ready **file**+**user** extraction in **props**; add a **lookup** of approved key fingerprints in v2 of this use case.

## Detailed Implementation

Prerequisites
• `auditd` with recursive watches, or a **FIM** product that can send equivalent events. Confirm **path**~ matches your actual home layout (`/data/home/*` etc.).

**CIM** — The `action IN ("created", "modified")` matches common FIM mappings; adjust if your CIM `action` vocabulary differs (`create` vs `created`).


Step 3 — Validate
`ausearch` filtered on the authorized_keys file path, or a single test key add on a **lab** host, then the row in Search.

Step 4 — Operationalize
Pair with the **PAM** failure + **lastlog** use cases the same day for the same `user` to see a complete story.



## SPL

```spl
index=os sourcetype=linux_audit path~=".ssh/authorized_keys" (action=modified OR nametype=create)
| stats count by host, auid, user
| where count>0
```

## CIM SPL

```spl
| tstats `summariesonly` count from datamodel=Change.All_Changes where All_Changes.action IN ("created", "modified") AND match(All_Changes.object, ".*authorized_keys.*") by All_Changes.user All_Changes.dest span=1d | where count>0
```

## Visualization

Alert, Table

## References

- [Splunk Add-on for Unix and Linux](https://splunkbase.splunk.com/app/833)
- [CIM: Change](https://docs.splunk.com/Documentation/CIM/latest/User/Change)
