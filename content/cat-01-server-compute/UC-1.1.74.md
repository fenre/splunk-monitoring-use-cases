<!-- AUTO-GENERATED from UC-1.1.74.json — DO NOT EDIT -->

---
id: "1.1.74"
title: "Login from Unusual Source IPs"
criticality: "high"
splunkPillar: "Security"
---

# UC-1.1.74 · Login from Unusual Source IPs

## Description

Within each **24h** **bucket**, compares the distinct **src** count for a **(host,user)** pair to that user’s same-day **average** distinct **src** from **eventstats**, flagging abnormally many client IPs in that window (requires a few days of history to behave).

## Value

Noisy in cloud NAT environments unless you add **CIDR** allowlists, but in fixed-VPC server estates it is a light-weight “more sources than this account usually has” check before full UEBA tools.

## Implementation

For pure burst detection, prefer a **7d**-long **inputlookup** baseline per **user**; the sample uses **eventstats** in-window as a day-one stand-in. Add `| where count>5` on underlying events if each row is a single line.

## Detailed Implementation

Prerequisites
• Successful logins with a parseable `src` (often from **OpenSSH** “Accepted” lines in **auth** / **secure** logs).

**SPL** — If you prefer machine learning, swap to **anomalydetection** on **dc(src)**. If **eventstats** is too fragile, pre-build **| inputlookup user_ssh_src_baseline.csv**.

**CIM** — The `cimSpl` is a different but related story (raw distinct sources per day); re-tune to mirror your org’s UEBA choice.


Step 3 — Validate
`last` / `wtmp` and **auth** on the host for a known **user** and compare the **IP** set to the Search output for the day.

Step 4 — Operationalize
Correlate with **MFA** enrollments; if a user is meant to travel, use **Okta/Entra** travel signals instead of raw IP alone on laptops.



## SPL

```spl
index=os sourcetype=linux_secure ("Accepted publickey" OR "Accepted password")
| bin _time span=24h
| stats dc(src) as unique_ips by host, user, _time
| eventstats avg(unique_ips) as baseline_ips by user, _time
| where isnotnull(baseline_ips) AND unique_ips > baseline_ips + 3
```

## CIM SPL

```spl
| tstats `summariesonly` dc(Authentication.src) as nsrc from datamodel=Authentication.Authentication where Authentication.action=success by Authentication.user Authentication.dest span=24h | where nsrc>5
```

## Visualization

Table, Scatter Plot

## References

- [Splunk Add-on for Unix and Linux](https://splunkbase.splunk.com/app/833)
- [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)
