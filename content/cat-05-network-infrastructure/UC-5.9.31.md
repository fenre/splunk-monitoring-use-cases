---
id: "5.9.31"
title: "Multi-Cloud Network Performance"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.9.31 · Multi-Cloud Network Performance

## Description

Measures network path performance to workloads hosted across AWS, Azure, GCP, and other cloud providers, identifying which provider or region delivers the best connectivity from each user location.

## Value

Measures network path performance to workloads hosted across AWS, Azure, GCP, and other cloud providers, identifying which provider or region delivers the best connectivity from each user location.

## Implementation

Deploy ThousandEyes Cloud Agents in each cloud provider region and create Agent-to-Server tests targeting your workloads. ThousandEyes supports Cloud Agents in AWS, Azure, GCP, IBM Cloud, and Alibaba Cloud. Name tests with the provider and region for easy filtering.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco ThousandEyes App for Splunk` (Splunkbase 7719).
• Ensure the following data sources are available: `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Deploy ThousandEyes Cloud Agents in each cloud provider region and create Agent-to-Server tests targeting your workloads. ThousandEyes supports Cloud Agents in AWS, Azure, GCP, IBM Cloud, and Alibaba Cloud. Name tests with the provider and region for easy filtering.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
`stream_index` thousandeyes.test.type="agent-to-server"
| search thousandeyes.test.name="*AWS*" OR thousandeyes.test.name="*Azure*" OR thousandeyes.test.name="*GCP*"
| stats avg(network.latency) as avg_latency_s avg(network.loss) as avg_loss by thousandeyes.test.name, thousandeyes.source.agent.name
| eval avg_latency_ms=round(avg_latency_s*1000,1)
| sort thousandeyes.source.agent.name, avg_latency_ms
```

Understanding this SPL

**Multi-Cloud Network Performance** — Measures network path performance to workloads hosted across AWS, Azure, GCP, and other cloud providers, identifying which provider or region delivers the best connectivity from each user location.

Documented **Data sources**: `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics. **App/TA** (typical add-on context): `Cisco ThousandEyes App for Splunk` (Splunkbase 7719). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

**Pipeline walkthrough**

• Invokes macro `stream_index` — in Search, use the UI or expand to inspect the underlying SPL.
• Applies an explicit `search` filter to narrow the current result set.
• `stats` rolls up events into metrics; results are split **by thousandeyes.test.name, thousandeyes.source.agent.name** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **avg_latency_ms** — often to normalize units, derive a ratio, or prepare for thresholds.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Column chart (latency by cloud provider), Table (agent, cloud target, latency, loss), Map (agent-to-cloud paths).

## SPL

```spl
`stream_index` thousandeyes.test.type="agent-to-server"
| search thousandeyes.test.name="*AWS*" OR thousandeyes.test.name="*Azure*" OR thousandeyes.test.name="*GCP*"
| stats avg(network.latency) as avg_latency_s avg(network.loss) as avg_loss by thousandeyes.test.name, thousandeyes.source.agent.name
| eval avg_latency_ms=round(avg_latency_s*1000,1)
| sort thousandeyes.source.agent.name, avg_latency_ms
```

## Visualization

Column chart (latency by cloud provider), Table (agent, cloud target, latency, loss), Map (agent-to-cloud paths).

## References

- [Splunkbase app 7719](https://splunkbase.splunk.com/app/7719)
