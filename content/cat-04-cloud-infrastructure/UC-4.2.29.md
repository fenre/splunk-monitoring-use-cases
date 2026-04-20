---
id: "4.2.29"
title: "Azure Front Door Origin Health"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-4.2.29 · Azure Front Door Origin Health

## Description

Origin probe failures cause automatic failover. Repeated failures indicate backend issues or misconfigured health probes; critical for global load balancing and CDN reliability.

## Value

Origin probe failures cause automatic failover. Repeated failures indicate backend issues or misconfigured health probes; critical for global load balancing and CDN reliability.

## Implementation

Enable Front Door diagnostic logs (FrontDoorHealthProbeLog) and route to Log Analytics or Event Hub. Ingest in Splunk. Alert on any Unhealthy probe result or non-200 status. Correlate with origin availability and probe configuration (path, interval). Dashboard by backend pool and origin.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk Add-on for Microsoft Cloud Services.
• Ensure the following data sources are available: Azure Front Door health probe logs, FrontDoorHealthProbeLog.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable Front Door diagnostic logs (FrontDoorHealthProbeLog) and route to Log Analytics or Event Hub. Ingest in Splunk. Alert on any Unhealthy probe result or non-200 status. Correlate with origin availability and probe configuration (path, interval). Dashboard by backend pool and origin.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=azure sourcetype="mscs:azure:diagnostics" resourceType="Microsoft.Cdn/profiles" log_s="FrontDoorHealthProbeLog"
| spath path=properties
| search properties.httpStatusCode!=200 OR properties.healthProbeSentResult="Unhealthy"
| stats count by resourceId, properties.backendPoolName, properties.healthProbeSentResult
| sort -count
```

Understanding this SPL

**Azure Front Door Origin Health** — Origin probe failures cause automatic failover. Repeated failures indicate backend issues or misconfigured health probes; critical for global load balancing and CDN reliability.

Documented **Data sources**: Azure Front Door health probe logs, FrontDoorHealthProbeLog. **App/TA** (typical add-on context): Splunk Add-on for Microsoft Cloud Services. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: azure; **sourcetype**: mscs:azure:diagnostics, Microsoft.Cdn/profiles. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=azure, sourcetype="mscs:azure:diagnostics". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Extracts structured paths (JSON/XML) with `spath`.
• Applies an explicit `search` filter to narrow the current result set.
• `stats` rolls up events into metrics; results are split **by resourceId, properties.backendPoolName, properties.healthProbeSentResult** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (backend pool, result, count), Status grid (origin health), Timeline (probe failures).

## SPL

```spl
index=azure sourcetype="mscs:azure:diagnostics" resourceType="Microsoft.Cdn/profiles" log_s="FrontDoorHealthProbeLog"
| spath path=properties
| search properties.httpStatusCode!=200 OR properties.healthProbeSentResult="Unhealthy"
| stats count by resourceId, properties.backendPoolName, properties.healthProbeSentResult
| sort -count
```

## Visualization

Table (backend pool, result, count), Status grid (origin health), Timeline (probe failures).

## References

- [Splunk Add-on for Microsoft Cloud Services](https://splunkbase.splunk.com/app/3110)
