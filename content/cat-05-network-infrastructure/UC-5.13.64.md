---
id: "5.13.64"
title: "Event Notification Volume and Type Distribution"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.13.64 · Event Notification Volume and Type Distribution

## Description

Provides an overview of all Catalyst Center Platform event notifications received via webhook, categorized by type, category, and severity.

## Value

Event notifications are Catalyst Center's real-time alerting channel. Understanding the volume and distribution establishes a baseline and validates the notification pipeline.

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
     - URL: `https://<splunk-hec-host>:8088/services/collector/event`
     - Method: POST
     - Headers: `Authorization: Splunk <your-HEC-token>`
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

Prerequisites
• Splunk with HTTP Event Collector enabled; network path from Catalyst Center to Splunk:8088 (or your load balancer fronting HEC); TLS plan for production.

Step 1 — HEC in Splunk
- Settings → Data Inputs → HTTP Event Collector → New Token.
- Set source type to `cisco:dnac:event:notification` (or set default in `inputs.conf` for the token).
- Index: `catalyst` (or a dedicated `catalyst_events`).
- Record the HEC global URL, typically `https://<sh-or-hfw>:8088/services/collector/event` and the `Authorization: Splunk <token>` header value.

Step 2 — Catalyst Center Webhook destination
- System → Settings → External Services (or **Design → Network Settings** → **Event Notifications** / **Webhooks** depending on release) — add **Webhook** destination: URL as above, POST, add header for Splunk. Complete SSL trust (upload CA or allow with governance approval).
- Test: Catalyst Center may offer “Send test” — then verify in `index=catalyst`.

Step 3 — Event Notification subscriptions
- **Platform** → **Developer Toolkit** → **Event Notifications** — for each class (Network, System, Security, App, Integration), add rules pointing to the Splunk webhook, broad severities to build this baseline view.

Step 4 — Field extraction
- If the payload is JSON, ensure **props.conf** for this sourcetype has `KV_MODE=json` or use **SEARCH-TIME** `spath` in dashboards. Normalize `eventType`, `eventCategory`, `eventSeverity` in the collector if you need consistent casing.

Step 5 — Search

```spl
index=catalyst sourcetype="cisco:dnac:event:notification" | stats count as event_count by eventType, eventCategory, eventSeverity | sort -event_count
```

Step 6 — Validate
- Baseline daily volume; alert if zero events when you expect a heartbeat of admin activity. Document subscription scope so volume changes are explainable after Catalyst Center upgrades.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:event:notification" | stats count as event_count by eventType, eventCategory, eventSeverity | sort -event_count
```

## Visualization

Bar chart of event_count by `eventType`, treemap or pivot by `eventCategory` and `eventSeverity`, single value of total event volume in window.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
