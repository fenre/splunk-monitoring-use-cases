---
id: "5.13.67"
title: "Event Notification Correlation with TA Poll Data"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.13.67 · Event Notification Correlation with TA Poll Data

## Description

Correlates real-time webhook event notifications with the TA's polled issue data to verify comprehensive coverage and identify events that only appear in one data stream.

## Value

Running both push (webhook) and pull (TA polling) channels provides defense-in-depth. Correlation validates that both pipelines are capturing the same events.

## Implementation

**Push path:** HEC to `index=catalyst` `sourcetype=cisco:dnac:event:notification` (UC-5.13.64). **Pull path:** TA `issue` input → `cisco:dnac:issue` (UC-5.13.21), Intent API `GET /dna/intent/api/v1/issues`.

**Correlation key:** The SPL assumes a shared identifier `eventId` on webhook events can join to `issueId` in TA issue events (`| rename issueId as eventId`). If your Catalyst Center payload uses a different name (`id`, `eventUuid`), update the `join` and `rename` to match. If no stable shared ID exists, use secondary correlation: `last(deviceId) + strftime` window or `left` time-based join within ±5m — that alternative is not in the base SPL here.

**HEC setup:** Webhook to `https://<splunk>:8088/services/collector/event`, `Authorization: Splunk <HEC-token>`, `sourcetype=cisco:dnac:event:notification`.

## Detailed Implementation

Prerequisites
• UC-5.13.64 (HEC + Event Notifications) and UC-5.13.21 (`cisco:dnac:issue` from the TA) both producing events in the same or joinable time window.

Step 1 — Verify identifiers
- On a sample: `index=catalyst sourcetype="cisco:dnac:event:notification" eventType=NETWORK | head 1` — list fields. Repeat for `cisco:dnac:issue` and confirm `issueId` / `id` / `eventId` naming.
- If the webhook uses `id` and issues use `issueId`, use `| eval eventId=coalesce(eventId, id)` on the left side and `| rename issueId as eventId` on the right, or a common `string` CIDR-safe key as applicable.

Step 2 — Join performance
- For high volume, replace `join` with `| lookup` to a **KV/CSV** summary of latest issues, or `| stats` both sides to `| join` on small sets. This advanced UC expects moderate volume; use subsearch time bounds: `[search index=catalyst ... earliest=-24h@h latest=now]` on the right.

Step 3 — Search (baseline)

```spl
index=catalyst sourcetype="cisco:dnac:event:notification" eventType="NETWORK" | join type=left eventId [search index=catalyst sourcetype="cisco:dnac:issue" | rename issueId as eventId] | eval data_source=if(isnotnull(priority),"Both webhook + TA","Webhook only") | stats count by eventType, data_source | eval coverage_status=if(data_source="Both webhook + TA","Full coverage","Webhook-only — check TA input")
```

Step 4 — Interpretation
- **Both webhook + TA** — correlation succeeded; defense-in-depth confirmed for those IDs.
- **Webhook only** — TA may be delayed, the issue not yet in `issues` API, or different ID scheme; investigate a failing `issue` input or schema drift after upgrade.

Step 5 — HEC and TA recap
- HEC: token on Search Head or Heavy Forwarder; Catalyst Center → Webhook destination; Event Notification subscriptions to Splunk; sourcetype `cisco:dnac:event:notification`.
- TA: `issue` input enabled; poll interval default ~15m per TA docs; `index=catalyst` `sourcetype=cisco:dnac:issue`.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:event:notification" eventType="NETWORK" | join type=left eventId [search index=catalyst sourcetype="cisco:dnac:issue" | rename issueId as eventId] | eval data_source=if(isnotnull(priority),"Both webhook + TA","Webhook only") | stats count by eventType, data_source | eval coverage_status=if(data_source="Both webhook + TA","Full coverage","Webhook-only — check TA input")
```

## Visualization

Table of `data_source` distribution, pie of Full coverage vs Webhook-only, optional Sankey (webhook stream vs issues stream) if you export to a data model.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
