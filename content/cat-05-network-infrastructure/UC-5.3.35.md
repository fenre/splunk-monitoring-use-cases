<!-- AUTO-GENERATED from UC-5.3.35.json — DO NOT EDIT -->

---
id: "5.3.35"
title: "Citrix ADC AAA Audit Trail and Command Logging"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.3.35 · Citrix ADC AAA Audit Trail and Command Logging

> **Criticality:** High &middot; **Difficulty:** Beginner &middot; **Pillar:** Security &middot; **Type:** Security, Compliance

*We keep an audit line for shell and high-privilege work on the same box so who touched what, and when, is plain in one trail.*

---

## Description

Administrative changes on a Citrix ADC (CLI, GUI, and NITRO API) are security- and compliance-relevant. Retaining a tamper-resistant audit trail of who did what, when, from where—and whether configuration was saved—supports investigations, break-glass reviews, and control frameworks that expect full accountability for network edge devices.

## Value

Security and compliance teams track Citrix ADC administrative command execution with risk classification, detecting destructive operations, unauthorized changes, and failed admin login attempts.

## Implementation

Enable audit logging, command logging, and API access logging on the ADC; ensure administrators cannot disable logging without a separate control. Forward to `index=netscaler` with role-based read restrictions in Splunk. Retention per policy. Consider streaming critical commands to a write-once store. Alert on new admin accounts, off-hours `save ns config` bursts, or API keys used from new subnets.

## Detailed Implementation

### Prerequisites
* Splunk Add-on for Citrix NetScaler (`Splunk_TA_citrix-netscaler`, Splunkbase 2770). Citrix ADC audit/command logs. Key fields: `username`, `command`, `source_ip`, `timestamp`, `result` (SUCCESS/FAILURE), `session_id`.
* AAA audit trail tracks: (1) all CLI commands executed (nsconfig, add/remove/set), (2) GUI actions, (3) API calls, (4) admin login/logout. Essential for: change management, compliance, security investigation, troubleshooting config changes that caused issues.

### Step 1 — - Configure data collection
Enable command logging:
```
set audit syslogParams -logLevel ALL
add audit syslogAction splunk_audit <splunk_ip> -logLevel ALL -loglevel ALL
add audit syslogPolicy splunk_audit_policy ns_true splunk_audit
bind system global splunk_audit_policy -priority 1
```
Verify:
```spl
index=netscaler sourcetype="citrix:netscaler:syslog" ("CMD_EXECUTED" OR "LOGIN" OR "LOGOUT" OR "nsconfig" OR "save config") earliest=-24h
| stats count by host
```

### Step 2 — - Create the search and alert

**Primary search -- Admin activity audit trail:**
```spl
index=netscaler sourcetype="citrix:netscaler:syslog" ("CMD_EXECUTED" OR "command" OR "LOGIN" OR "LOGOUT" OR "nsconfig") earliest=-24h
| eval user=coalesce(username, user, admin_user)
| eval cmd=coalesce(command, cmd)
| eval src=coalesce(source_ip, client_ip)
| eval cmd_risk=case(match(cmd, "(?i)(rm |remove |unbind |clear |reset )"), "HIGH_RISK -- destructive command", match(cmd, "(?i)(set |add |bind ).*ssl"), "MEDIUM -- SSL config change", match(cmd, "(?i)(set |add |bind ).*lb"), "MEDIUM -- LB config change", match(cmd, "(?i)save config"), "INFO -- config saved", match(cmd, "(?i)(login|logout)"), "INFO -- session event", 1==1, "LOW")
| stats count as commands dc(cmd) as unique_cmds values(cmd_risk) as risk_levels latest(cmd) as last_cmd by user, src
| where match(mvjoin(risk_levels, ","), "HIGH_RISK|MEDIUM")
| sort -commands
```

**Unauthorized access detection:**
```spl
index=netscaler sourcetype="citrix:netscaler:syslog" ("LOGIN" AND ("fail" OR "invalid" OR "denied")) earliest=-4h
| eval user=coalesce(username, user)
| eval src=coalesce(source_ip, client_ip)
| stats count as failures dc(src) as source_ips by user
| where failures > 3
| sort -failures
```

### Step 3 — - Validate
(a) Execute a command on the ADC and verify it appears in Splunk with user context.
(b) Attempt login with wrong credentials and verify the failure is logged.
(c) Verify that all admin users appear in the audit trail.

### Step 4 — - Operationalize
Dashboard ("Citrix ADC -- Audit Trail"):
* Row 1 -- Single-value: "Admin commands (24h)", "Unique admins", "High-risk commands", "Failed logins".
* Row 2 -- Admin activity table with risk classification.
* Row 3 -- Failed login attempts.

Alerting:
* High (destructive command on prod ADC outside change window): unauthorized change.
* Warning (> 3 failed admin logins from same source): brute force attempt.

### Step 5 — - Troubleshooting

* **No audit events** -- Check: (1) audit syslog policy is bound to system global, (2) syslog action destination is correct, (3) log level includes ALL.

* **Command detail truncated** -- Long commands may be truncated in syslog. Increase message length: `set audit syslogParams -maxLogDataSizeToHold 4096`.

* **Correlating config change with outage** -- Use the audit trail timestamp to identify which command was executed before an outage. Common culprits: `save config` after `unbind` or `remove` commands.

## SPL

```spl
index=netscaler sourcetype="citrix:netscaler:syslog" ("audit" OR NITRO OR "nsconfig" OR "cmd" OR "set " OR "add " OR "rm " OR "save ns config" OR "Command" OR "local" OR API)
| eval admin=coalesce(adc_user, admin_user, user, "unknown")
| eval action=if(match(_raw, "(?i)save[\\s_]+ns[\\s_]+config"),"config_save",if(match(_raw, "(?i)NITRO|Rest|API|HTTP"),"api","cli_gui"))
| bin _time span=1h
| stats count as cmds, values(action) as actions, dc(_raw) as unique_patterns by _time, host, admin
| where cmds>0
| sort - cmds
| table _time, host, admin, actions, unique_patterns, cmds
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  by Authentication.user Authentication.action Authentication.src Authentication.app span=1h
| sort -count
```

## Visualization

Table: recent high-risk commands, user timeline, count of `save` events per day, map of source IP (if approved).

## Known False Positives

Break-glass, automation, and many admins on-call can add audit lines that look high but are expected.

## References

- [Splunk Documentation: Splunk Add-on for Citrix NetScaler](https://docs.splunk.com/Documentation/AddOns/released/CitrixNetScaler/CitrixNetScaler)
- [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)
- [Citrix ADC — Auditing and logging](https://docs.citrix.com/en-us/citrix-adc/current-release/system/audit-logging.html)
