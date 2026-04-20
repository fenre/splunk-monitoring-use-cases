---
id: "4.2.14"
title: "Azure Load Balancer Health Probe Failures"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-4.2.14 · Azure Load Balancer Health Probe Failures

## Description

Probe failures mean backends are unhealthy; traffic stops flowing to those instances. Critical for load balancer and application availability.

## Value

Probe failures mean backends are unhealthy; traffic stops flowing to those instances. Critical for load balancer and application availability.

## Implementation

ProbeHealthStatus 1 = healthy, 0 = unhealthy. Alert when any backend pool shows unhealthy. Correlate with VM availability and application logs. Monitor SNAT exhaustion (SnatConnectionCount) for outbound issues.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_microsoft-cloudservices`.
• Ensure the following data sources are available: Azure Monitor metrics (ProbeHealthStatus, SnatConnectionCount).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
ProbeHealthStatus 1 = healthy, 0 = unhealthy. Alert when any backend pool shows unhealthy. Correlate with VM availability and application logs. Monitor SNAT exhaustion (SnatConnectionCount) for outbound issues.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=azure sourcetype="mscs:azure:metrics" metricName="ProbeHealthStatus" namespace="Microsoft.Network/loadBalancers"
| where average == 0
| table _time resourceId backendPoolName average
```

Understanding this SPL

**Azure Load Balancer Health Probe Failures** — Probe failures mean backends are unhealthy; traffic stops flowing to those instances. Critical for load balancer and application availability.

Documented **Data sources**: Azure Monitor metrics (ProbeHealthStatus, SnatConnectionCount). **App/TA** (typical add-on context): `Splunk_TA_microsoft-cloudservices`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: azure; **sourcetype**: mscs:azure:metrics. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=azure, sourcetype="mscs:azure:metrics". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where average == 0` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Azure Load Balancer Health Probe Failures**): table _time resourceId backendPoolName average


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Status panel (probe health), Table (LB, backend, status), Timeline.

## SPL

```spl
index=azure sourcetype="mscs:azure:metrics" metricName="ProbeHealthStatus" namespace="Microsoft.Network/loadBalancers"
| where average == 0
| table _time resourceId backendPoolName average
```

## Visualization

Status panel (probe health), Table (LB, backend, status), Timeline.

## References

- [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)
