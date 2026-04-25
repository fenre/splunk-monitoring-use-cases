<!-- AUTO-GENERATED from UC-6.1.80.json — DO NOT EDIT -->

---
id: "6.1.80"
title: "Pure Storage SAN port errors and fabric connectivity health"
criticality: "high"
splunkPillar: "Observability"
---

# UC-6.1.80 · Pure Storage SAN port errors and fabric connectivity health

## Description

Physical layer issues on FC ports manifest as CRC and signal loss before host multipath exhausts. Early port-level visibility avoids mysterious latency across many LUNs.

## Value

Shortens SAN bridge troubleshooting and prevents prolonged degraded multipathing.

## Implementation

Ensure hardware alert categories are not filtered at the HF. Correlate with switch syslog (separate UC) using port WWPN lookup.

## SPL

```spl
index=storage (sourcetype="purestorage:alert" OR sourcetype="purestorage:array")
| search crc OR "link down" OR "port error" OR LOS OR "signal loss"
| eval port=coalesce(fc_port, port_name, interface)
| eval arr=coalesce(array_name, array)
| stats count as errs latest(_time) as last_seen by arr, port
| sort - errs
```

## Visualization

Table (array, port, errors), timeline.

## References

- [Pure Storage Unified Add-on for Splunk (Splunkbase)](https://splunkbase.splunk.com/app/5513)
- [Pure Storage Splunk reference](https://support.purestorage.com/Solutions/Splunk/Splunk_Reference/Array_Monitoring_on_Splunk_with_PureStorage_Unified_App_and_TA)
