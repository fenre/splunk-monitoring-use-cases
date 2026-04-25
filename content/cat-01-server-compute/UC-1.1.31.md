<!-- AUTO-GENERATED from UC-1.1.31.json — DO NOT EDIT -->

---
id: "1.1.31"
title: "Hugepage Allocation and Usage"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-1.1.31 · Hugepage Allocation and Usage

## Description

Hugepage contention or allocation failures impact database and large memory workload performance.

## Value

Hugepage contention or allocation failures impact database and large memory workload performance.

## Implementation

Create a scripted input parsing /proc/meminfo for hugepage metrics. Track HugePages_Total, HugePages_Free, HugePages_Rsvd, and HugePages_Surp. Alert when free hugepages fall below 10% or when failed allocations occur.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_nix, custom scripted input`.
• Ensure the following data sources are available: `sourcetype=custom:hugepages, /proc/meminfo`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Create a scripted input parsing /proc/meminfo for hugepage metrics. Track HugePages_Total, HugePages_Free, HugePages_Rsvd, and HugePages_Surp. Alert when free hugepages fall below 10% or when failed allocations occur.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=custom:hugepages host=*
| stats avg(HugePages_Total) as total, avg(HugePages_Free) as free by host
| eval usage_pct=(total-free)/total*100
| where usage_pct > 90
```

Understanding this SPL

**Hugepage Allocation and Usage** — Hugepage contention or allocation failures impact database and large memory workload performance.

Documented **Data sources**: `sourcetype=custom:hugepages, /proc/meminfo`. **App/TA** (typical add-on context): `Splunk_TA_nix, custom scripted input`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: custom:hugepages. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=os, sourcetype=custom:hugepages. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host** so each row reflects one combination of those dimensions.
• `eval` defines or adjusts **usage_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where usage_pct > 90` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
On the host, compare with `top`, `htop`, `vmstat`, `iostat`, or `sar` as appropriate to this use case. For log-only detections, compare with the relevant file under `/var/log` (or `journalctl`) on a test host. Confirm that indexed event counts and field values line up with what you see on the system and that your role can search the right indexes and fields.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Gauge, Single Value

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
index=os sourcetype=custom:hugepages host=*
| stats avg(HugePages_Total) as total, avg(HugePages_Free) as free by host
| eval usage_pct=(total-free)/total*100
| where usage_pct > 90
```

## Visualization

Gauge, Single Value

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
