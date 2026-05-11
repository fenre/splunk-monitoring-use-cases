<!-- AUTO-GENERATED from UC-5.7.17.json — DO NOT EDIT -->

---
id: "5.7.17"
title: "Asymmetric Routing Detection via Flow Analysis"
status: "verified"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.7.17 · Asymmetric Routing Detection via Flow Analysis

> **Criticality:** Medium &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Fault, Performance, Operations &middot; **Wave:** Walk &middot; **Status:** Verified

*We weigh traffic leaving point A toward B against traffic leaving B toward A on the same conversation. When one side almost disappears while the other roars, something on the path may be lopsided or we may only see half the road.*

---

## Description

Rebuilds unordered endpoint pairs and compares byte totals measured from each direction’s viewpoint to flag conversations where one leg dominates despite bidirectional traffic expectations.

## Value

Routing engineers localize multi-homed misconfigurations and firewall state bypass attempts faster; security analysts distinguish purposeful one-way bulk copies from asymmetric-path blind spots that hide return-channel threats.

## Implementation

Ensure overlapping collectors cover both directions or annotate partial visibility per site; tune minimum-megabyte and imbalance ratios; document legitimate multicast and satellite asymmetry exceptions.

## Detailed Implementation

### Prerequisites
- Topology maps identifying multipath equal-cost routes and Network Address Translation boundaries.
- Agreement that sampled NetFlow introduces statistical noise—use higher byte floors on busy links.
- Optional verification dataset from traceroute utilities during calibration.

### Step 1 — Configure data collection
Place exporters on core-facing interfaces rather than access-edge-only vantage points when diagnosing campus asymmetry. Record ingress and egress interface identifiers if available for drilldowns.

### Step 2 — Create the search
Augment with `| lookup asym_allowlist.csv left right OUTPUT reason` to suppress known satellite feeds. Add parallel panel counting pairs where `bytes_rl==0` indicating missing reverse visibility.

### Step 3 — Validate
Introduce controlled asymmetric routing in lab using policy-based routing and verify detection within the observation window.

### Step 4 — Operationalize
Integrate alerts with topology-aware ticketing; attach recommended Border Gateway Protocol or static-route checks per pair classification.

### Step 5 — Troubleshooting
Symmetric hashing across link bundles may split flows unevenly in sampling—raise thresholds on aggregated uplinks. Timestamp skew between collectors falsifies pairing—monitor `_time` deltas.

## SPL

```spl
index=netflow earliest=-4h
| eval left=min(src,dest), right=max(src,dest)
| eval fwd_bytes=if(src=left, bytes, 0), rev_bytes=if(src=right, bytes, 0)
| stats sum(fwd_bytes) as bytes_lr sum(rev_bytes) as bytes_rl sum(bytes) as total_bytes sum(packets) as pkts by left right
| eval imbalance=abs(bytes_lr-bytes_rl)/(bytes_lr+bytes_rl+1)
| eval mb_total=round(total_bytes/1048576,2)
| where mb_total>50 AND imbalance>0.80 AND bytes_lr>0 AND bytes_rl>0
| sort -imbalance
| head 75
```

## Visualization

Chord-like table of left/right with imbalance bar; dual-axis chart bytes_lr versus bytes_rl; map interfaces when fields exist.

## Known False Positives

Large file downloads behind caching proxies appear one-way at certain taps. Backup jobs using separate return paths remain legitimate. Wireless clients roaming produce transient imbalance.

## References

- [RFC 791 — Internet Protocol (routing asymmetry context)](https://www.rfc-editor.org/rfc/rfc791)
- [Splunk — Traffic mirroring and NetFlow best practices](https://docs.splunk.com/Documentation/NetFlow/)
