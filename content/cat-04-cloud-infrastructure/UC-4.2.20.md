---
id: "4.2.20"
title: "Event Grid Delivery Failures"
criticality: "high"
splunkPillar: "Observability"
---

# UC-4.2.20 · Event Grid Delivery Failures

## Description

Delivery failures mean subscribers did not receive events. Critical for event-driven architecture and integration reliability.

## Value

Delivery failures mean subscribers did not receive events. Critical for event-driven architecture and integration reliability.

## Implementation

Enable Event Grid diagnostic logging to Event Hub or storage. Ingest in Splunk. Alert when DeliveryFailure count > 0. Correlate with dead-letter and subscriber endpoint health.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_microsoft-cloudservices`.
• Ensure the following data sources are available: Event Grid diagnostic logs (DeliveryFailure, DeliverySuccess).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable Event Grid diagnostic logging to Event Hub or storage. Ingest in Splunk. Alert when DeliveryFailure count > 0. Correlate with dead-letter and subscriber endpoint health.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=azure sourcetype="mscs:azure:diagnostics" Category="DeliveryFailure"
| stats count by topic eventSubscriptionName errorCode
| sort -count
```

Understanding this SPL

**Event Grid Delivery Failures** — Delivery failures mean subscribers did not receive events. Critical for event-driven architecture and integration reliability.

Documented **Data sources**: Event Grid diagnostic logs (DeliveryFailure, DeliverySuccess). **App/TA** (typical add-on context): `Splunk_TA_microsoft-cloudservices`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: azure; **sourcetype**: mscs:azure:diagnostics. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=azure, sourcetype="mscs:azure:diagnostics". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by topic eventSubscriptionName errorCode** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (topic, subscription, failures), Line chart (deliveries vs failures), Single value (failed deliveries).

## SPL

```spl
index=azure sourcetype="mscs:azure:diagnostics" Category="DeliveryFailure"
| stats count by topic eventSubscriptionName errorCode
| sort -count
```

## Visualization

Table (topic, subscription, failures), Line chart (deliveries vs failures), Single value (failed deliveries).

## References

- [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)
