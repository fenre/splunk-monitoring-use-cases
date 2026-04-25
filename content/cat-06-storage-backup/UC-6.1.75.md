<!-- AUTO-GENERATED from UC-6.1.75.json — DO NOT EDIT -->

---
id: "6.1.75"
title: "Pure Storage FlashArray host group LUN mapping inventory audit"
criticality: "high"
splunkPillar: "Observability"
---

# UC-6.1.75 · Pure Storage FlashArray host group LUN mapping inventory audit

## Description

Orphaned or over-broad host groups violate least-privilege zoning and complicate forensic containment after a host compromise.

## Value

Supports access reviews and SAN segmentation programs without manual CLI exports.

## Implementation

If `mapped_volumes` is multivalue JSON, use `spath` or `rex` in `props.conf` at index time. Schedule weekly CSV to CMDB ETL.

## SPL

```spl
index=storage sourcetype="purestorage:host"
| eval hg=coalesce(host_group, hostgroup, initiator_group)
| eval vols=coalesce(mapped_volumes, volumes, lun_list)
| mvexpand vols
| stats dc(vols) as lun_count values(array_name) as arrays by hg
| sort - lun_count
```

## Visualization

Table (host group, LUN count), Sankey (optional advanced).

## References

- [Pure Storage Unified Add-on for Splunk (Splunkbase)](https://splunkbase.splunk.com/app/5513)
- [Pure Storage Splunk reference](https://support.purestorage.com/Solutions/Splunk/Splunk_Reference/Array_Monitoring_on_Splunk_with_PureStorage_Unified_App_and_TA)
