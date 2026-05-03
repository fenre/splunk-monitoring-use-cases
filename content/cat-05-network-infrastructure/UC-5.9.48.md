<!-- AUTO-GENERATED from UC-5.9.48.json — DO NOT EDIT -->

---
id: "5.9.48"
title: "ThousandEyes Activity Log Audit Trail"
status: "verified"
criticality: "medium"
splunkPillar: "Security"
---

# UC-5.9.48 · ThousandEyes Activity Log Audit Trail

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Security &middot; **Type:** Compliance &middot; **Wave:** Walk &middot; **Status:** Verified

*We keep a diary of who changed what in our network monitoring system, so if a test suddenly disappears or an alert stops working, we know who did it and when.*

---

## Description

Captures administrative changes to the ThousandEyes account — test modifications, alert rule changes, user management, and agent configuration — providing an audit trail for compliance and change management. Detects unauthorized or unexpected configuration changes that could affect monitoring coverage.

## Value

A deleted test means a monitoring blind spot. A modified alert threshold means a changed detection sensitivity. A new user account could be unauthorized access. Without auditing ThousandEyes administrative activity, these changes happen silently. This UC provides the same change-management visibility for ThousandEyes that organizations already have for their other infrastructure — ensuring that monitoring configuration changes are tracked, reviewed, and reversible.

## Implementation

Activity log events flow through the same Event input as Internet Insights events (UC-5.9.18). Filter by event type to isolate administrative activities.

## Detailed Implementation

### Prerequisites
- All prerequisites from UC-5.9.18 apply — Event API input configured and polling ThousandEyes for event data.
- **Activity Log API access.** The ThousandEyes user account associated with the Splunk app's OAuth token must have permissions to read activity logs. In ThousandEyes: **Account Settings → Users and Roles** — the account needs at least "Regular User" role with API access. "Organization Admin" or "Account Admin" can see all activity logs across the organization.
  - The ThousandEyes Activity Log API (v7) endpoint is `https://api.thousandeyes.com/v7/audit-user-events`. The `ta_cisco_thousandeyes` Event input polls this alongside other event types.
- **Understand what ThousandEyes logs.** The Activity Log captures administrative changes to the ThousandEyes platform, NOT test results. Common logged actions:
  - **Test changes:** Created, modified, deleted, enabled, disabled.
  - **Agent changes:** Agent added, removed, cluster modified.
  - **Alert rule changes:** Rule created, modified, deleted, enabled, disabled.
  - **User changes:** User added, removed, role changed, API token generated.
  - **Account changes:** Account group modified, usage limits changed.
  - **Label/tag changes:** Labels created, modified, deleted, assignments changed.
- **Retention.** ThousandEyes retains activity logs for 90 days via API. Ingesting into Splunk provides longer retention and cross-correlation with other security and audit data.
- **Splunk role:** `srchIndexesAllowed` must include `thousandeyes_events`.

### Step 1 — Configure data collection
Activity log events flow through the Event API input configured in UC-5.9.18. The `ta_cisco_thousandeyes` polls the ThousandEyes Activity Log API at the configured interval (default: 5 minutes).

Verify activity log data is being ingested:
```spl
index=thousandeyes_events sourcetype="cisco:thousandeyes:event" earliest=-30d
| search event_type="*activity*" OR event_type="*audit*" OR type="*Activity*" OR type="*Audit*" OR aid_type="*activity*"
| stats count by event_type, type
| sort -count
```
Note: Field names depend on the `ta_cisco_thousandeyes` version and the ThousandEyes API version. If the above returns 0 results, discover the available fields:
```spl
index=thousandeyes_events sourcetype="cisco:thousandeyes:event" earliest=-30d
| head 100
| fieldsummary
| where count > 10
| table field, count, distinct_count, values
```
Look for fields containing "user", "action", "resource", "event_type", or "type" to identify activity log events.

**Key fields to identify (version-dependent):**
- `user` or `actor` or `created_by` — who made the change.
- `action` or `event_type` or `type` — what type of change (create, update, delete).
- `resource_type` or `object_type` — what was changed (test, alert rule, agent, user).
- `resource_name` or `object_name` — the name of the changed resource.
- `_time` — when the change occurred.

