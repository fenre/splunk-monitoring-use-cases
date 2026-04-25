<!-- AUTO-GENERATED from UC-1.1.71.json — DO NOT EDIT -->

---
id: "1.1.71"
title: "/etc/shadow Modifications"
criticality: "critical"
splunkPillar: "Security"
---

# UC-1.1.71 · /etc/shadow Modifications

## Description

Detects any audit trail row that points at a write to **/etc/shadow**, the local password-hash store, with actor fields for accountability.

## Value

Legitimate **shadow** changes are rare and usually tied to `passwd`, `chpasswd`, or **IAM** automation; anything else deserves an immediate, high-severity look.

## Implementation

Add **auditd** `-w /etc/shadow -p wa -k shadow` (key name to taste). Tighten to `| where auid>0` if you only care about non-root original logins, but keep break-glass root stories in a parallel search for regulated shops.

## Detailed Implementation

Prerequisites
• Same FIM+audit story as the **passwd** use case; do **not** put raw hash contents in Splunk—only the audit metadata.

**CIM** — `object` in **All_Changes** should be the file path, not a hash field.


Step 3 — Validate
`ausearch -f /etc/shadow` and compare to Search; for binary proof, add **KEY** to include syscall class when needed.

Step 4 — Operationalize
Page the **CISO** queue per your playbooks when **exe** is a shell in `/tmp`.



## SPL

```spl
index=os sourcetype=linux_audit path="/etc/shadow" (action=modified OR nametype=normal)
| stats count by host, auid, exe
| where count>0
```

## CIM SPL

```spl
| tstats `summariesonly` count from datamodel=Change.All_Changes where All_Changes.action=modified AND match(All_Changes.object, ".*shadow.*") by All_Changes.user All_Changes.dest span=1h | where count>0
```

## Visualization

Alert, Table

## References

- [Splunk Add-on for Unix and Linux](https://splunkbase.splunk.com/app/833)
- [CIM: Change](https://docs.splunk.com/Documentation/CIM/latest/User/Change)
