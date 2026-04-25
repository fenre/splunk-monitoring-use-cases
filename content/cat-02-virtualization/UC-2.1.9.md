<!-- AUTO-GENERATED from UC-2.1.9.json — DO NOT EDIT -->

---
id: "2.1.9"
title: "VM Sprawl Detection"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-2.1.9 · VM Sprawl Detection

## Description

Orphaned, powered-off, or idle VMs waste storage, IP addresses, backup capacity, and licenses. Regular cleanup frees significant resources.

## Value

Orphaned, powered-off, or idle VMs waste storage, IP addresses, backup capacity, and licenses. Regular cleanup frees significant resources.

## Implementation

Run weekly report on powered-off VMs >30 days. Also identify idle VMs: powered on but CPU usage <5% and network <1Kbps consistently. Send reports to VM owners for review.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_vmware`.
• Ensure the following data sources are available: `sourcetype=vmware:inv:vm`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Run weekly report on powered-off VMs >30 days. Also identify idle VMs: powered on but CPU usage <5% and network <1Kbps consistently. Send reports to VM owners for review.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=vmware sourcetype="vmware:inv:vm"
| where power_state="poweredOff"
| eval days_off = round((now() - strptime(lastPowerOffTime, "%Y-%m-%dT%H:%M:%S")) / 86400, 0)
| where days_off > 30
| table vm_name, host, days_off, numCpu, memoryMB, storage_committed
| sort -days_off
```

Understanding this SPL

**VM Sprawl Detection** — Orphaned, powered-off, or idle VMs waste storage, IP addresses, backup capacity, and licenses. Regular cleanup frees significant resources.

Documented **Data sources**: `sourcetype=vmware:inv:vm`. **App/TA** (typical add-on context): `Splunk_TA_vmware`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: vmware; **sourcetype**: vmware:inv:vm. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=vmware, sourcetype="vmware:inv:vm". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where power_state="poweredOff"` — typically the threshold or rule expression for this monitoring goal.
• `eval` defines or adjusts **days_off** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where days_off > 30` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **VM Sprawl Detection**): table vm_name, host, days_off, numCpu, memoryMB, storage_committed
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (VM, state, days, resources), Pie chart (powered on vs. off), Bar chart (resource waste by team).

## SPL

```spl
index=vmware sourcetype="vmware:inv:vm"
| where power_state="poweredOff"
| eval days_off = round((now() - strptime(lastPowerOffTime, "%Y-%m-%dT%H:%M:%S")) / 86400, 0)
| where days_off > 30
| table vm_name, host, days_off, numCpu, memoryMB, storage_committed
| sort -days_off
```

## Visualization

Table (VM, state, days, resources), Pie chart (powered on vs. off), Bar chart (resource waste by team).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
