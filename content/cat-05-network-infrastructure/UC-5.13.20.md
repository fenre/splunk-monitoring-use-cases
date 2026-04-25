<!-- AUTO-GENERATED from UC-5.13.20.json — DO NOT EDIT -->

---
id: "5.13.20"
title: "Network Health Score Anomaly Detection"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.13.20 · Network Health Score Anomaly Detection

## Description

Applies statistical anomaly detection to the network health score, identifying significant deviations from the historical baseline that may indicate emerging issues.

## Value

Fixed thresholds for network health may not account for normal variations. Anomaly detection catches unusual drops relative to your network's specific baseline.

## Implementation

Requires UC-5.13.16 and enough history for UC-5.13.17 to establish variance. The `eventstats` here runs across the whole result set, so use a long lookback and watch for missing hours that can inflate `stdev`. Consider seasonal baselines in a follow-on if the network’s score drifts with quarters or school terms.

## Detailed Implementation

Prerequisites
• **networkhealth** feed with continuous `cisco:dnac:networkhealth` in `index=catalyst` (Cisco Catalyst Add-on 7538).
• **UC-5.13.16** and **UC-5.13.17** to validate the basic score and a simple trend before you add statistics.
• **Rule of thumb:** use a **7–30 day** lookback in tests so `eventstats` has enough **hourly** buckets; a **single day** window makes **baseline** and **stdev** unstable.
• Document that this technique uses **all rows in the search job** for **baseline/stdev**—it is a **tactical** NOC view, not a pre-trained **ML** model.
• `docs/implementation-guide.md` for scheduled search limits and **search head** load.

Step 1 — Configure data collection
• **API:** `GET /dna/intent/api/v1/network-health`; **input** **networkhealth**; **sourcetype** `cisco:dnac:networkhealth`.
• **Interval:** **900s** typical; if you have **sub-hour** re-emits, `avg(healthScore)` in an hour still behaves sensibly, but check for **duplicate** timestamps in validation.
• **Key field:** `healthScore` must be **numeric** (`| where isnum(healthScore)` in QA).

Step 2 — Create the search and report
```spl
index=catalyst sourcetype="cisco:dnac:networkhealth" | bin _time span=1h | stats avg(healthScore) as health by _time | eventstats avg(health) as baseline stdev(health) as stdev_health | where health < (baseline - 2*stdev_health) AND stdev_health > 0 | eval deviation=round((baseline-health)/stdev_health,1) | sort -deviation
```

Understanding this SPL (same-window stats, 2-sigma, caveats)
• **`eventstats` baseline/stdev** are computed from **all hourly rows returned**; changing the time picker **changes** the “normal” line—set expectations in the runbook.
• **Guard `stdev_health > 0`** avoids divide-by-near-zero noise when the score is **flat** for days.
• **Tune** the **2x** multiplier to **2.5x** or **3x** if leadership sees too many “yellow” hours during ordinary volatility.
• **Missing hours:** if **ingest** drops, a single low hour can look anomalous—pair with a **concurrent** `timechart` of `count` to detect **gaps**.

**Pipeline walkthrough**
• Hourly `bin` + `stats` build one **health** per bucket.
• **Z-score** style filter surfaces **unusual** lows for triage with **UC-5.13.18** (threshold alerts) and **UC-5.13.16** (executive view).

Step 3 — Validate
• **Known incident week:** the search should return **rows** in hours you already documented; if not, the multiplier or lookback is too loose.
• **`| timechart count`** in parallel: zero-hour gaps should **not** be treated as “health dropped to null.”
• After **Catalyst** major upgrade, re-baseline: scoring changes can **shift** the whole curve.

Step 4 — Operationalize
• **Dashboard:** table of anomalous hours **plus** a **line** chart of **health** with **shaded** band for **baseline − 2σ** (clone this search into two panels).
• **Alerting:** schedule **2× daily** for **review** or **on-demand**; many teams **do not** page on **statistical** health alone without **UC-5.13.18** also firing—document that policy.

Step 5 — Troubleshooting
• **Hundreds of rows:** baseline window too short or **stdev** very small after a long flatline—lengthen **earliest** or increase **span** to **4h** to match **UC-5.13.17** cadence.
• **No rows ever:** `healthScore` stringified or **ingest** missing—`fieldsummary` and raw JSON.
• **All rows after TA upgrade:** **field** rename in add-on; compare release notes and fix **props**.


## SPL

```spl
index=catalyst sourcetype="cisco:dnac:networkhealth" | bin _time span=1h | stats avg(healthScore) as health by _time | eventstats avg(health) as baseline stdev(health) as stdev_health | where health < (baseline - 2*stdev_health) AND stdev_health > 0 | eval deviation=round((baseline-health)/stdev_health,1) | sort -deviation
```

## Visualization

Table of anomalous hours with deviation, overlay plot of `health` with a ribbon for baseline minus two sigma, combined alert card.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
- [Catalyst Center Integration Guide](docs/guides/catalyst-center.md)
