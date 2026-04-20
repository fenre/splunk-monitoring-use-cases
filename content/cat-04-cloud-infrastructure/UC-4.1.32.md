---
id: "4.1.32"
title: "NAT Gateway Bytes Processed and Connection Tracking"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-4.1.32 · NAT Gateway Bytes Processed and Connection Tracking

## Description

NAT Gateway is a single point of egress for private subnets. Monitoring bytes and connection count supports capacity and cost (data processed) planning.

## Value

NAT Gateway is a single point of egress for private subnets. Monitoring bytes and connection count supports capacity and cost (data processed) planning.

## Implementation

Collect NAT Gateway metrics. Alert on sudden drop in BytesOutToDestination (possible outage) or spike in ActiveConnectionCount (possible connection exhaustion). Track data processed for cost.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_aws`.
• Ensure the following data sources are available: CloudWatch NAT Gateway metrics (BytesOutToDestination, ActiveConnectionCount).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Collect NAT Gateway metrics. Alert on sudden drop in BytesOutToDestination (possible outage) or spike in ActiveConnectionCount (possible connection exhaustion). Track data processed for cost.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/NATGateway"
| timechart span=1h sum(Sum) as bytes, avg(Average) as connections by NatGatewayId
```

Understanding this SPL

**NAT Gateway Bytes Processed and Connection Tracking** — NAT Gateway is a single point of egress for private subnets. Monitoring bytes and connection count supports capacity and cost (data processed) planning.

Documented **Data sources**: CloudWatch NAT Gateway metrics (BytesOutToDestination, ActiveConnectionCount). **App/TA** (typical add-on context): `Splunk_TA_aws`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:cloudwatch. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=aws, sourcetype="aws:cloudwatch". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=1h** buckets with a separate series **by NatGatewayId** — ideal for trending and alerting on this use case.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (bytes, connections by NAT GW), Table (NAT GW, bytes today), Single value.

## SPL

```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/NATGateway"
| timechart span=1h sum(Sum) as bytes, avg(Average) as connections by NatGatewayId
```

## Visualization

Line chart (bytes, connections by NAT GW), Table (NAT GW, bytes today), Single value.

## References

- [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)
