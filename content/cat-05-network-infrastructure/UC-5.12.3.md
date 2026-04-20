---
id: "5.12.3"
title: "Call Duration Distribution Analysis"
criticality: "medium"
splunkPillar: "Security"
---

# UC-5.12.3 · Call Duration Distribution Analysis

## Description

Shifts toward very short or very long holds may indicate robocall, modem, or toll fraud vs. normal conversational distribution.

## Value

Shifts toward very short or very long holds may indicate robocall, modem, or toll fraud vs. normal conversational distribution.

## Implementation

Compare to historical histogram; alert on >2× share in `<6s` buckets (wangiri / scanners).

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: CDR.
• Ensure the following data sources are available: `sourcetype="cdr:voip"` `duration_sec`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Compare to historical histogram; alert on >2× share in `<6s` buckets (wangiri / scanners).

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=voip sourcetype="cdr:voip" call_status="answered"
| bucket duration_sec span=30 as dur_bin
| stats count by dur_bin
| eventstats sum(count) as tot
| eval pct=round(100*count/tot,2)
| sort dur_bin
```

Understanding this SPL

**Call Duration Distribution Analysis** — Shifts toward very short or very long holds may indicate robocall, modem, or toll fraud vs. normal conversational distribution.

Documented **Data sources**: `sourcetype="cdr:voip"` `duration_sec`. **App/TA** (typical add-on context): CDR. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: voip; **sourcetype**: cdr:voip. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=voip, sourcetype="cdr:voip". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Discretizes time or numeric ranges with `bin`/`bucket`.
• `stats` rolls up events into metrics; results are split **by dur_bin** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eventstats` aggregates the pipeline (counts, distinct values, sums, percentiles, etc.) into fewer rows.
• `eval` defines or adjusts **pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Histogram (duration), Line chart (percentile trend via `eventstats perc*`).

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

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
