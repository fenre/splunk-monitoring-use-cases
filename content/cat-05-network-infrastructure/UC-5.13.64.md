<!-- AUTO-GENERATED from UC-5.13.64.json — DO NOT EDIT -->

---
id: "5.13.64"
title: "Event Notification Volume and Type Distribution"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.13.64 · Event Notification Volume and Type Distribution

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Operations &middot; **Wave:** Crawl &middot; **Status:** Verified

*We monitor the real-time alert pipeline from the network management system — making sure that urgent notifications are actually being delivered to us. This is like checking that the fire alarm system is connected and working before you rely on it to warn you of a fire.*

---

## Description

Provides a complete overview of all Catalyst Center Platform event notifications received via webhook, categorised by type (NETWORK, SYSTEM, SECURITY, APP), category, and severity — establishing the baseline event volume and validating that the HEC webhook pipeline is functioning correctly as the foundation for real-time alerting UCs (UC-5.13.65, UC-5.13.66).

## Value

Event notifications are Catalyst Center's real-time alerting channel — sub-minute detection for device unreachability, security events, and system health changes, compared to the 15-minute polling latency of the TA's modular inputs. This UC validates that the webhook pipeline is delivering events and establishes volume baselines so anomalies (spikes or gaps) can be detected. Without this foundational view, the real-time alerting UCs (UC-5.13.65, UC-5.13.66) have no confirmation that data is actually flowing.

## Implementation

Configure Catalyst Center Platform to send event notifications to Splunk via HEC webhook:

1. **Create a Splunk HEC token:**
   - In Splunk, go to Settings → Data Inputs → HTTP Event Collector
   - Create a new token with `sourcetype=cisco:dnac:event:notification` and `index=catalyst`
   - Note the HEC URL and token value

2. **Configure Catalyst Center webhook destination:**
   - Navigate to System → Settings → External Services → Destinations → Webhook
   - Add a new webhook destination:
     - Name: `Splunk-HEC`
     - URL: HTTPS URL of your Splunk HTTP Event Collector host (commonly port 8088) with path `/services/collector/event`
     - Method: POST
     - Headers: `Authorization` using Splunk HEC form: the word Splunk, one space, then the token value from Splunk Data Inputs → HTTP Event Collector
     - Trust certificate: configure as needed for your TLS setup
   - Test the webhook to verify connectivity

3. **Subscribe to event notifications:**
   - Navigate to Platform → Developer Toolkit → Event Notifications
   - For each event type you want to monitor (Network, System, Security, App, Integration):
     - Create a notification rule
     - Select the Splunk-HEC webhook destination
     - Configure severity filters (recommend: all severities for comprehensive monitoring)

4. **Validate in Splunk:**
   - Run: `index=catalyst sourcetype="cisco:dnac:event:notification" | head 10`
   - Verify events arrive with expected fields: `eventType`, `eventCategory`, `eventSeverity`, `description`, `timestamp`

## Detailed Implementation

### Prerequisites
- Cisco Catalyst Center **2.3.5+** with Event Management enabled.
- Splunk HEC endpoint configured on port 8088/tcp (TLS recommended), with a dedicated HEC token scoped to `index=catalyst`.
- Catalyst Center Webhook destination created under **System > Settings > External Services > Destinations > Webhook**, pointing to `https://<splunk-hec>:8088/services/collector/event` with the HEC token in the Authorization header.
- At least one Event Notification subscription active under **System > Settings > External Services > Events > Notifications** — subscribe to the event categories relevant to your operations (Network, System, Security, etc.).
- Verify the first events arrive: `index=catalyst sourcetype="cisco:dnac:event:notification" earliest=-1h | stats count`.

### Step 1 — Configure data collection
Unlike TA-polled sourcetypes, event notifications arrive in real-time via Catalyst Center's webhook mechanism. Catalyst Center pushes JSON payloads to the Splunk HEC endpoint whenever a subscribed event occurs.

**Webhook path:** `POST /services/collector/event` — Catalyst Center formats the payload as a valid HEC JSON object (`{"event":{...}}`).
**Sourcetype assignment:** Configure the HEC token to set `sourcetype=cisco:dnac:event:notification` and `index=catalyst` (or set these in the HEC Global Settings).
**Expected volume:** Varies dramatically by subscription scope. A broad subscription (all categories) in a 1,000-device network may generate 100-500 events/day during normal operations, with spikes of 1,000+ during outages or upgrades.

Key fields:
- `eventType`: string identifying the event category (e.g., "NETWORK-DEVICES-UNREACHABLE", "CONFIG-CHANGE").
- `eventSeverity`: integer 1-5 (1 = most severe). May appear as string in some Catalyst Center versions — validate with `| fieldsummary eventSeverity`.
- `eventCategory`: high-level category (e.g., "NETWORK", "SYSTEM", "SECURITY").
- `description`: human-readable event description.
- `timestamp`: event occurrence time from Catalyst Center (may differ from `_time` if there is webhook delivery delay).
- `instanceId`: unique event instance identifier — critical for deduplication.

### Step 2 — Create the search and alert

