<!-- AUTO-GENERATED from UC-1.1.59.json — DO NOT EDIT -->

---
id: "1.1.59"
title: "Network Team Failover Detection (Linux)"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-1.1.59 · Network Team Failover Detection (Linux)

## Description

Surfaces any teamd log lines about ports or links moving between down, up, enabled, and disabled, grouped by host and team device name, for teams using libteam instead of traditional bonding drivers.

## Value

Team interfaces aggregate links much like bonds; you want the same early warning when a leg drops so you are not a single port failure away from an outage.

## Implementation

Point syslog collection at the facility teamd already uses. If your distro logs teamd into **journald** only, add a `journald` to **syslog** forwarder. Consider raising `>0` to a five-minute `stats` + threshold when the daemon is very chatty at info level.

## Detailed Implementation

Prerequisites
• **teamd** must log to a facility Splunk already ingests; if not, enable **syslog** forwarding from **journald** for `teamd.service` only.

Step 1 — Configure data collection
Add **SEDCMD** to extract `team_interface` if the raw text embeds the device name; otherwise alert at host level first and refine later.

Step 2 — Create the search and alert
`where count>0` is minimal; in production, change to `| where count>5` in a five-minute `bucket` to ignore single stray lines.

**Understanding this SPL** — Boolean match on the verb list; you can split into two saved searches: one for **down/disabled** (page) and one for **up/enabled** (info).


Step 3 — Validate
`teamdctl` state on the host, `ip link show team0`, and switch interface counters should align with the Splunk time window. Use `ping` and `mtr` only as traffic checks, not as proof of LACP/team state.

Step 4 — Operationalize
Coordinate with the network on physical ports whenever **down** lines appear, even if user traffic still works on the surviving link.



## SPL

```spl
index=os sourcetype=syslog "teamd" ("port" OR "link") ("down" OR "up" OR "enabled" OR "disabled")
| stats count by host, team_interface
| where count > 0
```

## Visualization

Alert, Table

## References

- [Splunk Add-on for Unix and Linux](https://splunkbase.splunk.com/app/833)
- [Splunk Lantern — use case library](https://lantern.splunk.com/)
