<!-- AUTO-GENERATED from UC-5.3.29.json — DO NOT EDIT -->

---
id: "5.3.29"
title: "Citrix ADC Frontend vs Backend RTT Analysis"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.3.29 · Citrix ADC Frontend vs Backend RTT Analysis

## Description

Separating client-side from server-side round-trip time on the Application Delivery Controller pinpoints where delay accumulates: last mile, middle mile, or data center. AppFlow or equivalent records expose both legs so you can tell user Wi-Fi issues from database latency without guessing. Sustained backend-side RTT growth drives pool tuning and app fixes; client-heavy RTT points to peering, DNS, or edge problems.

## Value

Separating client-side from server-side round-trip time on the Application Delivery Controller pinpoints where delay accumulates: last mile, middle mile, or data center. AppFlow or equivalent records expose both legs so you can tell user Wi-Fi issues from database latency without guessing. Sustained backend-side RTT growth drives pool tuning and app fixes; client-heavy RTT points to peering, DNS, or edge problems.

## Implementation

Enable AppFlow with timing fields; ensure the Splunk TA extracts numeric RTT. Index to `index=netscaler`. If field names differ, create aliases in props. Use segment classification to tag tickets (network vs app). Add geo or ASN for client leg only if policy allows. Trend weekly for capacity reports.

## Detailed Implementation

Prerequisites: AppFlow to Splunk with client/server RTT and vserver; a short field-knowledge document with exact field names. Step 1: Configure data collection — Match AppFlow sampling to visibility; props.conf [citrix:netscaler:appflow] with FIELDALIAS for client_rtt_ms and server_rtt_ms; use transforms.conf to redact high-cardinality URL paths if required. Step 2: Create the search and alert — Tweak 1.2x ratio to your app mix; page when backend p95 RTT regresses 50% from a 7d baseline, or when segment flips to client_network during known backbone work; start with p95>200ms and tune. Step 3: Validate — Correlate with synthetics: `index=netscaler sourcetype="citrix:netscaler:appflow" earliest=-4h | stats p95(client_rtt) p95(server_rtt) by vserver` during a known backend slowdown; server leg should rise while client stable. Step 4: Operationalize — One shared Network and App team dashboard and escalation runbook; if skew persists, escalate to Citrix ADC and application teams jointly.

## SPL

```spl
index=netscaler sourcetype="citrix:netscaler:appflow"
| eval client_rtt=coalesce('client_rtt_ms', 'avg_client_rtt', client_rtt, 0), server_rtt=coalesce('server_rtt_ms', 'avg_server_rtt', server_rtt, 0)
| where client_rtt>0 OR server_rtt>0
| eval rtt_diff=abs(client_rtt - server_rtt), segment=if(client_rtt>1.2*server_rtt,
  "client_network", if(server_rtt>1.2*client_rtt, "server_network_or_backend", "balanced"))
| bin _time span=5m
| stats median(client_rtt) as p50_c, median(server_rtt) as p50_s, p95(client_rtt) as p95_c, p95(server_rtt) as p95_s, count as flows by _time, host, vserver, segment
| where p95_c>200 OR p95_s>200 OR p95_s>1.5*p95_c
| table _time, host, vserver, segment, p50_c, p50_s, p95_c, p95_s, flows
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.action All_Traffic.dvc span=1h
| where count>0
| sort -count
```

## Visualization

Stacked time chart: median client vs server RTT, heatmap of vservers by segment, box plot for tail latency by region.

## References

- [Splunk Documentation: Splunk Add-on for Citrix NetScaler](https://docs.splunk.com/Documentation/AddOns/released/CitrixNetScaler/CitrixNetScaler)
- [CIM: Network_Traffic](https://docs.splunk.com/Documentation/CIM/latest/User/Network_Traffic)
- [Citrix ADC — AppFlow and analytics](https://docs.citrix.com/en-us/citrix-adc/current-release/application-analytics.html)