```spl
index=catalyst sourcetype="cisco:dnac:event:notification"
| stats count as event_count dc(instanceId) as unique_events values(eventCategory) as categories by eventType, eventSeverity
| sort eventSeverity, -event_count
```

#### Understanding this SPL:
- **`stats count ... dc(instanceId)`**: Counts total events and unique events per type. If `event_count` is significantly higher than `unique_events`, webhook retries are creating duplicates — see the deduplication guidance in Troubleshooting.
- **`values(eventCategory) as categories`**: Shows which categories each event type belongs to, useful for identifying miscategorized events.
- **`sort eventSeverity, -event_count`**: Surfaces the most severe events first, then sorts by volume within each severity level.

For a volume timechart: `| timechart span=1h count by eventCategory` — reveals daily patterns and helps identify volume anomalies.

### Step 3 — Validate
- **UI comparison:** Open Catalyst Center > System > Settings > External Services > Events > Notification list. Compare the event types and counts with the Splunk results for the same time window.
- **Subscription coverage:** In Catalyst Center, navigate to the Notification subscriptions list and verify that all intended event categories are subscribed. Compare the `eventCategory` values in Splunk with the subscription list — missing categories indicate subscription gaps.
- **Delivery check:** Compare `timestamp` (Catalyst Center event time) with `_time` (Splunk indexing time). A consistent delta of >5 minutes indicates webhook delivery delays.
- **Count check:** `| stats dc(instanceId)` in Splunk should approximate the event count shown in Catalyst Center's notification history (within ±5% due to timing).
- **Vendor UI parity:** cross-reference the Splunk results with the corresponding **Catalyst Center > Assurance** page for the same time window to confirm counts and values match.
### Step 4 — Operationalize
- **Dashboard:** Stacked timechart of event volume by category (top panel), severity distribution pie chart (middle), and a table of the most recent 50 events with drill-down to event details (bottom).
- **Baseline:** After 7 days of data, compute `| stats avg(count) as baseline by eventCategory, date_wday, date_hour` to establish time-of-day and day-of-week baselines for anomaly detection.
- **Deduplication:** If webhook retries create duplicates, prepend `| dedup instanceId` to all event notification SPL.

### Step 5 — Troubleshoot
- **No events arriving:** Check Catalyst Center webhook destination health under System > Settings > External Services > Destinations. Verify the HEC endpoint URL, port, TLS certificate, and token. Test with `curl -k https://<splunk-hec>:8088/services/collector/event -H "Authorization: Splunk <token>" -d '{"event":"test"}'`.
- **Events arriving with wrong sourcetype:** Verify the HEC token configuration sets `sourcetype=cisco:dnac:event:notification` explicitly, not relying on Catalyst Center to set it.
- **`eventSeverity` field type mismatch:** Run `| fieldsummary eventSeverity` — if the field appears as both integer and string, use `| eval eventSeverity=tonumber(eventSeverity)` to normalize.
- **Volume spike during upgrade:** Catalyst Center may replay pending notifications after a restart. This is expected and transient — filter by `| where _time > relative_time(now(), "-30m@m")` to focus on recent events only.
- **No event notification events arriving:** verify the HEC token is enabled and the webhook destination is configured in Catalyst Center; check for endpoint timeout or API error in Splunk HEC logs.

Additional operational context for Event Notification Volume and Type Distribution:

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
index=catalyst sourcetype="cisco:dnac:event:notification" | stats count as event_count by eventType, eventCategory, eventSeverity | sort -event_count
```

## Visualization

Bar chart of event_count by `eventType`, treemap or pivot by `eventCategory` and `eventSeverity`, single value of total event volume in window.

## Known False Positives

**Volume spike during Catalyst Center upgrade or restart.** When Catalyst Center restarts or is upgraded, the event notification system may replay pending notifications, creating a burst of events. Distinguish by checking whether the spike coincides with platform maintenance or upgrade events. Suppress by excluding the 30-minute window after a Catalyst Center restart from volume anomaly detection.

**Broad event subscription configuration generating high volume.** If the Catalyst Center event notification subscription is configured with many event types (especially informational ones), the volume will be naturally high. Distinguish by checking the event type distribution — if INFORMATIONAL events dominate, the subscription may be too broad. Suppress by refining the event subscription in Catalyst Center to include only operationally relevant event types.

**Network-wide event (e.g., widespread AP reboot) generating correlated notifications.** A single root cause (e.g., power outage, controller failover) can generate hundreds of event notifications simultaneously. Distinguish by checking whether many events share the same timestamp and related event type. Suppress by grouping correlated events within a 5-minute window and counting distinct root causes rather than individual notifications.

**Webhook retry creating duplicate event notifications.** If Splunk HEC responds slowly, Catalyst Center may retry the webhook, delivering duplicate events. Distinguish by deduplicating: `| stats count by eventType, timestamp, description | where count>1`. Suppress by deduplicating event notifications using a combination of `eventType`, `timestamp`, and `instanceId`.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
- [Catalyst Center Integration Guide](docs/guides/catalyst-center.md)
- [Catalyst Center Event Management API — Cisco DevNet](https://developer.cisco.com/docs/catalyst-center/#!get-notifications)
