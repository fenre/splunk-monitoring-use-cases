---
id: "4.4.18"
title: "Cloud Endpoint and DNS Resolution Health"
criticality: "medium"
splunkPillar: "Security"
---

# UC-4.4.18 · Cloud Endpoint and DNS Resolution Health

## Description

PrivateLink, VPC endpoints, and private DNS zones enable secure access to AWS/Azure/GCP services. Endpoint or DNS failures cause application outages that are hard to diagnose.

## Value

PrivateLink, VPC endpoints, and private DNS zones enable secure access to AWS/Azure/GCP services. Endpoint or DNS failures cause application outages that are hard to diagnose.

## Implementation

Run periodic probes (DNS lookup for private hosted zone, HTTPS to VPC endpoint) from a central host or Lambda. Ingest success/failure and latency. Alert when endpoint is unreachable or RTT exceeds threshold.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom scripted input (nslookup, curl to endpoint), CloudWatch Route53 health.
• Ensure the following data sources are available: Route53 Resolver query logs, VPC endpoint connection acceptance, Azure Private Endpoint status.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Run periodic probes (DNS lookup for private hosted zone, HTTPS to VPC endpoint) from a central host or Lambda. Ingest success/failure and latency. Alert when endpoint is unreachable or RTT exceeds threshold.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cloud sourcetype="endpoint:health"
| stats latest(connect_ok) as ok, latest(rtt_ms) as rtt by endpoint_id, vpc_id
| where ok != 1 OR rtt > 500
| table endpoint_id vpc_id ok rtt _time
```

Understanding this SPL

**Cloud Endpoint and DNS Resolution Health** — PrivateLink, VPC endpoints, and private DNS zones enable secure access to AWS/Azure/GCP services. Endpoint or DNS failures cause application outages that are hard to diagnose.

Documented **Data sources**: Route53 Resolver query logs, VPC endpoint connection acceptance, Azure Private Endpoint status. **App/TA** (typical add-on context): Custom scripted input (nslookup, curl to endpoint), CloudWatch Route53 health. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cloud; **sourcetype**: endpoint:health. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=cloud, sourcetype="endpoint:health". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by endpoint_id, vpc_id** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where ok != 1 OR rtt > 500` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Cloud Endpoint and DNS Resolution Health**): table endpoint_id vpc_id ok rtt _time


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Status grid (endpoint, OK/fail), Table (endpoint, RTT), Line chart (RTT over time).

## SPL

```spl
index=cloud sourcetype="endpoint:health"
| stats latest(connect_ok) as ok, latest(rtt_ms) as rtt by endpoint_id, vpc_id
| where ok != 1 OR rtt > 500
| table endpoint_id vpc_id ok rtt _time
```

## Visualization

Status grid (endpoint, OK/fail), Table (endpoint, RTT), Line chart (RTT over time).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
