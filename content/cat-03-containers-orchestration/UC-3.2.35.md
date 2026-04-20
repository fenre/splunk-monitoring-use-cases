---
id: "3.2.35"
title: "Pod Anti-Affinity Violations"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-3.2.35 · Pod Anti-Affinity Violations

## Description

Scheduling cannot always satisfy anti-affinity; detecting pending pods or topology spread skew avoids accidental single-AZ concentration.

## Value

Scheduling cannot always satisfy anti-affinity; detecting pending pods or topology spread skew avoids accidental single-AZ concentration.

## Implementation

Capture scheduler `FailedScheduling` messages with affinity terms. Optional: compare replica distribution by zone label versus `topologySpreadConstraints`. Alert when scheduling failures mention anti-affinity for >10 minutes.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: kube-scheduler logs, Kubernetes events.
• Ensure the following data sources are available: `sourcetype=kube:scheduler`, `sourcetype=kube:events`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Capture scheduler `FailedScheduling` messages with affinity terms. Optional: compare replica distribution by zone label versus `topologySpreadConstraints`. Alert when scheduling failures mention anti-affinity for >10 minutes.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=k8s sourcetype="kube:events" reason="FailedScheduling"
| search "affinity" OR "anti-affinity" OR "topology spread"
| stats count by namespace, involvedObject.name, message
| sort -count
```

Understanding this SPL

**Pod Anti-Affinity Violations** — Scheduling cannot always satisfy anti-affinity; detecting pending pods or topology spread skew avoids accidental single-AZ concentration.

Documented **Data sources**: `sourcetype=kube:scheduler`, `sourcetype=kube:events`. **App/TA** (typical add-on context): kube-scheduler logs, Kubernetes events. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: k8s; **sourcetype**: kube:events. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=k8s, sourcetype="kube:events". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Applies an explicit `search` filter to narrow the current result set.
• `stats` rolls up events into metrics; results are split **by namespace, involvedObject.name, message** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (pod, message), Bar chart by zone (replica counts), Timeline.

## SPL

```spl
index=k8s sourcetype="kube:events" reason="FailedScheduling"
| search "affinity" OR "anti-affinity" OR "topology spread"
| stats count by namespace, involvedObject.name, message
| sort -count
```

## Visualization

Table (pod, message), Bar chart by zone (replica counts), Timeline.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
