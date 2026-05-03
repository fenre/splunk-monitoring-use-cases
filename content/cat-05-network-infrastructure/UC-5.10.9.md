<!-- AUTO-GENERATED from UC-5.10.9.json — DO NOT EDIT -->

---
id: "5.10.9"
title: "ISP Peering Point Saturation Detection"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.10.9 · ISP Peering Point Saturation Detection

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Capacity, Performance &middot; **Wave:** Walk &middot; **Status:** Verified

*We measure how busy each front door to the internet becomes so our team adds lanes or spreads traffic before videos start buffering for everyone.*

---

## Description

Aggregates five-minute flow volume per ISP hand-off or peering interface to expose sustained saturation—either versus engineered nominal capacity or versus a thirty-minute adaptive baseline—highlighting choke points before packet loss manifests on subscriber services.

## Value

Peering coordinators gain quantitative justification for augmenting ports, shifting traffic across diverse paths, or invoking contracted burst clauses—often avoiding reactive finger-pointing during sporting or retail traffic spikes.

## Implementation

Ensure NetFlow/IPFIX templates export interface IDs resolvable to names; maintain lookup tying exporter+interface to carriers; blend SNMP when flows lack counters; tune nominal_bps yearly after upgrades.

## Detailed Implementation

### Prerequisites
- NetFlow v9/IPFIX exporters on provider-edge routers with templates exposing OUTPUT_INTERFACE/SOURCE_INTERFACE IDs plus optional SNMP mapping tables.
- Splunk Technology Add-on or Stream pipeline translating numeric interface indexes into human-readable `dst_inf_name` strings aligned with peering documentation.
- Authoritative engineering workbook listing nominal capacity per interconnect (sometimes lower than line rate due to policers).
- Baseline observation window (≥14 days) before trusting adaptive spike ratios.

### Step 1 — Normalize sourcetypes so `bytes` counts octets per flow and `_time` reflects flow end; deduplicate when multiple collectors mirror identical exports.

### Step 2 — Bucket traffic into five-minute spans per exporter/interface pair, multiply summed octets by eight to obtain bits, divide by three hundred seconds for average bps.

### Step 3 — Enrich with `peering_interfaces.csv`; compute engineered utilization when `nominal_bps` exists, otherwise rely on `baseline_spike` comparing against thirty-minute rolling averages per peer.

### Step 4 — Visualization stacks Top-N saturated peers, overlays SNMP discard counters (optional join), and publishes automated carrier-facing PDF summaries.

### Step 5 — Troubleshooting: sampled flows miss microbursts—spot-check with switchingASIC telemetry; confirm bidirectional exports since asymmetric configs blind one direction; update lookups whenever circuits relocate between routers.

## SPL

```spl
index=netflow earliest=-35m
| bin _time span=5m
| stats sum(eval(bytes*8)) as bits by _time, host, dst_inf_name
| eval peer_key=host."|".dst_inf_name
| lookup peering_interfaces.csv peer_key OUTPUT peer_name pop nominal_bps peer_as
| where isnotnull(peer_name)
| eval interval_sec=300
| eval bps=bits/interval_sec
| eventstats avg(bps) as baseline by peer_name
| eval util_pct=if(isnotnull(nominal_bps) AND nominal_bps>0, round(100*bps/nominal_bps,2), null())
| eval baseline_spike=if(isnotnull(baseline) AND baseline>0 AND bps>(baseline*1.35), 1, 0)
| where util_pct>80 OR baseline_spike=1
| stats latest(util_pct) as util_pct latest(bps) as current_bps latest(baseline) as baseline_bps latest(peer_as) as peer_as by peer_name, pop
| sort -util_pct
```

## Visualization

Treemap of peers sized by bits; alert table listing peer_name, util_pct, baseline delta; correlation panel with UC-5.10.8 SNMP chart for same interface.

## Known False Positives

BGP traffic engineering shifting volumes between peers triggers adaptive baseline swings; DDoS scrubbing redirection concentrates flows temporarily; midnight backup sweeps mimic saturation unless excluded by AS filters.

## References

- [Splunk Docs — NetFlow data onboard](https://docs.splunk.com/)
- [RFC 7011 — IPFIX Protocol Specification](https://www.rfc-editor.org/rfc/rfc7011)
