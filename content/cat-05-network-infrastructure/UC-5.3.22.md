---
id: "5.3.22"
title: "Citrix ADC SSL Offload Performance (NetScaler)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.3.22 · Citrix ADC SSL Offload Performance (NetScaler)

## Description

Citrix ADC offloads SSL/TLS processing from back-end servers, handling certificate exchange, cipher negotiation, and encryption/decryption. SSL transactions per second (TPS) is a capacity-bound metric — hardware ADC models have fixed SSL TPS limits, and VPX instances are licensed by throughput tier. Approaching the SSL TPS ceiling causes SSL handshake delays and new connection failures. Monitoring SSL performance ensures cryptographic operations do not become a bottleneck.

## Value

Citrix ADC offloads SSL/TLS processing from back-end servers, handling certificate exchange, cipher negotiation, and encryption/decryption. SSL transactions per second (TPS) is a capacity-bound metric — hardware ADC models have fixed SSL TPS limits, and VPX instances are licensed by throughput tier. Approaching the SSL TPS ceiling causes SSL handshake delays and new connection failures. Monitoring SSL performance ensures cryptographic operations do not become a bottleneck.

## Implementation

Poll the NITRO API `ssl` statistics endpoint for SSL transaction counters: `ssltotsessions`, `ssltotnewsessions`, `ssltottlsv12sessions`, `ssltottlsv13sessions`, and session reuse rates. Calculate TPS as delta of `ssltotsessions` over the poll interval. Key thresholds: SSL TPS approaching 80% of licensed/hardware capacity (plan upgrade), session reuse rate below 50% (misconfigured session caching — excessive full handshakes), and TLS 1.0/1.1 session count > 0 (deprecated protocols in use). Track cipher suite distribution to ensure compliance with security policies (disable weak ciphers like RC4, DES, 3DES).

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom scripted input polling Citrix ADC NITRO API.
• Ensure the following data sources are available: `index=network` `sourcetype="citrix:netscaler:ssl"` fields `ssl_tps`, `ssl_sessions`, `ssl_new_sessions`, `ssl_session_reuse_pct`, `ssl_protocol_version`, `cipher_suite`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll the NITRO API `ssl` statistics endpoint for SSL transaction counters: `ssltotsessions`, `ssltotnewsessions`, `ssltottlsv12sessions`, `ssltottlsv13sessions`, and session reuse rates. Calculate TPS as delta of `ssltotsessions` over the poll interval. Key thresholds: SSL TPS approaching 80% of licensed/hardware capacity (plan upgrade), session reuse rate below 50% (misconfigured session caching — excessive full handshakes), and TLS 1.0/1.1 session count > 0 (deprecated protocols in use). Track…

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network sourcetype="citrix:netscaler:ssl" metric_type="ssl_stats"
| bin _time span=5m
| stats avg(ssl_tps) as avg_tps, max(ssl_tps) as peak_tps, avg(ssl_session_reuse_pct) as reuse_pct by host, _time
| where peak_tps > 5000 OR reuse_pct < 50
| table _time, host, avg_tps, peak_tps, reuse_pct
```

Understanding this SPL

**Citrix ADC SSL Offload Performance (NetScaler)** — Citrix ADC offloads SSL/TLS processing from back-end servers, handling certificate exchange, cipher negotiation, and encryption/decryption. SSL transactions per second (TPS) is a capacity-bound metric — hardware ADC models have fixed SSL TPS limits, and VPX instances are licensed by throughput tier. Approaching the SSL TPS ceiling causes SSL handshake delays and new connection failures. Monitoring SSL performance ensures cryptographic operations do not become a bottleneck.

Documented **Data sources**: `index=network` `sourcetype="citrix:netscaler:ssl"` fields `ssl_tps`, `ssl_sessions`, `ssl_new_sessions`, `ssl_session_reuse_pct`, `ssl_protocol_version`, `cipher_suite`. **App/TA** (typical add-on context): Custom scripted input polling Citrix ADC NITRO API. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: citrix:netscaler:ssl. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype="citrix:netscaler:ssl". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Discretizes time or numeric ranges with `bin`/`bucket`.
• `stats` rolls up events into metrics; results are split **by host, _time** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where peak_tps > 5000 OR reuse_pct < 50` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Citrix ADC SSL Offload Performance (NetScaler)**): table _time, host, avg_tps, peak_tps, reuse_pct


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (SSL TPS over time), Gauge (current TPS vs capacity), Pie chart (protocol version distribution).

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

## References

- [Aruba Networks Add-on for Splunk](https://splunkbase.splunk.com/app/4668)
- [HPE Aruba ClearPass App for Splunk](https://splunkbase.splunk.com/app/7865)
- [Splunk Add-on for Cisco Meraki](https://splunkbase.splunk.com/app/5580)
