---
id: "3.3.1"
title: "Cluster Version & Upgrade Status"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-3.3.1 · Cluster Version & Upgrade Status

## Description

OpenShift upgrades can stall. Tracking upgrade progress and version across clusters ensures consistency and support compliance.

## Value

OpenShift upgrades can stall. Tracking upgrade progress and version across clusters ensures consistency and support compliance.

## Implementation

Create scripted input querying `oc get clusterversion -o json`. Run hourly. Alert when upgrade is progressing but stalled (>2 hours without progress).

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom API input (ClusterVersion API).
• Ensure the following data sources are available: ClusterVersion resource, OpenShift events.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Create scripted input querying `oc get clusterversion -o json`. Run hourly. Alert when upgrade is progressing but stalled (>2 hours without progress).

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=openshift sourcetype="openshift:clusterversion"
| stats latest(version) as version, latest(progressing) as upgrading, latest(available) as available by cluster
| table cluster version upgrading available
```

Understanding this SPL

**Cluster Version & Upgrade Status** — OpenShift upgrades can stall. Tracking upgrade progress and version across clusters ensures consistency and support compliance.

Documented **Data sources**: ClusterVersion resource, OpenShift events. **App/TA** (typical add-on context): Custom API input (ClusterVersion API). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: openshift; **sourcetype**: openshift:clusterversion. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=openshift, sourcetype="openshift:clusterversion". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by cluster** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Pipeline stage (see **Cluster Version & Upgrade Status**): table cluster version upgrading available


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (cluster, version, status), Status indicator.

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
index=openshift sourcetype="openshift:clusterversion"
| stats latest(version) as version, latest(progressing) as upgrading, latest(available) as available by cluster
| table cluster version upgrading available
```

## Visualization

Table (cluster, version, status), Status indicator.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
