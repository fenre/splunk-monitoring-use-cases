---
id: "8.2.5"
title: "Deployment Tracking"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.2.5 · Deployment Tracking

## Description

Correlating deployments with performance changes is the fastest way to identify deployment-caused regressions. Essential for change management.

## Value

Correlating deployments with performance changes is the fastest way to identify deployment-caused regressions. Essential for change management.

## Implementation

Configure CI/CD pipeline to send deployment events to Splunk HEC (JSON payload with app, version, environment, deployer). Annotate timecharts with deployment markers. Correlate deployment times with error rate and latency changes.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Webhook input, CI/CD integration.
• Ensure the following data sources are available: Deployment tool webhooks (Jenkins, GitHub Actions, ArgoCD), application version endpoints.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Configure CI/CD pipeline to send deployment events to Splunk HEC (JSON payload with app, version, environment, deployer). Annotate timecharts with deployment markers. Correlate deployment times with error rate and latency changes.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=deployments sourcetype="deployment_event"
| table _time, application, version, environment, deployer, status
| sort -_time
```

Understanding this SPL

**Deployment Tracking** — Correlating deployments with performance changes is the fastest way to identify deployment-caused regressions. Essential for change management.

Documented **Data sources**: Deployment tool webhooks (Jenkins, GitHub Actions, ArgoCD), application version endpoints. **App/TA** (typical add-on context): Webhook input, CI/CD integration. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: deployments; **sourcetype**: deployment_event. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=deployments, sourcetype="deployment_event". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Pipeline stage (see **Deployment Tracking**): table _time, application, version, environment, deployer, status
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Timeline (deployment events overlaid on performance charts), Table (recent deployments), Annotation layer on dashboards.

## SPL

```spl
index=deployments sourcetype="deployment_event"
| table _time, application, version, environment, deployer, status
| sort -_time
```

## Visualization

Timeline (deployment events overlaid on performance charts), Table (recent deployments), Annotation layer on dashboards.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
