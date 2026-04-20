---
id: "5.12.1"
title: "CDR Call Failure Statistics"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.12.1 · CDR Call Failure Statistics

## Description

Aggregates release causes, SIP response codes, and ISUP cause values from CDRs to spot trunk, routing, or peer outages early.

## Value

Aggregates release causes, SIP response codes, and ISUP cause values from CDRs to spot trunk, routing, or peer outages early.

## Implementation

Normalize vendor-specific cause codes to Q.850 / SIP mapping table; baseline by destination prefix (emergency, international).

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: SBC CDR CSV/JSON ingestion, custom props.
• Ensure the following data sources are available: `sourcetype="cdr:voip"`, `sourcetype="broadworks:cdr"`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Normalize vendor-specific cause codes to Q.850 / SIP mapping table; baseline by destination prefix (emergency, international).

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=voip sourcetype="cdr:voip"
| eval is_fail=if(call_status!="answered" OR match(lower(call_status),"fail"),1,0)
| timechart span=15m sum(is_fail) as fails count as total
| eval fail_pct=if(total>0, round(100*fails/total,2), 0)
```

Understanding this SPL

**CDR Call Failure Statistics** — Aggregates release causes, SIP response codes, and ISUP cause values from CDRs to spot trunk, routing, or peer outages early.

Documented **Data sources**: `sourcetype="cdr:voip"`, `sourcetype="broadworks:cdr"`. **App/TA** (typical add-on context): SBC CDR CSV/JSON ingestion, custom props. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: voip; **sourcetype**: cdr:voip. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=voip, sourcetype="cdr:voip". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **is_fail** — often to normalize units, derive a ratio, or prepare for thresholds.
• `timechart` plots the metric over time using **span=15m** buckets — ideal for trending and alerting on this use case.
• `eval` defines or adjusts **fail_pct** — often to normalize units, derive a ratio, or prepare for thresholds.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Stacked area (causes over time), Pie chart (cause mix), Single value (fail %).

## SPL

```spl
index=voip sourcetype="cdr:voip"
| eval is_fail=if(call_status!="answered" OR match(lower(call_status),"fail"),1,0)
| timechart span=15m sum(is_fail) as fails count as total
| eval fail_pct=if(total>0, round(100*fails/total,2), 0)
```

## Visualization

Stacked area (causes over time), Pie chart (cause mix), Single value (fail %).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
