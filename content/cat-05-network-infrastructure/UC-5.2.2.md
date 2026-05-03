<!-- AUTO-GENERATED from UC-5.2.2.json — DO NOT EDIT -->

---
id: "5.2.2"
title: "Policy Change Audit"
status: "verified"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.2.2 · Policy Change Audit

> **Criticality:** Critical &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Configuration, Compliance &middot; **Status:** Verified

*We keep an eye on when firewall rules and settings change so we can show who did what, and when, for audits and clean rollbacks.*

---

## Description

Firewall rule changes can expose the network. Compliance must-have (PCI, SOX, HIPAA).

## Value

Security teams maintain a complete audit trail of firewall policy changes with admin attribution, detecting unauthorized off-hours modifications and bulk change activity.

## Implementation

Forward configuration change logs. Alert on any rule modification. Require change ticket correlation. Keep 1-year retention.

## Detailed Implementation

### Prerequisites
* Firewall system/config logs in `index=firewall`. Sourcetypes: Palo Alto `pan:system` and `pan:config`, Fortinet `fgt_event`, Cisco FTD `cisco:firepower:syslog`, Juniper SRX `juniper:junos:firewall`. Key events: rule add/modify/delete, policy commit, admin login, configuration push.
* Firewall management platforms: Panorama (PA), FortiManager (Fortinet), FMC (Cisco), Junos Space / J-Web (Juniper).

### Step 1 — - Configure data collection
**Palo Alto (config log):**
```
# Device > Log Settings > Config
# Ensure config change logging is enabled
# Forward config logs via syslog profile
```
**Fortinet:**
```
config log syslogd filter
    set severity information
    set forward-traffic enable
    set event enable
end
```
Verify:
```spl
index=firewall (sourcetype="pan:config" OR sourcetype="pan:system" OR sourcetype="fgt_event") earliest=-24h
| where match(_raw, "(?i)policy|rule|config|commit|push|change|modify|create|delete|admin")
| stats count by sourcetype, host
```

### Step 2 — - Create the search and alert

**Primary search -- Policy change audit trail:**
```spl
index=firewall earliest=-24h
| where match(_raw, "(?i)commit|policy.*(add|delete|modify|change|install)|rule.*(add|delete|modify)|configuration.*change|admin.*config")
| eval change_type=case(match(_raw, "(?i)delete|remove"), "DELETE", match(_raw, "(?i)add|create|new"), "CREATE", match(_raw, "(?i)modify|change|edit|update"), "MODIFY", match(_raw, "(?i)commit|install|push"), "COMMIT", 1==1, "OTHER")
| eval admin_user=coalesce(user, admin, src_user, dvc_user)
| eval change_target=coalesce(object_name, rule_name, policy_name, config_path)
| stats count as changes values(change_type) as change_types values(change_target) as targets latest(_time) as last_change by admin_user, host
| sort -last_change
```

**Unauthorized change window detection:**
```spl
index=firewall earliest=-7d
| where match(_raw, "(?i)commit|policy.*(add|delete|modify)|config.*change")
| eval hour=strftime(_time, "%H")
| eval is_offhours=if(hour < 7 OR hour > 19, 1, 0)
| eval is_weekend=if(strftime(_time, "%w")=0 OR strftime(_time, "%w")=6, 1, 0)
| where is_offhours=1 OR is_weekend=1
| eval admin_user=coalesce(user, admin, src_user)
| stats count as offhour_changes by admin_user, host
| where offhour_changes > 0
```

### Step 3 — - Validate
(a) Make a test policy change and verify it appears in Splunk within 1-2 minutes.
(b) Compare with firewall audit log: Panorama `Monitor > Logs > Config`, FortiManager `Log & Report > Event Log`.
(c) Verify admin user attribution is correct -- some firewalls log the management IP, not the username.

### Step 4 — - Operationalize
Dashboard ("Firewall -- Policy Change Audit"):
* Row 1 -- Single-value: "Changes (24h)", "Admins making changes", "Off-hours changes".
* Row 2 -- Change timeline with admin attribution.
* Row 3 -- Off-hours and weekend changes (potential unauthorized).

Alerting:
* High (policy delete during off-hours): potential unauthorized change.
* Warning (> 20 changes in 1 hour): bulk change activity -- verify planned.
* Info (any commit/push): audit trail for compliance.

### Step 5 — - Troubleshooting

* **Admin user showing as IP address** -- Firewall may not log the authenticated username for API/CLI changes. Check: (1) authentication is enabled for management access, (2) RADIUS/TACACS+ accounting sends username, (3) configure admin username logging in device settings.

* **Missing change events** -- Verify: (1) config/system log severity is set to informational, (2) log forwarding profile includes config events, (3) syslog destination is correctly configured.

* **Changes show in Panorama but not Splunk** -- Panorama-level changes may log differently than device-level changes. Ensure both Panorama and managed firewalls forward config logs.

## SPL

```spl
index=firewall sourcetype="pan:config" cmd="set" OR cmd="edit" OR cmd="delete"
| table _time host admin cmd path | sort -_time
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  by All_Changes.user All_Changes.object All_Changes.action span=1h
| sort -count
```

## Visualization

Table (who, what, when), Timeline, Single value (changes last 24h).

## Known False Positives

Scheduled policy pushes during change windows, automated deployments, or template updates can spike configuration events.

## References

- [Splunk_TA_paloalto](https://splunkbase.splunk.com/app/2757)
- [CIM: Change](https://docs.splunk.com/Documentation/CIM/latest/User/Change)
