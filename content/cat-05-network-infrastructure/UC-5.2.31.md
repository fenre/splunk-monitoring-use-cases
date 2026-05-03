<!-- AUTO-GENERATED from UC-5.2.31.json — DO NOT EDIT -->

---
id: "5.2.31"
title: "Application Visibility and Network Application Trending (Meraki MX)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.2.31 · Application Visibility and Network Application Trending (Meraki MX)

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Capacity

*We trend which applications and traffic types dominate so heavy cloud use, file shares, and video do not take you by surprise.*

---

## Description

Identifies top applications and protocols on network to understand usage patterns and detect anomalies.

## Value

Operations teams trend Meraki MX application visibility data to identify bandwidth-dominant applications and track usage patterns for capacity planning and policy enforcement.

## Implementation

Extract application field from flow logs. Aggregate by app and category.

## Detailed Implementation

### Prerequisites
* Meraki MX application visibility data from Dashboard API. Data in `index=meraki` with `sourcetype=meraki:api:traffic` or `sourcetype=meraki:api:clients`. Key fields: `application`, `sent_kbps`, `recv_kbps`, `num_clients`, `network`.
* Meraki application visibility: MX uses Layer 7 DPI to classify traffic by application (e.g., Zoom, Microsoft 365, YouTube, Salesforce). API endpoint: `/networks/{networkId}/traffic`.

### Step 1 — - Configure data collection
```
# inputs.conf
[meraki_traffic_analytics]
interval = 900
sourcetype = meraki:api:traffic
index = meraki
# API: GET /networks/{networkId}/traffic?timespan=900
```
Verify:
```spl
index=meraki sourcetype="meraki:api:traffic" earliest=-4h
| stats sum(sent) as total_sent sum(recv) as total_recv by application
| sort -total_sent | head 20
```

### Step 2 — - Create the search and alert

**Primary search -- Application visibility trending:**
```spl
index=meraki sourcetype="meraki:api:traffic" earliest=-24h
| eval app=coalesce(application, app_name)
| eval sent_mb=tonumber(sent)/1048576
| eval recv_mb=tonumber(recv)/1048576
| eval total_mb=sent_mb + recv_mb
| eval clients=tonumber(numClients)
| bin _time span=1h
| stats sum(total_mb) as total_mb avg(clients) as avg_clients by _time, app
| eventstats sum(total_mb) as hourly_total by _time
| eval app_pct=round(100*total_mb/hourly_total, 1)
| eval severity=case(app_pct > 30, "WARNING -- ".app." consuming >30% of bandwidth", total_mb > 1000 AND match(app, "(?i)youtube|netflix|tiktok|streaming"), "INFO -- high streaming bandwidth", 1==1, "OK")
| where severity != "OK"
| table _time, app, total_mb, app_pct, avg_clients, severity
```

### Step 3 — - Validate
(a) Dashboard: Network-wide > Traffic analytics -- compare top applications.
(b) Verify application classification accuracy for critical apps (Office 365, Zoom).
(c) Compare bandwidth totals with WAN uplink utilization.

### Step 4 — - Operationalize
Dashboard ("Meraki MX -- Application Visibility"):
* Row 1 -- Single-value: "Top application", "Total bandwidth (GB)", "Application categories".
* Row 2 -- Application bandwidth timechart.
* Row 3 -- Application distribution pie chart.

### Step 5 — - Troubleshooting

* **Unknown/unclassified application** -- Application may use non-standard ports or encryption. Check: (1) Meraki DPI database version, (2) consider adding custom application rules.

* **Critical app misclassified** -- Verify application classification in Dashboard. Custom applications can be defined for internal services.

* **Streaming consuming excessive bandwidth** -- Apply traffic shaping (UC-5.2.24) to limit streaming categories. Prioritize business applications.

## SPL

```spl
index=cisco_network sourcetype="meraki" type=flow application=*
| stats sum(bytes) as app_bytes, count as flow_count by application, application_category
| eval app_bandwidth_pct=round(app_bytes*100/sum(app_bytes), 2)
| sort - app_bytes
| head 20
```

## CIM SPL

```spl
| tstats `summariesonly` sum(All_Traffic.bytes_in) as bytes_in sum(All_Traffic.bytes_out) as bytes_out
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.app span=1h
| eval bytes=bytes_in+bytes_out
| sort -bytes
```

## Visualization

App bandwidth pie chart; top apps bar chart; bandwidth timeline by app.

## Known False Positives

Releases, batch jobs, and video calls can make one application or department dominate bandwidth in a good week.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
- [CIM: Network_Traffic](https://docs.splunk.com/Documentation/CIM/latest/User/Network_Traffic)
