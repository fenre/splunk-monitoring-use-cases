<!-- AUTO-GENERATED from UC-5.1.53.json — DO NOT EDIT -->

---
id: "5.1.53"
title: "Cellular Data Usage and Overage Monitoring (Meraki MG)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.1.53 · Cellular Data Usage and Overage Monitoring (Meraki MG)

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance

*We help you know early when something looks wrong with cellular data usage and overage monitoring so the team can act before it grows into a bigger outage.*

---

## Description

Tracks cellular data consumption to manage carrier costs and prevent overages.

## Value

Operations teams monitor Meraki MG cellular data usage against plan limits, preventing overage charges by alerting before data caps are reached and identifying high-consumption patterns.

## Implementation

Query MG API for data usage metrics. Track monthly consumption.

## Detailed Implementation

### Prerequisites
* Meraki MG cellular data usage from Dashboard API. Data in `index=meraki` with `sourcetype=meraki:api:cellular:usage` or `sourcetype=meraki:api:clients`. Key fields: `sent`, `recv`, `sim`, `apn`.
* Meraki MG data plans: cellular has per-GB data costs. Monitoring usage prevents bill shock and enables proactive data plan adjustments. API: `GET /devices/{serial}/cellular/sims` returns data usage per SIM.

### Step 1 — - Configure data collection
```
[meraki_mg_usage]
interval = 3600
sourcetype = meraki:api:cellular:usage
index = meraki
# Poll hourly: GET /devices/{serial}/cellular/sims
```
Verify:
```spl
index=meraki sourcetype="meraki:api:cellular:usage" earliest=-7d
| stats sum(sent) sum(recv) by host
```

### Step 2 — - Create the search and alert

**Primary search -- Cellular data usage and overage monitoring:**
```spl
index=meraki sourcetype="meraki:api:cellular:usage" earliest=-30d
| eval device=coalesce(serial, host)
| eval sent_gb=tonumber(sent)/1073741824
| eval recv_gb=tonumber(recv)/1073741824
| eval total_gb=sent_gb + recv_gb
| lookup meraki_networks.csv serial AS device OUTPUT network_name, site_name
| lookup cellular_plans.csv serial AS device OUTPUT data_limit_gb, plan_cost_monthly
| bin _time span=1d
| stats sum(total_gb) as daily_gb by _time, network_name, device, data_limit_gb
| eventstats sum(daily_gb) as month_total by device
| eval month_total=round(month_total, 2)
| eval daily_gb=round(daily_gb, 2)
| eval pct_used=if(isnotnull(data_limit_gb) AND data_limit_gb > 0, round(100*month_total/data_limit_gb, 1), null())
| eval severity=case(
    pct_used > 90, "CRITICAL -- cellular data plan at ".pct_used."% (overage imminent)",
    pct_used > 75, "WARNING -- cellular data plan at ".pct_used."%",
    daily_gb > 5, "INFO -- high daily cellular usage (".daily_gb." GB)",
    1==1, "OK")
| where severity != "OK"
| dedup device sortby -_time
| table network_name, device, month_total, data_limit_gb, pct_used, severity
| sort severity, -pct_used
```

### Step 3 — - Validate
(a) Dashboard: Cellular gateway > Data usage -- check current usage.
(b) Compare with carrier billing portal usage data.
(c) Verify data plan limits in lookup.

### Step 4 — - Operationalize
Dashboard ("Meraki MG -- Data Usage"):
* Row 1 -- Single-value: "Monthly usage (GB)", "Plan limit (GB)", "% used".
* Row 2 -- Daily data usage timechart.

Alert: Critical (>90% of data plan): contact carrier or reduce cellular traffic.

### Step 5 — - Troubleshooting

* **Unexpected high usage** -- Check what devices/applications are consuming data. Apply traffic shaping rules to limit non-essential traffic over cellular.

* **Data plan limit reached** -- Options: (1) increase plan, (2) restrict traffic to business-critical only, (3) add supplemental plan, (4) failback to primary WAN.

* **Usage tracking mismatch** -- API and carrier may report differently (carrier counts overhead). Use carrier portal as billing source of truth.

## SPL

```spl
index=cisco_network sourcetype="meraki:api" device_type=MG data_usage=*
| stats sum(data_usage) as total_data_usage_mb by cellular_gateway_id
| eval overage_alert=if(total_data_usage_mb > 100000, "Yes", "No")
```

## Visualization

Data usage gauge per gateway; consumption timeline; overage alert table.

## Known False Positives

Carrier testing, local SIM swaps, and planned tower work can look like a connectivity fault. Compare the Meraki event log to the same window in Splunk.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
