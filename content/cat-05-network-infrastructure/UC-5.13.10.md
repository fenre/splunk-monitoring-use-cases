<!-- AUTO-GENERATED from UC-5.13.10.json — DO NOT EDIT -->

---
id: "5.13.10"
title: "Client Health Trending by Time"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.13.10 · Client Health Trending by Time

## Description

Tracks client health percentages over time to identify patterns such as degradation during peak hours, recurring issues, or the impact of changes.

## Value

Time-based trending reveals patterns invisible in point-in-time snapshots: peak-hour degradation, weekend improvements, or the impact of configuration changes.

## Implementation

With the client health input writing to `index=catalyst` at regular intervals, keep sufficient retention (for example 90 days) for `timechart` baselines. If `healthyClientsPercentage` is not numeric in some events, add `where isnum()` before the chart. Align dashboard time pickers with business hours to see shift-based patterns clearly.

## Detailed Implementation

Prerequisites
• **clienthealth** must be **continuous** into `cisco:dnac:clienthealth`; retain **90+ days** for seasonal baselines (retail peaks, return-to-office patterns).
• **Assurance** license; Catalyst **2.3.5+** for consistent `healthyClientsPercentage` in nested `scoreDetail`.
• API user roles consistent with other Assurance read feeds; confirm **WLC-**managed clients are in inventory or wireless percentages look artificially low.
• `docs/implementation-guide.md` for index sizing (low volume, but do not use a 1-day test index in production by mistake).

Step 1 — Configure data collection
• **Intent API:** `GET /dna/intent/api/v1/client-health`.
• **TA input name:** **clienthealth**; sourcetype `cisco:dnac:clienthealth`, index `catalyst`.
• **Default interval:** **900s**; `timechart span=1h` expects several polls per hour to average inside each bucket in busy environments.
• **Volume:** still **aggregate** events—disk growth is modest compared to **flow** or **syslog** indices.
• **Key metrics for this search:** `scoreDetail{}.healthyClientsPercentage` and `scoreDetail{}.scoreCategory.scoreCategory` (series names).

Step 2 — Create the search and alert
```spl
index=catalyst sourcetype="cisco:dnac:clienthealth" | timechart span=1h avg(scoreDetail{}.healthyClientsPercentage) as healthy_pct by scoreDetail{}.scoreCategory.scoreCategory
```

Understanding this SPL (span choice, null handling, and SLO lines)
• **`span=1h`** smooths 15m polls; try **`30m`** for campus incidents, **`4h`** for long-range exec trends (hides short spikes—pick based on audience).
• **`avg(healthyClientsPercentage)`** only works if the field is **numeric**—add **`| where isnum(healthyClientsPercentage)`** in a pre-search or wrap with **`where mvcount`** logic if the TA sometimes emits null arrays.
• **Legend series** will mirror **Catalyst** category groupings; hide noisy series in **Dashboard Studio** if “All clients” drowns out a focused line you care about.
• Draw a **visual reference** at your agreed **SLO** (e.g. **90%** healthy) in the chart settings—the SPL does not hard-code SLO text.

**Pipeline walkthrough**
• `timechart` buckets to one hour and averages the nested `healthyClientsPercentage` for each `scoreCategory` name.
• **Multiple** lines make **divergence** between wireless-focused vs wired-focused categories easy to see—interpretation depends on the exact **strings** in your data.
• Cross-reference with **change calendar** for WLC upgrades, RADIUS work, or new SSIDs.

Step 3 — Validate
• Compare a single **hour** to **Catalyst > Client health** for that hour (small **rounding** diffs are normal between JSON and UI).
• If one series is **flat at 100%**, the category may be **inapplicable** to your design—not necessarily an error.
• Gaps: verify **ingest** lag (`_indextime - _time`) is minutes, not hours; fix forwarder/queue if not.
• After a **TA upgrade**, re-check **`| fieldsummary`** for renamed nested paths.

Step 4 — Operationalize
• **Placement:** **trend row** of the **Catalyst executive** or **NOC** dashboard; default **30 days** with a **1d/7d/24h** token strip.
• **Annotations:** add markers for **code upgrades** and **HLD**-documented “expected dip” events so leadership does not misread a planned blip.
• **Pair** with a **per-site** filter token when the **TA** or a **post-process** enriches **site**—global-only charts hide a single **bad building**.
• **Do not** use this chart for **P1** detection without **issue**-based UCs; it lags user-perceived **Wi-Fi** pain during micro-outages.

Step 5 — Troubleshooting
• **Nulls in the chart:** wrong MV path or empty **scoreDetail** on that poll; validate one **full JSON** and adjust field names in the SPL.
• **Percentages out of 0–100 range** in edge builds: **clamp** in presentation or open a TAC case; do not hide silently.
• **Sawtooth on poll alignment:** you may be **re-ingesting** duplicate buckets—`dedup` on known keys in an intermediate **summary** if needed.
• **Region mismatch vs GUI:** the modular input may be **global** while an engineer looks at a **single site** in the UI—align **scope** in the TA where filters exist.


## SPL

```spl
index=catalyst sourcetype="cisco:dnac:clienthealth" | timechart span=1h avg(scoreDetail{}.healthyClientsPercentage) as healthy_pct by scoreDetail{}.scoreCategory.scoreCategory
```

## Visualization

Line timechart of healthy_pct by category, overlay markers for change windows, stat panels for min/max/avg over the range.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
- [Catalyst Center Integration Guide](docs/guides/catalyst-center.md)
