<!-- AUTO-GENERATED from UC-5.3.31.json — DO NOT EDIT -->

---
id: "5.3.31"
title: "Citrix ADC Compression Savings and CPU Impact"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.3.31 · Citrix ADC Compression Savings and CPU Impact

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance

*We look at how much data compression is saving and what it does to the cpu so a policy change is not a surprise in cost and heat.*

---

## Description

HTTP compression shrinks bytes on the wire but costs CPU on the Application Delivery Controller. Monitoring compression ratio, bandwidth saved, and CPU headroom together prevents turning compression on blindly when hardware is already near limits. A low savings percentage with high CPU can justify selective policies (only text types) or moving compression to origins.

## Value

Infrastructure teams monitor Citrix ADC HTTP compression ratio and CPU impact, ensuring bandwidth savings justify the processing overhead on packet engine CPUs.

## Implementation

Ingest NITRO compression and CPU counters into `citrix:netscaler:perf`. Join per vserver or content group. Add alerts for CPU above policy threshold while compression impact is low (candidates to disable) and for high savings with headroom (good candidates to expand). Document SSL versus compress ordering if applicable.

## Detailed Implementation

### Prerequisites
* Splunk Add-on for Citrix NetScaler (`Splunk_TA_citrix-netscaler`, Splunkbase 2770). NITRO stats for compression. Key metrics: `compression_ratio`, `compressed_bytes_saved`, `compression_requests`, `compression_cpu_pct`.
* Citrix ADC HTTP compression reduces response size for compressible content (HTML, JS, CSS, JSON). Compression saves bandwidth but consumes CPU. If PE CPU is already high, compression can worsen performance.

### Step 1 — - Configure data collection
Poll NITRO API: `GET /nitro/v1/stat/cmp` for compression stats. Verify:
```spl
index=netscaler sourcetype="citrix:netscaler:perf" earliest=-4h
| where isnotnull(compression_ratio) OR isnotnull(cmpbandwidthsaving)
| stats latest(compression_ratio) as ratio by host
```

### Step 2 — - Create the search and alert

**Primary search -- Compression savings vs CPU impact:**
```spl
index=netscaler sourcetype="citrix:netscaler:perf" earliest=-4h
| eval ratio=coalesce(compression_ratio, cmpratio)
| eval saved_bytes=coalesce(compressed_bytes_saved, cmpbandwidthsaving)
| eval cmp_cpu=coalesce(compression_cpu_pct, cmpcpupct)
| eval pe_cpu=coalesce(packet_engine_cpu_pct, pktcpuusagepcnt)
| bin _time span=15m
| stats avg(ratio) as avg_ratio sum(saved_bytes) as bytes_saved avg(cmp_cpu) as avg_cmp_cpu avg(pe_cpu) as avg_pe_cpu by _time, host
| eval saved_GB=round(bytes_saved/1073741824, 2)
| eval status=case(avg_cmp_cpu > 30 AND avg_pe_cpu > 80, "RISK -- compression consuming CPU on saturated system", avg_ratio < 1.5, "LOW_SAVINGS -- compression not effective", avg_cmp_cpu > 20, "MONITOR -- high compression CPU", 1==1, "OK")
| where status != "OK"
| sort status
```

### Step 3 — - Validate
(a) On ADC CLI: `stat cmp` -- compare ratio and bandwidth savings.
(b) Check: `show cmp parameter` for compression level and content types.
(c) Verify compression is applied: `curl -H "Accept-Encoding: gzip" -v https://app/` should return `Content-Encoding: gzip`.

### Step 4 — - Operationalize
Dashboard ("Citrix ADC -- Compression"):
* Row 1 -- Single-value: "Compression ratio", "Bandwidth saved (GB)", "CMP CPU %", "PE CPU %".
* Row 2 -- Compression efficiency trending.

Alerting:
* Warning (CMP CPU > 30% AND PE CPU > 80%): disable compression to free CPU.

### Step 5 — - Troubleshooting

* **Low compression ratio** -- Content may already be compressed (images, videos, PDFs). Compression only helps text-based content. Check content type configuration.

* **High compression CPU** -- Reduce compression level from gzip-9 to gzip-1 (faster, slightly less compression).

* **Compression not applied** -- Check: (1) compression policy is bound, (2) client sends `Accept-Encoding: gzip`, (3) response content type matches compression filter.

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

## Known False Positives

Incompressible or already compressed payloads can make compression savings look small without misconfiguration.

## References

- [Splunk Documentation: Splunk Add-on for Citrix NetScaler](https://docs.splunk.com/Documentation/AddOns/released/CitrixNetScaler/CitrixNetScaler)
- [Citrix ADC — Compression](https://docs.citrix.com/en-us/citrix-adc/current-release/optimization/)
