<!-- AUTO-GENERATED from UC-5.13.4.json — DO NOT EDIT -->

---
id: "5.13.4"
title: "Device Health by Category (Access/Distribution/Core/Router/Wireless)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.13.4 · Device Health by Category (Access/Distribution/Core/Router/Wireless)

## Description

Breaks down device health by network role category (access, distribution, core, router, wireless controller), revealing which infrastructure tier is most affected.

## Value

Enables targeted remediation by identifying which tier of the network architecture is contributing most to overall health degradation.

## Implementation

Complete UC-5.13.1 baseline ingestion first, then use this search for role-tier rollups. Ensure `deviceType` is populated in your events; if your naming differs, map values with a lookup. Pin the panel to a dashboard for monthly operations reviews and capacity planning.

## Detailed Implementation

Prerequisites
• **UC-5.13.1** live: `cisco:dnac:devicehealth` in `index=catalyst` from the **devicehealth** input (`GET /dna/intent/api/v1/device-health`).
• Cisco Catalyst Add-on (Splunkbase 7538); service account with **`NETWORK-ADMIN-ROLE`** or **`SUPER-ADMIN-ROLE`**.
• `deviceType` must be present and stable—if Catalyst Center re-labels a family after an upgrade, maintain a **lookup** from old to new strings for trending.
• See `docs/implementation-guide.md` for app layout and credentials.

Step 1 — Configure data collection
• **TA input:** **devicehealth**; sourcetype `cisco:dnac:devicehealth`; default **900s** poll.
• **Volume:** ~one event per managed device per successful poll; this UC aggregates by **`deviceType`**, not per-site.
• **Tuning note:** the title lists architectural tiers (access, distribution, core, wireless); your data uses Catalyst Center’s **`deviceType`** labels—map them in a dashboard footnote if names differ (for example `C9300` vs “Access”).

Step 2 — Create the search and alert
```spl
index=catalyst sourcetype="cisco:dnac:devicehealth" | stats avg(overallHealth) as avg_health count as device_count count(eval(overallHealth<50)) as unhealthy_count by deviceType | eval unhealthy_pct=round(unhealthy_count*100/device_count,1) | sort -unhealthy_pct
```

Understanding this SPL
• **`unhealthy_count`** uses **`overallHealth<50`** to align with the **Poor** band in common Assurance views—raise to **<70** if your SLOs require it.
• **`unhealthy_pct`** is the share of devices of that type below the threshold, comparable across small and large populations.
• **Sort** descending on **`unhealthy_pct`** lists the **worst tier first**; pair with a **bar chart** of **`avg_health`** for a second opinion when averages and percentages disagree.

**Pipeline walkthrough**
• `stats` rolls **avg**, **count**, and **sub-threshold count** by **`deviceType`**.
• `eval` computes **percentage**; `sort` orders tiers for NOC triage, then **drill to UC-5.13.1** for device names.

Step 3 — Validate
• `| stats values(deviceType) count` over 7d to catch unexpected **new** type strings after upgrades.
• Manually sum device counts in Catalyst **Inventory** by family and compare to **`device_count`** for a major `deviceType`.
• If **`unhealthy_pct` is 0** for all types but the fleet feels bad, your threshold may be too loose or **`overallHealth`** is missing—`fieldsummary overallHealth` first.

Step 4 — Operationalize
• **Dashboard:** **bar** of **`unhealthy_pct`** and **table** of **`avg_health`**, **device_count**, **unhealthy_count**; place on a **tier health** row above site-level **UC-5.13.5**.
• **Alerting (optional):** fire when **`unhealthy_pct`** for a **critical** `deviceType` (for example **core**) exceeds a **lookup**-defined cap—**not** usually for every tier at once without tuning.
• **Runbook:** assign backlog owners **by device family** and link to **Catalyst Center** Assurance **device health** filtered by that type.

Step 5 — Troubleshooting
• **Missing `deviceType`:** re-sync **inventory**; check raw JSON; add **coalesce** or **lookup** if the TA maps alternate keys.
• **100% unhealthy for a type with one device:** use **min device_count** in alert logic or **exclude** lab types via **`where device_count>5`** in scheduled searches.
• **Stale rows:** if **`_time`** is old, the **devicehealth** input or API token may be failing—check **`splunkd.log`** and Catalyst **API** health.


## SPL

```spl
index=catalyst sourcetype="cisco:dnac:devicehealth" | stats avg(overallHealth) as avg_health count as device_count count(eval(overallHealth<50)) as unhealthy_count by deviceType | eval unhealthy_pct=round(unhealthy_count*100/device_count,1) | sort -unhealthy_pct
```

## Visualization

Bar chart (unhealthy_pct or avg_health by deviceType), table with device_count and unhealthy_count, pie chart of tier mix when combined with a fleet summary.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
- [Catalyst Center Integration Guide](docs/guides/catalyst-center.md)
