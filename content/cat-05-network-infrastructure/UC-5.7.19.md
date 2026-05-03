<!-- AUTO-GENERATED from UC-5.7.19.json — DO NOT EDIT -->

---
id: "5.7.19"
title: "Top Conversation Pairs and New Communication Detection"
status: "verified"
criticality: "medium"
splunkPillar: "Security"
---

# UC-5.7.19 · Top Conversation Pairs and New Communication Detection

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Security &middot; **Type:** Security, Analytics, Operations &middot; **Wave:** Walk &middot; **Status:** Verified

*We list who talked the most to whom lately and call out brand-new friendships that moved serious traffic. That helps guardians notice odd introductions without reading every chat.*

---

## Description

Lists the heaviest unordered endpoint pairs from the last day while highlighting pairs with meaningful volume that lacked any sampled flows during the prior thirty-day baseline window.

## Value

Hunting teams surface lateral movement staging and shadow information-technology links without predefined indicators; capacity planners still read the embedded top-volume appendix for hotspot remediation.

## Implementation

Tune megabyte floor and join limits per hardware tier; materialize baseline pairs nightly into a KV store when subsearch ceilings bite; separate dashboards for volume champions versus novelty-only rows.

## Detailed Implementation

### Prerequisites
- Adequate indexer compute for wide-time joins or prebuilt baseline lookups refreshed nightly.
- Data retention exceeding the baseline horizon so absence truly implies novelty rather than expiry.
- Change-management feed optionally merged to annotate expected new pairs.

### Step 1 — Configure data collection
Ensure Network Address Translation logging aligns internal hosts so pairs reflect true endpoints rather than translated gateways.

### Step 2 — Create the search
When `join max` truncates, pivot to `| lookup baseline_pairs.csv pair OUTPUT first_seen` populated by a scheduled transform. Add asset enrichment columns for business unit labels.

### Step 3 — Validate
Seed a fresh lab virtual machine talking solely to a new file share and confirm novelty classification within one reporting interval.

### Step 4 — Operationalize
SOC reviewers receive CSV extracts limited to regulated subnets; network operations consumes only the top-volume portion via saved-search ACL separation.

### Step 5 — Troubleshooting
Sampling bias misses rare pairs—lower megabyte thresholds cautiously. Split exporters duplicates inflate prior counts—deduplicate using `dedup _raw` cautiously only after verifying redundancy patterns.

## SPL

```spl
index=netflow earliest=-24h
| eval lo=min(src,dest), hi=max(src,dest), pair=lo."|".hi
| stats sum(bytes) as recent_bytes sum(packets) as recent_packets first(lo) as endpoint_a first(hi) as endpoint_b by pair
| join max=500000 type=left pair [
    search index=netflow earliest=-30d latest=-24h
    | eval lo=min(src,dest), hi=max(src,dest), pair=lo."|".hi
    | stats count as prior_flow_records by pair
]
| fillnull value=0 prior_flow_records
| eval mb_recent=round(recent_bytes/1048576, 2)
| eval insight=if(prior_flow_records=0 AND mb_recent>5, "NEW_HIGH_VOLUME_PAIR", "KNOWN_PAIR")
| sort -recent_bytes
| head 40
| table insight endpoint_a endpoint_b mb_recent recent_packets prior_flow_records pair
```

## Visualization

Force-directed graph sampling for top pairs (sample cap); dual tables split NEW_PAIR versus TOP_VOLUME_PAIR; sparklines when fed from summary index.

## Known False Positives

Short-retention archives pretend novelty after retention rollover. Cloud auto-scaling introduces ephemeral pairs hourly. Penetration tests purposely mimic suspicious connectivity.

## References

- [Splunk — Hunting with NetFlow data](https://www.splunk.com/en_us/blog/learn/network-security-monitoring.html)
- [MITRE ATT&CK — Lateral Movement](https://attack.mitre.org/tactics/TA0008/)
