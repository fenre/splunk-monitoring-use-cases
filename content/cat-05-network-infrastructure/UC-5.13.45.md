<!-- AUTO-GENERATED from UC-5.13.45.json — DO NOT EDIT -->

---
id: "5.13.45"
title: "Audit Log Activity Overview"
status: "verified"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.13.45 · Audit Log Activity Overview

> **Criticality:** High &middot; **Difficulty:** Beginner &middot; **Pillar:** Security &middot; **Type:** Audit, Operational &middot; **Wave:** Crawl &middot; **Status:** Verified

*We keep a complete record of everything administrators do on the network management system — every change, every login, every action — so when something goes wrong, you can look up exactly what happened, who did it, and when. This record is also what auditors ask for to prove your team follows proper procedures.*

---

## Description

Provides a complete overview of all administrative activity on the Catalyst Center platform — every configuration change, policy update, device provisioning action, and system event — giving security and compliance teams full visibility into who did what and when on the network management plane.

## Value

The audit log is the forensic backbone of network security. When a configuration change breaks connectivity at 3 AM, the audit log tells you who logged in, what they changed, and when — turning a 4-hour investigation into a 5-minute lookup. For NIST AU-2 (Event Logging), continuous audit log collection demonstrates that administrative events are captured and available for review. For SOX ITGC, it provides the change management evidence trail that external auditors require. Catalyst Center's own audit log retention is limited; Splunk provides unlimited retention for the multi-year evidence horizon auditors expect.

## Implementation

Install `TA_cisco_catalyst` (Splunkbase 7538). Enable the `audit_logs` input (Inputs → Create → Audit Logs: account `catcenter-prod`, index `catalyst`, interval `300`). **Requires SUPER-ADMIN-ROLE** on the service account. The 5-minute poll interval captures changes quickly. Retain 365+ days for compliance evidence.

## Detailed Implementation

### Prerequisites
- `TA_cisco_catalyst` (Splunkbase 7538) ≥1.0 installed on Search Heads AND the Heavy Forwarder running inputs.
- Service account with **SUPER-ADMIN-ROLE** — audit log access requires elevated privileges beyond NETWORK-ADMIN-ROLE. If the input produces no events, this is the most common cause.
- Network: HTTPS (TCP 443) from Splunk HF to Catalyst Center management IP/FQDN.
- Retain **365+ days** of audit data for compliance evidence. Audit log volume is low (~10–100 events/day × ~500 bytes ≈ 50 KB/day) so storage cost is negligible. NIST AU-11 recommends retention per your organisation's records retention policy — typically 1–3 years. SOX requires audit trail availability for the full assessment period.
- CIM: this sourcetype maps to the **Change** data model. Verify CIM tagging with `| search tag=change sourcetype="cisco:dnac:audit:logs"` after installation.

### Step 1 — Configure data collection
Enable the `audit_logs` input:

| Setting | Value |
|---------|-------|
| Input type | Audit Logs |
| Account | `catcenter-prod` (must have SUPER-ADMIN-ROLE) |
| Index | `catalyst` |
| Interval | `300` (5 minutes — audit events should be captured quickly for security investigations) |

The TA polls `GET /dna/data/api/v1/event/event-series/audit-log`. Each event represents one administrative action on the Catalyst Center platform.

Sample event:
```json
{
  "auditId": "audit-abc123",
  "auditUserName": "netadmin@example.com",
  "auditRequestType": "PUT",
  "auditDescription": "Updated network profile template for Branch-Standard",
  "auditParentId": "parent-xyz789",
  "createdDateTime": 1714060200000,
  "isSystemEvent": false
}
```

Verification:
```spl
index=catalyst sourcetype="cisco:dnac:audit:logs" earliest=-1h
| stats count by auditRequestType
```
You should see rows for GET, PUT, POST, and/or DELETE. If count = 0 after an hour, check the service account role (must be SUPER-ADMIN-ROLE) and `index=_internal sourcetype=splunkd "TA_cisco_catalyst" "403"` for permission errors.

