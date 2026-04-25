<!-- AUTO-GENERATED from UC-6.2.56.json — DO NOT EDIT -->

---
id: "6.2.56"
title: "TrueNAS alert notification delivery failures for email SNMP and webhooks"
criticality: "high"
splunkPillar: "Observability"
---

# UC-6.2.56 · TrueNAS alert notification delivery failures for email SNMP and webhooks

## Description

If alerting channels fail silently, operators miss pool degradations until users complain. Monitoring the notifier proves the control plane works.

## Value

Closes the last-mile gap in observability for remote edge TrueNAS deployments.

## Implementation

Test webhooks with synthetic alerts weekly. Dedupe on `message_id` if present.

## SPL

```spl
index=storage sourcetype="truenas:alert" earliest=-24h
| search "notification failed" OR "smtp error" OR "webhook" OR snmp OR "alert send"
| eval channel=coalesce(notifier, channel, transport)
| stats count as failures latest(_time) as last_fail by hostname, channel
| where failures > 0
| sort - failures
```

## Visualization

Table (channel, failures), timeline.

## References

- [TrueNAS SCALE API documentation](https://www.truenas.com/docs/scale/scaletutorials/toptoolbar/reportinggraphs/)
- [TrueNAS CORE/SCALE docs — alerts](https://www.truenas.com/docs/)
