<!-- AUTO-GENERATED from UC-5.2.48.json — DO NOT EDIT -->

---
id: "5.2.48"
title: "Check Point Policy Install and Publish Tracking (Check Point)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.2.48 · Check Point Policy Install and Publish Tracking (Check Point)

> **Criticality:** High &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Configuration

*We follow policy install and publish steps so a bad push, a late night edit, or a missing approval is not invisible when auditors ask why.*

---

## Description

Policy install pushes new rulebase and object changes from the management server (SmartConsole/Smart-1 Cloud) to enforcement gateways. A failed install leaves old policy active; a successful install with errors may silently break specific rules. Tracking install timestamps, success/failure, and who published enables change management correlation and root-cause analysis when traffic patterns shift unexpectedly after a policy push.

## Value

Security teams track Check Point policy install and publish events with administrator attribution, detecting failed installs that leave gateways on stale policies and unauthorized changes.

## Implementation

Forward management audit logs via Log Exporter. Track policy install duration (publish → install complete). Alert on install failures or partial installs (some gateways succeeded, others failed). Require ITSM ticket IDs in SmartConsole session descriptions for audit correlation. Report on policy change frequency by admin and gateway.

## Detailed Implementation

### Prerequisites
* Check Point policy install and publish audit logs. Data in `index=checkpoint` or `index=firewall` with `sourcetype=cp_log`. Key fields: `product` (SmartConsole, Management Server), `action` (Install Policy, Publish), `administrator`, `policy_name`, `target`, `status`, `rule_count`.
* Check Point policy workflow: (1) Admin edits rules in SmartConsole, (2) Publishes changes (creates audit trail), (3) Installs policy to gateway(s). Each step generates audit logs. Failed installs leave gateways on previous policy version. CLI: `show-sessions`, `install-policy`.

### Step 1 — - Configure data collection
```
# Check Point Management Server -- enable audit logging
# SmartConsole > Manage & Settings > Logs & Masters
# Log policy install and configuration changes
# Ensure "Audit" blade is enabled

# Log Exporter (captures audit and system logs)
cp_log_export add name splunk_audit target-server <splunk-ip> target-port 514 protocol udp format syslog
cp_log_export set name splunk_audit read-mode audit
cp_log_export restart name splunk_audit
```
Verify:
```spl
index=checkpoint sourcetype="cp_log" earliest=-30d
| where match(action, "(?i)install.*policy|publish|policy.*install") OR match(product, "(?i)SmartConsole|Audit")
| stats count by action, administrator, status
```

### Step 2 — - Create the search and alert

**Primary search -- Policy install and publish audit trail:**
```spl
index=checkpoint sourcetype="cp_log" earliest=-30d
| where match(action, "(?i)install.*policy|publish|policy.*install|accept.*changes")
| eval admin=coalesce(administrator, user, src_user_name)
| eval policy=coalesce(policy_name, policy, rule_name)
| eval target_gw=coalesce(target, dst, gateway)
| eval install_status=case(
    match(status, "(?i)succeeded|success|completed"), "SUCCESS",
    match(status, "(?i)failed|error|timeout"), "FAILED",
    match(status, "(?i)warning|partial"), "PARTIAL",
    1==1, "UNKNOWN")
| eval change_type=case(
    match(action, "(?i)publish"), "PUBLISH",
    match(action, "(?i)install"), "INSTALL",
    1==1, "OTHER")
| stats count as events count(eval(install_status="FAILED")) as failures count(eval(install_status="SUCCESS")) as successes values(target_gw) as targets by admin, policy, change_type, install_status
| eval severity=case(
    install_status="FAILED", "CRITICAL -- policy install FAILED",
    install_status="PARTIAL", "WARNING -- partial policy install",
    change_type="INSTALL" AND match(admin, "(?i)unknown|system|api"), "WARNING -- non-interactive policy install",
    1==1, "INFO")
| eval last_time=strftime(now(), "%Y-%m-%d %H:%M:%S")
| where severity != "INFO" OR change_type="INSTALL"
| sort severity, -events
```

### Step 3 — - Validate
(a) SmartConsole: Logs & Monitor > Audit -- verify install events appear.
(b) CLI: `show-gateways` -- check policy date on each gateway.
(c) Verify: `show-sessions limit 5` -- recent management sessions.

### Step 4 — - Operationalize
Dashboard ("Check Point -- Policy Management"):
* Row 1 -- Single-value: "Policy installs (30d)", "Failed installs", "Administrators active".
* Row 2 -- Policy install timeline.
* Row 3 -- Audit trail table (admin, action, gateway, status).

Alert: Critical (policy install failed): gateway running stale policy, investigate immediately.

### Step 5 — - Troubleshooting

* **Policy install failed** -- Common causes: (1) SIC (Secure Internal Communication) certificate issue between management and gateway, (2) disk space on gateway, (3) rule conflict or invalid object reference. Check: `cpca_client lscert` for SIC, and SmartConsole install log for detailed error.

* **Unauthorized policy change** -- Review audit log for admin identity. Cross-reference with change management tickets. Consider requiring approval for policy installs via SmartWorkflow.

* **Policy install timeout** -- Large rulebases (>10K rules) or slow management-to-gateway links. Consider: optimizing rulebase, using policy packages, or increasing timeout.

## SPL

```spl
index=checkpoint sourcetype="cp_log" earliest=-30d
| where match(lower(product),"(?i)smartconsole|smartcenter|management") AND match(lower(operation),"(?i)install|publish|verify")
| stats count earliest(_time) as first latest(_time) as last values(operation) as ops by administrator, target_gateway
| sort -last
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  by All_Changes.user All_Changes.object All_Changes.action span=1h
| sort -count
```

## Visualization

Table (recent policy installs), Timeline (publish/install events), Bar chart (installs by admin), Single value (failed installs this week).

## Known False Positives

Planned install windows, many admins, and repeated templates can make install and publish events look excessive.

## References

- [Check Point App for Splunk](https://splunkbase.splunk.com/app/4293)
- [CIM: Change](https://docs.splunk.com/Documentation/CIM/latest/User/Change)
- [CCX Add-on for Checkpoint Smart-1 Cloud](https://splunkbase.splunk.com/app/7259)
- [Splunkbase app 5402](https://splunkbase.splunk.com/app/5402)
