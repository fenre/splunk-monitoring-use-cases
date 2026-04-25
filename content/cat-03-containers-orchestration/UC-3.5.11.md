<!-- AUTO-GENERATED from UC-3.5.11.json — DO NOT EDIT -->

---
id: "3.5.11"
title: "Sidecar Injection Validation"
criticality: "medium"
splunkPillar: "Security"
---

# UC-3.5.11 · Sidecar Injection Validation

## Description

Pods without injection bypass mesh policy and mTLS; continuous validation enforces namespace labels and mutating webhook coverage.

## Value

Pods without injection bypass mesh policy and mTLS; continuous validation enforces namespace labels and mutating webhook coverage.

## Implementation

Periodically inventory pods in `istio-injection=enabled` namespaces (CI job or Splunk scheduled search against cached object JSON). Flag workloads missing `istio-proxy`. Optionally parse audit logs for pod create with webhook bypass. Integrate with policy-as-code to fail builds that skip mesh membership.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Kubernetes API audit or controller logs, `kube:objects` snapshot.
• Ensure the following data sources are available: `sourcetype=kubernetes:audit` or `sourcetype=kube:objects`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Periodically inventory pods in `istio-injection=enabled` namespaces (CI job or Splunk scheduled search against cached object JSON). Flag workloads missing `istio-proxy`. Optionally parse audit logs for pod create with webhook bypass. Integrate with policy-as-code to fail builds that skip mesh membership.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=containers sourcetype="kubernetes:audit" objectRef.resource="pods"
| eval has_sidecar=if(match(_raw, "istio-proxy"), 1, 0)
| join type=left max=1 objectRef.namespace [
    search index=containers sourcetype="kube:objects" kind="Namespace"
    | eval inject=if(match(_raw, "istio-injection=enabled"), 1, 0)
    | stats max(inject) as should_inject by metadata.name
    | rename metadata.name as objectRef.namespace
]
| where should_inject=1 AND has_sidecar=0
| stats count by objectRef.namespace, objectRef.name
```

Understanding this SPL

**Sidecar Injection Validation** — Pods without injection bypass mesh policy and mTLS; continuous validation enforces namespace labels and mutating webhook coverage.

Documented **Data sources**: `sourcetype=kubernetes:audit` or `sourcetype=kube:objects`. **App/TA** (typical add-on context): Kubernetes API audit or controller logs, `kube:objects` snapshot. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: containers; **sourcetype**: kubernetes:audit. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=containers, sourcetype="kubernetes:audit". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **has_sidecar** — often to normalize units, derive a ratio, or prepare for thresholds.
• Joins to a subsearch with `join` — set `max=` to match cardinality and avoid silent truncation.
• Filters the current rows with `where should_inject=1 AND has_sidecar=0` — typically the threshold or rule expression for this monitoring goal.
• `stats` rolls up events into metrics; results are split **by objectRef.namespace, objectRef.name** so each row reflects one combination of those dimensions.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. For Kubernetes and OpenShift data, sample rows should line up with what you see from the cluster command-line tool, the Kubernetes Dashboard (or OpenShift console), and your Splunk Add-on for Kubernetes (`Splunk_TA_kubernetes`) or OpenTelemetry collector view of the same objects. Compare with known good and bad scenarios where you have them. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (namespace, pod, missing sidecar), Single value (non-compliant pod count), Trend (compliance %).

## SPL

```spl
index=containers sourcetype="kubernetes:audit" objectRef.resource="pods"
| eval has_sidecar=if(match(_raw, "istio-proxy"), 1, 0)
| join type=left max=1 objectRef.namespace [
    search index=containers sourcetype="kube:objects" kind="Namespace"
    | eval inject=if(match(_raw, "istio-injection=enabled"), 1, 0)
    | stats max(inject) as should_inject by metadata.name
    | rename metadata.name as objectRef.namespace
]
| where should_inject=1 AND has_sidecar=0
| stats count by objectRef.namespace, objectRef.name
```

## Visualization

Table (namespace, pod, missing sidecar), Single value (non-compliant pod count), Trend (compliance %).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
