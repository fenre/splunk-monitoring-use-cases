<!-- AUTO-GENERATED from UC-5.3.31.json — DO NOT EDIT -->

---
id: "5.3.31"
title: "Citrix ADC Compression Savings and CPU Impact"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.3.31 · Citrix ADC Compression Savings and CPU Impact

## Description

HTTP compression shrinks bytes on the wire but costs CPU on the Application Delivery Controller. Monitoring compression ratio, bandwidth saved, and CPU headroom together prevents turning compression on blindly when hardware is already near limits. A low savings percentage with high CPU can justify selective policies (only text types) or moving compression to origins.

## Value

HTTP compression shrinks bytes on the wire but costs CPU on the Application Delivery Controller. Monitoring compression ratio, bandwidth saved, and CPU headroom together prevents turning compression on blindly when hardware is already near limits. A low savings percentage with high CPU can justify selective policies (only text types) or moving compression to origins.

## Implementation

Ingest NITRO compression and CPU counters into `citrix:netscaler:perf`. Join per vserver or content group. Add alerts for CPU above policy threshold while compression impact is low (candidates to disable) and for high savings with headroom (good candidates to expand). Document SSL versus compress ordering if applicable.

## Detailed Implementation

Prerequisites
• `index=netscaler` with compression bytes (`compress_*`/`comp_*`) and `cpu_use_pct` or per-PE; `lbvserver` when present. Note SSL offload: compression is often on plaintext only—state that in the SOP.

Step 1 — Configure data collection
One TA poll per interval binding CPU+comp. If multi-PE, pre-`stats` by host. `props` to force `tonumber()`. Tag vservers with text vs binary policy if split.

Step 2 — Create the search and alert
SPL `peak_cpu>85 AND avg_comp_pct<5` means high CPU, low gain—narrow to `text/*` or disable. Inverse: `avg_comp_pct>20 AND avg_cpu<70` to expand. Set CPU threshold 80–90 by MPX/VPX class in lookup. Ignore first hour after ADC reboot (warmup).

Step 3 — Validate
Compare vservers, services, and load-balancing state in the Citrix ADC management view or command line for the same time window and objects.
Step 4 — Operationalize
Panel: comp ratio + same-axis CPU; table top vservers by `total_saved_mb`. Escalation: cap team. Review after SSL/cipher or vCPU change. Cross-check high CPU with other ADC features in perf sourcetype.

## SPL

```spl
index=netscaler sourcetype="citrix:netscaler:perf" ("compress" OR comp_ OR gzip OR deflate)
| eval bytes_in=coalesce(compress_bytes_in, comp_bytes_in, 0), bytes_out=coalesce(compress_bytes_out, comp_bytes_out, 0), cpu=coalesce(cpu_use_pct, packet_cpu_use_pct, 0)
| eval comp_ratio=if(bytes_out>0, round((bytes_in-bytes_out)/bytes_in*100,1), 0), savings_mb=if(bytes_in>0, (bytes_in-bytes_out)/1024/1024, 0)
| bin _time span=5m
| stats avg(comp_ratio) as avg_comp_pct, sum(savings_mb) as total_saved_mb, avg(cpu) as avg_cpu, max(cpu) as peak_cpu by _time, host, lbvserver
| where avg_comp_pct>0
| where peak_cpu>85 AND avg_comp_pct<5
| table _time, host, lbvserver, avg_comp_pct, total_saved_mb, avg_cpu, peak_cpu
```

## Visualization

Line chart: compression percent saved, overlay CPU; table of top vservers by saved megabytes; stacked bar: CPU time estimate by feature if available.

## References

- [Splunk Documentation: Splunk Add-on for Citrix NetScaler](https://docs.splunk.com/Documentation/AddOns/released/CitrixNetScaler/CitrixNetScaler)
- [Citrix ADC — Compression](https://docs.citrix.com/en-us/citrix-adc/current-release/optimization/compression.html)
