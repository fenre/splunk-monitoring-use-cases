<!-- AUTO-GENERATED from UC-5.16.7.json — DO NOT EDIT -->

---
id: "5.16.7"
title: "Bandwidth Savings Trending and ROI Reporting"
status: "verified"
criticality: "medium"
splunkPillar: "Platform"
---

# UC-5.16.7 · Bandwidth Savings Trending and ROI Reporting

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Platform &middot; **Type:** Business, Cost, Analytics &middot; **Wave:** Run &middot; **Status:** Verified

*We translate squished traffic into everyday money language—how much expensive long-distance pipe we did not have to buy—so leaders see why those invisible boxes still deserve maintenance dollars.*

---

## Description

Splunk blends appliance-reported byte savings with finance-approved tariff lookups so executive dashboards translate compression into gibibytes removed from billed WAN transports month over month.

## Value

Finance validates WAN renewal ROI without spreadsheet archaeology while network leadership prioritizes upgrade budgets using Splunk-scheduled PDF evidence consumed by procurement workflows.

## Implementation

Maintain tariff CSV with owner attestations, run weekly saved search writing summary index, integrate export into CFO briefing slides automatically.

## Detailed Implementation

### Prerequisites
- Legal approval storing tariff multipliers inside Splunk KVStore or secured CSV.
- Alignment with carrier metering cadence (calendar vs billing cycle).
- Historical baseline month labeled before optimizer rollout.

### Step 1 — Configure data collection
Ensure appliances emit cumulative counters compatible with daily deltas—convert via `delta` command if only totals arrive.

### Step 2 — Create the search and alert
Wrap SPL inside scheduled report `wanopt_roi_monthly`; chain `collect` into summary index for BI tools.

### Step 3 — Validate
Reconcile Splunk `gib_saved` against carrier portal usage graphs ±10% tolerance acknowledging encapsulation overhead.

### Step 4 — Operationalize
Publish narrative captions interpreting swings (seasonality, acquisitions).

### Step 5 — Troubleshooting
**Missing tariff rows:** default zero cost skews story—alert on lookup misses.**Double counting HA pairs:** dedupe using designated reporting master.**Currency mixes:** normalize FX nightly.

## SPL

```spl
index=wanop OR index=network earliest=-35d@d latest=@d
| eval v=lower(sourcetype)
| eval vendor=case(match(v,"riverbed|steelhead"),"Riverbed SteelHead",match(v,"silverpeak|edgeconnect"),"Silver Peak EdgeConnect",match(v,"citrix"),"Citrix SD-WAN WANOP",match(v,"zdx|zscaler"),"Zscaler Digital Experience","other")
| where vendor!="other"
| eval saved_bytes=tonumber(coalesce(bytes_saved,wan_bytes_saved,reduction_bytes,opt_saved_octets))
| eval saved_bits=if(isnotnull(saved_bytes), saved_bytes*8, tonumber(bits_saved))
| bin _time span=1d
| stats sum(eval(if(isnotnull(saved_bits),saved_bits/8,0))) as bytes_saved_sum by _time vendor site_code
| eval gib_saved=round(bytes_saved_sum/pow(1024,3),3)
| lookup wan_carrier_tariffs.csv site_code OUTPUT cost_per_gib_usd
| eval est_cost_avoided_usd=round(gib_saved*coalesce(cost_per_gib_usd,0),2)
| sort _time vendor site_code
| head 1000
```

## Visualization

Combo chart: stacked gib_saved by vendor with overlaid line est_cost_avoided_usd; executive summary table MoM delta.

## Known False Positives

**Metering granularity mismatch:** carrier rounds nightly differently.**Free circuits:** cost avoidance zero despite savings.**Acquisitions:** site_code churn blanks lookups.**Lab traffic pollution:** exclude tagged sandbox hosts.

## References

- [Splunk Documentation — Lookup commands overview](https://docs.splunk.com/Documentation/Splunk/latest/SearchReference/Lookup)
- [Riverbed Community — WAN Optimization Reporting Concepts](https://support.riverbed.com/content/support/software/steelhead.html)
