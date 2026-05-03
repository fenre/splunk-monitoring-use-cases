<!-- AUTO-GENERATED from UC-5.1.57.json — DO NOT EDIT -->

---
id: "5.1.57"
title: "Junos Commit History and Configuration Rollback Audit (Juniper)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.1.57 · Junos Commit History and Configuration Rollback Audit (Juniper)

> **Criticality:** High &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Configuration, Compliance

*We keep a simple story of who committed Junos config changes and when, so you can prove what changed during an incident or an audit.*

---

## Description

Junos treats configuration as a sequence of commits, so every change is tied to a user, time, and optional comment—ideal for audit and rollback to any of the last stored revisions. Without central logging, you lose the evidence needed to prove who changed routing, security zones, or interfaces during an incident. Correlating commits with change tickets catches unapproved changes and commits outside maintenance windows before they propagate through routing or firewall policy.

## Value

Operations teams audit Junos commit history including rollbacks and unconfirmed commits, tracking who changed device configuration and correlating changes with incidents.

## Implementation

Ensure `interactive-commands` (or equivalent) is logged to the host that forwards to Splunk. Parse `UI_COMMIT` / `UI_COMMIT_COMPLETED` lines; if the TA already extracts `user`, prefer that field over `rex`. Alert on commits from break-glass accounts or when `_time` is outside approved windows (lookup). Join to change-management lookup by ticket ID when comments include ticket numbers.

## Detailed Implementation

### Prerequisites
* Junos commit history and configuration audit logs. Data in `index=juniper` with `sourcetype=juniper:structured`. Key Junos syslog: `UI_COMMIT`, `UI_COMMIT_COMPLETED`, `UI_COMMIT_NOT_CONFIRMED`, `UI_CMDLINE_READ_LINE`.
* Junos commit model: all configuration changes require explicit `commit` to apply. Junos logs each commit with username, timestamp, and commit comment. `commit confirmed` provides rollback safety. `rollback <n>` reverts to previous configs (up to 50 stored).

### Step 1 — - Configure data collection
```
# Junos -- commit logging is enabled by default
set system syslog host <splunk-ip> any info
set system syslog host <splunk-ip> interactive-commands any
set system syslog host <splunk-ip> change-log any

# Splunk inputs.conf
[udp://514]
sourcetype = juniper:structured
index = juniper
```
Verify:
```spl
index=juniper earliest=-30d
| where match(_raw, "(?i)UI_COMMIT|commit|rollback|CMDLINE")
| stats count by host
```

### Step 2 — - Create the search and alert

**Primary search -- Commit history and rollback audit:**
```spl
index=juniper earliest=-30d
| where match(_raw, "(?i)UI_COMMIT|UI_CMDLINE_READ_LINE.*commit|UI_CMDLINE_READ_LINE.*rollback")
| eval device=coalesce(host, device_name)
| rex field=_raw "(?i)user\s+'(?<commit_user>[^']+)'"
| rex field=_raw "(?i)comment\s+'(?<commit_comment>[^']+)'"
| eval user=coalesce(commit_user, user, admin)
| eval action=case(
    match(_raw, "(?i)COMMIT_COMPLETED|commit complete"), "COMMIT",
    match(_raw, "(?i)COMMIT_NOT_CONFIRMED"), "COMMIT_NOT_CONFIRMED",
    match(_raw, "(?i)rollback"), "ROLLBACK",
    match(_raw, "(?i)UI_COMMIT"), "COMMIT",
    1==1, "CONFIG_CHANGE")
| eval severity=case(
    action="ROLLBACK", "WARNING -- configuration rollback performed",
    action="COMMIT_NOT_CONFIRMED", "WARNING -- commit not confirmed (auto-rollback)",
    action="COMMIT" AND user="root", "INFO -- root user commit",
    1==1, "INFO")
| stats count as events values(action) as actions values(commit_comment) as comments by device, user, severity
| sort severity, -events
```

### Step 3 — - Validate
(a) CLI: `show system commit` -- display commit history with timestamps.
(b) CLI: `show configuration | compare rollback <n>` -- diff between current and rollback point.
(c) Cross-reference commits with change management tickets.

### Step 4 — - Operationalize
Dashboard ("Juniper -- Commit History"):
* Row 1 -- Single-value: "Commits (30d)", "Rollbacks", "Unique administrators".
* Row 2 -- Commit history timeline.

Alert: Warning (rollback performed): investigate why change was reverted.

### Step 5 — - Troubleshooting

* **Rollback indicates bad change** -- Check: `show system commit` for the commit that was rolled back. Review the diff: `show configuration | compare rollback <n>`.

* **Commit not confirmed** -- Auto-rollback occurred because `commit confirmed <minutes>` was used and confirmation wasn't sent in time. Useful safety feature but indicates the admin lost access after commit.

* **Unauthorized commit** -- Review user, source IP, and time. Cross-reference with TACACS+/RADIUS logs. Verify change management approval.

## SPL

```spl
index=network sourcetype="juniper:junos:structured"
| search UI_COMMIT OR UI_COMMIT_COMPLETED OR "UI_COMMIT_EVENT"
| rex field=_raw "(?i)user\s+['\"]?(?<commit_user>[^\s'\"]+)"
| rex field=_raw "(?i)comment\s*[:=]\s*['\"]?(?<commit_comment>[^'\"\n]+)"
| rex field=_raw "configuration committed by (?<commit_user2>\S+)"
| eval operator=coalesce(commit_user, commit_user2, user)
| stats earliest(_time) as first_seen, latest(_time) as last_seen, count as commits, latest(commit_comment) as last_comment by host, operator
| sort -last_seen
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  by All_Changes.user All_Changes.command All_Changes.action span=1h
| sort -count
```

## Visualization

Commit timeline by device; table of last commit per host with user and comment; compliance panel for commits without matching change record.

## Known False Positives

Automated commit scripts, hitless GRES sync, and off-hours break-glass logins are normal when documented—tie alerts to the change record.

## References

- [CIM: Change](https://docs.splunk.com/Documentation/CIM/latest/User/Change)
