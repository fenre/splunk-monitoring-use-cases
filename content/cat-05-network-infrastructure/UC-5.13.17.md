---
id: "5.13.17"
title: "Network Health Score Trending"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.13.17 · Network Health Score Trending

## Description

Tracks the network health score over time to reveal trends, correlate with changes, and establish baselines for anomaly detection.

## Value

Trending the network health score reveals the impact of changes, maintenance windows, and external events on overall network quality.

## Implementation

Enable continuous collection of `cisco:dnac:networkhealth` to `index=catalyst` and retain 90+ days for meaningful baselines. If multiple overlapping events share an hour, `avg(healthScore)` still yields a useful compromise; for stricter control, pre-dedup with `stats latest(healthScore) as healthScore by date_hour` in a `lookup`-backed summary before `timechart`.

## Detailed Implementation

Prerequisites
• **Continuous** `cisco:dnac:networkhealth` with **>90 days** retention for meaningful week-over-week and seasonal baselines.
• Stakeholder agreement that **`timechart` + `avg(healthScore)`** is the official **trend** method (vs. a pre-deduped hourly **latest**).
• A documented **SLO** reference (for example, **“hourly average stays above 85”**) for the line chart’s **visual threshold** in the UI.
• Same API and RBAC context as the **Network Health Score Overview (UC-5.13.16)**.
• `docs/implementation-guide.md` if you schedule **summary indexing** (usually unnecessary at this data volume).

Step 1 — Configure data collection
• **Intent API:** `GET /dna/intent/api/v1/network-health`.
• **TA input name:** **networkhealth**; default poll **900s**; increase only if the controller rate-limits or you hit **HTTP 429**.
• **Volume:** a **small** number of events per day per controller; chart noise usually means **duplicates** or **multiple** clusters in one sourcetype without a split.
• **Key field:** `healthScore` (numeric); confirm it is not extracted as a **string** (`| where isnum(healthScore)` in validation).

Step 2 — Create the search and alert
```spl
index=catalyst sourcetype="cisco:dnac:networkhealth" | timechart span=1h avg(healthScore) as avg_health | eval avg_health=round(avg_health,1)
```

Understanding this SPL (averaging within the hour vs. one poll per hour)
• **`timechart` + `avg(healthScore)`** handles **multiple** summary refreshes inside the same hour; if the TA only sends **one** point per hour, `avg` equals that point.
• If you see **jagged** intra-hour behavior, the TA may be **re-emitting** on sub-hour timers—try **`| bin _time span=1h | stats latest(healthScore) as healthScore by _time | timechart ...`** in an advanced follow-on.
• **Round** to one decimal for readability; keep two for **SLOs** with tight tolerances.
• **Red / yellow** zones on the y-axis: **tune** to **80/90** (examples) per **business risk**—the SPL is intentionally **unclad** in business logic.

**Pipeline walkthrough**
• Hourly buckets **smooth** 15m noise while still catching **afternoon** brownouts in retail and office.
• A **single** line is easy for **exec** slides; pair with a **trellis** if you **split** by cluster in the future (fields permitting).

Step 3 — Validate
• Overlay **known** maintenance: you should see **dips** that **recover** or a **step** after a major release changes scoring.
• **`| timechart count`** in parallel to detect a **day** of **zero** ingest.
• **Compare** a selected hour to the **Catalyst** timeline—expect **1–2 point** deltas at bucket **edges**, not a random walk.
• **M&A / controller merge:** expect a **one-time** level shift; annotate in the runbook so leadership does not misread a platform change as “magic improvement.”

Step 4 — Operationalize
• **Placement:** **center** of **row 1** on a **Catalyst executive** dashboard; default **90-day** with **1-click** to **7d/24h** in tokens.
• **Add** a **delta** or **% change vs prior week** in a second panel using **trendline** or **two** `addinfo`-style searches, not in this **base** SPL.
• **Not for** paging: use **companion** **issue** and **client/device** UCs for operational response; this is **trend** storytelling.
• **Annotation layer:** add **Cisco TAC** case markers for leadership reviews (manual or from SOAR).

Step 5 — Troubleshooting
• **Flat line for days** while the UI moves:** **stale** API cache or the **input** is pointed at a **standby**—verify the **active** cluster URL in the add-on.
• **Gaps:** expired credentials, network loss to the controller, or **search head** in **maintenance**—check `splunkd.log` and **HEC/UF** if applicable.
• **Out-of-range** values: rare **TAC** bugs; **clamp** in presentation and open a case with **Catalyst** logs.
• **Step jump after TA upgrade:** **field** extraction or **parsing** change—`fieldsummary` the week of upgrade.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:networkhealth" | timechart span=1h avg(healthScore) as avg_health | eval avg_health=round(avg_health,1)
```

## Visualization

Line or area timechart of avg_health, reference lines for SLO, annotations for change windows, companion stat of latest versus prior week mean.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
