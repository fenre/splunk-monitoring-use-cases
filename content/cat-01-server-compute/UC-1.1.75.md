<!-- AUTO-GENERATED from UC-1.1.75.json — DO NOT EDIT -->

---
id: "1.1.75"
title: "Failed su Attempts"
criticality: "high"
splunkPillar: "Security"
---

# UC-1.1.75 · Failed su Attempts

## Description

Counts each **(host,user)** line where **su** failed in the time window, then pages when a tuple is above a few failures (credential guessing or a stuck script).

## Value

**su** failures are a tight signal on servers where people should be using **sudo** or **SAML**-backed access instead of direct **su** to **root** or shared break-glass accounts.

## Implementation

Tighten the `OR` to your distro’s exact `su` failure substring. Add `| search user=root OR target=root` if you only want privilege-escalation style **su** attempts, not all failed `su` to a normal user.

## Detailed Implementation

Prerequisites
• A single sourcetype for all **auth** events so you are not `union`ing three indexes.

**CIM** — `match(Authentication.app,"su")` is a best-effort mirror; if your CIM build uses `signature=SU`, re-target that field instead.


Step 3 — Validate
`grep su /var/log/secure` (RHEL) or `auth.log` (Debian) and compare the row count in Search for a window.

Step 4 — Operationalize
Send straight to the **access** team when the **user** is a shared break-glass account; send to the **app** owner for service accounts with automation bugs.



## SPL

```spl
index=os sourcetype=linux_secure ("su:" AND ("FAILED" OR "authentication failure"))
| stats count as failures by host, user
| where failures>3
```

## CIM SPL

```spl
| tstats `summariesonly` count from datamodel=Authentication.Authentication where Authentication.action=failure AND match(Authentication.app, "su") by Authentication.user Authentication.src span=1h | where count>3
```

## Visualization

Table, Alert

## References

- [Splunk Add-on for Unix and Linux](https://splunkbase.splunk.com/app/833)
- [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)
