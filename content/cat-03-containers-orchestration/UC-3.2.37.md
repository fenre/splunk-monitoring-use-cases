---
id: "3.2.37"
title: "Pod Disruption Budget Violations"
criticality: "high"
splunkPillar: "Observability"
---

# UC-3.2.37 · Pod Disruption Budget Violations

## Description

PDBs protect availability during voluntary disruptions; monitoring expected vs healthy pods avoids accidental full service outages during drains.

## Value

PDBs protect availability during voluntary disruptions; monitoring expected vs healthy pods avoids accidental full service outages during drains.

## Implementation

Scrape PDB status metrics; correlate with `Cannot evict pod` events during drains. Alert when healthy < expected minimum for PDB.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: kube-state-metrics.
• Ensure the following data sources are available: `sourcetype=kube:metrics`, `sourcetype=kube:events`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Scrape PDB status metrics; correlate with `Cannot evict pod` events during drains. Alert when healthy < expected minimum for PDB.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=k8s sourcetype="kube:metrics" metric_name="kube_poddisruptionbudget_status_expected_pods"
| stats latest(_value) as expected by namespace, poddisruptionbudget
| join type=left max=1 namespace poddisruptionbudget [
    search index=k8s sourcetype="kube:metrics" metric_name="kube_poddisruptionbudget_status_current_healthy"
    | stats latest(_value) as healthy by namespace, poddisruptionbudget
]
| where isnotnull(healthy) AND healthy<expected
| table namespace poddisruptionbudget expected healthy
```

Understanding this SPL

**Pod Disruption Budget Violations** — PDBs protect availability during voluntary disruptions; monitoring expected vs healthy pods avoids accidental full service outages during drains.

Documented **Data sources**: `sourcetype=kube:metrics`, `sourcetype=kube:events`. **App/TA** (typical add-on context): kube-state-metrics. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: k8s; **sourcetype**: kube:metrics. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=k8s, sourcetype="kube:metrics". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by namespace, poddisruptionbudget** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Joins to a subsearch with `join` — set `max=` to match cardinality and avoid silent truncation.
• Filters the current rows with `where isnotnull(healthy) AND healthy<expected` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Pod Disruption Budget Violations**): table namespace poddisruptionbudget expected healthy


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (PDB, healthy vs expected), Timeline (blocked evictions), Status panel.

## SPL

```spl
index=k8s sourcetype="kube:metrics" metric_name="kube_poddisruptionbudget_status_expected_pods"
| stats latest(_value) as expected by namespace, poddisruptionbudget
| join type=left max=1 namespace poddisruptionbudget [
    search index=k8s sourcetype="kube:metrics" metric_name="kube_poddisruptionbudget_status_current_healthy"
    | stats latest(_value) as healthy by namespace, poddisruptionbudget
]
| where isnotnull(healthy) AND healthy<expected
| table namespace poddisruptionbudget expected healthy
```

## Visualization

Table (PDB, healthy vs expected), Timeline (blocked evictions), Status panel.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
