<!-- AUTO-GENERATED from UC-5.13.61.json — DO NOT EDIT -->

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
• UC-5.13.60 context (APs in Catalyst) and the TA **`issue`** input writing `cisco:dnac:issue` (see UC-5.13.21).
• For **real time**, Splunk HEC with `sourcetype=cisco:dnac:event:notification` and `index=catalyst`.

Step 1 — Pull path (Catalyst Center TA)
The TA polls `GET /dna/intent/api/v1/issues` into `cisco:dnac:issue`. Use `category="Security"` and wildcard **name** matches for rogue, aWIPS, or **unauthorized**; confirm `name` and `deviceName` exist in your build with `| fieldsummary`.

Step 2 — Push path (Catalyst webhooks to Splunk HEC)
1. In Splunk: **Settings → Data Inputs → HTTP Event Collector** — token with index `catalyst` and default sourcetype `cisco:dnac:event:notification` (or set sourcetype in the HEC event JSON).
2. In **Catalyst Center:** create a **Webhook** destination to `https://<splunk-hec>:8088/services/collector/event` (POST) with `Authorization: Splunk <HEC-token>`. Under **Platform → Developer Toolkit → Event Notifications**, subscribe to **Security** events that include rogue and wireless-intrusion categories.
3. Test: `index=catalyst sourcetype="cisco:dnac:event:notification" | head 5`.

Step 3 — Combined SPL

```spl
index=catalyst (sourcetype="cisco:dnac:issue" category="Security" (name="*rogue*" OR name="*aWIPS*" OR name="*unauthorized*")) OR (sourcetype="cisco:dnac:event:notification" eventType="SECURITY" (description="*rogue*" OR description="*wireless intrusion*")) | stats count as alert_count values(name) as alert_types by deviceName, siteId | sort -alert_count
```

On the HEC path, if `name` is null, use `values(coalesce(name,description))` in a follow-on `eval`.

Step 4 — Operationalize
Route to **SecOps** with a deep link to **Wireless** security views in Catalyst Center; throttle duplicate `deviceName+siteId` in a short window.

Step 5 — Troubleshooting
• **No HEC events:** wrong token, wrong index for the token, or firewall from Catalyst to Splunk:8088 — check HEC `splunkd.log` for `httpevent` errors.
• **Pull only, no push:** you still get issues, but with TA poll delay — expected if HEC is not configured. **Over-matching terms:** narrow wildcards to Cisco’s exact issue **name** strings after reviewing sample events in Search.


## SPL

```spl
index=catalyst (sourcetype="cisco:dnac:issue" category="Security" (name="*rogue*" OR name="*aWIPS*" OR name="*unauthorized*")) OR (sourcetype="cisco:dnac:event:notification" eventType="SECURITY" (description="*rogue*" OR description="*wireless intrusion*")) | stats count as alert_count values(name) as alert_types by deviceName, siteId | sort -alert_count
```

## Visualization

Table (deviceName, siteId, alert_count, alert_types), timeline of security alerts, drilldown to raw event in Catalyst Center.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
