<!-- AUTO-GENERATED from UC-5.12.3.json — DO NOT EDIT -->

---
id: "5.12.3"
title: "Call Duration Distribution Analysis"
criticality: "medium"
splunkPillar: "Security"
---

# UC-5.12.3 · Call Duration Distribution Analysis

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Security &middot; **Type:** Performance, Fraud

*We help you see if call lengths clump in odd ways—very short or very long—which can be fraud, scanners, or a broken app, not a normal talk pattern.*

---

## Description

Shifts toward very short or very long holds may indicate robocall, modem, or toll fraud vs. normal conversational distribution.

## Value

Fraud and voice quality teams detect Wangiri scams, toll fraud, and system anomalies through statistical analysis of call duration patterns vs. established baselines.

## Implementation

Compare to historical histogram; alert on >2× share in `<6s` buckets (wangiri / scanners).

## Detailed Implementation

### Prerequisites
- CDR data in `index=voip` with `sourcetype=cdr:voip`. Required field: `duration_sec` (call duration in seconds, set on answered/completed calls). The field must be numeric and present on all answered CDR records.
- Filter to answered calls only (`call_status="answered"`) — duration on failed or unanswered calls is meaningless or zero.
- Understand normal call duration distributions: a healthy enterprise PBX shows a bell curve centered around 60-180 seconds (1-3 min conversations), with a long tail of conference calls. A carrier network shows a bimodal distribution: short calls (IVR, voicemail) < 30s and conversations 60-300s.
- Fraud indicators in duration analysis: (a) Very short calls (<6 seconds): Wangiri fraud (one-ring calls designed to trick callbacks to premium numbers), robocall/scanner probing, or SIP brute-force attacks. (b) Very long calls (>3600 seconds / 1 hour): Modem fraud, SIM box relay, or toll fraud holding lines open to premium numbers. (c) Uniform-length calls: Automated systems generating calls of identical duration suggest bot activity.

### Step 1 — Configure data collection
Verify `duration_sec` is extracted and numeric:
```spl
index=voip sourcetype="cdr:voip" call_status="answered" earliest=-1h
| stats count avg(duration_sec) as avg_dur median(duration_sec) as med_dur max(duration_sec) as max_dur
```
If `duration_sec` is null, check if your CDR format uses a different field name (`talk_time`, `elapsed_time`, `billsec` for Asterisk). Add a field alias in `props.conf`: `FIELDALIAS-duration = billsec AS duration_sec`.

Establish your baseline distribution (save for comparison):
```spl
index=voip sourcetype="cdr:voip" call_status="answered" earliest=-7d
| bucket duration_sec span=30 as dur_bin
| stats count by dur_bin
| eventstats sum(count) as total
| eval pct=round(100*count/total, 2)
| sort dur_bin
```

### Step 2 — Create the search and alert

**Primary search — Duration distribution with fraud bucketing:**
```spl
index=voip sourcetype="cdr:voip" call_status="answered" earliest=-24h
| eval dur_category=case(duration_sec < 6, "Ultra-short (<6s) - Wangiri/Scanner", duration_sec < 30, "Short (6-30s) - IVR/Voicemail", duration_sec < 180, "Normal (30s-3m)", duration_sec < 600, "Medium (3-10m)", duration_sec < 3600, "Long (10m-1h)", 1==1, "Very Long (>1h) - Investigate")
| stats count by dur_category
| eventstats sum(count) as total
| eval pct=round(100*count/total, 2)
| sort dur_category
```

#### Understanding this SPL: We categorize call durations into operationally meaningful buckets. The "Ultra-short" and "Very Long" categories are flagged for investigation because they match known fraud patterns. The percentages show the distribution shape — if "Ultra-short" suddenly jumps from 2% to 15%, something is scanning your number space or generating Wangiri calls.

**Wangiri / scanner detection — short-call anomaly:**
```spl
index=voip sourcetype="cdr:voip" call_status="answered" duration_sec < 6 earliest=-24h
| stats count as short_calls dc(calling_party) as unique_callers dc(called_number) as unique_destinations by dest
| where short_calls > 50
| sort -short_calls
```

