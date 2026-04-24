---
id: "5.13.16"
title: "Network Health Score Overview"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.13.16 · Network Health Score Overview

## Description

Displays the overall network health score from Catalyst Center, which aggregates device, client, and application health into a single executive-level metric.

## Value

The network health score is the single most important metric from Catalyst Center — it tells you at a glance whether the network is serving users well.

## Implementation

Install the Cisco Catalyst Add-on for Splunk (Splunkbase 7538) and enable the network health input to `index=catalyst` with sourcetype `cisco:dnac:networkhealth`. Confirm fields `healthScore`, `goodCount`, `badCount`, and `totalCount` in props; poll interval is typically 15 minutes. This panel should mirror the top-level score in the Catalyst Center Assurance UI for a given time.

## Detailed Implementation

Prerequisites
• **networkhealth** sourcetype landing in `catalyst` via the Cisco Catalyst Add-on (Splunkbase 7538).
• Catalyst **2.3.5+** for a stable top-level **`healthScore`** with **`goodCount` / `badCount` / `totalCount`** fields in the API response.
• Agree with leadership which number is the **primary** KPI: **`healthScore`** vs **derived `healthy_pct`**—title the panel to match what **Catalyst Center** already shows in meetings.
• API user with read access to **Assurance** summary objects (same roles as other **Assurance** REST reads in your tenant).
• `docs/implementation-guide.md` for index retention on **low-volume, high-visibility** executive data.

Step 1 — Configure data collection
• **Intent API:** `GET /dna/intent/api/v1/network-health` (cluster-wide **Assurance** summary rollups—not per-device detail).
• **TA input name:** **networkhealth** modular input; sourcetype `cisco:dnac:networkhealth`, index `catalyst`.
• **Default interval:** **900 seconds**; expect **roughly one summary event per poll cycle** per configured scope (not one per switch).
• **Volume:** very **low** compared to device or client feeds—safe to retain **long** for board-level history if policy allows.
• **Key fields to validate:** `healthScore`, `goodCount`, `badCount`, `totalCount` (and any **scope** fields your TA adds, e.g. domain or instance ID).

Step 2 — Create the search and alert
```spl
index=catalyst sourcetype="cisco:dnac:networkhealth" | stats latest(healthScore) as health_score latest(goodCount) as good latest(badCount) as bad latest(totalCount) as total by _time | eval healthy_pct=round(good*100/total,1) | table _time health_score good bad total healthy_pct
```

Understanding this SPL (ratio math, dedup caveats, multi-cluster)
• **`healthy_pct = good*100/total`** is a **directional** “good share” when **`total`** matches the **denominator** Catalyst uses; if the API adds **unknown** or **mixed** states, treat the ratio as a **trend**, not an **audited** headcount.
• **`latest()` by `_time`:** if multiple events share a second, **`dedup`** first; if you run **multiple** Catalyst instances, add a **`by cluster_id`** (or equivalent) once that field exists in your payload.
• **Tuning:** leadership often wants **one row**—append **`| sort 0 - _time | head 1`** in a separate **single-value** panel; this table is for **recent history** snapshots.
• **SLO:** if **`healthScore`** and **`healthy_pct`** disagree slightly, **follow the metric your CIO already cites** from the **Assurance** home page to avoid dueling “truth.”

**Pipeline walkthrough**
• `stats` takes the most recent `healthScore` and the three **count** fields for each event timestamp the TA wrote.
• `eval` turns counts into a **rounded** percentage.
• `table` formats **CSV / PDF**-friendly **exec** exports.

Step 3 — Validate
• Compare **`healthScore`** and **counts** in Splunk to **Catalyst Center > Assurance** top-level **Network health** for the same controller and **time**.
• `| timechart count` of `cisco:dnac:networkhealth`—roughly **four points per hour** on a **15m** poll (fewer if you stretched the interval to **1h**).
• If **`total` is 0** intermittently, re-check when **Assurance** finishes **recomputation** after an upgrade—validate during **business hours** steady state.
• **Sanity:** during a **known incident**, you should see **bad** and **`healthScore`** move in the **expected direction** (even if not pixel-perfect to memory).

Step 4 — Operationalize
• **Dashboard layout:** **KPI row**—**single value** of `health_score` plus this **table** of the last **5–10** rows for the board **packet**.
• **Time picker default:** **30 days**; add a **week-over-week** comparison panel in Dashboard Studio (separate search with **earliest/latest** offset).
• **Drilldown:** buttons to **device** (UC-5.13.1) and **client** (UC-5.13.9) dashboards when the score drops.
• **Export:** **monthly** **PDF** to **change advisory** or **Cisco QBR** slide decks.

Step 5 — Troubleshooting
• **Missing `cisco:dnac:networkhealth`:** **networkhealth** input not enabled, wrong index, or **TA** version rename—search **`index=catalyst` `networkhealth`** broadly.
• **NULL counts:** **Assurance** may still be **initializing** after upgrade—watch **Catalyst** job status, not just Splunk.
• **100% while users complain**—this is a **synthetic** health score: triangulate with **client** and **device** UCs the same hour.
• **`_time` vs API `updateTime`:** for audit, compare raw JSON; Splunk’s `_time` is usually **ingest** unless the **TA** sets it from a JSON field.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:networkhealth" | stats latest(healthScore) as health_score latest(goodCount) as good latest(badCount) as bad latest(totalCount) as total by _time | eval healthy_pct=round(good*100/total,1) | table _time health_score good bad total healthy_pct
```

## Visualization

Single value (health_score and healthy_pct), table for historical snapshots, simple gauge of healthy_pct against an SLO line.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
