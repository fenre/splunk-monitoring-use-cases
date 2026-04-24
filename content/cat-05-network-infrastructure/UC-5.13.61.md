---
id: "5.13.61"
title: "Rogue AP and aWIPS Alert Monitoring"
criticality: "critical"
splunkPillar: "Security"
---

# UC-5.13.61 · Rogue AP and aWIPS Alert Monitoring

## Description

Monitors for rogue access point detections and aWIPS (Adaptive Wireless Intrusion Prevention System) alerts from Catalyst Center, which indicate unauthorized wireless infrastructure.

## Value

Rogue APs represent a direct security threat — they can be used for eavesdropping, man-in-the-middle attacks, or unauthorized network access. Immediate detection is critical.

## Implementation

Rogue AP alerts appear in two ways:

1. **Via TA (already configured):** Rogue AP issues appear as `sourcetype=cisco:dnac:issue` with `category=Security`. Filter the existing issue input for security-related names.

2. **Via Event Notifications (recommended for real-time):** Configure Catalyst Center Platform event notifications:
   a. Navigate to Platform → Developer Toolkit → Event Notifications
   b. Create a new notification with Type=SECURITY
   c. Set destination to a Splunk HEC endpoint:
      - URL: `https://your-splunk-hec:8088/services/collector/event`
      - Method: POST
      - Headers: `Authorization: Splunk <HEC-token>`
   d. Use `sourcetype=cisco:dnac:event:notification`
   e. Subscribe to Security events including rogue AP and aWIPS categories

## Detailed Implementation

Prerequisites
• UC-5.13.60 context (APs managed in Catalyst Center) and the `issue` input enabled to `cisco:dnac:issue` (UC-5.13.21).
• For real-time: Splunk HEC token with `sourcetype=cisco:dnac:event:notification` and `index=catalyst`.

Step 1 — TA path (pull)
**Intent API (TA):** The TA already polls `GET /dna/intent/api/v1/issues` into `cisco:dnac:issue`. Filter: `category="Security"` and name text matching rogue/aWIPS/unauthorized. No new stanza is required; validate field `name` exists for your build.

Step 2 — HEC path (push)
1. In Splunk: Settings → Data Inputs → HTTP Event Collector — create a token, set index `catalyst`, default sourcetype `cisco:dnac:event:notification` (or set sourcetype in the JSON `event` metadata if using raw endpoint).
2. In Catalyst Center: add a **Webhook** destination: URL `https://<splunk-hec>:8088/services/collector/event`, method POST, header `Authorization: Splunk <HEC-token>`, content type per your integration (HEC raw vs JSON). Under Platform → Developer Toolkit → Event Notifications, create a Security subscription for rogue and wireless-intrusion related events, pointing at that destination.
3. Ingest test event and run `index=catalyst sourcetype="cisco:dnac:event:notification" | head 5`.

Step 3 — Combined SPL

```spl
index=catalyst (sourcetype="cisco:dnac:issue" category="Security" (name="*rogue*" OR name="*aWIPS*" OR name="*unauthorized*")) OR (sourcetype="cisco:dnac:event:notification" eventType="SECURITY" (description="*rogue*" OR description="*wireless intrusion*")) | stats count as alert_count values(name) as alert_types by deviceName, siteId | sort -alert_count
```

**Note:** If `name` is null on HEC path, add `coalesce` with `description` in `values()`.

Step 4 — Operationalize
High-severity alert to SecOps; include drilldown to Catalyst Center Wireless Assurance/Security view.

## SPL

```spl
index=catalyst (sourcetype="cisco:dnac:issue" category="Security" (name="*rogue*" OR name="*aWIPS*" OR name="*unauthorized*")) OR (sourcetype="cisco:dnac:event:notification" eventType="SECURITY" (description="*rogue*" OR description="*wireless intrusion*")) | stats count as alert_count values(name) as alert_types by deviceName, siteId | sort -alert_count
```

## Visualization

Table (deviceName, siteId, alert_count, alert_types), timeline of security alerts, drilldown to raw event in Catalyst Center.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
