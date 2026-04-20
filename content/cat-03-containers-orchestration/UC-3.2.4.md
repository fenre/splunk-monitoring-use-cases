---
id: "3.2.4"
title: "Resource Quota Exhaustion"
criticality: "high"
splunkPillar: "Observability"
---

# UC-3.2.4 · Resource Quota Exhaustion

## Description

When namespace quotas are exhausted, new pods can't be created. Impacts deployments, autoscaling, and job scheduling within the namespace.

## Value

When namespace quotas are exhausted, new pods can't be created. Impacts deployments, autoscaling, and job scheduling within the namespace.

## Implementation

kube-state-metrics exposes resource quota data. Collect via OTel Collector. Alert when any resource (cpu, memory, pods, services) exceeds 80% of quota.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk OTel Collector, kube-state-metrics.
• Ensure the following data sources are available: `sourcetype=kube:resourcequota:meta`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
kube-state-metrics exposes resource quota data. Collect via OTel Collector. Alert when any resource (cpu, memory, pods, services) exceeds 80% of quota.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=k8s sourcetype="kube:resourcequota:meta"
| eval used_pct = round(used / hard * 100, 1)
| where used_pct > 80
| table namespace resource used hard used_pct
| sort -used_pct
```

Understanding this SPL

**Resource Quota Exhaustion** — When namespace quotas are exhausted, new pods can't be created. Impacts deployments, autoscaling, and job scheduling within the namespace.

Documented **Data sources**: `sourcetype=kube:resourcequota:meta`. **App/TA** (typical add-on context): Splunk OTel Collector, kube-state-metrics. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: k8s; **sourcetype**: kube:resourcequota:meta. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=k8s, sourcetype="kube:resourcequota:meta". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **used_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where used_pct > 80` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Resource Quota Exhaustion**): table namespace resource used hard used_pct
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Gauge per namespace/resource, Table, Bar chart by namespace.

## SPL

```spl
index=k8s sourcetype="kube:resourcequota:meta"
| eval used_pct = round(used / hard * 100, 1)
| where used_pct > 80
| table namespace resource used hard used_pct
| sort -used_pct
```

## Visualization

Gauge per namespace/resource, Table, Bar chart by namespace.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
