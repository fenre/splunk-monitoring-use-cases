<!-- AUTO-GENERATED from UC-5.10.10.json — DO NOT EDIT -->

---
id: "5.10.10"
title: "BGP Community and AS-Path Anomaly from Upstream Providers"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.10.10 · BGP Community and AS-Path Anomaly from Upstream Providers

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Security, Anomaly &middot; **Wave:** Run &middot; **Status:** Verified

*We compare the little stickers and directions carriers put on internet routes against what we agreed so weird detours or sneaky tags show up before they mess up billing or security.*

---

## Description

Parses carrier-facing BGP syslog updates for communities and ordered AS paths, comparing observed attributes against curated allowlists per upstream neighbor to flag unexpected tagging, opaque reroutes, or path-length inflation indicative of policy mistakes or upstream leaks.

## Value

Peering engineers gain automated audit evidence when wholesale providers prepend unexpected transit segments or stamp foreign communities—shortening mean-time-to-comprehension during billing disputes, route leaks, or mitigation actions like selective de-peering.

## Implementation

Enable BGP update logging at sane rates on edge routers; throttle Splunk ingestion via filters dropping repetitive withdraw churn; maintain CSV lookups synchronized from IRR/peering DB exports; alert on community mismatch before ASPATH if noise dominates.

## Detailed Implementation

### Prerequisites
- Stable syslog forwarding with millisecond timestamps and consistent timezone normalization.
- Documented policy stating which standard communities (including informational versus action communities) each upstream may attach.
- IRR or internal source-of-truth exporting regex-friendly allowlists.
- Splunk knowledge manager owning CSV lifecycle with Git-backed change control.

### Step 1 — Enable selective BGP logging features (`bgp log-neighbor-changes`, Junos `traceoptions`) limiting verbosity to avoid control-plane CPU exhaustion—consult vendor caps.

### Step 2 — Normalize sourcetypes; extract `comm_raw`, flattened AS sequence, and neighbor identifiers via `rex`; collapse whitespace on Junos formats differing from Cisco.

### Step 3 — Layer lookups translating neighbor IPs into regex constraints; implement dual alerts—warning for community drift, critical when ASPATH violates transit contract.

### Step 4 — Dashboard overlays anomaly timeline with BGP session state panels from UC-5.10.15 for holistic carrier correlation.

### Step 5 — Troubleshooting: ephemeral debugging communities during migrations trigger benign alerts—annotate maintenance CSV column `suppress_until`; overly greedy regex causes misses—test with `regex` command interactively; missing logs often mean rate-limited drops—verify router buffer statistics.

## SPL

```spl
index=network earliest=-4h (sourcetype="cisco:ios" OR sourcetype="juniper:junos")
    ("%BGP" OR "BGP-5" OR "bgp_" OR "COMMUNITY" OR "Community" OR "community" OR "AS PATH" OR "AS_PATH")
| rex field=_raw "neighbor\s+(?<bgp_neighbor>[0-9a-fA-F:\.]+)"
| rex field=_raw max_match=20 "(?i)community(?:[^0-9a-fA-F:\s]|\s)+(?<comm_raw>[0-9a-fA-F:\s,.]+)"
| rex field=_raw "(?i)(?:AS[_ ]?PATH|ASPATH|As-Path)\s*:\s*(?<as_path>[0-9\s\.]+)"
| lookup expected_upstream_communities.csv bgp_neighbor OUTPUT allowed_community_regex transit_allow_regex
| eval path_tokens=split(trim(as_path)," ")
| eval path_len=if(isnotnull(path_tokens), mvcount(path_tokens), 0)
| eval unexpected_comm=if(isnotnull(allowed_community_regex) AND len(comm_raw)>2 AND NOT match(comm_raw,allowed_community_regex),1,0)
| eval path_join=mvjoin(path_tokens," ")
| eval unexpected_transit=if(isnotnull(transit_allow_regex) AND len(path_join)>2 AND NOT match(path_join,transit_allow_regex),1,0)
| eval anomaly=case(unexpected_comm==1,"COMMUNITY_MISMATCH", unexpected_transit==1,"ASPATH_MISMATCH", path_len>12,"LONG_PATH", true(),null())
| where isnotnull(anomaly)
| stats count by host, bgp_neighbor, anomaly, comm_raw, path_join
| sort -count
```

## Visualization

Timeline with anomaly icons; Sankey-style AS path explorer fed by stats; table listing neighbor, anomaly class, sample community string, last occurrence.

## Known False Positives

Carriers legitimately attach informational communities during DDoS mitigation; temporary prepending for hot-potato tuning resembles leaks; route-server peers emit redundant paths that lengthen ASPATH without fault.

## References

- [RFC 4271 — A Border Gateway Protocol 4 (BGP-4)](https://www.rfc-editor.org/rfc/rfc4271)
- [RFC 1997 — BGP Communities Attribute](https://www.rfc-editor.org/rfc/rfc1997)
