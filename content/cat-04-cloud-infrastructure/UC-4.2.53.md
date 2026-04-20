---
id: "4.2.53"
title: "Azure Traffic Manager Endpoint Health"
criticality: "high"
splunkPillar: "Observability"
---

# UC-4.2.53 · Azure Traffic Manager Endpoint Health

## Description

Traffic Manager provides DNS-based global load balancing. Degraded endpoints cause traffic to shift, but undetected health changes can leave users routed to unhealthy regions.

## Value

Traffic Manager provides DNS-based global load balancing. Degraded endpoints cause traffic to shift, but undetected health changes can leave users routed to unhealthy regions.

## Implementation

Collect Azure Monitor metrics for Traffic Manager profiles. Monitor `ProbeAgentCurrentEndpointStateByProfileResourceId` for endpoint health percentage and `QpsByEndpoint` for query distribution. Alert when any endpoint degrades or goes offline. Track DNS query patterns to verify failover behavior is correct after endpoint changes.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_microsoft-cloudservices` (Azure Monitor metrics).
• Ensure the following data sources are available: `sourcetype=azure:monitor:metric` (Microsoft.Network/trafficManagerProfiles).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Collect Azure Monitor metrics for Traffic Manager profiles. Monitor `ProbeAgentCurrentEndpointStateByProfileResourceId` for endpoint health percentage and `QpsByEndpoint` for query distribution. Alert when any endpoint degrades or goes offline. Track DNS query patterns to verify failover behavior is correct after endpoint changes.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cloud sourcetype="azure:monitor:metric" resource_type="microsoft.network/trafficmanagerprofiles" metric_name="ProbeAgentCurrentEndpointStateByProfileResourceId"
| timechart span=5m latest(average) as health_pct by resource_name
| where health_pct < 100
```

Understanding this SPL

**Azure Traffic Manager Endpoint Health** — Traffic Manager provides DNS-based global load balancing. Degraded endpoints cause traffic to shift, but undetected health changes can leave users routed to unhealthy regions.

Documented **Data sources**: `sourcetype=azure:monitor:metric` (Microsoft.Network/trafficManagerProfiles). **App/TA** (typical add-on context): `Splunk_TA_microsoft-cloudservices` (Azure Monitor metrics). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cloud; **sourcetype**: azure:monitor:metric. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=cloud, sourcetype="azure:monitor:metric". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by resource_name** — ideal for trending and alerting on this use case.
• Filters the current rows with `where health_pct < 100` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Status grid (endpoint × health), Line chart (health % per endpoint), Single value (degraded endpoint count).

## SPL

```spl
index=cloud sourcetype="azure:monitor:metric" resource_type="microsoft.network/trafficmanagerprofiles" metric_name="ProbeAgentCurrentEndpointStateByProfileResourceId"
| timechart span=5m latest(average) as health_pct by resource_name
| where health_pct < 100
```

## Visualization

Status grid (endpoint × health), Line chart (health % per endpoint), Single value (degraded endpoint count).

## References

- [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)
