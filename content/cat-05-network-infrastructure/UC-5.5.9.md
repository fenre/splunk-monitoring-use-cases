<!-- AUTO-GENERATED from UC-5.5.9.json — DO NOT EDIT -->

---
id: "5.5.9"
title: "Application Routing Decisions"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.5.9 · Application Routing Decisions

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance

*We keep an eye on how our wide-area links and SD-WAN paths are behaving so we spot a bad circuit or policy issue before branch users lose voice, video, or critical apps.*

---

## Description

Validates that SD-WAN policies are steering traffic correctly. Detects policy misconfigurations that route real-time traffic over suboptimal paths.

## Value

Network operations teams track SD-WAN application-aware routing decisions to verify that critical applications use preferred WAN transports, identify persistent transport degradation, and validate AAR policy compliance across all sites.

## Implementation

Collect flow and app-route data from vManage. Verify voice/video uses MPLS, web traffic uses Internet. Alert when critical apps route over non-preferred transports.

## Detailed Implementation

### Prerequisites
- Cisco Catalyst Add-on for Splunk polling vManage API for application-aware routing decisions. Data in `index=sdwan` with `sourcetype=cisco:sdwan:approute`. Key fields: `site_id`, `system_ip`, `app_name` (or `app_family`), `dest_ip`, `src_ip`, `sla_class`, `preferred_color`, `actual_color`, `latency`, `loss`, `jitter`.
- SD-WAN Application-Aware Routing (AAR) dynamically selects the best WAN path for each application based on real-time SLA metrics. Applications are classified using DPI (Deep Packet Inspection) and mapped to SLA policies. For example: Webex → Voice SLA → prefer MPLS, fallback to Internet.
- Build `sdwan_app_policies.csv` lookup: `app_name,sla_class,preferred_color,business_priority` (e.g., `webex,VoiceAndVideo,mpls,critical`, `office365,BusinessCritical,biz-internet,high`, `youtube,BestEffort,biz-internet,low`).

### Step 1 — Configure data collection
Verify application routing data:
```spl
index=sdwan sourcetype="cisco:sdwan:approute" earliest=-15m
| stats count dc(app_name) as apps by site_id
```

### Step 2 — Create the search and alert

**Primary search — Application routing decisions with policy compliance:**
```spl
index=sdwan sourcetype="cisco:sdwan:approute" earliest=-1h
| lookup sdwan_app_policies.csv app_name OUTPUT sla_class preferred_color business_priority
| eval policy_compliant=if(actual_color=preferred_color, "YES", "NO")
| stats count as decisions count(eval(policy_compliant="NO")) as non_compliant avg(latency) as avg_latency avg(loss) as avg_loss by site_id, app_name, sla_class, preferred_color, actual_color
| where non_compliant > 0
| eval compliance_pct=round(100*(decisions - non_compliant)/decisions, 1)
| lookup sdwan_sites.csv site_id OUTPUT site_name tier
| eval reason=case(avg_loss > 1, "Loss on preferred path", avg_latency > 150, "Latency on preferred path", 1==1, "Unknown — check AAR policy")
| sort business_priority, -non_compliant
```

#### Understanding this SPL: When SD-WAN routes an application over a different transport than the preferred one, it means the preferred path failed the SLA check. This is working as designed (failover), but persistent non-compliance indicates the preferred transport is consistently degraded. Tracking this helps identify ISP issues and capacity planning needs.

**Application routing distribution by transport:**
```spl
index=sdwan sourcetype="cisco:sdwan:approute" earliest=-4h
| stats count as flows by app_name, actual_color
| eval transport=case(actual_color="mpls", "MPLS", actual_color="biz-internet", "Internet", actual_color="lte", "LTE", 1==1, actual_color)
| chart sum(flows) by app_name transport
| sort -MPLS
```

**Top applications not using preferred path:**
```spl
index=sdwan sourcetype="cisco:sdwan:approute" earliest=-4h
| lookup sdwan_app_policies.csv app_name OUTPUT preferred_color business_priority
| where isnotnull(preferred_color) AND actual_color != preferred_color
| stats count as redirected_flows dc(site_id) as affected_sites by app_name, preferred_color, actual_color, business_priority
| sort business_priority, -redirected_flows
```

### Step 3 — Validate
(a) In vManage: Monitor > Application-Aware Routing > select device > check application routing table. Compare preferred vs. actual path.
(b) Generate traffic for a known application (e.g., Webex call) and verify it appears routed over the expected transport color.
(c) Degrade the preferred transport (add latency via traffic shaping) and verify the application switches to the backup transport.

### Step 4 — Operationalize
Dashboard ("SD-WAN — Application Routing"):
- Row 1 — Single-value tiles: "Critical apps on non-preferred path", "AAR policy compliance %", "Applications tracked", "Sites with routing deviations".
- Row 2 — Application routing table: app, SLA class, preferred transport, actual transport, compliance %, affected sites.
- Row 3 — Transport distribution chart: bar chart showing application flow distribution across MPLS/Internet/LTE.
- Row 4 — Non-compliant application trending over 24h.

Alerting:
- High (critical-priority app on non-preferred path for > 10 min): voice/video on backup transport — quality may degrade.
- Warning (business-priority app consistently non-compliant): preferred transport degraded — capacity planning.

### Step 5 — Troubleshooting

- **All applications showing actual_color different from preferred** — The preferred transport may be completely down. Check tunnel health (UC-5.5.1) and path failover events (UC-5.5.4).

- **app_name shows as "unknown"** — DPI classification may not recognize the application. Check if the application definition list in vManage is up to date. Some encrypted applications need SNI-based classification or custom application definitions.

- **Application routed to preferred path but SLA is bad** — AAR policy may be in monitoring mode (not enforcement). Check the policy configuration in vManage.

## SPL

```spl
index=network sourcetype="cisco:sdwan:flow"
| stats sum(octets) as bytes by app_name, local_color, remote_system_ip
| eval MB=round(bytes/1048576,1)
| sort -MB
| head 50
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

Sankey diagram (app → transport), Table (app, path, volume), Pie chart.

## Known False Positives

Utilization and top-application charts jump during backups, patch windows, video calls, or large file transfers; compare to baselines and scheduled jobs before treating a spike as fault.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
