<!-- AUTO-GENERATED from UC-5.3.32.json — DO NOT EDIT -->

---
id: "5.3.32"
title: "Citrix ADC DNS/ADNS Service Health"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.3.32 · Citrix ADC DNS/ADNS Service Health

## Description

Authoritative and DNS proxy workloads on the Application Delivery Controller (ADNS) must resolve fast and with valid responses. Spikes in failure codes, DNSSEC validation errors, or response-time percentiles show overload, bad zones, or upstream issues before applications fail name resolution. Query-rate anomalies also reveal floods or cache misses.

## Value

Authoritative and DNS proxy workloads on the Application Delivery Controller (ADNS) must resolve fast and with valid responses. Spikes in failure codes, DNSSEC validation errors, or response-time percentiles show overload, bad zones, or upstream issues before applications fail name resolution. Query-rate anomalies also reveal floods or cache misses.

## Implementation

Forward high-severity and DNS service syslog to `index=netscaler`. Parse Rcode, query type, and latency if available. For SNMP, poll process CPU and request counters. Alert on any sustained SERVFAIL, DNSSEC `Bogus` or `Insecure` transition when policy says secure, and on p95 latency above SLO. Rate-limit log volume with filters if needed.

## Detailed Implementation

Prerequisites: DNS/ADNS logging enabled with reviewed rate and privacy; index=netscaler receiving citrix:netscaler:syslog and optional citrix:netscaler:snmp. Step 1: Configure data collection — Set syslog verbosity to capture Rcode, query type, and latency; props.conf [citrix:netscaler:syslog] with EXTRACT-DNS for SERVFAIL/timeout and FIELDALIAS dns_rtt_ms; NTP on all ADCs. Step 2: Create the search and alert — Tune events/300 to your TPS; page on sustained Rcode surges, DNSSEC chain breaks, p95_rtt>150ms (start near this value and adjust to baseline). Step 3: Validate — In lab, induce validation failure; confirm; run synthetic queries and compare `| timechart p95(dns_rtt_ms)` to ADC CLI stats. Step 4: Operationalize — Align with the enterprise DNS team; if ADNS is proxying, add upstream resolver checks; chronic failures go to the Citrix ADC and DNS service owners; validation search: `index=netscaler sourcetype="citrix:netscaler:syslog" earliest=-30m DNS | stats count by host, Rcode`.

## SPL

```spl
index=netscaler (sourcetype="citrix:netscaler:syslog" OR sourcetype="citrix:netscaler:snmp") (ADNS OR "dns" OR nameserver OR NXDOMAIN OR SERVFAIL OR DNSSEC OR Rcode)
| eval is_fail=if(match(_raw, "(?i)(SERVFAIL|Refused|timeout)"),1,0)
| rex field=_raw max_match=0 "response[\\s:]+(?<rtt_parsed>\\d+)\\s*ms"
| eval rtt=coalesce(dns_rtt_ms, rtt_parsed)
| bin _time span=5m
| stats count as events, sum(is_fail) as fail_ct, p95(rtt) as p95_rtt, dc(dns_name) as zones, latest(host) as adc by _time, host
| where fail_ct>0 OR p95_rtt>150 OR events/300 > 10000
| table _time, adc, events, fail_ct, p95_rtt, zones
```

## Visualization

Time chart: queries per second and failures, single value: p95 response time, table: top failure strings.

## References

- [Splunk Documentation: Splunk Add-on for Citrix NetScaler](https://docs.splunk.com/Documentation/AddOns/released/CitrixNetScaler/CitrixNetScaler)
- [Citrix ADC — DNS](https://docs.citrix.com/en-us/citrix-adc/current-release/dns/dns-citrix.html)
