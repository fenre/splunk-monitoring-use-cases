<!-- AUTO-GENERATED from UC-5.2.24.json — DO NOT EDIT -->

---
id: "5.2.24"
title: "Traffic Shaping Effectiveness and QoS Policy Analysis (Meraki MX)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.2.24 · Traffic Shaping Effectiveness and QoS Policy Analysis (Meraki MX)

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance

*We look at how traffic is shaped and marked so the team can see whether important apps still get a fair share when the link is full.*

---

## Description

Measures the impact of traffic shaping policies on bandwidth distribution and priority.

## Value

Operations teams evaluate Meraki MX traffic shaping effectiveness by application category, identifying over-shaped critical applications and under-shaped bandwidth hogs.

## Implementation

Extract priority_queue field from flow logs. Measure bandwidth by priority.

## Detailed Implementation

### Prerequisites
* Meraki MX traffic shaping logs and API data. Data in `index=meraki` with `sourcetype=meraki:api:trafficshaping` or `sourcetype=meraki:events`. Key metrics: bandwidth allocated, bandwidth consumed, traffic shaping rule, application category.
* Traffic shaping: Meraki MX classifies applications using Layer 7 DPI and applies bandwidth limits, priority levels, and DSCP tags. Shapes traffic per application category (e.g., video streaming low priority, VoIP high priority).

### Step 1 — - Configure data collection
```
# Dashboard > Security & SD-WAN > Traffic shaping
# Configure per-application bandwidth limits and priorities
# API: GET /networks/{networkId}/appliance/trafficShaping
```
Verify:
```spl
index=meraki earliest=-4h
| where match(_raw, "(?i)traffic.shaping|bandwidth|qos|throttl|shape")
| stats count by sourcetype
```

### Step 2 — - Create the search and alert

**Primary search -- Traffic shaping effectiveness:**
```spl
index=meraki (sourcetype="meraki:events" OR sourcetype="meraki:api:trafficshaping") earliest=-4h
| where match(_raw, "(?i)traffic.shaping|shap|bandwidth|limit|throttl|application.*category")
| eval app_category=coalesce(application, app_category, category)
| eval shaped=if(match(_raw, "(?i)shaped|throttl|limit.*applied"), 1, 0)
| eval bandwidth_kbps=tonumber(coalesce(bandwidth, sent_kbps, recv_kbps))
| stats count as events sum(shaped) as shaped_events avg(bandwidth_kbps) as avg_bw_kbps by app_category
| eval shape_rate=if(events > 0, round(100*shaped_events/events, 1), 0)
| eval severity=case(shape_rate > 50, "WARNING -- >50% traffic shaped for ".app_category, avg_bw_kbps > 10000, "INFO -- high bandwidth category", 1==1, "OK")
| where severity != "OK"
| sort -shape_rate
```

### Step 3 — - Validate
(a) Dashboard: Security & SD-WAN > Traffic shaping -- review rules and application categories.
(b) Compare bandwidth usage with Dashboard > Network-wide > Traffic analytics.
(c) Test shaping by generating traffic for a shaped category and verifying throttling.

### Step 4 — - Operationalize
Dashboard ("Meraki MX -- Traffic Shaping"):
* Row 1 -- Single-value: "Shaped flows", "Top shaped category", "Bandwidth savings".
* Row 2 -- Shaping by application category.

### Step 5 — - Troubleshooting

* **Critical application being shaped** -- Review traffic shaping rules. Ensure business-critical apps (VoIP, video conferencing) have "High" priority and are not bandwidth-limited.

* **Shaping not applied** -- Check: (1) traffic shaping is enabled per-network, (2) application classification is correct (DPI may misidentify apps), (3) bandwidth limits are set.

* **High bandwidth despite shaping** -- Shaping limits may be per-client, not aggregate. Check if limits are per-SSID or per-client.

## SPL

```spl
index=cisco_network sourcetype="meraki" type=flow priority_queue=*
| stats sum(bytes) as total_bytes, avg(latency) as avg_latency by priority_queue
| eval efficiency=round(total_bytes/sum(total_bytes)*100, 2)
```

## Visualization

Stacked bar chart of bandwidth by priority; latency by QoS class; efficiency gauge.

## Known False Positives

Overnight jobs, large downloads, and guest traffic can shift which queues look busy; compare to known workloads.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
