<!-- AUTO-GENERATED from UC-3.3.5.json — DO NOT EDIT -->

---
id: "3.3.5"
title: "Helm Release Drift Detection"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-3.3.5 · Helm Release Drift Detection

## Description

Deployed state differs from declared chart version.

## Value

Deployed state differs from declared chart version.

## Implementation

Scripted input: `helm list -A -o json` (all namespaces). Parse name, namespace, chart (includes version), app_version, status, updated. Run every 600 seconds. Optionally ingest GitOps desired state (Argo CD, Flux) from API or Git. Compare deployed chart version to desired. Alert when drift detected (deployed != desired). Useful for detecting manual changes or failed syncs.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom scripted input (helm list --output json).
• Ensure the following data sources are available: helm list output, GitOps desired state.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Scripted input: `helm list -A -o json` (all namespaces). Parse name, namespace, chart (includes version), app_version, status, updated. Run every 600 seconds. Optionally ingest GitOps desired state (Argo CD, Flux) from API or Git. Compare deployed chart version to desired. Alert when drift detected (deployed != desired). Useful for detecting manual changes or failed syncs.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=k8s (sourcetype="helm:list" OR sourcetype="gitops:desired")
| eval chart_version = mvindex(split(chart, "-"), -1)
| stats values(chart_version) as versions by namespace, name, source
| eval version_count = mvcount(versions)
| where version_count > 1
| table namespace name versions source
```

Understanding this SPL

**Helm Release Drift Detection** — Deployed state differs from declared chart version.

Documented **Data sources**: helm list output, GitOps desired state. **App/TA** (typical add-on context): Custom scripted input (helm list --output json). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: k8s; **sourcetype**: helm:list, gitops:desired. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=k8s, sourcetype="helm:list". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **chart_version** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by namespace, name, source** so each row reflects one combination of those dimensions.
• `eval` defines or adjusts **version_count** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where version_count > 1` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Helm Release Drift Detection**): table namespace name versions source


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. For Kubernetes and OpenShift data, sample rows should line up with what you see from the cluster command-line tool, the Kubernetes Dashboard (or OpenShift console), and your Splunk Add-on for Kubernetes (`Splunk_TA_kubernetes`) or OpenTelemetry collector view of the same objects. Compare with known good and bad scenarios where you have them. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (namespace, release, chart, version, status), Drift indicator (deployed vs desired), Timeline of updates.

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
index=k8s (sourcetype="helm:list" OR sourcetype="gitops:desired")
| eval chart_version = mvindex(split(chart, "-"), -1)
| stats values(chart_version) as versions by namespace, name, source
| eval version_count = mvcount(versions)
| where version_count > 1
| table namespace name versions source
```

## Visualization

Table (namespace, release, chart, version, status), Drift indicator (deployed vs desired), Timeline of updates.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
