<!-- AUTO-GENERATED from UC-5.3.22.json — DO NOT EDIT -->

---
id: "5.3.22"
title: "Citrix ADC SSL Offload Performance (NetScaler)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.3.22 · Citrix ADC SSL Offload Performance (NetScaler)

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance, Capacity

*We look at how hard encryption is working on the front side so a cipher change or a busy card is not invisible to the ops team.*

---

## Description

Citrix ADC offloads SSL/TLS processing from back-end servers, handling certificate exchange, cipher negotiation, and encryption/decryption. SSL transactions per second (TPS) is a capacity-bound metric — hardware ADC models have fixed SSL TPS limits, and VPX instances are licensed by throughput tier. Approaching the SSL TPS ceiling causes SSL handshake delays and new connection failures. Monitoring SSL performance ensures cryptographic operations do not become a bottleneck.

## Value

Infrastructure teams track Citrix ADC SSL offload performance including transactions per second, session reuse rates, and hardware vs software encryption ratios to prevent SSL-related bottlenecks.

## Implementation

Poll the NITRO API `ssl` statistics endpoint for SSL transaction counters: `ssltotsessions`, `ssltotnewsessions`, `ssltottlsv12sessions`, `ssltottlsv13sessions`, and session reuse rates. Calculate TPS as delta of `ssltotsessions` over the poll interval. Key thresholds: SSL TPS approaching 80% of licensed/hardware capacity (plan upgrade), session reuse rate below 50% (misconfigured session caching — excessive full handshakes), and TLS 1.0/1.1 session count > 0 (deprecated protocols in use). Track cipher suite distribution to ensure compliance with security policies (disable weak ciphers like RC4, DES, 3DES).

## Detailed Implementation

### Prerequisites
* Splunk Add-on for Citrix NetScaler (`Splunk_TA_citrix-netscaler`, Splunkbase 2770). NITRO API SSL statistics or SNMP data. Key metrics: `ssl_new_sessions`, `ssl_session_reuse_pct`, `ssl_transactions_per_sec`, `ssl_backend_sessions`, `ssl_hw_encryption_rate`, `ssl_sw_encryption_rate`.
* SSL offload: Citrix ADC terminates SSL from clients (frontend) and optionally re-encrypts to backends (backend SSL). High SSL TPS requires hardware acceleration (MPX/SDX Cavium chips). If SSL TPS exceeds hardware capacity, requests queue.

### Step 1 — - Configure data collection
Poll NITRO API: `GET /nitro/v1/stat/ssl`. Verify:
```spl
index=netscaler sourcetype="citrix:netscaler:perf" earliest=-4h
| where isnotnull(ssl_transactions_per_sec) OR isnotnull(ssltottransactions) OR isnotnull(sslsessionreusepct)
| stats latest(ssl_transactions_per_sec) as tps latest(ssl_session_reuse_pct) as reuse by host
```

### Step 2 — - Create the search and alert

**Primary search -- SSL offload performance:**
```spl
index=netscaler sourcetype="citrix:netscaler:perf" earliest=-4h
| eval ssl_tps=coalesce(ssl_transactions_per_sec, ssltottransactions)
| eval reuse_pct=coalesce(ssl_session_reuse_pct, sslsessionreusepct)
| eval hw_rate=coalesce(ssl_hw_encryption_rate, sslhwencrate)
| eval sw_rate=coalesce(ssl_sw_encryption_rate, sslswencrate)
| bin _time span=5m
| stats avg(ssl_tps) as avg_tps max(ssl_tps) as peak_tps avg(reuse_pct) as avg_reuse avg(hw_rate) as avg_hw avg(sw_rate) as avg_sw by _time, host
| eval hw_offload_pct=if((avg_hw + avg_sw) > 0, round(100*avg_hw/(avg_hw + avg_sw), 1), null())
| eval status=case(avg_reuse < 50, "LOW_REUSE -- excessive full handshakes", hw_offload_pct < 80 AND isnotnull(hw_offload_pct), "SW_FALLBACK -- hardware not handling all SSL", peak_tps > 50000, "HIGH_VOLUME", 1==1, "OK")
| where status != "OK"
| sort status, -peak_tps
```

### Step 3 — - Validate
(a) On ADC CLI: `stat ssl` -- compare TPS and session reuse with Splunk.
(b) Check hardware acceleration: `show ssl hardware` -- verify chips are operational.
(c) Compare peak TPS with the ADC model's rated SSL TPS capacity.

### Step 4 — - Operationalize
Dashboard ("Citrix ADC -- SSL Performance"):
* Row 1 -- Single-value: "SSL TPS", "Session reuse %", "HW offload %", "Peak TPS".
* Row 2 -- Per-ADC SSL performance table.
* Row 3 -- SSL TPS trending timechart.

Alerting:
* Warning (session reuse < 50%): excessive full handshakes -- performance impact.
* Warning (HW offload < 80%): SSL falling back to software -- CPU impact.

### Step 5 — - Troubleshooting

* **Low session reuse** -- Clients not reusing SSL sessions. Check: (1) SSL profile session cache size, (2) session timeout (default 300s -- increase if needed), (3) client compatibility (some older clients don't support session tickets).

* **High SW encryption** -- Hardware SSL chip may be at capacity or disabled. Check: `show ssl hardware` -- if "Status: DOWN", the chip needs attention.

* **SSL TPS approaching model limit** -- Consider upgrading the ADC or deploying additional instances behind a DNS/GSLB layer.

## SPL

```spl
index=network sourcetype="citrix:netscaler:ssl" metric_type="ssl_stats"
| bin _time span=5m
| stats avg(ssl_tps) as avg_tps, max(ssl_tps) as peak_tps, avg(ssl_session_reuse_pct) as reuse_pct by host, _time
| where peak_tps > 5000 OR reuse_pct < 50
| table _time, host, avg_tps, peak_tps, reuse_pct
```

## Visualization

Line chart (SSL TPS over time), Gauge (current TPS vs capacity), Pie chart (protocol version distribution).

## Known False Positives

Old ciphers, pinned apps, and hardware offload quirks can all move SSL front-end numbers without a single root cause.

## References

- [Aruba Networks Add-on for Splunk](https://splunkbase.splunk.com/app/4668)
- [HPE Aruba ClearPass App for Splunk](https://splunkbase.splunk.com/app/7865)
- [Splunk Add-on for Cisco Meraki](https://splunkbase.splunk.com/app/5580)
