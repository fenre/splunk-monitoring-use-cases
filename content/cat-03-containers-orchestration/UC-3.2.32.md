<!-- AUTO-GENERATED from UC-3.2.32.json — DO NOT EDIT -->

---
id: "3.2.32"
title: "Namespace Quota Utilization Trending"
criticality: "high"
splunkPillar: "Observability"
---

# UC-3.2.32 · Namespace Quota Utilization Trending

## Description

Namespaces hitting CPU/memory/object quotas block rollouts; trending utilization prevents deployment freezes during releases.

## Value

Namespaces hitting CPU/memory/object quotas block rollouts; trending utilization prevents deployment freezes during releases.

## Implementation

Same quota feed as UC-3.2.4; use a stricter 90% threshold for release windows. Split alerts by resource type (cpu, memory, pods).

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk OTel Collector.
• Ensure the following data sources are available: `sourcetype=kube:resourcequota:meta`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Same quota feed as UC-3.2.4; use a stricter 90% threshold for release windows. Split alerts by resource type (cpu, memory, pods).

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=k8s sourcetype="kube:resourcequota:meta"
| eval used_pct = round(used / hard * 100, 1)
| where used_pct > 90
| table namespace resource used hard used_pct
| sort -used_pct
```

Understanding this SPL

**Namespace Quota Utilization Trending** — Namespaces hitting CPU/memory/object quotas block rollouts; trending utilization prevents deployment freezes during releases.

Documented **Data sources**: `sourcetype=kube:resourcequota:meta`. **App/TA** (typical add-on context): Splunk OTel Collector. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: k8s; **sourcetype**: kube:resourcequota:meta. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=k8s, sourcetype="kube:resourcequota:meta". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **used_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where used_pct > 90` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Namespace Quota Utilization Trending**): table namespace resource used hard used_pct
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. For Kubernetes and OpenShift data, sample rows should line up with what you see from the cluster command-line tool, the Kubernetes Dashboard (or OpenShift console), and your Splunk Add-on for Kubernetes (`Splunk_TA_kubernetes`) or OpenTelemetry collector view of the same objects. Compare with known good and bad scenarios where you have them. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Stacked bar (used vs hard), Gauge per quota, Table.

## SPL

```spl
index=k8s sourcetype="kube:resourcequota:meta"
| eval used_pct = round(used / hard * 100, 1)
| where used_pct > 90
| table namespace resource used hard used_pct
| sort -used_pct
```

## Visualization

Stacked bar (used vs hard), Gauge per quota, Table.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
