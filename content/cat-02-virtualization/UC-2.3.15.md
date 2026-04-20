---
id: "2.3.15"
title: "VM Disk Cache Mode Audit"
criticality: "medium"
splunkPillar: "Security"
---

# UC-2.3.15 · VM Disk Cache Mode Audit

## Description

The disk cache mode determines data safety vs. performance. `writeback` is fast but risks data loss on host crash. `none` (O_DIRECT) provides safe passthrough for guests with their own journaling. `writethrough` is safest but slowest. Incorrect cache modes cause either data loss or unnecessary performance penalties.

## Value

The disk cache mode determines data safety vs. performance. `writeback` is fast but risks data loss on host crash. `none` (O_DIRECT) provides safe passthrough for guests with their own journaling. `writethrough` is safest but slowest. Incorrect cache modes cause either data loss or unnecessary performance penalties.

## Implementation

Create scripted input: parse `virsh dumpxml <domain>` to extract `<driver cache='...' io='...' discard='...'/>` for each disk. Run daily. Alert on `cache='unsafe'` (never safe for production). Flag `cache='writeback'` for review — acceptable only if the host has battery-backed write cache. Recommend `cache='none'` for most production workloads.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom scripted input.
• Ensure the following data sources are available: `virsh dumpxml` disk configuration.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Create scripted input: parse `virsh dumpxml <domain>` to extract `<driver cache='...' io='...' discard='...'/>` for each disk. Run daily. Alert on `cache='unsafe'` (never safe for production). Flag `cache='writeback'` for review — acceptable only if the host has battery-backed write cache. Recommend `cache='none'` for most production workloads.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=virtualization sourcetype="kvm_disk_config"
| stats latest(cache_mode) as cache, latest(io_mode) as io, latest(discard) as discard by host, vm_name, disk_target
| eval risk=case(cache="writeback", "High - data loss risk on crash", cache="unsafe", "Critical - no fsync", cache="none", "Safe - direct I/O", cache="writethrough", "Safe - slow", 1==1, "Unknown")
| where cache="writeback" OR cache="unsafe"
| table host, vm_name, disk_target, cache, io, risk
```

Understanding this SPL

**VM Disk Cache Mode Audit** — The disk cache mode determines data safety vs. performance. `writeback` is fast but risks data loss on host crash. `none` (O_DIRECT) provides safe passthrough for guests with their own journaling. `writethrough` is safest but slowest. Incorrect cache modes cause either data loss or unnecessary performance penalties.

Documented **Data sources**: `virsh dumpxml` disk configuration. **App/TA** (typical add-on context): Custom scripted input. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: virtualization; **sourcetype**: kvm_disk_config. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=virtualization, sourcetype="kvm_disk_config". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host, vm_name, disk_target** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **risk** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where cache="writeback" OR cache="unsafe"` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **VM Disk Cache Mode Audit**): table host, vm_name, disk_target, cache, io, risk


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (VM, disk, cache mode, risk), Pie chart (cache mode distribution), Bar chart (risky VMs by host).

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
index=virtualization sourcetype="kvm_disk_config"
| stats latest(cache_mode) as cache, latest(io_mode) as io, latest(discard) as discard by host, vm_name, disk_target
| eval risk=case(cache="writeback", "High - data loss risk on crash", cache="unsafe", "Critical - no fsync", cache="none", "Safe - direct I/O", cache="writethrough", "Safe - slow", 1==1, "Unknown")
| where cache="writeback" OR cache="unsafe"
| table host, vm_name, disk_target, cache, io, risk
```

## Visualization

Table (VM, disk, cache mode, risk), Pie chart (cache mode distribution), Bar chart (risky VMs by host).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
