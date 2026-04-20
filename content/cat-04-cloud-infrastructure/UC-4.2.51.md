---
id: "4.2.51"
title: "Azure API Management (APIM) Health"
criticality: "high"
splunkPillar: "Security"
---

# UC-4.2.51 · Azure API Management (APIM) Health

## Description

APIM is the gateway for API-first architectures. Backend errors, high latency, and rate limit breaches directly impact API consumers and downstream applications.

## Value

APIM is the gateway for API-first architectures. Backend errors, high latency, and rate limit breaches directly impact API consumers and downstream applications.

## Implementation

Enable diagnostics on APIM to send GatewayLogs via Event Hub to Splunk. Collect metrics for `Requests`, `BackendDuration`, `OverallDuration`, `FailedRequests`, and `UnauthorizedRequests`. Alert on backend error rate spikes, latency exceeding SLA thresholds, and capacity exhaustion (approaching unit limits). Track API-level usage patterns for capacity planning.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_microsoft-cloudservices` (Azure Monitor metrics/diagnostics).
• Ensure the following data sources are available: `sourcetype=azure:monitor:metric` (Microsoft.ApiManagement/service), `sourcetype=azure:diagnostics` (GatewayLogs).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable diagnostics on APIM to send GatewayLogs via Event Hub to Splunk. Collect metrics for `Requests`, `BackendDuration`, `OverallDuration`, `FailedRequests`, and `UnauthorizedRequests`. Alert on backend error rate spikes, latency exceeding SLA thresholds, and capacity exhaustion (approaching unit limits). Track API-level usage patterns for capacity planning.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cloud sourcetype="azure:diagnostics" Category="GatewayLogs"
| eval is_error=if(responseCode>=500,1,0)
| timechart span=5m count as requests, sum(is_error) as errors, avg(totalTime) as avg_latency_ms by apiId
| eval error_pct=round(100*errors/requests,2)
| where error_pct > 5 OR avg_latency_ms > 2000
```

Understanding this SPL

**Azure API Management (APIM) Health** — APIM is the gateway for API-first architectures. Backend errors, high latency, and rate limit breaches directly impact API consumers and downstream applications.

Documented **Data sources**: `sourcetype=azure:monitor:metric` (Microsoft.ApiManagement/service), `sourcetype=azure:diagnostics` (GatewayLogs). **App/TA** (typical add-on context): `Splunk_TA_microsoft-cloudservices` (Azure Monitor metrics/diagnostics). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cloud; **sourcetype**: azure:diagnostics. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=cloud, sourcetype="azure:diagnostics". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **is_error** — often to normalize units, derive a ratio, or prepare for thresholds.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by apiId** — ideal for trending and alerting on this use case.
• `eval` defines or adjusts **error_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where error_pct > 5 OR avg_latency_ms > 2000` — typically the threshold or rule expression for this monitoring goal.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t count from datamodel=Web.Web by Web.status, Web.http_method, Web.dest span=5m | sort - count
```

Understanding this CIM / accelerated SPL

**Azure API Management (APIM) Health** — APIM is the gateway for API-first architectures. Backend errors, high latency, and rate limit breaches directly impact API consumers and downstream applications.

Documented **Data sources**: `sourcetype=azure:monitor:metric` (Microsoft.ApiManagement/service), `sourcetype=azure:diagnostics` (GatewayLogs). **App/TA** (typical add-on context): `Splunk_TA_microsoft-cloudservices` (Azure Monitor metrics/diagnostics). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Web.Web` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (request rate and error rate by API), Gauge (latency vs. SLA), Table (top errors by API and operation).

## SPL

```spl
index=cloud sourcetype="azure:diagnostics" Category="GatewayLogs"
| eval is_error=if(responseCode>=500,1,0)
| timechart span=5m count as requests, sum(is_error) as errors, avg(totalTime) as avg_latency_ms by apiId
| eval error_pct=round(100*errors/requests,2)
| where error_pct > 5 OR avg_latency_ms > 2000
```

## CIM SPL

```spl
| tstats summariesonly=t count from datamodel=Web.Web by Web.status, Web.http_method, Web.dest span=5m | sort - count
```

## Visualization

Line chart (request rate and error rate by API), Gauge (latency vs. SLA), Table (top errors by API and operation).

## References

- [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)
- [CIM: Web](https://docs.splunk.com/Documentation/CIM/latest/User/Web)
