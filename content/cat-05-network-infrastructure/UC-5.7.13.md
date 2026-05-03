<!-- AUTO-GENERATED from UC-5.7.13.json — DO NOT EDIT -->

---
id: "5.7.13"
title: "Traffic Matrix Baseline Deviation Detection"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.7.13 · Traffic Matrix Baseline Deviation Detection

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Anomaly, Performance, Security &middot; **Wave:** Run &middot; **Status:** Verified

*We compare how much traffic usually flows between each pair of sites with how much moved recently. When one corridor suddenly spikes or dries up, we raise a hand before customers feel it.*

---

## Description

Measures hourly bytes between zone pairs against a trailing median derived from the same search window to spotlight pairs whose volume jumped or collapsed compared with recent behavior.

## Value

Operators catch routing leaks, bulk data movement, or failed reroutes early; executives gain a simple east-west versus north-south imbalance signal without deploying new agents beyond existing flow exporters.

## Implementation

Maintain authoritative zone lookups; run hourly matrix stats; tune deviation multiplier and minimum-byte guardrails per environment; integrate alerts with change-management calendars.

## Detailed Implementation

### Prerequisites
- Reliable `zone_matrix.csv` with CIDR keys covering internal and partner prefixes; refresh weekly from your internet protocol address management source.
- At least fourteen days of retained netflow data for seasonal baselines when moving beyond the inline median example.
- Agreement on minimum-byte thresholds so tiny flows do not noise the alert channel.

### Step 1 — Configure data collection
Confirm exporters preserve internal addressing without excessive summarization. If Network Address Translation hides sources, attach post-address-allocation fields via intermediate syslog correlation.

### Step 2 — Create the search
Materialize a summary index `traffic_matrix_hourly` using `collect` or scheduled transforms for scale. Replace inline `eventstats` with `| join type=left src_zone dest_zone [|inputlookup matrix_baseline_weekly]` when baselines are precomputed.

### Step 3 — Validate
Replay a known maintenance failover that shifts metro traffic and verify the affected pair exceeds deviation threshold within one hour while unaffected pairs remain quiet.

### Step 4 — Operationalize
Color a chord or sankey visualization from the stats output; attach recommended triage steps distinguishing symmetric denial-of-service floods from single-direction copy jobs.

### Step 5 — Troubleshooting
Sudden widespread deviation often indicates a broken lookup rather than the network—spot-check `| stats count by src_zone`. Clock skew across exporters widens artificial deltas; enforce Network Time Protocol discipline.

## SPL

```spl
index=netflow earliest=-8h
| lookup zone_matrix.csv ip as src OUTPUT zone as src_zone
| lookup zone_matrix.csv ip as dest OUTPUT zone as dest_zone
| where isnotnull(src_zone) AND isnotnull(dest_zone)
| bin _time span=1h
| stats sum(bytes) as bytes by _time src_zone dest_zone
| eventstats median(bytes) as med by src_zone dest_zone
| eval deviation=if(med>0, abs(bytes-med)/med, 0)
| where bytes>104857600 AND deviation>2
| sort - deviation
| head 100
```

## Visualization

Heatmap of zones × zones with deviation score; companion single-value for count of hot pairs; timeline overlay of change tickets.

## Known False Positives

Large backups and cloud synchronization windows mimic data theft burst patterns. Retail peaks and payroll batches seasonally skew medians when the window is short. Misclassified Dynamic Host Configuration Protocol ranges mis-bucket flows.

## References

- [Splunk Blog — Building Network Insights](https://www.splunk.com/en_us/blog/learn/network-security-monitoring.html)
- [NIST SP 800-53 AU-6 — Audit Record Review](https://csrc.nist.gov/projects/cprt/catalog#/control?version=SP_800_53_5_1_1&control=AU-6)
