<!-- AUTO-GENERATED from UC-6.2.51.json — DO NOT EDIT -->

---
id: "6.2.51"
title: "TrueNAS network interface errors discards and packet loss rate"
criticality: "high"
splunkPillar: "Observability"
---

# UC-6.2.51 · TrueNAS network interface errors discards and packet loss rate

## Description

Rising interface errors correlate with cable, SFP, or switch issues that manifest as mysterious NFS timeouts.

## Value

Shortens layer-1 troubleshooting for high-throughput NAS uplinks.

## Implementation

Prefer 1-minute SNMP counters; compute delta with `streamstats`. Join to switch port from CMDB.

## SPL

```spl
index=storage sourcetype="truenas:alert" earliest=-4h
| search NIC OR interface OR "rx err" OR "tx err" OR discard
| eval iface=coalesce(interface, nic)
| eval err=coalesce(rx_errors, tx_errors, errors)
| eval drop=coalesce(rx_dropped, tx_dropped, drops)
| stats sum(err) as errs sum(drop) as drops by hostname, iface
| where errs > 0 OR drops > 0
| sort - errs
```

## Visualization

Timechart (errors), table (iface, errs).

## References

- [TrueNAS SCALE API documentation](https://www.truenas.com/docs/scale/scaletutorials/toptoolbar/reportinggraphs/)
- [TrueNAS CORE/SCALE docs — alerts](https://www.truenas.com/docs/)
