---
id: "2.3.14"
title: "ZFS Pool Health for Proxmox/KVM"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-2.3.14 · ZFS Pool Health for Proxmox/KVM

## Description

ZFS is the recommended storage backend for Proxmox and many KVM deployments. A degraded ZFS pool means a disk has failed and data is at risk until the pool is resilvered. ZFS capacity above 80% significantly degrades performance due to copy-on-write fragmentation.

## Value

ZFS is the recommended storage backend for Proxmox and many KVM deployments. A degraded ZFS pool means a disk has failed and data is at risk until the pool is resilvered. ZFS capacity above 80% significantly degrades performance due to copy-on-write fragmentation.

## Implementation

Create scripted input: `zpool list -Hp` for capacity and `zpool status` for health. Parse pool name, size, allocated, free, fragmentation, capacity, dedup ratio, and health. Run every 5 minutes. Alert on any non-ONLINE health status. Alert at 80% capacity. Monitor ZFS Event Daemon (ZED) for disk failures and scrub errors.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_nix`, custom scripted input.
• Ensure the following data sources are available: `zpool status`, `zpool list`, ZFS event daemon (ZED).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Create scripted input: `zpool list -Hp` for capacity and `zpool status` for health. Parse pool name, size, allocated, free, fragmentation, capacity, dedup ratio, and health. Run every 5 minutes. Alert on any non-ONLINE health status. Alert at 80% capacity. Monitor ZFS Event Daemon (ZED) for disk failures and scrub errors.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype="zfs_pool_status"
| stats latest(health) as health, latest(capacity_pct) as capacity, latest(fragmentation) as frag_pct by host, pool_name
| where health!="ONLINE" OR capacity > 80
| sort -capacity
| table host, pool_name, health, capacity, frag_pct
```

Understanding this SPL

**ZFS Pool Health for Proxmox/KVM** — ZFS is the recommended storage backend for Proxmox and many KVM deployments. A degraded ZFS pool means a disk has failed and data is at risk until the pool is resilvered. ZFS capacity above 80% significantly degrades performance due to copy-on-write fragmentation.

Documented **Data sources**: `zpool status`, `zpool list`, ZFS event daemon (ZED). **App/TA** (typical add-on context): `Splunk_TA_nix`, custom scripted input. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: zfs_pool_status. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=os, sourcetype="zfs_pool_status". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host, pool_name** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where health!="ONLINE" OR capacity > 80` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
• Pipeline stage (see **ZFS Pool Health for Proxmox/KVM**): table host, pool_name, health, capacity, frag_pct


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Status grid (pool health), Gauge (capacity per pool), Table (pool details), Line chart (capacity trend).

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
index=os sourcetype="zfs_pool_status"
| stats latest(health) as health, latest(capacity_pct) as capacity, latest(fragmentation) as frag_pct by host, pool_name
| where health!="ONLINE" OR capacity > 80
| sort -capacity
| table host, pool_name, health, capacity, frag_pct
```

## Visualization

Status grid (pool health), Gauge (capacity per pool), Table (pool details), Line chart (capacity trend).

## References

- [Splunk_TA_nix](https://splunkbase.splunk.com/app/833)
