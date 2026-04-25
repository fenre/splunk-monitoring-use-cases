<!-- AUTO-GENERATED from UC-5.13.65.json — DO NOT EDIT -->

---
id: "5.13.65"
title: "Critical Event Notification Alerting (Severity 1-2)"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.13.65 · Critical Event Notification Alerting (Severity 1-2)

## Description

Alerts on Catalyst Center severity 1 and 2 event notifications, which represent the most critical platform and network events requiring immediate response.

## Value

Severity 1-2 events represent critical failures or security incidents. Real-time alerting via webhooks ensures sub-minute detection compared to the TA's 15-minute polling cycle.

## Implementation

Requires the HEC + webhook + Event Notification pipeline from UC-5.13.64. **Sourcetype:** `cisco:dnac:event:notification`. **HEC URL:** `https://<host>:8088/services/collector/event` with `Authorization: Splunk <HEC-token>`. In Catalyst Center, ensure subscriptions include severity 1 and 2 for Network, System, and Security (and others as your policy requires). If `eventSeverity` is delivered as a string, normalize in props or add `| eval eventSeverity=tonumber(eventSeverity)` before filtering. For alerting in Splunk: save this search with `eventSeverity=1` as highest priority, route to on-call, and add SMS/email. Optional: add `lookup` for eventType to a runbook table.

## Detailed Implementation

Prerequisites
• UC-5.13.64 complete: HEC token, Webhook destination, and at least one active Event Notification subscription to Splunk with `sourcetype=cisco:dnac:event:notification` and `index=catalyst`.

Step 1 — Confirm field typing
- Run `| fieldsummary eventSeverity` to see whether the field is numeric or string. Use `| where (eventSeverity=1 OR eventSeverity=2 OR eventSeverity="1" OR eventSeverity="2")` if mixed.

Step 2 — HEC and Catalyst Center (recap)
- Splunk: HEC on port 8088, token scoped to the catalyst index; Global Settings: enable SSL and indexes as per your hardening standard.
- Catalyst Center: Webhook to `/services/collector/event`; for JSON events, the body must be valid HEC format (`{"event":{...}}` or `{"event": "..." }` per Splunk HEC spec).
- Event Notifications: subscribe to **all** categories you must react to for S1/S2, not just Network.

Step 3 — Search / alert

```spl
index=catalyst sourcetype="cisco:dnac:event:notification" (eventSeverity=1 OR eventSeverity=2) | stats count as event_count values(eventCategory) as categories latest(description) as last_description by eventType, eventSeverity | sort eventSeverity -event_count
```

Step 4 — Operationalize
- Alert when `count>0` in last 5m for S1, throttle per `eventType` to avoid flapping. Pair with `sendemail` or ITSM ticket integration. Compare latency with TA pollers (UC-5.13.1 / issues) in post-incident review.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:event:notification" (eventSeverity=1 OR eventSeverity=2) | stats count as event_count values(eventCategory) as categories latest(description) as last_description by eventType, eventSeverity | sort eventSeverity -event_count
```

## Visualization

Table (eventType, eventSeverity, event_count, last_description), time chart of S1/S2 over time, single value of open critical notifications.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
