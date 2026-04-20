---
id: "3.2.31"
title: "Sidecar Injection Validation"
criticality: "medium"
splunkPillar: "Security"
---

# UC-3.2.31 · Sidecar Injection Validation

## Description

Ensures service mesh or security sidecars are present where policy requires—avoiding accidental unencrypted east-west traffic.

## Value

Ensures service mesh or security sidecars are present where policy requires—avoiding accidental unencrypted east-west traffic.

## Implementation

Periodically snapshot pod container lists and namespace labels (`istio-injection`, etc.). Flag mismatches. Integrate with CI to fail deploys that skip injection in labeled namespaces.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: kube-state-metrics, policy controller (optional).
• Ensure the following data sources are available: `sourcetype=kube:pod:meta`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Periodically snapshot pod container lists and namespace labels (`istio-injection`, etc.). Flag mismatches. Integrate with CI to fail deploys that skip injection in labeled namespaces.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=k8s sourcetype="kube:pod:meta"
| eval has_proxy=if(match(container_names, "(istio-proxy|linkerd-proxy|envoy)"),1,0)
| where namespace_injection_enabled=1 AND has_proxy=0
| table namespace pod_name container_names
```

Understanding this SPL

**Sidecar Injection Validation** — Ensures service mesh or security sidecars are present where policy requires—avoiding accidental unencrypted east-west traffic.

Documented **Data sources**: `sourcetype=kube:pod:meta`. **App/TA** (typical add-on context): kube-state-metrics, policy controller (optional). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: k8s; **sourcetype**: kube:pod:meta. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=k8s, sourcetype="kube:pod:meta". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **has_proxy** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where namespace_injection_enabled=1 AND has_proxy=0` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Sidecar Injection Validation**): table namespace pod_name container_names


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (namespace, pod, missing sidecar), Compliance %, Bar chart by team.

## SPL

```spl
index=k8s sourcetype="kube:pod:meta"
| eval has_proxy=if(match(container_names, "(istio-proxy|linkerd-proxy|envoy)"),1,0)
| where namespace_injection_enabled=1 AND has_proxy=0
| table namespace pod_name container_names
```

## Visualization

Table (namespace, pod, missing sidecar), Compliance %, Bar chart by team.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