Expected volume: highly variable. A quiet day may produce 10 events; a major change window may produce 500+. Budget license for peak, not average.

### Step 2 — Create the search and report
```spl
index=catalyst sourcetype="cisco:dnac:audit:logs" isSystemEvent=false
| stats count as actions count(eval(auditRequestType IN ("PUT","POST","DELETE"))) as changes by auditUserName
| sort -changes
```

Why `isSystemEvent=false`: excludes automated Catalyst Center background operations (inventory sync, certificate rotation) that generate audit events without human involvement. Keeps the focus on human-initiated actions.

Why separate `actions` from `changes`: `actions` counts all events including GETs (browsing). `changes` counts only state-modifying operations (PUT/POST/DELETE). A user with 100 actions but 0 changes was just browsing — not concerning. A user with 50 changes warrants review.

Why `by auditUserName`: the per-user breakdown is the most operationally useful view. It answers: 'Who made changes today?' and 'Is anyone making an unusual number of modifications?'

For a recent activity timeline (useful for incident investigation):
```spl
index=catalyst sourcetype="cisco:dnac:audit:logs" isSystemEvent=false earliest=-24h
| table _time, auditUserName, auditRequestType, auditDescription
| sort -_time
```

Schedule as Report: daily (cron `0 7 * * *`), output to the Administration dashboard. Monthly PDF export for SOX ITGC log-review evidence.

### Step 3 — Validate
(a) Make a deliberate change in Catalyst Center (e.g., edit a template description). Within 5 minutes, run the timeline search. Your username should appear with `auditRequestType=PUT` and a description matching the change.

(b) Compare the user activity summary with **Catalyst Center > System > Audit Logs** for the same time window. The user list and action counts should approximately match.

(c) Confirm `isSystemEvent` filter works: `| stats count by isSystemEvent`. You should see both `true` (system) and `false` (user) events. The filtered search should show only `false`.

(d) Check CIM tagging: `| head 1 | eval _tag_check=if(searchmatch("tag=change"), "tagged", "MISSING")`. If missing, the TA's knowledge objects are not installed on the Search Head.

(e) Verify `createdDateTime` parsing: `| eval time_check=strftime(createdDateTime/1000, "%Y-%m-%d %H:%M:%S") | table _time, time_check`. The two times should agree — `_time` is set by Splunk ingest, `time_check` is from the API timestamp.

