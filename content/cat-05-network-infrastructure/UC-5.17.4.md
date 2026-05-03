<!-- AUTO-GENERATED from UC-5.17.4.json — DO NOT EDIT -->

---
id: "5.17.4"
title: "Filter Map Rule Hit Counts and Efficiency"
status: "verified"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.17.4 · Filter Map Rule Hit Counts and Efficiency

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Analytics, Operations, Quality &middot; **Wave:** Walk &middot; **Status:** Verified

*We count how often each traffic-sorting recipe actually sees packets compared to what used to be normal. That tells us which recipes went useless or turned into fire hoses so we tidy them before they waste space or drown our watchers.*

---

## Description

Hourly Splunk compares current filter-map hit rates against a rolling peer baseline per chassis so stale ACLs consuming scarce TCAM or accidental wildcard maps flooding tool ports become obvious without manual CLI exports.

## Value

Engineering governance trims redundant rules that steal appliance capacity while security architects detect overly broad matches that could overwhelm IDS clusters during benign flash crowds.

## Implementation

Bootstrap baseline after fourteen days of stable traffic; freeze comparisons during approved change freezes using eventtypes; output CSV snapshots weekly for architecture review boards.

## Detailed Implementation

### Prerequisites
- Tagged ownership metadata per `rule_key` including cost center and annual review date.
- Agreement on acceptable variance bands per environment (prod vs lab).
- Storage tier sized for one-year hourly aggregates (~few GB per chassis).

### Step 1 — Instrument exports
Enable hit counters at safe sampling cadence (≤60s) without overwhelming management planes; throttle via vendor-supported bulk APIs.

### Step 2 — Build macros
Create reusable macros `pktbrk_hit_normalize` handling vendor-specific counter resets and scientific notation quirks.

### Step 3 — Implement searches
Primary discovery search identifies stale/noisy maps; secondary verification search joins latest configuration revision IDs to prove drift versus Git-backed templates.

### Step 4 — Validate
Disable a lab map intentionally—ensure `stale_map` triggers within two hours while production siblings remain quiet.

### Step 5 — Operationalize
Dashboard pairs heatmaps with annotated bar charts of wasted estimated bandwidth; integrate Splunk drilldown to ServiceNow rule-defect queue.

## SPL

```spl
index=visibility earliest=-24h
| eval v=lower(sourcetype)
| eval vendor=case(match(v,"gigamon"),"Gigamon",match(v,"keysight|ixia|vision"),"Keysight",match(v,"apcon"),"APCON","other")
| where vendor!="other"
| eval rule_key=coalesce(rule_id,map_name,filter_name,"unset")
| eval hps=tonumber(coalesce(hits_per_sec,hit_rate,hps))
| bin _time span=1h
| stats sum(hps) as sum_hits avg(hps) as avg_hps latest(matched_bytes) as bytes_marker by _time vendor rule_key host
| streamstats global=f window=168 avg(avg_hps) as baseline by vendor rule_key host
| eval efficiency_ratio=if(baseline>0, round(avg_hps/baseline,3), null())
| eval stale_map=if(avg_hps=0 AND baseline>10,1,0)
| eval noisy_map=if(avg_hps>(baseline*5) AND baseline>0,1,0)
| where stale_map=1 OR noisy_map=1 OR efficiency_ratio < 0.2 OR efficiency_ratio > 5
| sort vendor rule_key _time
```

## Visualization

`splunk.parallelcoordinates` comparing baseline vs avg_hps across vendors; supporting table with efficiency_ratio color scales; optional scatter of bytes_marker vs hits.

## Known False Positives

**Seasonal traffic troughs:** holiday weekends mimic stale maps—extend baseline windows.**New maps warming up:** zero-hit alarms fire until caches populate—suppress first twelve hours via lookup.**Vendor counter quantization:** low-volume maps oscillate around zero confusing ratios.**Failover events:** asymmetric hashing shifts hits between chassis pairs—evaluate cluster-wide sums.

## References

- [Splunk Documentation — streamstats command](https://docs.splunk.com/Documentation/Splunk/latest/SearchReference/Streamstats)
- [Gigamon Technical Documentation — Flow mapping](https://docs.gigamon.com/)
- [Keysight Vision Network Packet Broker overview](https://www.keysight.com/us/en/products/network-test/network-visibility-solutions.html)
