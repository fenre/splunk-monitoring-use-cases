<!-- AUTO-GENERATED from UC-5.2.32.json — DO NOT EDIT -->

---
id: "5.2.32"
title: "Bandwidth by Application and Department (Meraki MX)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.2.32 · Bandwidth by Application and Department (Meraki MX)

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance

*We slice bandwidth by team or site when you bring your own table so you can see who is driving cost and help before bills spike.*

---

## Description

Tracks bandwidth consumption by application and business unit for chargeback and optimization.

## Value

Operations teams break down Meraki MX bandwidth consumption by application and organizational department, enabling cost allocation and policy enforcement per business unit.

## Implementation

Correlate flows with IP-to-department mapping. Aggregate by app and dept.

## Detailed Implementation

### Prerequisites
* Meraki MX application and client traffic data from API. Data in `index=meraki` with `sourcetype=meraki:api:traffic` or `sourcetype=meraki:api:clients`. Enrichment: `department_mapping.csv` lookup (client_mac or IP to department/team).
* Per-department bandwidth analysis requires client identification (via VLAN, subnet, or client metadata) mapped to organizational units.

### Step 1 — - Configure data collection
Create department mapping:
```
# department_mapping.csv
# vlan_id, subnet, department, cost_center
# 10, 10.10.10.0/24, Engineering, CC-1001
# 20, 10.10.20.0/24, Marketing, CC-2001
```
Verify:
```spl
index=meraki sourcetype="meraki:api:traffic" earliest=-4h
| eval app=coalesce(application, app_name)
| stats sum(sent) sum(recv) by app
| sort -sum(sent) | head 10
```

### Step 2 — - Create the search and alert

**Primary search -- Bandwidth by application and department:**
```spl
index=meraki (sourcetype="meraki:api:traffic" OR sourcetype="meraki:api:clients") earliest=-24h
| eval app=coalesce(application, app_name)
| eval client=coalesce(ip, client_ip)
| eval sent_mb=tonumber(sent)/1048576
| eval recv_mb=tonumber(recv)/1048576
| eval total_mb=sent_mb + recv_mb
| rex field=client "^(?<subnet>\d+\.\d+\.\d+)\.\d+$"
| lookup department_mapping.csv subnet OUTPUT department, cost_center
| eval dept=coalesce(department, "Unknown")
| stats sum(total_mb) as total_mb dc(client) as unique_clients by dept, app
| eventstats sum(total_mb) as dept_total by dept
| eval app_pct=round(100*total_mb/dept_total, 1)
| where total_mb > 100
| sort dept, -total_mb
```

### Step 3 — - Validate
(a) Verify department mapping covers all VLANs/subnets.
(b) Compare with Dashboard network traffic analytics.
(c) Cross-reference with department headcount for per-user bandwidth.

### Step 4 — - Operationalize
Dashboard ("Meraki MX -- Bandwidth by Department"):
* Row 1 -- Single-value: "Total bandwidth (GB)", "Top department", "Top application".
* Row 2 -- Department bandwidth breakdown.

### Step 5 — - Troubleshooting

* **Unknown department** -- Client subnet not in lookup. Update `department_mapping.csv` with all VLANs.

* **Unexpected high bandwidth in department** -- Investigate: (1) specific users/devices, (2) application type (legitimate large transfer vs streaming), (3) time of day pattern.

* **Shared VLAN across departments** -- Map at finer granularity (per-IP or per-MAC) or use Meraki group policies for department tagging.

## SPL

```spl
index=cisco_network sourcetype="meraki" type=flow
| lookup department_by_ip.csv src OUTPUTNEW department
| stats sum(sent_bytes) as upload_mb, sum(received_bytes) as download_mb by application, department
| eval total_mb=upload_mb+download_mb
| sort -total_mb
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

Stacked bar of bandwidth by dept/app; heatmap of app usage per dept.

## Known False Positives

Backups, cloud sync, and software updates can shift "who used the most" without any misuse.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
- [CIM: Network_Traffic](https://docs.splunk.com/Documentation/CIM/latest/User/Network_Traffic)
