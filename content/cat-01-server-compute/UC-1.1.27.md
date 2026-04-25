<!-- AUTO-GENERATED from UC-1.1.27.json — DO NOT EDIT -->

---
id: "1.1.27"
title: "CPU Steal Time Elevation (Virtual Machines)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-1.1.27 · CPU Steal Time Elevation (Virtual Machines)

## Description

High steal time indicates VM is contending with host resources, affecting application performance.

## Value

When a guest loses CPU to 'steal' time, it means the hypervisor or neighbors are eating the host; we surface that so you can move VMs or add host capacity before users feel the drag.

## Implementation

Use Splunk_TA_nix vmstat input which automatically extracts steal time percentage. Create alerts for hosts where average steal time exceeds 5% over a 10-minute window, indicating overcommitment on hypervisor.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_nix`.
• Ensure the following data sources are available: `sourcetype=vmstat`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Use Splunk_TA_nix vmstat input which automatically extracts steal time percentage. Create alerts for hosts where average steal time exceeds 5% over a 10-minute window, indicating overcommitment on hypervisor.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=vmstat host=*
| stats avg(st) as avg_steal_time by host
| where avg_steal_time > 5
```

Understanding this SPL

**CPU Steal Time Elevation (Virtual Machines)** — High steal time indicates VM is contending with host resources, affecting application performance.

Documented **Data sources**: `sourcetype=vmstat`. **App/TA** (typical add-on context): `Splunk_TA_nix`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: vmstat. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=os, sourcetype=vmstat. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host** so each row reflects one combination of those dimensions.
• Filters the current rows with `where avg_steal_time > 5` — typically the threshold or rule expression for this monitoring goal.

Step 3 — Validate
On the host, compare with `top`, `htop`, `vmstat`, `iostat`, or `sar` as appropriate to this use case. For log-only detections, compare with the relevant file under `/var/log` (or `journalctl`) on a test host. Confirm that indexed event counts and field values line up with what you see on the system and that your role can search the right indexes and fields.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Timechart, Gauge

## SPL

```spl
index=os sourcetype=vmstat host=*
| stats avg(st) as avg_steal_time by host
| where avg_steal_time > 5
```

## Visualization

Timechart, Gauge

## References

- [Splunk_TA_nix](https://splunkbase.splunk.com/app/833)
- [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)