#### Understanding this SPL: Identifies trunks carrying high volumes of ultra-short calls. A high count with many unique called_numbers (scanning pattern) or many unique callers to the same called_number (Wangiri callback fraud) are both concerning. The trunk identification pinpoints the entry point.

**Duration shift detection — week-over-week comparison:**
```spl
index=voip sourcetype="cdr:voip" call_status="answered" earliest=-14d
| eval week=if(_time > relative_time(now(), "-7d"), "This Week", "Last Week")
| eval dur_bucket=case(duration_sec < 6, "<6s", duration_sec < 30, "6-30s", duration_sec < 180, "30s-3m", duration_sec < 600, "3-10m", 1==1, ">10m")
| stats count by week, dur_bucket
| xyseries dur_bucket, week, count
```

#### Understanding this SPL: Compares this week's duration distribution to last week's. A significant shift in any bucket (e.g. ultra-short calls doubling) is an early warning of a new fraud pattern or system issue.

Schedule as Alert: short-call anomaly search runs every 4 hours. Trigger when any trunk has >100 ultra-short calls. Route to fraud team.

### Step 3 — Validate
(a) Compare the distribution histogram to a known-good baseline week. The shape should be recognizable — a major shift in any bucket warrants investigation.
(b) For Wangiri detection: check if the ultra-short calls correlate with callbacks to premium international numbers.
(c) For long calls: verify that very long duration calls are legitimate conference bridges or support lines, not toll fraud.
(d) Pull sample CDRs from each duration bucket and verify the categorization makes sense for your traffic mix.

### Step 4 — Operationalize
Dashboard ("Voice — Call Duration Analytics"):
- Row 1 — Histogram: duration distribution with fraud-indicator buckets color-coded (ultra-short=red, very-long=orange).
- Row 2 — Week-over-week comparison: overlay this week's distribution vs. last week's.
- Row 3 — Ultra-short call table: trunk, count, unique callers, unique destinations.
- Row 4 — Very long call table: calling party (masked), called number (masked), duration, trunk.

Alerting:
- Fraud (ultra-short calls > 100 in 4 hours on any trunk): alert fraud/security team.
- Anomaly (duration distribution shift > 3 percentage points in any bucket): alert voice engineering.

Runbook (owner: Fraud / Voice Operations):
1. **Wangiri spike**: Block inbound calls from the originating number range on the SBC. Alert subscribers who may have received one-ring calls to not call back.
2. **Long-call fraud**: Identify the calling party and called number. If the called number is a premium/satellite number, disconnect the call and block the destination.
3. **Uniform-duration calls**: Automated traffic. Investigate the calling party for bot activity or compromised PBX.

### Step 5 — Troubleshooting

- **Duration is always 0 on answered calls** — The CDR may report duration in a different field. Some SBCs only set duration on the "stop" record, not the "start" record. Filter to CDR record type = stop.

- **Distribution looks flat with no clear pattern** — You may be mixing different call types (internal, external, voicemail, IVR). Segment by `route_label` or call type to see distinct distributions.

- **Too many "normal" calls flagged as ultra-short** — IVR self-service calls naturally complete in <6 seconds. Exclude known IVR number ranges using a lookup.

- **Max duration seems impossibly high** — Parked calls, hold music, and conference bridges can run for hours. These are legitimate. Filter to non-conference/non-IVR calls for fraud analysis.

## SPL

```spl
index=voip sourcetype="cdr:voip" call_status="answered"
| bucket duration_sec span=30 as dur_bin
| stats count by dur_bin
| eventstats sum(count) as tot
| eval pct=round(100*count/tot,2)
| sort dur_bin
```

## Visualization

Histogram (duration), Line chart (percentile trend via `eventstats perc*`).

## Known False Positives

Call-center wrap-up, hold music, and parked calls can stretch tails; very short successful calls are normal for callbacks and IVR self-service.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
