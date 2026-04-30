<!-- AUTO-GENERATED from UC-5.13.65.json — DO NOT EDIT -->

---
id: "5.13.65"
title: "Critical Event Notification Alerting (Severity 1-2)"
status: "verified"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.13.65 · Critical Event Notification Alerting (Severity 1-2)

> **Criticality:** Critical &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Availability, Fault &middot; **Wave:** Walk &middot; **Status:** Verified

*We set up the fastest possible alarm for the most serious network problems — using real-time notifications that arrive within seconds, not the regular 15-minute checks. When a core switch goes down, every second of delay before your team knows about it means more people without network access.*

---

## Description

Fires an alert on Catalyst Center event notifications with severity 1 (critical) or 2 (high) — the real-time webhook events that represent the fastest detection path for major network events like device unreachability, link failures, and security incidents, with sub-minute latency compared to the 15-minute polling of UC-5.13.3 and UC-5.13.23.

## Value

The TA's modular inputs poll every 15 minutes. Event notifications arrive in real-time via webhook. For P1 incidents (core switch down, WLC failure, major link loss), the difference between 15-minute detection and sub-minute detection is the difference between users experiencing a brief blip and users experiencing a 15-minute outage before anyone even knows. This UC is the fastest alert path in the entire Catalyst Center UC family — it should be the primary paging mechanism for critical infrastructure events.

## Implementation

Requires the HEC + webhook + Event Notification pipeline from UC-5.13.64. **Sourcetype:** `cisco:dnac:event:notification`. **HEC URL:** `https://<host>:8088/services/collector/event` with `Authorization: Splunk <HEC-token>`. In Catalyst Center, ensure subscriptions include severity 1 and 2 for Network, System, and Security (and others as your policy requires). If `eventSeverity` is delivered as a string, normalize in props or add `| eval eventSeverity=tonumber(eventSeverity)` before filtering. For alerting in Splunk: save this search with `eventSeverity=1` as highest priority, route to on-call, and add SMS/email. Optional: add `lookup` for eventType to a runbook table.

## Detailed Implementation

### Prerequisites
- UC-5.13.64 complete: HEC token, webhook destination, and at least one active Event Notification subscription to Splunk with `sourcetype=cisco:dnac:event:notification` and `index=catalyst`.
- Verify severity 1-2 events exist in your data: `index=catalyst sourcetype="cisco:dnac:event:notification" (eventSeverity=1 OR eventSeverity=2) earliest=-7d | stats count`. If zero, subscribe to additional event categories in Catalyst Center.
- Alert action configured: email relay, Slack webhook, PagerDuty/Splunk On-Call integration, or ITSM ticket creation.

### Step 1 — Confirm field typing and subscription coverage
Run `| fieldsummary eventSeverity` to determine whether the field is numeric or string. Catalyst Center versions differ — some send `eventSeverity` as integer, others as string "1". Use `(eventSeverity=1 OR eventSeverity=2 OR eventSeverity="1" OR eventSeverity="2")` to cover both.

Subscription scope: Severity 1-2 events include network device unreachable, AP down, controller failover, critical security events, and license violations. Ensure the webhook subscription includes all categories: **Network**, **System**, **Security**, and **Config** at minimum.

Event notification delivery path: Catalyst Center → Webhook → Splunk HEC → `index=catalyst`. Real-time delivery — no TA poll delay. Events arrive within seconds of detection.

Key fields for critical alerting:
- `eventSeverity`: 1 (most critical) or 2 (high).
- `eventType`: specific event identifier (e.g., "NETWORK-DEVICES-UNREACHABLE").
- `eventCategory`: event classification (NETWORK, SYSTEM, SECURITY).
- `description`: human-readable event detail.
- `instanceId`: unique event ID for deduplication.

### Step 2 — Create the search and alert

```spl
index=catalyst sourcetype="cisco:dnac:event:notification" (eventSeverity=1 OR eventSeverity=2)
| stats count as event_count values(eventCategory) as categories latest(description) as last_description by eventType, eventSeverity
| sort eventSeverity -event_count
```

#### Understanding this SPL:
- **`(eventSeverity=1 OR eventSeverity=2)`**: Filters to only the most severe events. Severity 1 typically indicates a critical outage or security breach; severity 2 indicates a high-priority issue requiring immediate attention.
- **`stats ... by eventType, eventSeverity`**: Groups events by type and severity, providing a count and the latest description for each. This helps operators quickly identify the most active critical event types.
- **`values(eventCategory)`**: Shows which categories each critical event type belongs to, useful for routing to the correct team (network ops, security, etc.).

For real-time alerting, save as a **real-time alert** with: trigger on `count > 0` for severity 1, or `count >= 3` for severity 2 within a 5-minute window. Throttle per `eventType` for 15 minutes to avoid alert storms during widespread outages.

### Step 3 — Validate
- **Trigger a test event:** In Catalyst Center, navigate to a managed device and put it into maintenance mode, then remove it. This should generate a severity 1-2 event notification. Verify it appears in Splunk within 30 seconds.
- **UI comparison:** In Catalyst Center > System > Issues & Settings > notifications, filter by severity 1-2. Compare event types and counts with the Splunk results for the same time window.
- **Latency check:** Compare `timestamp` (Catalyst Center detection time) with `_time` (Splunk indexing time). End-to-end latency should be <30 seconds for real-time alerting effectiveness.
- **Vendor UI parity:** cross-reference the Splunk results with the corresponding **Catalyst Center > Assurance** page for the same time window to confirm counts and values match.
### Step 4 — Operationalize
- **Alert configuration:** Save as scheduled search running every 5 minutes over the last 10 minutes. Trigger when `count > 0`. Route severity 1 to PagerDuty/on-call; route severity 2 to email + Slack.
- **Throttling:** Throttle per `eventType + deviceName` (if available) for 30 minutes to avoid repeated pages for the same issue. During widespread outages, many severity 1-2 events may fire simultaneously — consider grouping by `eventCategory` in the throttle.
- **Correlation:** Compare event notification latency with TA poll-based detection (UC-5.13.1 / issues). Event notifications typically arrive 5-15 minutes before the TA detects the same issue via polling, making them the preferred source for real-time alerting.
- **SOAR integration:** Route severity 1 events to Splunk SOAR for automated enrichment and playbook execution (see UC-5.13.76).

