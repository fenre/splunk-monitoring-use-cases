<!-- AUTO-GENERATED from UC-2.3.12.json — DO NOT EDIT -->

---
id: "2.3.12"
title: "Proxmox Cluster Corosync and Quorum Health"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-2.3.12 · Proxmox Cluster Corosync and Quorum Health

## Description

Proxmox clusters use Corosync for node communication and quorum. A split-brain scenario can cause data corruption on shared storage. Nodes losing corosync connectivity cannot access cluster resources, and quorum loss stops all HA-protected VMs. Early detection of communication issues prevents cluster-wide outages.

## Value

Proxmox clusters use Corosync for node communication and quorum. A split-brain scenario can cause data corruption on shared storage. Nodes losing corosync connectivity cannot access cluster resources, and quorum loss stops all HA-protected VMs. Early detection of communication issues prevents cluster-wide outages.

## Implementation

Create scripted input: `pvecm status` to get quorum state, node count, and ring status. Also monitor Corosync syslog for retransmit failures and membership changes. Alert immediately on quorum loss. Alert when any node goes offline. Monitor Corosync ring latency — high latency indicates network issues between nodes.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom scripted input, syslog.
• Ensure the following data sources are available: Corosync logs, `pvecm status`, Proxmox cluster API.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Create scripted input: `pvecm status` to get quorum state, node count, and ring status. Also monitor Corosync syslog for retransmit failures and membership changes. Alert immediately on quorum loss. Alert when any node goes offline. Monitor Corosync ring latency — high latency indicates network issues between nodes.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=virtualization sourcetype="proxmox_cluster"
| stats latest(quorate) as quorum, latest(total_nodes) as total, latest(online_nodes) as online by cluster_name
| eval quorum_ok=if(quorum="Yes", "OK", "CRITICAL")
| eval nodes_ok=if(online=total, "All Online", online . "/" . total . " Online")
| table cluster_name, quorum_ok, nodes_ok, total, online
```

Understanding this SPL

**Proxmox Cluster Corosync and Quorum Health** — Proxmox clusters use Corosync for node communication and quorum. A split-brain scenario can cause data corruption on shared storage. Nodes losing corosync connectivity cannot access cluster resources, and quorum loss stops all HA-protected VMs. Early detection of communication issues prevents cluster-wide outages.

Documented **Data sources**: Corosync logs, `pvecm status`, Proxmox cluster API. **App/TA** (typical add-on context): Custom scripted input, syslog. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: virtualization; **sourcetype**: proxmox_cluster. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=virtualization, sourcetype="proxmox_cluster". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by cluster_name** so each row reflects one combination of those dimensions.
• `eval` defines or adjusts **quorum_ok** — often to normalize units, derive a ratio, or prepare for thresholds.
• `eval` defines or adjusts **nodes_ok** — often to normalize units, derive a ratio, or prepare for thresholds.
• Pipeline stage (see **Proxmox Cluster Corosync and Quorum Health**): table cluster_name, quorum_ok, nodes_ok, total, online

Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Status grid (node health), Single value (quorum status), Timeline (membership changes).

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
index=virtualization sourcetype="proxmox_cluster"
| stats latest(quorate) as quorum, latest(total_nodes) as total, latest(online_nodes) as online by cluster_name
| eval quorum_ok=if(quorum="Yes", "OK", "CRITICAL")
| eval nodes_ok=if(online=total, "All Online", online . "/" . total . " Online")
| table cluster_name, quorum_ok, nodes_ok, total, online
```

## Visualization

Status grid (node health), Single value (quorum status), Timeline (membership changes).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
