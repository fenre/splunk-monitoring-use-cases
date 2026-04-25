<!-- AUTO-GENERATED from UC-1.1.77.json — DO NOT EDIT -->

---
id: "1.1.77"
title: "Unauthorized Cron Job Additions"
criticality: "critical"
splunkPillar: "Security"
---

# UC-1.1.77 · Unauthorized Cron Job Additions

## Description

Flags **auditd** file events that touch user or system crontab paths, grouped by who (`auid`) and which `file_name`, as a first line of defense against persistence in scheduled jobs.

## Value

**cron** and **systemd** timers are a favorite persistence vector after initial access; catching unexpected writers closes a gap between pure shell history review and EDR in many Linux-only shops.

## Implementation

Paths differ per distro (`/var/spool/cron/crontabs` vs `cron/tabs`). Broaden the `path~` until your coverage matches your **CMDB**; add `| lookup` for package-managed cron files in `/etc/cron.d` once you have an inventory.

## Detailed Implementation

Prerequisites
• `auditd` with watches that cover all **cron** drop directories you use, including per-user `crontab -e` locations.

**SPL** — `match` on `action` assumes your **KEY** sets **action=**; if you only have **type=PATH**, rephrase the filter.


Step 3 — Validate
`ls -l` the path on host and `crontab -l -u` for the user. Compare the **auid** to **sudoreplay** or **btmp** for interactive proof when needed (never on production without a change).

Step 4 — Operationalize
Any **.sh** in **cron** that lives under `/tmp` is almost always a red flag in regulated environments.



## SPL

```spl
index=os sourcetype=linux_audit path~="/var/spool/cron" OR path~="/etc/cron"
| where match(action, "(modified|created)") OR nametype=create
| stats count by host, auid, file_name
| where count>0
```

## CIM SPL

```spl
| tstats `summariesonly` count from datamodel=Change.All_Changes where All_Changes.action IN ("created", "modified") AND match(All_Changes.object, ".*cron.*") by All_Changes.user All_Changes.dest span=1d | where count>0
```

## Visualization

Alert, Table

## References

- [Splunk Add-on for Unix and Linux](https://splunkbase.splunk.com/app/833)
- [CIM: Change](https://docs.splunk.com/Documentation/CIM/latest/User/Change)
