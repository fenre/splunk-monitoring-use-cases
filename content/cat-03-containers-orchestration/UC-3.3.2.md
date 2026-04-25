<!-- AUTO-GENERATED from UC-3.3.2.json — DO NOT EDIT -->

---
id: "3.3.2"
title: "Operator Degraded Detection"
criticality: "high"
splunkPillar: "Observability"
---

# UC-3.3.2 · Operator Degraded Detection

## Description

Cluster operators manage core OpenShift components (networking, ingress, monitoring, authentication). Degraded operators mean partial cluster functionality loss.

## Value

Cluster operators manage core OpenShift components (networking, ingress, monitoring, authentication). Degraded operators mean partial cluster functionality loss.

## Implementation

Scripted input: `oc get clusteroperators -o json`. Run every 300 seconds. Alert when any operator reports `Degraded=True` or `Available=False`.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom API input.
• Ensure the following data sources are available: ClusterOperator resources.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Scripted input: `oc get clusteroperators -o json`. Run every 300 seconds. Alert when any operator reports `Degraded=True` or `Available=False`.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=openshift sourcetype="openshift:clusteroperator"
| where degraded="True" OR available="False"
| table _time cluster operator degraded available message
| sort -_time
```

Understanding this SPL

**Operator Degraded Detection** — Cluster operators manage core OpenShift components (networking, ingress, monitoring, authentication). Degraded operators mean partial cluster functionality loss.

Documented **Data sources**: ClusterOperator resources. **App/TA** (typical add-on context): Custom API input. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: openshift; **sourcetype**: openshift:clusteroperator. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=openshift, sourcetype="openshift:clusteroperator". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where degraded="True" OR available="False"` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Operator Degraded Detection**): table _time cluster operator degraded available message
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. For Kubernetes and OpenShift data, sample rows should line up with what you see from the cluster command-line tool, the Kubernetes Dashboard (or OpenShift console), and your Splunk Add-on for Kubernetes (`Splunk_TA_kubernetes`) or OpenTelemetry collector view of the same objects. Compare with known good and bad scenarios where you have them. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Operator status grid (green/yellow/red), Table with details, Timeline.

Scripted input (generic example)
This use case relies on a scripted input. In the app's local/inputs.conf add a stanza such as:

```ini
[script://$SPLUNK_HOME/etc/apps/YourApp/bin/collect.sh]
interval = 300
sourcetype = your_sourcetype
index = main
disabled = 0
```

The script should print one event per line (e.g. key=value). Example minimal script (bash):

```bash
#!/usr/bin/env bash
# Output metrics or events, one per line
echo "metric=value timestamp=$(date +%s)"
```

For full details (paths, scheduling, permissions), see the Implementation guide: docs/implementation-guide.md

## SPL

```spl
index=openshift sourcetype="openshift:clusteroperator"
| where degraded="True" OR available="False"
| table _time cluster operator degraded available message
| sort -_time
```

## Visualization

Operator status grid (green/yellow/red), Table with details, Timeline.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
