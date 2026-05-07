<!-- AUTO-GENERATED from UC-5.13.47.json — DO NOT EDIT -->

---
id: "5.13.47"
title: "Privileged User Activity Monitoring"
status: "verified"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.13.47 · Privileged User Activity Monitoring

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Security &middot; **Type:** Security, Audit &middot; **Wave:** Walk &middot; **Status:** Verified

*We watch what administrators do on the network management system, especially those with the highest access levels. If someone with admin powers starts making unusual changes — like 50 modifications at 2 AM — we flag it so your security team can check whether it is legitimate or if the account has been compromised.*

---

## Description

Monitors administrative activity by privileged users on the Catalyst Center platform, tracking the volume and type of actions per user to detect privilege abuse, compromised accounts, or policy violations — the detective control for NIST AC-6 (Least Privilege) that catches misuse of powerful network management accounts.

## Value

Privileged accounts have the power to modify network configurations, disable security features, and access sensitive data. A SUPER-ADMIN making 50 configuration changes at 2 AM without a change ticket is either an emergency response (legitimate) or a compromised account (critical incident). This UC provides the visibility to distinguish between them by showing each user's total activity, state-changing operations, and active time window. For NIST AC-6, it demonstrates that privileged account usage is monitored and reviewed. For security operations, it's the baseline that makes anomalous behaviour detectable.

## Implementation

Same `audit_logs` input as UC-5.13.45. Focus on human-initiated activity (`isSystemEvent=false`). Maintain a `catalyst_admins` lookup of authorised users. Schedule daily for security review. Alert on unknown usernames immediately.

## Detailed Implementation

### Prerequisites
- UC-5.13.45 (Audit Log Overview) must be operational — same `audit_logs` data feed.
- Maintain a `catalyst_admins` lookup (CSV: `auditUserName, role, team, is_authorized`) for known-user verification. Update when team members join or leave.
- For NIST AC-6 compliance, document the expected set of privileged users and their roles. This UC provides the detective evidence that those users are the only ones exercising privilege.

### Step 1 — Configure data collection
Same `audit_logs` input as UC-5.13.45. No additional configuration.

### Step 2 — Create the search and report
```spl
index=catalyst sourcetype="cisco:dnac:audit:logs" isSystemEvent=false
| stats count as total_actions count(eval(auditRequestType IN ("PUT","POST","DELETE"))) as changes earliest(_time) as first_action latest(_time) as last_action by auditUserName
| eval active_hours=round((last_action-first_action)/3600,1)
| sort -changes
```

Why `isSystemEvent=false`: focuses on human-initiated actions, excluding automated Catalyst Center background operations.

Why track `total_actions` vs `changes`: total_actions includes browsing (GETs). `changes` counts only state-modifying operations. A user with 100 total_actions but 0 changes was just browsing — not concerning. A user with 50 changes in 2 hours warrants investigation.

Why `active_hours`: shows the time span of the user's activity. Activity compressed into a 30-minute window suggests a focused task. Activity spanning 12 hours suggests either a long shift or a persistent session.

For unknown-user detection:
```spl
index=catalyst sourcetype="cisco:dnac:audit:logs" isSystemEvent=false earliest=-24h
| stats dc(auditRequestType) as action_types count as actions by auditUserName
| lookup catalyst_admins auditUserName OUTPUT is_authorized, role
| where isnull(is_authorized)
| table auditUserName, actions, action_types
```

For per-user activity heatmap:
```spl
index=catalyst sourcetype="cisco:dnac:audit:logs" isSystemEvent=false earliest=-7d
| eval hour=strftime(_time, "%H")
| eval day=strftime(_time, "%A")
| stats count by auditUserName, day, hour
| xyseries day, hour, count
```

Schedule: daily (cron `0 7 * * *`). Unknown-user search: real-time alert.

### Step 3 — Validate
(a) Verify your own username appears with the correct action count for today.
(b) Cross-reference with **Catalyst Center > System > Audit Logs** filtered by user.
(c) Check the `catalyst_admins` lookup catches all known usernames. Run the unknown-user search — it should return 0 rows.
(d) Vendor UI parity: compare per-user activity counts with the Catalyst Center audit log view.

### Step 4 — Operationalize
- Daily security review: check for unusual user activity volumes and unknown usernames.
- Monthly access review: compare active users against the `catalyst_admins` lookup. Remove users who haven't logged in for 90 days (NIST AC-6).
- Alert: unknown username → immediate security investigation.
- SOX evidence: monthly privileged-activity report with reviewer attestation.

Runbook (owner: Security Operations):
1. Review the daily per-user activity summary.
2. For unknown usernames: investigate immediately — new admin (update lookup), shared account (fix), or compromised credential (incident response).
3. For unusual activity volumes (> 50 changes/day): verify against approved work (change tickets, scheduled maintenance).
4. For activity outside business hours: cross-reference with UC-5.13.49.
5. For failed login attempts: cross-reference with UC-5.13.48.
6. Monthly: review the full user list against HR records. Disable accounts for departed employees.

### Step 5 — Troubleshooting

- **Service account appears with high action count** — the TA's polling generates GET events. Filter it out or track it separately.

- **Unknown username appears** — investigate immediately. May be a new admin (update the lookup), a shared account (policy violation), or a compromised credential (security incident).

- **No user events** — all events are `isSystemEvent=true`. Check if the audit log API is returning user-initiated events for your service account scope.

- **Same user appears with different name formats** — normalise with `| eval auditUserName=lower(auditUserName)`.

- **Activity heatmap shows unexpected overnight patterns** — investigate with UC-5.13.49 (After-Hours Activity).

