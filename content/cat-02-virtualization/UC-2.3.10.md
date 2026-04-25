<!-- AUTO-GENERATED from UC-2.3.10.json — DO NOT EDIT -->

---
id: "2.3.10"
title: "Storage Pool Capacity Monitoring"
criticality: "high"
splunkPillar: "Observability"
---

# UC-2.3.10 · Storage Pool Capacity Monitoring

## Description

Libvirt storage pools (LVM, directory, NFS, Ceph, ZFS) provide disk backing for VMs. A full storage pool prevents new VM creation, snapshot operations, and can cause running VMs to pause when using thin provisioning. Monitoring pool capacity prevents VM outages.

## Value

Libvirt storage pools (LVM, directory, NFS, Ceph, ZFS) provide disk backing for VMs. A full storage pool prevents new VM creation, snapshot operations, and can cause running VMs to pause when using thin provisioning. Monitoring pool capacity prevents VM outages.

## Implementation

Create scripted input: `for pool in $(virsh pool-list --name); do virsh pool-info $pool; done`. Parse capacity, allocation, and available fields. Run every 5 minutes. Alert at 80% (warning) and 90% (critical). Include pool type in output — LVM pools cannot auto-extend, while directory pools grow with the filesystem.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom scripted input.
• Ensure the following data sources are available: `virsh pool-info`, storage pool metrics.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Create scripted input: `for pool in $(virsh pool-list --name); do virsh pool-info $pool; done`. Parse capacity, allocation, and available fields. Run every 5 minutes. Alert at 80% (warning) and 90% (critical). Include pool type in output — LVM pools cannot auto-extend, while directory pools grow with the filesystem.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=virtualization sourcetype=kvm_storage_pools
| eval used_pct=round(used_gb/capacity_gb*100, 1)
| where used_pct > 80
| sort -used_pct
| table host, pool_name, pool_type, capacity_gb, used_gb, used_pct
```

Understanding this SPL

**Storage Pool Capacity Monitoring** — Libvirt storage pools (LVM, directory, NFS, Ceph, ZFS) provide disk backing for VMs. A full storage pool prevents new VM creation, snapshot operations, and can cause running VMs to pause when using thin provisioning. Monitoring pool capacity prevents VM outages.

Documented **Data sources**: `virsh pool-info`, storage pool metrics. **App/TA** (typical add-on context): Custom scripted input. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: virtualization; **sourcetype**: kvm_storage_pools. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=virtualization, sourcetype=kvm_storage_pools. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **used_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where used_pct > 80` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
• Pipeline stage (see **Storage Pool Capacity Monitoring**): table host, pool_name, pool_type, capacity_gb, used_gb, used_pct

Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Gauge (per pool), Table (pool status), Line chart (capacity trend with prediction).

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
index=virtualization sourcetype=kvm_storage_pools
| eval used_pct=round(used_gb/capacity_gb*100, 1)
| where used_pct > 80
| sort -used_pct
| table host, pool_name, pool_type, capacity_gb, used_gb, used_pct
```

## Visualization

Gauge (per pool), Table (pool status), Line chart (capacity trend with prediction).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
