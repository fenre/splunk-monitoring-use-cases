<!-- AUTO-GENERATED from UC-5.3.29.json — DO NOT EDIT -->

---
id: "5.3.29"
title: "Citrix ADC Frontend vs Backend RTT Analysis"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.3.29 · Citrix ADC Frontend vs Backend RTT Analysis

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Performance

*We compare front and back delay from flow data so a slow data center, a far user, and a hot middle are not one vague "slowness" in chat.*

---

## Description

Separating client-side from server-side round-trip time on the Application Delivery Controller pinpoints where delay accumulates: last mile, middle mile, or data center. AppFlow or equivalent records expose both legs so you can tell user Wi-Fi issues from database latency without guessing. Sustained backend-side RTT growth drives pool tuning and app fixes; client-heavy RTT points to peering, DNS, or edge problems.

## Value

Application delivery teams decompose Citrix ADC transaction latency into frontend (client-to-ADC) and backend (ADC-to-server) RTT components, isolating whether slowness originates from the network or backends.

## Implementation

Enable AppFlow with timing fields; ensure the Splunk TA extracts numeric RTT. Index to `index=netscaler`. If field names differ, create aliases in props. Use segment classification to tag tickets (network vs app). Add geo or ASN for client leg only if policy allows. Trend weekly for capacity reports.

## Detailed Implementation

### Prerequisites
* Splunk Add-on for Citrix NetScaler (`Splunk_TA_citrix-netscaler`, Splunkbase 2770). AppFlow or NITRO stats providing RTT data. Key metrics: `client_rtt_ms` (frontend RTT between client and ADC), `server_rtt_ms` (backend RTT between ADC and backend), `total_response_time_ms`.
* RTT decomposition: Total latency = Client RTT + ADC processing + Server RTT + Backend processing. By comparing frontend and backend RTT, you can isolate: (1) network latency (WAN/LAN), (2) ADC processing time, (3) backend application time.

### Step 1 — - Configure data collection
AppFlow records include both client and server RTT. NITRO API: `GET /nitro/v1/stat/protocolhttp` for aggregate RTT. Verify:
```spl
index=netscaler (sourcetype="citrix:netscaler:appflow" OR sourcetype="citrix:netscaler:perf") earliest=-4h
| where isnotnull(client_rtt_ms) OR isnotnull(server_rtt_ms)
| stats avg(client_rtt_ms) as avg_client_rtt avg(server_rtt_ms) as avg_server_rtt by host
```

### Step 2 — - Create the search and alert

**Primary search -- Frontend vs backend RTT analysis:**
```spl
index=netscaler (sourcetype="citrix:netscaler:appflow" OR sourcetype="citrix:netscaler:perf") earliest=-4h
| eval client_rtt=coalesce(client_rtt_ms, clientrtt)
| eval server_rtt=coalesce(server_rtt_ms, serverrtt)
| eval vs=coalesce(vserver_name, vs_name)
| bin _time span=5m
| stats avg(client_rtt) as avg_client_rtt p95(client_rtt) as p95_client avg(server_rtt) as avg_server_rtt p95(server_rtt) as p95_server count as transactions by _time, host, vs
| eval rtt_ratio=if(avg_server_rtt > 0, round(avg_client_rtt/avg_server_rtt, 1), null())
| eval bottleneck=case(p95_server > 100 AND p95_client < 50, "BACKEND -- server latency is the bottleneck", p95_client > 100 AND p95_server < 20, "NETWORK -- client WAN latency is dominant", p95_server > 100 AND p95_client > 100, "BOTH -- high latency on both sides", 1==1, "OK")
| where bottleneck != "OK"
| sort bottleneck, -p95_server
```

### Step 3 — - Validate
(a) On ADC CLI: `stat protocolhttp` -- compare RTT values.
(b) Compare client RTT with expected WAN latency for remote users.
(c) Compare server RTT with ping latency to backend servers.

### Step 4 — - Operationalize
Dashboard ("Citrix ADC -- RTT Analysis"):
* Row 1 -- Single-value: "Avg client RTT", "Avg server RTT", "P95 client RTT", "P95 server RTT".
* Row 2 -- Per-vserver RTT breakdown with bottleneck identification.
* Row 3 -- RTT trending timechart (client vs server).

Alerting:
* Warning (server P95 RTT > 100ms): backend latency degradation.
* Info (client P95 RTT > 200ms): remote users experiencing high latency.

### Step 5 — - Troubleshooting

* **High server RTT** -- Backend application is slow. Check: database, external API calls, GC pauses. Not a network issue.

* **High client RTT** -- Clients are far from the ADC (WAN latency). Consider: CDN, GSLB to direct users to closer data center, TCP optimization profiles (window scaling, congestion control).

* **Both high** -- May be ADC overloaded. Check PE CPU (UC-5.3.20).

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

## Known False Positives

Wi-Fi, internet paths, and user geography spread client times; a gap between front and back is not always the appliance.

## References

- [Splunk Documentation: Splunk Add-on for Citrix NetScaler](https://docs.splunk.com/Documentation/AddOns/released/CitrixNetScaler/CitrixNetScaler)
- [CIM: Network_Traffic](https://docs.splunk.com/Documentation/CIM/latest/User/Network_Traffic)
- [Citrix ADC — AppFlow and analytics](https://docs.citrix.com/en-us/citrix-adc/current-release/application-analytics.html)
