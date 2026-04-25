<!-- AUTO-GENERATED from UC-6.1.65.json — DO NOT EDIT -->

---
id: "6.1.65"
title: "Pure Storage FlashArray write amplification factor trending"
criticality: "high"
splunkPillar: "Observability"
---

# UC-6.1.65 · Pure Storage FlashArray write amplification factor trending

## Description

Rising write amplification consumes flash endurance and effective capacity as garbage collection works harder. Trending WAF highlights snapshot-heavy or overwrite-heavy workloads before latency climbs.

## Value

Avoids surprise capacity purchases and premature SSD wear by steering QoS, host alignment, and snapshot retention policies.

## Implementation

Deploy Unified Add-on REST inputs per array with an API token scoped for observability. If WAF is not returned, derive from logical/physical used and document the approximation. Store daily samples for YoY comparison.

## SPL

```spl
index=storage (sourcetype="purestorage:array" OR sourcetype="PureStorage_REST")
| eval logical_b=coalesce(space_logical_used, logical_used_bytes)
| eval physical_b=coalesce(space_physical_used, physical_used_bytes)
| eval waf=coalesce(write_amplification, if(physical_b>0, round(logical_b/physical_b,3), null()))
| timechart span=1d latest(waf) as waf by array_name
```

## CIM SPL

```spl
| tstats `summariesonly` max(Performance.storage_used_percent) as used_pct
  from datamodel=Performance where nodename=Performance.Storage
  by Performance.host Performance.object span=1h
| where used_pct > 80
| sort - used_pct
```

## Visualization

Line chart (WAF by array), table (logical vs physical TB, WAF).

## References

- [Pure Storage Unified Add-on for Splunk (Splunkbase)](https://splunkbase.splunk.com/app/5513)
- [Pure Storage Splunk reference](https://support.purestorage.com/Solutions/Splunk/Splunk_Reference/Array_Monitoring_on_Splunk_with_PureStorage_Unified_App_and_TA)
- [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)
