<!-- AUTO-GENERATED from UC-1.1.73.json — DO NOT EDIT -->

---
id: "1.1.73"
title: "PAM Authentication Failure Tracking"
criticality: "high"
splunkPillar: "Security"
---

# UC-1.1.73 · PAM Authentication Failure Tracking

## Description

Counts PAM **authentication failure** lines per **host**, **user**, and **source** IP, then raises when a tuple exceeds a small number of failures in the search window (brute-force or typo clusters).

## Value

A burst of PAM denials is one of the cheapest ways to see password-spray, stolen-account retries, and broken automation accounts before a lockout policy even fires on every system.

## Implementation

The Distro’s **syslog** format varies—tune the quoted phrase. Add **geo** and **threat** lookups later; for day one, a simple **failures>5** with `earliest=-15m` in the saved search is enough to page.

## Detailed Implementation

Prerequisites
• **linux_secure** (or the sourcetype your TA actually uses for **auth.log** / **secure**).

**SPL** — The `src` field must be extracted; if it is not, add `rex` for **rhost=** on OpenSSH PAM sub-events.

**CIM** — The `cimSpl` threshold ( **>5** in **15m** ) matches the spirit of the **failures>5** raw search; align window and threshold together when you go **tstats**-only in production.


Step 3 — Validate
Run several bad passwords on a **test** user and see them in Search; on host, `faillock` or `grep` the **auth** file for the same second.

Step 4 — Operationalize
Auto-suppress a **src** that is your main **WAF** or **SOCKS** if all staff exit there and it creates thousands of false clusters.



## SPL

```spl
index=os sourcetype=linux_secure pam "authentication failure"
| stats count as failures by host, user, src
| where failures>5
```

## CIM SPL

```spl
| tstats `summariesonly` count from datamodel=Authentication.Authentication where Authentication.action=failure by Authentication.user Authentication.src span=15m | where count>5
```

## Visualization

Table, Timechart

## References

- [Splunk Add-on for Unix and Linux](https://splunkbase.splunk.com/app/833)
- [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)