### Step 2 — Create the search and alert
**Activity log summary (daily review):**
```spl
`event_index` (type="Activity Log" OR type="Audit" OR event_type="*activity*" OR event_type="*audit*") earliest=-24h
| stats count by user, action, resource_type
| sort -count
```

**Understanding this SPL**

The broad filter `(type="Activity Log" OR type="Audit" OR event_type=...)` accounts for different field names across app versions. Once you identify the exact field names in your deployment (from the `fieldsummary` query above), narrow the filter.

`stats count by user, action, resource_type` — summarizes who did what to what kind of resource. One row per user-action-resource_type combination. High counts for "delete" actions warrant investigation.

**After-hours activity detection (security audit):**
```spl
`event_index` (type="Activity Log" OR type="Audit" OR event_type="*activity*") earliest=-24h
| eval hour=tonumber(strftime(_time, "%H")), day_of_week=strftime(_time, "%A")
| where hour < 7 OR hour > 19 OR day_of_week="Saturday" OR day_of_week="Sunday"
| table _time, user, action, resource_type, resource_name, day_of_week
| sort -_time
```
This flags any ThousandEyes administrative changes made outside business hours (7 AM – 7 PM) or on weekends. After-hours changes may indicate: (a) legitimate maintenance, (b) a compromised account, or (c) an unauthorized change that someone hoped would go unnoticed.

**Test deletion tracking (critical for monitoring coverage):**
```spl
`event_index` (type="Activity Log" OR type="Audit" OR event_type="*activity*") action="delete" resource_type="test" earliest=-7d
| table _time, user, resource_name
| sort -_time
```
Deleted tests create monitoring blind spots. If a production test is deleted (accidentally or deliberately), you lose visibility into that application/path until the test is recreated. This search surfaces all test deletions so they can be reviewed.

**Alert rule modification tracking:**
```spl
`event_index` (type="Activity Log" OR type="Audit" OR event_type="*activity*") resource_type="alertRule" earliest=-7d
| table _time, user, action, resource_name
| sort -_time
```
Alert rule changes can silently disable alerting. If someone raises a threshold too high or disables a rule, you may stop receiving critical notifications without realizing it.

**User activity volume (detect unusual patterns):**
```spl
`event_index` (type="Activity Log" OR type="Audit" OR event_type="*activity*") earliest=-30d
| timechart span=1d count by user
```
A user making 50+ changes in a day may be performing bulk cleanup, automation, or something that warrants review.

**Change summary by resource type (weekly review):**
```spl
`event_index` (type="Activity Log" OR type="Audit" OR event_type="*activity*") earliest=-7d
| stats count as changes dc(user) as users values(action) as actions by resource_type
| sort -changes
```

