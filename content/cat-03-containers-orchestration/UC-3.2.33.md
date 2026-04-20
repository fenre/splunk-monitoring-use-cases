---
id: "3.2.33"
title: "Node Drain Events"
criticality: "high"
splunkPillar: "Observability"
---

# UC-3.2.33 · Node Drain Events

## Description

Draining nodes for maintenance evicts workloads; correlating drains with pod disruption helps explain transient unavailability.

## Value

Draining nodes for maintenance evicts workloads; correlating drains with pod disruption helps explain transient unavailability.

## Implementation

Capture cordon/drain API calls via audit. Dashboard maintenance windows. Alert on unexpected uncordon outside change windows.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Kubernetes audit, controller logs.
• Ensure the following data sources are available: `sourcetype=kube:audit`, `sourcetype=kube:objects:events`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Capture cordon/drain API calls via audit. Dashboard maintenance windows. Alert on unexpected uncordon outside change windows.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=k8s sourcetype="kube:objects:events" "*drain*" OR reason="NodeSchedulable"
| table _time involvedObject.name message
```

Understanding this SPL

**Node Drain Events** — Draining nodes for maintenance evicts workloads; correlating drains with pod disruption helps explain transient unavailability.

Documented **Data sources**: `sourcetype=kube:audit`, `sourcetype=kube:objects:events`. **App/TA** (typical add-on context): Kubernetes audit, controller logs. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: k8s; **sourcetype**: kube:objects:events. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=k8s, sourcetype="kube:objects:events". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Pipeline stage (see **Node Drain Events**): table _time involvedObject.name message


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Timeline (drain/cordon), Table (user, node), Map of affected nodes.

## SPL

```spl
index=k8s sourcetype="kube:objects:events" "*drain*" OR reason="NodeSchedulable"
| table _time involvedObject.name message
```

## Visualization

Timeline (drain/cordon), Table (user, node), Map of affected nodes.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
