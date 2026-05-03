<!-- AUTO-GENERATED from UC-5.3.32.json — DO NOT EDIT -->

---
id: "5.3.32"
title: "Citrix ADC DNS/ADNS Service Health"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.3.32 · Citrix ADC DNS/ADNS Service Health

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Availability

*We follow DNS and address service health in the same view so a dead listener or a loop in answers is a clear lead when apps fail in odd ways.*

---

## Description

Authoritative and DNS proxy workloads on the Application Delivery Controller (ADNS) must resolve fast and with valid responses. Spikes in failure codes, DNSSEC validation errors, or response-time percentiles show overload, bad zones, or upstream issues before applications fail name resolution. Query-rate anomalies also reveal floods or cache misses.

## Value

Infrastructure teams monitor Citrix ADC DNS/ADNS service health including query rates, error rates, and resolution latency, ensuring DNS infrastructure reliability for dependent applications.

## Implementation

Forward high-severity and DNS service syslog to `index=netscaler`. Parse Rcode, query type, and latency if available. For SNMP, poll process CPU and request counters. Alert on any sustained SERVFAIL, DNSSEC `Bogus` or `Insecure` transition when policy says secure, and on p95 latency above SLO. Rate-limit log volume with filters if needed.

## Detailed Implementation

### Prerequisites
* Splunk Add-on for Citrix NetScaler (`Splunk_TA_citrix-netscaler`, Splunkbase 2770). Citrix ADC DNS/ADNS service syslog and NITRO stats. Key fields: `dns_queries`, `dns_responses`, `dns_errors`, `dns_service_state`, `dns_latency_ms`.
* Citrix ADC as DNS/ADNS: (1) DNS proxy -- forwards DNS queries to backend DNS servers with caching, (2) ADNS -- authoritative DNS server (for GSLB domains), (3) DNS load balancing -- distributes queries across multiple DNS servers.

### Step 1 — - Configure data collection
Verify DNS service data:
```spl
index=netscaler (sourcetype="citrix:netscaler:syslog" OR sourcetype="citrix:netscaler:perf") ("DNS" OR "ADNS" OR "dns" OR "nameserver") earliest=-4h
| stats count by host
```

### Step 2 — - Create the search and alert

**Primary search -- DNS/ADNS service health:**
```spl
index=netscaler (sourcetype="citrix:netscaler:syslog" OR sourcetype="citrix:netscaler:perf") ("DNS" OR "ADNS" OR "dns" OR "nameserver") earliest=-4h
| eval dns_svc_state=coalesce(dns_service_state, service_state)
| eval queries=coalesce(dns_queries, dnsqueries)
| eval errors=coalesce(dns_errors, dnserrors)
| eval latency=coalesce(dns_latency_ms, dnsavglatency)
| bin _time span=5m
| stats latest(dns_svc_state) as state sum(queries) as total_queries sum(errors) as total_errors avg(latency) as avg_latency by _time, host
| eval error_rate=if(total_queries > 0, round(100*total_errors/total_queries, 2), 0)
| eval qps=round(total_queries/300, 0)
| eval status=case(match(lower(state), "down"), "CRITICAL -- DNS service DOWN", error_rate > 5, "HIGH -- elevated DNS errors", avg_latency > 50, "WARNING -- slow DNS resolution", 1==1, "OK")
| where status != "OK"
| sort status
```

### Step 3 — - Validate
(a) On ADC CLI: `stat dns` -- compare query counts and error rates.
(b) Test DNS resolution: `nslookup app.example.com <adc_ip>` -- verify response.
(c) Check ADNS records: `show dns addrec` for authoritative records.

### Step 4 — - Operationalize
Dashboard ("Citrix ADC -- DNS Health"):
* Row 1 -- Single-value: "DNS QPS", "Error rate", "Avg latency (ms)", "Service state".
* Row 2 -- DNS health trending.

Alerting:
* Critical (DNS service DOWN): DNS resolution will fail for dependent applications.
* Warning (DNS error rate > 5%): investigate backend DNS server health.

### Step 5 — - Troubleshooting

* **DNS service DOWN** -- Check: (1) backend nameserver health monitors, (2) service group members, (3) DNS vserver binding.

* **High error rate** -- Check: (1) NXDOMAIN responses (queried domains don't exist), (2) SERVFAIL (backend DNS server errors), (3) DNS cache pollution.

* **High latency** -- Backend DNS servers slow. Check: DNS server load, network latency to backend DNS, enable DNS caching on the ADC.

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

## Known False Positives

Long TTLs, slow resolvers, and noisy clients can make DNS vserver health look worse than the real user path.

## References

- [Splunk Documentation: Splunk Add-on for Citrix NetScaler](https://docs.splunk.com/Documentation/AddOns/released/CitrixNetScaler/CitrixNetScaler)
- [Citrix ADC — DNS](https://docs.citrix.com/en-us/citrix-adc/current-release/dns/dns-citrix.html)