### Step 4 — Operationalize
Dashboard ("Catalyst Center — Administration & Audit"):
- Row 1 — Per-user activity summary table (this UC's search). Drilldown: click a user → show their recent activity timeline.
- Row 2 — Activity timechart by `auditRequestType` over 24h. Spikes correlate with change windows.
- Row 3 — Single values: total admin actions (24h), total changes (24h), unique active users (24h).

Security review (weekly):
1. Check for unknown usernames — `| lookup catalyst_admins auditUserName OUTPUT is_authorized | where isnull(is_authorized)`.
2. Check for unusual activity volumes — users with > 50 changes/day.
3. Check for after-hours activity — UC-5.13.49.
4. Check for failed login attempts — UC-5.13.48.

Compliance evidence (NIST AU-2 / SOX ITGC):
- Archive the daily activity report as PDF/CSV for the audit evidence folder.
- Attach reviewer attestation ('I reviewed the admin activity for the period X–Y and found no unapproved activity') for SOX log-review requirements.

Runbook (owner: Security Operations):
1. Open the daily audit summary. Review the user list and change counts.
2. For each user with state-changing actions: verify the changes correspond to approved work (change tickets, scheduled tasks).
3. For unknown users: investigate immediately — new admin, shared account, or compromised credential?
4. For high-volume users (> 50 changes): verify this corresponds to a bulk operation (template push, firmware campaign), not anomalous behavior.
5. Document findings in the weekly security review notes.

### Step 5 — Troubleshooting

- **No audit events at all** — the most common cause is the service account having NETWORK-ADMIN-ROLE instead of SUPER-ADMIN-ROLE. Audit log access requires SUPER-ADMIN. Check `index=_internal sourcetype=splunkd "TA_cisco_catalyst" "403"` for permission errors.

- **Only system events, no user events** — `isSystemEvent=true` events are Catalyst Center internal operations. If ALL events are `isSystemEvent=true`, the API may not be returning user-initiated activity for your service account scope. Verify the account's platform scope.

- **Very few events (< 5/day)** — normal for a stable deployment with few active administrators. Audit volume correlates with human activity on the platform.

- **TA service account dominates the activity count** — the TA's own API polling generates GET events. Filter with `| where auditUserName != "<ta-service-account>"` for human-only views.

- **`auditDescription` is truncated** — some Catalyst Center versions truncate long descriptions in the API response. Check `| head 1 | spath` for the full field content.

- **CIM Change model shows no data** — the TA's `tags.conf` may not include the `change` tag for audit events. Add `[eventtype=cisco_dnac_audit]
change = enabled` to `$SPLUNK_HOME/etc/apps/TA_cisco_catalyst/local/tags.conf`.

- **Event timestamps don't match expectations** — `createdDateTime` is epoch milliseconds. Verify `_time` is parsed correctly. If `_time` shows ingest time instead of event time, check `props.conf` for the sourcetype's `TIME_FORMAT` setting.

- **Duplicate events** — the TA may re-fetch events that were already ingested. Add `| dedup auditId` if the `auditId` field provides a unique identifier per event.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:audit:logs" isSystemEvent=false
| stats count as actions count(eval(auditRequestType IN ("PUT","POST","DELETE"))) as changes by auditUserName
| sort -changes
```

## Visualization

(1) Table: auditUserName, actions, changes — showing who is most active and who makes the most state-changing operations. (2) Timechart: `| timechart span=1h count by auditRequestType` showing activity patterns over 24h. (3) Single value: total admin actions and total changes in last 24h. (4) Pie: share by auditRequestType (GET vs PUT vs POST vs DELETE).

## Known False Positives

**TA service account generating high GET volume.** The TA's own API polling generates audit events (GET requests every 5 minutes for each enabled input). This inflates the `auditUserName` count for the service account. Distinguish by checking `auditUserName` — the TA's service account should be a known, dedicated API user. Suppress by filtering `| where auditUserName != "splunk-svc@example.com"` for human-activity views, or by using `isSystemEvent=false` to exclude automated operations.

**Automated Catalyst Center background tasks generating system events.** Catalyst Center runs periodic background operations (inventory sync, Assurance processing, certificate rotation) that produce audit events. Distinguish by checking `isSystemEvent=true` — these are system-generated, not human-initiated. Suppress with `isSystemEvent=false` for human-activity dashboards.

**Burst of activity during change windows.** A template push or firmware campaign generates many audit events in a short window, making the timechart spike dramatically. Distinguish by correlating with ITSM change records. Do not suppress — this is legitimate activity, but annotate the chart with the change window for context.

**Multiple usernames for the same person.** Catalyst Center may log the same administrator as `user@domain.com`, `user`, or `USER@DOMAIN.COM` depending on the authentication method. Distinguish by checking for near-duplicate usernames. Suppress by normalising with `| eval auditUserName=lower(auditUserName)`.

## References

- [Cisco Catalyst Add-on for Splunk (Splunkbase 7538)](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center Audit Log API](https://developer.cisco.com/docs/catalyst-center/#!get-audit-log-records)
- [Catalyst Center Integration Guide (this repo)](docs/guides/catalyst-center.md)
- [NIST SP 800-53 Rev. 5 — AU-2 Event Logging](https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=AU-2)