- **High GET count from unknown IPs** — possible API reconnaissance. Correlate with network firewall logs.

- **Lookup is stale** — update `catalyst_admins` when team members change. Schedule a monthly review.

- **Want to track specific sensitive operations** — filter `auditDescription` for keywords: `credential`, `certificate`, `user`, `role`, `password`, `template`, `policy`.

For sensitive-operation detection (operations that shouldn't be done by all admins):
```spl
index=catalyst sourcetype="cisco:dnac:audit:logs" isSystemEvent=false auditRequestType IN ("PUT","POST","DELETE")
| eval is_sensitive=if(match(auditDescription, "(?i)credential|certificate|user|role|password|template|policy|radius|tacacs"), 1, 0)
| where is_sensitive=1
| table _time, auditUserName, auditRequestType, auditDescription
| sort -_time
```
Sensitive operations (credential changes, user role modifications, certificate updates, policy changes) should be performed by a restricted set of administrators. This search isolates them for elevated review.

For user activity profiling (establish behavioral baselines per user):
```spl
index=catalyst sourcetype="cisco:dnac:audit:logs" isSystemEvent=false earliest=-30d
| stats count as total count(eval(auditRequestType IN ("PUT","POST","DELETE"))) as changes dc(date_wday) as active_days earliest(_time) as first_seen latest(_time) as last_seen by auditUserName
| eval daily_avg=round(total/active_days,1)
| eval changes_pct=round(changes*100/total,1)
| sort -changes
```
This profile shows each user's activity pattern — how many actions per day, what percentage are state-changing, and how many days they were active. Users with suddenly elevated activity (3× their baseline) warrant investigation.

For new-user detection (first-time admin activity):
```spl
index=catalyst sourcetype="cisco:dnac:audit:logs" isSystemEvent=false earliest=-7d
| stats earliest(_time) as first_action count as actions by auditUserName
| where first_action > relative_time(now(), "-7d")
| lookup catalyst_admins auditUserName OUTPUT is_authorized
| eval classification=if(isnotnull(is_authorized), "New authorized user", "UNKNOWN USER — investigate")
| table auditUserName, first_action, actions, classification
```

Runbook expansion:
1. Daily: review user activity summary. Flag unknown usernames.
2. Weekly: review sensitive-operation log. Each sensitive action should have a documented business justification.
3. Monthly: update the `catalyst_admins` lookup. Remove departed employees. Add new admins.
4. Quarterly: conduct a formal access review (NIST AC-6). Compare active users against the approved admin list. Disable unused accounts.
5. For anomalous activity: contact the user directly. Was this them? If not, initiate credential compromise investigation.

Troubleshooting expansion:
- **Same user appears with different name formats** — normalise: `| eval auditUserName=lower(auditUserName)`. Catalyst Center may log `user@domain.com` vs `DOMAIN\user` depending on the auth source.
- **Service account generates excessive GET events** — the TA's polling creates audit events. Filter with `| where auditUserName != "<ta-service-account>"` or maintain a `service_accounts` lookup.
- **Sensitive-operation regex too broad** — the `match()` pattern may flag operations that aren't truly sensitive (e.g., 'updated template description' matches 'template'). Refine the regex based on your review of flagged operations.
- **Want to integrate with UEBA** — export user activity profiles to Splunk UBA for behavioral anomaly detection across all platforms, not just Catalyst Center.


## SPL

```spl
index=catalyst sourcetype="cisco:dnac:audit:logs" isSystemEvent=false
| stats count as total_actions count(eval(auditRequestType IN ("PUT","POST","DELETE"))) as changes earliest(_time) as first_action latest(_time) as last_action by auditUserName
| eval active_hours=round((last_action-first_action)/3600,1)
| sort -changes
```

## Visualization

(1) Table: auditUserName, total_actions, changes, active_hours — sorted by changes. (2) Bar chart: changes per user. (3) Heatmap: per-user activity by hour-of-day and day-of-week for pattern analysis. (4) Alert: unknown username detected (not in `catalyst_admins` lookup).

## Known False Positives

**TA service account generating high activity volume.** The TA's own API polling generates GET events. The service account may appear as the top user by `total_actions`. Distinguish by checking `auditUserName` — the TA account should be known. Suppress by filtering `| where auditUserName != "splunk-svc@example.com"` for human-only views, or by focusing on `changes` (PUT/POST/DELETE) rather than `total_actions`.

**Bulk operations inflating per-user change count.** A legitimate template push to 100 devices by one admin generates 100+ change events. Distinguish by checking whether the high count corresponds to a single approved operation (same `auditParentId`). Document as one approved bulk change.

**Shared accounts masking individual accountability.** If multiple administrators share a single Catalyst Center account (bad practice but common), individual activity is not attributable. Distinguish by correlating with ISE/RADIUS logs for the actual login source. Fix by creating individual accounts per the NIST AC-6 least-privilege principle.

**Service accounts for ITSM integration generating automated changes.** ServiceNow or other ITSM platforms may use API accounts to push approved changes. Distinguish by checking the `auditUserName` against a list of known service/integration accounts. Present these separately from human-initiated activity.

## References

- [Cisco Catalyst Add-on for Splunk (Splunkbase 7538)](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center Audit Log API](https://developer.cisco.com/docs/catalyst-center/#!get-audit-log-records)
- [Catalyst Center Integration Guide (this repo)](../../docs/guides/catalyst-center.md)
- [NIST SP 800-53 Rev. 5 — AC-6 Least Privilege](https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=AC-6)
