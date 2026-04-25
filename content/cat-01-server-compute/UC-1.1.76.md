<!-- AUTO-GENERATED from UC-1.1.76.json — DO NOT EDIT -->

---
id: "1.1.76"
title: "Privilege Escalation Detection"
criticality: "critical"
splunkPillar: "Security"
---

# UC-1.1.76 · Privilege Escalation Detection

## Description

Lists **sudo** command lines (with a `command=` fragment) grouped by **host**, **user**, and **command**, so break-glass and automation owners can review anything outside their known patterns.

## Value

Unexpected **sudo** usage is a practical early sign of a stolen password or a job running under the wrong service account, especially on servers where only a few commands should ever be elevated.

## Implementation

Ingest the OS authentication log the TA maps to `linux_secure`. Tighten the search with a `lookup` of approved `(user, command)` pairs when you are ready, or with `| search NOT user=buildsvc` allowlists. Pair with `linux_audit` for the executed binary when you add syscall rules later.

## Detailed Implementation

Prerequisites
• `Splunk_TA_nix` with **linux_secure**-style input pointed at the OS authentication log (path depends on the distribution).

Step 1 — Configure data collection
Map Red Hat **secure** and Debian **auth.log** to the same sourcetype your TA documents; avoid duplicate ingestion of the same file via rsyslog and a second UF.

Step 2 — Create the search and alert
`sudo` with `command=` is common on modern distros; if your file omits the fragment, search only `"sudo:"` and extract **command** with `rex`.

**CIM** — The `cimSpl` counts successful, CIM-tagged `sudo` events per `Authentication.user` and `Authentication.src`—only after the TA+CIM add-on mark those fields.


Step 3 — Validate
Trigger `sudo` on a lab system and read the line with `tail -f` on the host, then the same line in Search. Keep **auditd** syscall trails if you need binary-level proof in regulated environments.

Step 4 — Operationalize
Tie alerts to a lookup of expected automation users before paging humans.


## SPL

```spl
index=os sourcetype=linux_secure "sudo:" "command="
| stats count by host, user, command
| where user!="root"
```

## CIM SPL

```spl
| tstats `summariesonly` count from datamodel=Authentication.Authentication where Authentication.app=sudo AND Authentication.action=success by Authentication.user Authentication.src span=1h | where count>0
```

## Visualization

Alert, Table

## References

- [Splunk Add-on for Unix and Linux](https://splunkbase.splunk.com/app/833)
- [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)
