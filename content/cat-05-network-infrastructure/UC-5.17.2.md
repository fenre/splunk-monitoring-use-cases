<!-- AUTO-GENERATED from UC-5.17.2.json — DO NOT EDIT -->

---
id: "5.17.2"
title: "Packet Drop Rate on Filter/Map Rules"
status: "verified"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.17.2 · Packet Drop Rate on Filter/Map Rules

> **Criticality:** Critical &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Fault, Data Quality, Operations &middot; **Wave:** Walk &middot; **Status:** Verified

*Sometimes the copying machinery quietly throws away little pieces of traffic when rules are too tight or boxes run out of room. We track which rule caused the waste so the right person can fix it before our watchers miss something real.*

---

## Description

Five-minute Splunk rollups attribute rising packet discard counters to specific broker filter or map identifiers so engineering teams know whether buffering, ACL tightening, or malformed rules—not vague chassis alarms—drive visibility loss.

## Value

Incident responders shorten MTTR by jumping straight to offending rule keys instead of spanning multiple vendor consoles while compliance teams preserve evidence that monitored spans stayed complete during audits.

## Implementation

Ensure every drop-bearing event carries stable `rule_key`; baseline benign drops with a weekly median lookup; alert only when peak_pps or drops-per-million exceeds curated thresholds per vendor tier.

## Detailed Implementation

### Prerequisites
- Exported rule catalog (`rule_key`, owner, business justification, expected drop budget).
- Understanding whether counters reset on rule edits—document rollover semantics per vendor OS.
- Capacity for five-minute retention searches without dominating search quota.

### Step 1 — Configure data collection
Turn on structured syslog or REST polling that emits both instantaneous and cumulative drop counters; prefer timestamps from the appliance, not the collector edge.

### Step 2 — Normalize counters
Convert burst counters to `drops_pps` using adjacent samples where vendors only publish totals; guard divide-by-zero when intervals stall.

### Step 3 — Build saved search
Materialize `pktbrk_map_drop_hotrules` with acceleration-friendly summary when cardinality explodes beyond fifty thousand rule keys—pre-aggregate per chassis hourly.

### Step 4 — Validate
Inject lab traffic through a sacrificial map known to drop synthetic flows; confirm Splunk surfaces the expected `rule_key` within two poll intervals.

### Step 5 — Operationalize
Wire alerts to SecOps with direct links to vendor edit screens; attach recommended actions (widen buffer, split map, add tool port) based on historical runbooks stored in a Splunk lookup.

## SPL

```spl
index=visibility OR index=network earliest=-8h
| eval v=lower(sourcetype)
| eval vendor=case(match(v,"gigamon"),"Gigamon",match(v,"keysight|ixia|vision"),"Keysight",match(v,"apcon"),"APCON","other")
| where vendor!="other"
| eval rule_key=coalesce(rule_id,map_name,filter_name,policy_rule,"unknown")
| eval drops_pps=tonumber(coalesce(drop_pps,drops_per_sec,packet_drop_rate))
| eval drops_total=tonumber(coalesce(drop_pkts,dropped_packets,map_drop_count))
| eval pmpp=tonumber(coalesce(drops_per_million,dpm))
| bin _time span=5m
| stats sum(drops_total) as sum_drops max(drops_pps) as peak_pps avg(pmpp) as avg_pmpp dc(host) as chassis_hits by _time vendor rule_key
| eval severity=case(peak_pps>1000 OR avg_pmpp>500,"critical",peak_pps>200 OR avg_pmpp>100,"high",peak_pps>0 OR sum_drops>0,"medium","info")
| where severity IN ("critical","high")
| sort - peak_pps vendor rule_key _time
```

## Visualization

Heatmap of sum_drops by rule_key vs `_time`; companion single-value for critical severity count; table drilldown showing vendor, chassis, and linked change ticket.

## Known False Positives

**Expected sampling maps:** lawful truncation for capped analytics ports mimics faults—whitelist by rule catalog.**Counter resets after failover:** transient spikes resemble floods.**Duplicate syslog streams:** summed drops double until dedupe keys applied.**Low-volume lab rules:** tiny denominators inflate drops-per-million—require minimum packet threshold.

## References

- [Splunk Documentation — stats command reference](https://docs.splunk.com/Documentation/Splunk/latest/SearchReference/Stats)
- [Gigamon Documentation — Visibility and analytics nodes](https://docs.gigamon.com/)
- [APCON — Network visibility and security fabric](https://www.apcon.com/)