### Step 5 — Troubleshoot
- **Severity 1-2 events not arriving:** Check the webhook subscription in Catalyst Center — ensure severity 1-2 event types are included. Some event types (e.g., maintenance notifications, license warnings) may be classified as severity 1-2 by Catalyst Center but are informational in nature.
- **Too many false alarms:** Review the `eventType` values triggering alerts. Some severity 1-2 types (certificate expiration, version update available) are informational. Build a `catalyst_event_exceptions` lookup to suppress non-operational severity 1-2 types.
- **Duplicate alerts from webhook retries:** If Splunk HEC responds slowly (>30s), Catalyst Center may retry, creating duplicate events. Add `| dedup instanceId` before the stats command.
- **Alert never fires despite severity 1-2 events in the data:** Check the alert's time range — it must cover the search window (e.g., `-10m to now`). Also verify that the alert action is configured correctly in Splunk's Settings > Alert Actions.
- **No event notification events arriving:** verify the HEC token is enabled and the webhook destination is configured in Catalyst Center; check for endpoint timeout or API error in Splunk HEC logs.

Additional operational context for Critical Event Notification Alerting (Severity 1-2):

For month-over-month comparison:
- Export the primary search results monthly as CSV to a `catalyst_monthly_snapshots` directory. Compare current month vs previous month to identify trends, improvements, and regressions.
- Track the key metric from this UC over 90 days with `| timechart span=1w` for the quarterly operations review.

For SLA alignment:
- Define the acceptable threshold for this UC's primary metric in your SLA documentation.
- Schedule a weekly check against the SLA target. Breaches should generate tickets in your ITSM with a link to this UC's dashboard panel for investigation context.

Cross-reference with related UCs:
- When this UC flags an issue, always cross-reference with UC-5.13.1 (Device Health) and UC-5.13.16 (Network Health) to assess the broader impact.
- For compliance-related findings, connect to UC-5.13.28-33 for the compliance posture context.
- For security-related findings, connect to UC-5.13.34-39 for PSIRT advisory exposure.

Runbook integration:
- Document the response procedure for each alert from this UC in your operations runbook.
- Include: who to contact, what to check first, typical root causes, and escalation criteria.
- Review and update the runbook quarterly based on actual alert outcomes (was the runbook helpful? did it miss common scenarios?).

Additional troubleshooting:
- If the search returns unexpected results, check `| fieldsummary` on the base data to verify field names and types match the SPL.
- If data is not arriving for the expected sourcetype, verify the TA input is enabled and check `index=_internal sourcetype=splunkd component=ExecProcessor "TA_cisco_catalyst"` for errors from the modular input.
- If field values changed after a Catalyst Center upgrade, compare `| fieldsummary` from before and after the upgrade to identify renamed or restructured fields.
- If the search is slow, narrow the time range to `earliest=-20m` for a real-time snapshot, or use summary indexing for historical analysis.
- For vendor UI parity, cross-reference the Splunk results with the corresponding **Catalyst Center > Assurance** page for the same time window to confirm counts and values match.


## SPL

```spl
index=catalyst sourcetype="cisco:dnac:event:notification" (eventSeverity=1 OR eventSeverity=2) | stats count as event_count values(eventCategory) as categories latest(description) as last_description by eventType, eventSeverity | sort eventSeverity -event_count
```

## Visualization

Table (eventType, eventSeverity, event_count, last_description), time chart of S1/S2 over time, single value of open critical notifications.

## Known False Positives

**Catalyst Center emitting severity 1-2 for a platform maintenance notification.** Some Catalyst Center versions classify certain platform events (certificate expiration, license warning, major version update available) as severity 1 or 2 even though they are informational rather than operational emergencies. Distinguish by checking the `eventType` — platform maintenance events have specific type identifiers that differ from network outage events. Suppress by maintaining a `catalyst_event_exceptions` lookup with event types that should not trigger critical alerting.

**Severity 1-2 event for a device in a scheduled maintenance window.** A device undergoing planned maintenance may trigger severity 1-2 event notifications (device unreachable, link down). Distinguish by correlating with ITSM change records or a `catalyst_maintenance_windows` lookup. Suppress by filtering events for devices within approved maintenance windows.

**Duplicate severity 1-2 events from webhook retries.** If Splunk HEC acknowledges slowly, Catalyst Center may retry the webhook, delivering duplicate critical events that could trigger multiple alert actions. Distinguish by checking for duplicate events: `| stats count by eventType, timestamp, instanceId | where count>1`. Suppress by deduplicating on `instanceId` before alerting.

**Event notification severity mapping different from Assurance issue priority.** The same underlying network event may appear as a P1 issue in Assurance and a severity-2 event notification, or vice versa. Distinguish by comparing the `severity` in the event notification with the `priority` in the corresponding issue. No suppression needed — be aware of the mapping difference when building correlation rules.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
- [Catalyst Center Event Management API — Cisco DevNet](https://developer.cisco.com/docs/catalyst-center/#!get-notifications)
