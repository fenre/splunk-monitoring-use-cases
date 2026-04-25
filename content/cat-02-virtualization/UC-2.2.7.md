<!-- AUTO-GENERATED from UC-2.2.7.json — DO NOT EDIT -->

---
id: "2.2.7"
title: "Dynamic Memory Pressure and Effectiveness"
criticality: "high"
splunkPillar: "Observability"
---

# UC-2.2.7 · Dynamic Memory Pressure and Effectiveness

## Description

Dynamic Memory allows Hyper-V to adjust VM memory allocations based on demand. When memory pressure is high, the host reduces VM allocations below their startup RAM — causing in-guest paging. Monitoring reveals whether Dynamic Memory is helping or hurting, and which VMs are being starved.

## Value

Dynamic Memory allows Hyper-V to adjust VM memory allocations based on demand. When memory pressure is high, the host reduces VM allocations below their startup RAM — causing in-guest paging. Monitoring reveals whether Dynamic Memory is helping or hurting, and which VMs are being starved.

## Implementation

Configure Perfmon inputs for `Hyper-V Dynamic Memory - VM` counters. Pressure >100 means the VM wants more memory than it has. Track over time — sustained pressure >80 indicates the VM needs a higher minimum RAM setting. Alert when pressure exceeds 100 for production VMs.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows` (Hyper-V Perfmon inputs).
• Ensure the following data sources are available: `sourcetype=Perfmon:HyperV` (Hyper-V Dynamic Memory - VM).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Configure Perfmon inputs for `Hyper-V Dynamic Memory - VM` counters. Pressure >100 means the VM wants more memory than it has. Track over time — sustained pressure >80 indicates the VM needs a higher minimum RAM setting. Alert when pressure exceeds 100 for production VMs.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=perfmon sourcetype="Perfmon:HyperV" object="Hyper-V Dynamic Memory - VM" (counter="Current Pressure" OR counter="Average Pressure" OR counter="Guest Visible Physical Memory")
| stats avg(eval(if(counter="Current Pressure", Value, null()))) as pressure, avg(eval(if(counter="Guest Visible Physical Memory", Value, null()))) as visible_mb by instance, host
| where pressure > 100
| sort -pressure
| table instance, host, pressure, visible_mb
```

Understanding this SPL

**Dynamic Memory Pressure and Effectiveness** — Dynamic Memory allows Hyper-V to adjust VM memory allocations based on demand. When memory pressure is high, the host reduces VM allocations below their startup RAM — causing in-guest paging. Monitoring reveals whether Dynamic Memory is helping or hurting, and which VMs are being starved.

Documented **Data sources**: `sourcetype=Perfmon:HyperV` (Hyper-V Dynamic Memory - VM). **App/TA** (typical add-on context): `Splunk_TA_windows` (Hyper-V Perfmon inputs). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: perfmon; **sourcetype**: Perfmon:HyperV. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=perfmon, sourcetype="Perfmon:HyperV". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by instance, host** so each row reflects one combination of those dimensions.
• Filters the current rows with `where pressure > 100` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
• Pipeline stage (see **Dynamic Memory Pressure and Effectiveness**): table instance, host, pressure, visible_mb

Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (pressure over time per VM), Table (VMs under pressure), Gauge (average pressure).

## SPL

```spl
index=perfmon sourcetype="Perfmon:HyperV" object="Hyper-V Dynamic Memory - VM" (counter="Current Pressure" OR counter="Average Pressure" OR counter="Guest Visible Physical Memory")
| stats avg(eval(if(counter="Current Pressure", Value, null()))) as pressure, avg(eval(if(counter="Guest Visible Physical Memory", Value, null()))) as visible_mb by instance, host
| where pressure > 100
| sort -pressure
| table instance, host, pressure, visible_mb
```

## Visualization

Line chart (pressure over time per VM), Table (VMs under pressure), Gauge (average pressure).

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
