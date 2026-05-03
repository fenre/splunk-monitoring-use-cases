<!-- AUTO-GENERATED from UC-5.5.15.json — DO NOT EDIT -->

---
id: "5.5.15"
title: "DPI Application Visibility"
criticality: "medium"
splunkPillar: "Security"
---

# UC-5.5.15 · DPI Application Visibility

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Security &middot; **Type:** Performance, Capacity

*We keep an eye on how our wide-area links and SD-WAN paths are behaving so we spot a bad circuit or policy issue before branch users lose voice, video, or critical apps.*

---

## Description

Deep Packet Inspection on SD-WAN edges classifies traffic by application. Visibility into top applications per site drives policy tuning, bandwidth planning, and identification of shadow IT or unauthorized SaaS usage.

## Value

Network operations teams leverage SD-WAN DPI classification to identify top bandwidth-consuming applications, detect unauthorized application usage, and validate application-aware routing policy effectiveness.

## Implementation

Enable DPI on SD-WAN edge routers (requires UTD container or native NBAR2). Collect application statistics via vManage. Identify top bandwidth consumers per site. Compare against policy expectations — flag when non-business applications (streaming, gaming, social media) consume more than 20% of WAN bandwidth.

## Detailed Implementation

### Prerequisites
- Cisco Catalyst Add-on for Splunk polling vManage API for DPI (Deep Packet Inspection) application statistics. Data in `index=sdwan` with `sourcetype=cisco:sdwan:dpi` or `sourcetype=cisco:sdwan:approute`. Key fields: `site_id`, `system_ip`, `app_name`, `app_family`, `bytes`, `packets`, `sessions`, `vpn_id`.
- SD-WAN DPI classifies traffic by application using: NBAR2 (Network-Based Application Recognition), SNI inspection for TLS traffic, and custom application definitions. This enables per-application visibility: which applications consume the most bandwidth, which use which WAN transport, and which are unauthorized.
- Build `sdwan_app_categories.csv` lookup: `app_name,category,business_critical,allowed` (e.g., `webex,Collaboration,yes,yes`, `netflix,Streaming,no,no`, `salesforce,SaaS,yes,yes`). This enables policy enforcement reporting.

### Step 1 — Configure data collection
Verify DPI data:
```spl
index=sdwan sourcetype="cisco:sdwan:dpi" earliest=-1h
| stats count dc(app_name) as apps by site_id
```

### Step 2 — Create the search and alert

**Primary search — Top applications by bandwidth with policy compliance:**
```spl
index=sdwan sourcetype="cisco:sdwan:dpi" earliest=-1h
| stats sum(bytes) as total_bytes sum(sessions) as total_sessions by site_id, app_name, app_family
| eval total_gb=round(total_bytes/1073741824, 2)
| eval total_mb=round(total_bytes/1048576, 0)
| lookup sdwan_app_categories.csv app_name OUTPUT category business_critical allowed
| lookup sdwan_sites.csv site_id OUTPUT site_name tier
| eval policy_status=case(allowed="no", "BLOCKED_BUT_ACTIVE", business_critical="yes", "BUSINESS", 1==1, "PERMITTED")
| sort -total_bytes
| head 50
```

#### Understanding this SPL: DPI visibility is the foundation of SD-WAN value. Without knowing which applications consume bandwidth, you can't create effective AAR policies. This search identifies: (1) top bandwidth consumers — often surprising (backup software, Windows updates, streaming), (2) unauthorized applications that should be blocked, (3) business-critical applications that need QoS protection.

**Unauthorized application detection:**
```spl
index=sdwan sourcetype="cisco:sdwan:dpi" earliest=-4h
| stats sum(bytes) as total_bytes dc(site_id) as site_count by app_name, app_family
| lookup sdwan_app_categories.csv app_name OUTPUT allowed category
| where allowed="no"
| eval total_mb=round(total_bytes/1048576, 0)
| sort -total_bytes
```

**Application bandwidth trending:**
```spl
index=sdwan sourcetype="cisco:sdwan:dpi" earliest=-24h
| lookup sdwan_app_categories.csv app_name OUTPUT category business_critical
| where business_critical="yes"
| bin _time span=1h
| stats sum(bytes) as bytes by _time, app_name
| eval mb=round(bytes/1048576, 0)
| timechart span=1h sum(mb) by app_name
```

### Step 3 — Validate
(a) In vManage: Monitor > Network > select device > DPI. Compare top applications by bandwidth with Splunk results.
(b) Generate known traffic (e.g., Webex call, large file download) and verify it appears classified correctly.
(c) Verify application category lookup: ensure all top-20 applications have entries in `sdwan_app_categories.csv`.

### Step 4 — Operationalize
Dashboard ("SD-WAN — Application Visibility"):
- Row 1 — Single-value tiles: "Applications tracked", "Unauthorized apps active", "Business app bandwidth (GB)", "Streaming bandwidth (GB)".
- Row 2 — Top applications table: app, category, bandwidth (GB), sessions, business-critical flag, policy status.
- Row 3 — Unauthorized applications alert table.
- Row 4 — Application bandwidth trending for business-critical apps over 24h.

Alerting:
- High (unauthorized application consuming > 1 GB/hour): policy violation — investigate and block.
- Warning (business-critical app bandwidth drop > 50%): possible service outage or user issue.
- Info (weekly): application bandwidth report for capacity planning.

### Step 5 — Troubleshooting

- **Many applications classified as "unknown"** — NBAR2 application definition pack may be outdated. Update the NBAR2 protocol pack on the edge devices from Cisco.com. Also, some encrypted applications need TLS decryption or custom application definitions.

- **DPI data not matching actual traffic** — DPI operates on a sampling basis on some device models. The byte counts may be estimates, not exact. Compare with interface byte counts (UC-5.5.7) for total accuracy.

- **app_family vs app_name confusion** — `app_family` is the broad category (e.g., "instant-messaging"), while `app_name` is the specific application (e.g., "webex-teams"). Use `app_name` for granular analysis and `app_family` for aggregate reporting.

## SPL

```spl
index=sdwan sourcetype="cisco:sdwan:dpi"
| stats sum(bytes) as total_bytes, sum(packets) as total_pkts by app_name, family, site_id
| eval GB=round(total_bytes/1073741824,2)
| sort -total_bytes
| head 50
| table app_name family site_id GB total_pkts
```

## CIM SPL

```spl
| tstats `summariesonly` sum(All_Traffic.bytes) as bytes
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.app span=1h
| where bytes>0
| sort -bytes
```

## Visualization

Bar chart (top 20 apps by volume), Treemap (app families), Table (app, site, volume).

## Known False Positives

Utilization and top-application charts jump during backups, patch windows, video calls, or large file transfers; compare to baselines and scheduled jobs before treating a spike as fault.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [CIM: Network_Traffic](https://docs.splunk.com/Documentation/CIM/latest/User/Network_Traffic)
