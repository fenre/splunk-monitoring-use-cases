---
id: "2.2.14"
title: "VM Resource Metering for Chargeback"
criticality: "low"
splunkPillar: "Observability"
---

# UC-2.2.14 · VM Resource Metering for Chargeback

## Description

Hyper-V's built-in resource metering tracks per-VM CPU, memory, disk, and network consumption for chargeback and showback. Without metering data, cost allocation is based on allocation rather than actual usage — leading to disputes and over-provisioning.

## Value

Hyper-V's built-in resource metering tracks per-VM CPU, memory, disk, and network consumption for chargeback and showback. Without metering data, cost allocation is based on allocation rather than actual usage — leading to disputes and over-provisioning.

## Implementation

Enable resource metering: `Enable-VMResourceMetering -VMName *`. Create scripted input: `Measure-VM | Select VMName, AvgCPU, AvgRAM, TotalDisk*, AggregatedAverageNormalizedIOPS, AggregatedDiskDataRead, AggregatedDiskDataWritten, NetworkMeteredTrafficReport`. Run hourly. Maintain cost-per-unit lookups for chargeback calculations.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows` (Hyper-V), custom scripted input.
• Ensure the following data sources are available: PowerShell scripted input (`Measure-VM`).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable resource metering: `Enable-VMResourceMetering -VMName *`. Create scripted input: `Measure-VM | Select VMName, AvgCPU, AvgRAM, TotalDisk*, AggregatedAverageNormalizedIOPS, AggregatedDiskDataRead, AggregatedDiskDataWritten, NetworkMeteredTrafficReport`. Run hourly. Maintain cost-per-unit lookups for chargeback calculations.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=hyperv sourcetype="hyperv_metering"
| bin _time span=1d
| stats avg(avg_cpu_mhz) as avg_cpu, avg(avg_memory_mb) as avg_mem, sum(disk_bytes_read) as disk_read, sum(disk_bytes_written) as disk_write, sum(network_bytes_in) as net_in, sum(network_bytes_out) as net_out by vm_name, host, _time
| eval disk_total_gb=round((disk_read+disk_write)/1073741824, 2)
| eval net_total_gb=round((net_in+net_out)/1073741824, 2)
| table _time, vm_name, host, avg_cpu, avg_mem, disk_total_gb, net_total_gb
```

Understanding this SPL

**VM Resource Metering for Chargeback** — Hyper-V's built-in resource metering tracks per-VM CPU, memory, disk, and network consumption for chargeback and showback. Without metering data, cost allocation is based on allocation rather than actual usage — leading to disputes and over-provisioning.

Documented **Data sources**: PowerShell scripted input (`Measure-VM`). **App/TA** (typical add-on context): `Splunk_TA_windows` (Hyper-V), custom scripted input. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: hyperv; **sourcetype**: hyperv_metering. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=hyperv, sourcetype="hyperv_metering". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Discretizes time or numeric ranges with `bin`/`bucket`.
• `stats` rolls up events into metrics; results are split **by vm_name, host, _time** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **disk_total_gb** — often to normalize units, derive a ratio, or prepare for thresholds.
• `eval` defines or adjusts **net_total_gb** — often to normalize units, derive a ratio, or prepare for thresholds.
• Pipeline stage (see **VM Resource Metering for Chargeback**): table _time, vm_name, host, avg_cpu, avg_mem, disk_total_gb, net_total_gb


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (VM, resource usage, estimated cost), Bar chart (cost by department), Timechart (usage trending).

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
index=hyperv sourcetype="hyperv_metering"
| bin _time span=1d
| stats avg(avg_cpu_mhz) as avg_cpu, avg(avg_memory_mb) as avg_mem, sum(disk_bytes_read) as disk_read, sum(disk_bytes_written) as disk_write, sum(network_bytes_in) as net_in, sum(network_bytes_out) as net_out by vm_name, host, _time
| eval disk_total_gb=round((disk_read+disk_write)/1073741824, 2)
| eval net_total_gb=round((net_in+net_out)/1073741824, 2)
| table _time, vm_name, host, avg_cpu, avg_mem, disk_total_gb, net_total_gb
```

## Visualization

Table (VM, resource usage, estimated cost), Bar chart (cost by department), Timechart (usage trending).

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
