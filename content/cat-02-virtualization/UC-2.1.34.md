---
id: "2.1.34"
title: "Orphaned VMDK Files on Datastores"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-2.1.34 · Orphaned VMDK Files on Datastores

## Description

When VMs are deleted without cleaning up their disk files, or when snapshots leave behind delta VMDKs, orphaned files accumulate and waste datastore space. In large environments, orphaned files can consume terabytes of storage that cannot be identified through normal VM inventory.

## Value

When VMs are deleted without cleaning up their disk files, or when snapshots leave behind delta VMDKs, orphaned files accumulate and waste datastore space. In large environments, orphaned files can consume terabytes of storage that cannot be identified through normal VM inventory.

## Implementation

Create a PowerCLI scripted input that lists all VMDK files on each datastore and compares against registered VM disk paths. Files not attached to any VM are orphans. Run weekly during off-peak hours (datastore browsing is I/O intensive). Alert when total orphan size exceeds 100GB per datastore.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_vmware`, custom scripted input.
• Ensure the following data sources are available: Custom scripted input (datastore file browser vs VM inventory comparison).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Create a PowerCLI scripted input that lists all VMDK files on each datastore and compares against registered VM disk paths. Files not attached to any VM are orphans. Run weekly during off-peak hours (datastore browsing is I/O intensive). Alert when total orphan size exceeds 100GB per datastore.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=vmware sourcetype="datastore_orphans"
| stats sum(size_gb) as total_waste_gb, count as orphan_count by datastore
| sort -total_waste_gb
| table datastore, orphan_count, total_waste_gb
```

Understanding this SPL

**Orphaned VMDK Files on Datastores** — When VMs are deleted without cleaning up their disk files, or when snapshots leave behind delta VMDKs, orphaned files accumulate and waste datastore space. In large environments, orphaned files can consume terabytes of storage that cannot be identified through normal VM inventory.

Documented **Data sources**: Custom scripted input (datastore file browser vs VM inventory comparison). **App/TA** (typical add-on context): `Splunk_TA_vmware`, custom scripted input. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: vmware; **sourcetype**: datastore_orphans. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=vmware, sourcetype="datastore_orphans". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by datastore** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
• Pipeline stage (see **Orphaned VMDK Files on Datastores**): table datastore, orphan_count, total_waste_gb


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (datastore, orphan count, wasted GB), Bar chart (waste by datastore), Single value (total waste).

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
index=vmware sourcetype="datastore_orphans"
| stats sum(size_gb) as total_waste_gb, count as orphan_count by datastore
| sort -total_waste_gb
| table datastore, orphan_count, total_waste_gb
```

## Visualization

Table (datastore, orphan count, wasted GB), Bar chart (waste by datastore), Single value (total waste).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
