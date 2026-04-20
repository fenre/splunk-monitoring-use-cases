---
id: "3.3.11"
title: "Operator Subscription Health"
criticality: "high"
splunkPillar: "Observability"
---

# UC-3.3.11 · Operator Subscription Health

## Description

OLM subscriptions deliver operator upgrades; unhealthy subscriptions block security patches and CRD updates for platform add-ons.

## Value

OLM subscriptions deliver operator upgrades; unhealthy subscriptions block security patches and CRD updates for platform add-ons.

## Implementation

Parse Subscription `status.state` and conditions. Alert on `CatalogSourcesUnhealthy`, `InstallPlanPending` beyond SLA, or repeated upgrade failures. Correlate with CatalogSource pod health.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `oc get subscription -A -o json` scripted input.
• Ensure the following data sources are available: `sourcetype=openshift:subscription`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Parse Subscription `status.state` and conditions. Alert on `CatalogSourcesUnhealthy`, `InstallPlanPending` beyond SLA, or repeated upgrade failures. Correlate with CatalogSource pod health.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=openshift sourcetype="openshift:subscription"
| where state!="AtLatestKnown" OR match(_raw,"InstallPlanPending|CatalogSourcesUnhealthy")
| stats latest(state) as state, latest(message) as msg by namespace, name, channel
| sort namespace, name
```

Understanding this SPL

**Operator Subscription Health** — OLM subscriptions deliver operator upgrades; unhealthy subscriptions block security patches and CRD updates for platform add-ons.

Documented **Data sources**: `sourcetype=openshift:subscription`. **App/TA** (typical add-on context): `oc get subscription -A -o json` scripted input. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: openshift; **sourcetype**: openshift:subscription. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=openshift, sourcetype="openshift:subscription". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where state!="AtLatestKnown" OR match(_raw,"InstallPlanPending|CatalogSourcesUnhealthy")` — typically the threshold or rule expression for this monitoring goal.
• `stats` rolls up events into metrics; results are split **by namespace, name, channel** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (subscription, state, message), Status grid by namespace, Timeline.

## SPL

```spl
index=openshift sourcetype="openshift:subscription"
| where state!="AtLatestKnown" OR match(_raw,"InstallPlanPending|CatalogSourcesUnhealthy")
| stats latest(state) as state, latest(message) as msg by namespace, name, channel
| sort namespace, name
```

## Visualization

Table (subscription, state, message), Status grid by namespace, Timeline.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
