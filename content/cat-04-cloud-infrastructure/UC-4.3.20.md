---
id: "4.3.20"
title: "Cloud Armor Security Policy and DDoS Metrics"
criticality: "high"
splunkPillar: "Security"
---

# UC-4.3.20 · Cloud Armor Security Policy and DDoS Metrics

## Description

Cloud Armor blocks and DDoS metrics indicate attack traffic and policy effectiveness. Essential for WAF and DDoS visibility.

## Value

Cloud Armor blocks and DDoS metrics indicate attack traffic and policy effectiveness. Essential for WAF and DDoS visibility.

## Implementation

Enable HTTP(S) LB logging with security policy info. Ingest in Splunk. Alert on high block rate or DDoS mitigation events. Dashboard allowed vs denied by rule and source.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_google-cloudplatform`.
• Ensure the following data sources are available: Cloud Logging (loadbalancing.googleapis.com/http_requests with security policy), Cloud Monitoring (DDoS metrics).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable HTTP(S) LB logging with security policy info. Ingest in Splunk. Alert on high block rate or DDoS mitigation events. Dashboard allowed vs denied by rule and source.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=gcp sourcetype="google:gcp:pubsub:message" jsonPayload.enforcedSecurityPolicy.name=*
| stats count by jsonPayload.enforcedSecurityPolicy.outcome jsonPayload.enforcedSecurityPolicy.name
| sort -count
```

Understanding this SPL

**Cloud Armor Security Policy and DDoS Metrics** — Cloud Armor blocks and DDoS metrics indicate attack traffic and policy effectiveness. Essential for WAF and DDoS visibility.

Documented **Data sources**: Cloud Logging (loadbalancing.googleapis.com/http_requests with security policy), Cloud Monitoring (DDoS metrics). **App/TA** (typical add-on context): `Splunk_TA_google-cloudplatform`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: gcp; **sourcetype**: google:gcp:pubsub:message. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=gcp, sourcetype="google:gcp:pubsub:message". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by jsonPayload.enforcedSecurityPolicy.outcome jsonPayload.enforcedSecurityPolicy.name** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (policy, outcome, count), Bar chart (blocks by rule), Timeline (block rate).

## SPL

```spl
index=gcp sourcetype="google:gcp:pubsub:message" jsonPayload.enforcedSecurityPolicy.name=*
| stats count by jsonPayload.enforcedSecurityPolicy.outcome jsonPayload.enforcedSecurityPolicy.name
| sort -count
```

## Visualization

Table (policy, outcome, count), Bar chart (blocks by rule), Timeline (block rate).

## References

- [Splunk_TA_google-cloudplatform](https://splunkbase.splunk.com/app/3088)