**Scheduling:** 
- Daily review: cron `0 8 * * 1-5` (weekday mornings), time range `-24h to now`.
- Test deletion alert: cron `*/30 * * * *`, time range `-35m to now`. Alert immediately on any test deletion. Throttle by `resource_name` for 24 hours (a deleted test won't be deleted twice).
- After-hours alert: cron `0 7 * * *` (each morning), time range `-12h to now` (covers overnight). Alert if any events found.

### Step 3 — Validate
(a) **Make a test change.** In the ThousandEyes UI, make a small change: rename a non-production test (e.g., append "_test" to the name). Wait for the next Event API polling cycle (5–15 minutes). Verify the change appears in Splunk:
```spl
index=thousandeyes_events sourcetype="cisco:thousandeyes:event" earliest=-1h
| search resource_name="*test*" OR resource_name="*_test*"
| table _time, user, action, resource_type, resource_name
```
If it appears, the activity log pipeline is working. Revert the test name change.

(b) **Verify user attribution.** Confirm the `user` field shows the actual email/username of the person who made the change, not a service account or generic name.

(c) **Check field names.** The exact field names may differ by app version. Use `| fieldsummary` to discover available fields if the default queries return 0 results. Adjust all SPL in this UC to match your actual field names.

(d) **Coverage check.** Make changes to different resource types (test, alert rule, agent label) and verify each appears. Some resource types may not be logged by the API.

(e) **Time zone alignment.** Verify `_time` on activity log events aligns with the actual change time in the ThousandEyes UI. The Event API returns timestamps in UTC; Splunk converts based on the sourcetype configuration.

### Step 4 — Operationalize
**Dashboard** ("ThousandEyes Configuration Audit" — designed for ThousandEyes administrators and security/compliance):
- Row 1 — Daily activity summary: total changes today, total unique users, changes by type (bar chart). Quick daily health check.
- Row 2 — Recent changes table: last 50 changes with timestamp, user, action, resource type, resource name. Sortable and filterable.
- Row 3 — Activity timeline: timechart of changes over 30 days. Reveals patterns (maintenance windows, bulk changes, unusual spikes).
- Row 4 — Audit flags: after-hours changes, test deletions, alert rule modifications. Red indicators for items requiring review.

**Alerting:**
- **Test deleted** → immediate medium-urgency notification to ThousandEyes admin channel. Include: who, what test, when. This creates a monitoring gap that must be reviewed.
- **Alert rule deleted or disabled** → immediate medium-urgency notification. Include: who, what rule, when. This may silently break alerting.
- **After-hours configuration change** → low-urgency next-morning notification. Include: summary of all overnight changes.
- **Bulk changes (> 20 actions in 1 hour by a single user)** → informational notification. May indicate automation run, bulk cleanup, or unauthorized mass modification.

**Runbook** (owner: ThousandEyes admin / security):
1. **Test deleted (unexpected).** (a) Contact the user who deleted it — was it intentional? (b) If accidental, recreate the test from the ThousandEyes UI or API. (c) If intentional, verify that monitoring coverage is maintained — another test may cover the same target.
2. **Alert rule modified.** (a) Review the change — was the threshold raised inappropriately? (b) If a rule was disabled, understand why. If for maintenance, set a reminder to re-enable.
3. **After-hours activity.** (a) Verify the user is legitimate and the change was authorized. (b) If the user's account may be compromised, initiate account security review (password reset, session revocation).
4. **Unknown user making changes.** (a) Verify the user is a current employee with ThousandEyes access. (b) If the user is a former employee or unknown, revoke access immediately and audit all their recent changes.

### Step 5 — Troubleshooting

- **No activity log data in Splunk** — The Event API input may not be polling activity log events. Check the `ta_cisco_thousandeyes` Event input configuration — ensure it includes activity/audit events. Some versions require a separate input for activity logs vs. test events. Also verify the OAuth token's permissions include activity log access.

- **Field names don't match the SPL** — Different versions of the app and the ThousandEyes API use different field names. Run `| fieldsummary` on a sample to discover the actual field names in your deployment, then adjust the SPL accordingly.

- **Activity log events missing some changes** — Not all ThousandEyes actions are logged via the API. Some UI-only changes may not appear. Check ThousandEyes documentation for which actions are included in the Activity Log API.

- **Time zone confusion** — Activity log events from the ThousandEyes API are in UTC. If your Splunk instance is in a different timezone, the after-hours detection logic needs adjustment. Use `| eval hour=tonumber(strftime(_time, "%H"))` with Splunk's timezone-aware `_time` field.

- **All common troubleshooting** — See UC-5.9.18 Step 5 for Event API issues, and UC-5.9.1 Step 5 for general app troubleshooting.

## SPL

```spl
`event_index` type="Activity Log" OR type="Audit"
| stats count by user, action, resource_type
| sort -count
```

## Visualization

(1) Table: recent administrative activities with user, action, resource, timestamp. (2) Bar chart: activity volume by user (identifies most active administrators). (3) Timechart: activity volume trending. (4) Alert: unexpected activity outside business hours.

## Known False Positives

**Automated configuration changes.** If ThousandEyes is managed via API (Terraform, Ansible, or scripts), automated changes generate activity log entries. Tag automated users/service accounts to distinguish from manual changes.

**ThousandEyes support access.** Cisco/ThousandEyes support engineers may access the account during support tickets. Verify with open support tickets.

**Bulk operations.** Renaming tests, updating alert rules across many tests, or deploying new agents generates many activity log entries. Correlate with planned change tickets.

## References

- [Cisco ThousandEyes App for Splunk (Splunkbase 7719)](https://splunkbase.splunk.com/app/7719)
- [ThousandEyes Activity Log](https://docs.thousandeyes.com/product-documentation/user-management/activity-log)
