<!-- AUTO-GENERATED from UC-5.3.35.json — DO NOT EDIT -->

---
id: "5.3.35"
title: "Citrix ADC AAA Audit Trail and Command Logging"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.3.35 · Citrix ADC AAA Audit Trail and Command Logging

## Description

Administrative changes on a Citrix ADC (CLI, GUI, and NITRO API) are security- and compliance-relevant. Retaining a tamper-resistant audit trail of who did what, when, from where—and whether configuration was saved—supports investigations, break-glass reviews, and control frameworks that expect full accountability for network edge devices.

## Value

Administrative changes on a Citrix ADC (CLI, GUI, and NITRO API) are security- and compliance-relevant. Retaining a tamper-resistant audit trail of who did what, when, from where—and whether configuration was saved—supports investigations, break-glass reviews, and control frameworks that expect full accountability for network edge devices.

## Implementation

Enable audit logging, command logging, and API access logging on the ADC; ensure administrators cannot disable logging without a separate control. Forward to `index=netscaler` with role-based read restrictions in Splunk. Retention per policy. Consider streaming critical commands to a write-once store. Alert on new admin accounts, off-hours `save ns config` bursts, or API keys used from new subnets.

## Detailed Implementation

Prerequisites
• NetScaler 12+ audit features enabled per security standard.
• Splunk access controls: admin logs readable only to security and few network owners.

Step 1 — Configure data collection
Point syslog to HEC with TLS. Verify timestamp and NTP. Mask sensitive strings if required. Use SNI-capable log forwarders if in cloud.

Step 2 — Create the search and alert
Build saved searches for: after-hours `save`, bulk deletions, user adds, and API mass operations. Throttle to avoid noise; route to a ticket with session context link.



Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  by Authentication.user Authentication.action Authentication.src Authentication.app span=1h
| sort -count
```

Understanding this CIM / accelerated SPL

This block uses `tstats` on the Authentication data model. Enable data model acceleration for the same dataset in Settings → Data models before you rely on summaries.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for the Authentication model — enable acceleration and confirm CIM tags on your source data.
• Order and filter as needed for your environment (index-time filters, allowlists, and buckets).

Enable Data Model Acceleration for the model referenced above; otherwise `tstats` may return no results from summaries.



Step 3 — Validate
Compare vservers, services, and load-balancing state in the Citrix ADC management view or command line for the same time window and objects.
Step 4 — Operationalize
Quarterly review: unused accounts, API keys, and certificate trust for automation callers.

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

## References

- [Splunk Documentation: Splunk Add-on for Citrix NetScaler](https://docs.splunk.com/Documentation/AddOns/released/CitrixNetScaler/CitrixNetScaler)
- [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)
- [Citrix ADC — Auditing and logging](https://docs.citrix.com/en-us/citrix-adc/current-release/system/audit-logging.html)
