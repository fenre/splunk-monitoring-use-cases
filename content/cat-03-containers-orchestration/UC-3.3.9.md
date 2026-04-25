<!-- AUTO-GENERATED from UC-3.3.9.json — DO NOT EDIT -->

---
id: "3.3.9"
title: "Cluster Version Upgrade Status"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-3.3.9 · Cluster Version Upgrade Status

## Description

Long-running or failing upgrades leave clusters on unsupported versions; monitoring `ClusterVersion` conditions and history pins down stuck machine-config or operator prerequisites.

## Value

Long-running or failing upgrades leave clusters on unsupported versions; monitoring `ClusterVersion` conditions and history pins down stuck machine-config or operator prerequisites.

## Implementation

Parse `status.conditions` (Failing, Progressing, Available) and `status.history[]` from JSON into indexed fields. Alert when `progressing` remains true >2 hours or `Failing=True`. Complements UC-3.3.1 with failure messages from `status.history[].message`.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom API input (`oc get clusterversion version -o json`).
• Ensure the following data sources are available: `sourcetype=openshift:clusterversion`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Parse `status.conditions` (Failing, Progressing, Available) and `status.history[]` from JSON into indexed fields. Alert when `progressing` remains true >2 hours or `Failing=True`. Complements UC-3.3.1 with failure messages from `status.history[].message`.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=openshift sourcetype="openshift:clusterversion"
| stats latest(version) as version, latest(progressing) as upgrading, latest(available) as available, latest(failing) as failing by cluster
| where upgrading="True" OR failing="True" OR available="False"
| table cluster version upgrading failing available
```

Understanding this SPL

**Cluster Version Upgrade Status** — Long-running or failing upgrades leave clusters on unsupported versions; monitoring `ClusterVersion` conditions and history pins down stuck machine-config or operator prerequisites.

Documented **Data sources**: `sourcetype=openshift:clusterversion`. **App/TA** (typical add-on context): Custom API input (`oc get clusterversion version -o json`). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: openshift; **sourcetype**: openshift:clusterversion. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=openshift, sourcetype="openshift:clusterversion". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by cluster** so each row reflects one combination of those dimensions.
• Filters the current rows with `where upgrading="True" OR failing="True" OR available="False"` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Cluster Version Upgrade Status**): table cluster version upgrading failing available


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. For Kubernetes and OpenShift data, sample rows should line up with what you see from the cluster command-line tool, the Kubernetes Dashboard (or OpenShift console), and your Splunk Add-on for Kubernetes (`Splunk_TA_kubernetes`) or OpenTelemetry collector view of the same objects. Compare with known good and bad scenarios where you have them. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Upgrade timeline per cluster, Table (version, phase, message), Single value (clusters not on target channel).

## SPL

```spl
index=openshift sourcetype="openshift:clusterversion"
| stats latest(version) as version, latest(progressing) as upgrading, latest(available) as available, latest(failing) as failing by cluster
| where upgrading="True" OR failing="True" OR available="False"
| table cluster version upgrading failing available
```

## Visualization

Upgrade timeline per cluster, Table (version, phase, message), Single value (clusters not on target channel).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
