---
id: "5.13.11"
title: "Poor Client Health Detection and Alerting"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.13.11 · Poor Client Health Detection and Alerting

## Description

Alerts when the percentage of clients in poor health exceeds a threshold, indicating widespread connectivity issues.

## Value

When more than 10% of clients are in poor health, it typically indicates a systemic issue (DHCP pool exhaustion, RADIUS failure, AP overload) requiring immediate attention.

## Implementation

Requires UC-5.13.9 so multivalue `scoreDetail` fields are known-good. Run as a 15–30 minute scheduled search with a non-empty trigger; tune the 10% limit per campus. If `ALL` is missing in some events, add a `fillnull` or alternate denominator from your environment.

## Detailed Implementation

Prerequisites
• **UC-5.13.9** (client health overview) is validated first so `scoreDetail` and **`clienthealth`** ingest are known-good.
• Cisco Catalyst Add-on (Splunkbase 7538); data in `index=catalyst`, sourcetype `cisco:dnac:clienthealth`.
• Catalyst Center **2.3.5+** with **Assurance** client health; API user with read access to client health Intent APIs.
• See `docs/implementation-guide.md` for modular input and index layout.

Step 1 — Configure data collection
• **Intent API:** `GET /dna/intent/api/v1/client-health` (aggregated rollups; not per-MAC in this search).
• **TA input name:** **clienthealth**; sourcetype `cisco:dnac:clienthealth`.
• **Default interval:** **900 seconds**—alerts are typically scheduled **every 15–30 minutes**; avoid sub-minute runs unless you have API capacity and a strong reason.
• **Key structure:** each poll carries a nested **`scoreDetail`** array; **`POOR`** and **`ALL`** category rows must be present for the percentage math below—if **`ALL` is missing**, use a lookup denominator or a **saved search** that computes fleet size another way (document the fallback in the runbook).

Step 2 — Create the search and alert
```spl
index=catalyst sourcetype="cisco:dnac:clienthealth" | spath output=categories path=scoreDetail{} | mvexpand categories | spath input=categories | where scoreCategory="POOR" OR scoreCategory="ALL" | stats sum(clientCount) as count by scoreCategory | eval poor_pct=round(count*100/max(count),1) | where scoreCategory="POOR" AND poor_pct > 10 | table _time poor_pct count
```

Understanding this SPL (flattened `scoreDetail`, poor share)
• **`spath path=scoreDetail{}` / `mvexpand` / `spath input=categories`** replaces fragile `mvindex`/`mvfind` on multivalue paths and survives typical TA JSON shaping changes.
• The **`stats ... by scoreCategory`** pass keeps only **POOR** and **ALL** rows; **`poor_pct`** uses **`max(count)`** across those two rows as the denominator—equivalent to **POOR ÷ ALL** when **ALL** is the largest bucket.
• **Tune the 10% threshold** per site or SLO; campus-specific baselines may justify **15%** or stricter **5%** for executive SSIDs only.

**Pipeline walkthrough**
• `where` limits expansion to the two categories needed for the ratio.
• `eval poor_pct` fires only after both rows exist in the `stats` result; the final `where` leaves **POOR** only when the breach is real.
• `table` is compact for **email/ITSM** alert bodies; add **`dedup _time`** or last poll only if the alert fires on every raw event in the window—often you run this on **last 15m** with **cron** aligned to poll times.

Step 3 — Validate
• Compare **`poor_pct` and raw counts** to **Catalyst Center > Client health** for the same window (one poll skew is normal).
• If **POOR** exists but **ALL** is missing, the search returns nothing—fix ingest or add an alternate **total** before enabling paging.
• Test with `| where scoreCategory="POOR"` only in a subsearch to confirm **clientCount** is numeric.

Step 4 — Operationalize
• **Alert:** **P2** routing when the threshold breaches; add **recurrence suppression** of **1 hour** to avoid ticket storms on noisy RF days.
• **Dashboard:** pair with **device/AP health (UC-5.13.1)** and **onboarding (UC-5.13.14)** drilldowns in the runbook.
• **Time picker:** last **4 hours** for triage, **24 hours** for problem management.

Step 5 — Troubleshooting
• **Empty `categories` after `mvexpand`:** confirm **clienthealth** is enabled and **Assurance** is licensed; inspect one raw JSON for `scoreDetail`.
• **False positives:** a transient **ALL** drop-inflate **poor_pct**—widen the window or require **two consecutive** breaches.
• **`max(count)` wrong when more than two categories slip through:** tighten the pre-`stats` `where` to only **POOR** and **ALL** (as written) and retest.
• **GUI mismatch:** align **time zone** and **site** scope in the TA with the operator’s Catalyst view before opening a TAC case.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:clienthealth" | spath output=categories path=scoreDetail{} | mvexpand categories | spath input=categories | where scoreCategory="POOR" OR scoreCategory="ALL" | stats sum(clientCount) as count by scoreCategory | eval poor_pct=round(count*100/max(count),1) | where scoreCategory="POOR" AND poor_pct > 10 | table _time poor_pct count
```

## Visualization

Table of breach rows, single value breach count, optional timechart of poor_pct for context.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
