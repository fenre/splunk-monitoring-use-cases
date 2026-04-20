---
id: "2.3.17"
title: "Proxmox VE Cluster Monitoring"
criticality: "high"
splunkPillar: "Observability"
---

# UC-2.3.17 · Proxmox VE Cluster Monitoring

## Description

Node status, storage usage, and HA fence events for Proxmox VE clusters. Ensures all nodes are online, storage is healthy, and HA operations complete successfully. Critical for multi-node Proxmox deployments.

## Value

Node status, storage usage, and HA fence events for Proxmox VE clusters. Ensures all nodes are online, storage is healthy, and HA operations complete successfully. Critical for multi-node Proxmox deployments.

## Implementation

Create scripted input polling Proxmox API: `GET /api2/json/cluster/status` for node membership and quorum; `GET /api2/json/nodes/{node}/storage` for storage usage; `GET /api2/json/cluster/ha/status` for HA resources. Authenticate via API token or ticket. Run every 60 seconds. Alert on node offline, quorum loss, or storage >85% used. Correlate with Corosync logs for fence events.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom (Proxmox API input).
• Ensure the following data sources are available: Proxmox REST API (`/api2/json/cluster/status`), cluster resources, HA manager.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Create scripted input polling Proxmox API: `GET /api2/json/cluster/status` for node membership and quorum; `GET /api2/json/nodes/{node}/storage` for storage usage; `GET /api2/json/cluster/ha/status` for HA resources. Authenticate via API token or ticket. Run every 60 seconds. Alert on node offline, quorum loss, or storage >85% used. Correlate with Corosync logs for fence events.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=virtualization sourcetype="proxmox_cluster_status"
| stats latest(node) as node, latest(status) as status, latest(quorum) as quorum, latest(name) as cluster_name by node
| eval node_ok = if(status="online", "OK", "CRITICAL")
| where node_ok="CRITICAL" OR quorum!="1"
| table cluster_name, node, status, quorum, node_ok
```

Understanding this SPL

**Proxmox VE Cluster Monitoring** — Node status, storage usage, and HA fence events for Proxmox VE clusters. Ensures all nodes are online, storage is healthy, and HA operations complete successfully. Critical for multi-node Proxmox deployments.

Documented **Data sources**: Proxmox REST API (`/api2/json/cluster/status`), cluster resources, HA manager. **App/TA** (typical add-on context): Custom (Proxmox API input). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: virtualization; **sourcetype**: proxmox_cluster_status. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=virtualization, sourcetype="proxmox_cluster_status". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by node** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **node_ok** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where node_ok="CRITICAL" OR quorum!="1"` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Proxmox VE Cluster Monitoring**): table cluster_name, node, status, quorum, node_ok


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Status grid (node health per cluster), Table (storage usage by node), Timeline (HA fence events).

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
index=virtualization sourcetype="proxmox_cluster_status"
| stats latest(node) as node, latest(status) as status, latest(quorum) as quorum, latest(name) as cluster_name by node
| eval node_ok = if(status="online", "OK", "CRITICAL")
| where node_ok="CRITICAL" OR quorum!="1"
| table cluster_name, node, status, quorum, node_ok
```

## Visualization

Status grid (node health per cluster), Table (storage usage by node), Timeline (HA fence events).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
