<!-- AUTO-GENERATED from UC-2.3.1.json — DO NOT EDIT -->

---
id: "2.3.1"
title: "Guest VM Resource Monitoring"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-2.3.1 · Guest VM Resource Monitoring

## Description

Per-VM resource tracking for capacity planning and performance troubleshooting in KVM environments.

## Value

Per-VM resource tracking for capacity planning and performance troubleshooting in KVM environments.

## Implementation

Create scripted input: `virsh domstats --cpu-total --balloon --interface --block`. Run every 60 seconds. Parse per-VM CPU time, balloon current, block read/write, and net rx/tx.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom scripted input (`virsh domstats`).
• Ensure the following data sources are available: Custom sourcetype from `virsh domstats` or `virt-top`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Create scripted input: `virsh domstats --cpu-total --balloon --interface --block`. Run every 60 seconds. Parse per-VM CPU time, balloon current, block read/write, and net rx/tx.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=virtualization sourcetype=virsh_stats
| stats latest(cpu_pct) as cpu, latest(mem_used_mb) as memory by vm_name, host
| sort -cpu
```

Understanding this SPL

**Guest VM Resource Monitoring** — Per-VM resource tracking for capacity planning and performance troubleshooting in KVM environments.

Documented **Data sources**: Custom sourcetype from `virsh domstats` or `virt-top`. **App/TA** (typical add-on context): Custom scripted input (`virsh domstats`). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: virtualization; **sourcetype**: virsh_stats. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=virtualization, sourcetype=virsh_stats. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by vm_name, host** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table, Line chart per VM, Heatmap.

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
index=virtualization sourcetype=virsh_stats
| stats latest(cpu_pct) as cpu, latest(mem_used_mb) as memory by vm_name, host
| sort -cpu
```

## Visualization

Table, Line chart per VM, Heatmap.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
