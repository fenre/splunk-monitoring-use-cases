<!-- AUTO-GENERATED from UC-5.5.1.json — DO NOT EDIT -->

---
id: "5.5.1"
title: "Tunnel Health Monitoring"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.5.1 · Tunnel Health Monitoring

> **Criticality:** Critical &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Availability

*We keep an eye on how our wide-area links and SD-WAN paths are behaving so we spot a bad circuit or policy issue before branch users lose voice, video, or critical apps.*

---

## Description

Tunnel loss/latency/jitter directly impacts application experience over WAN.

## Value

Network operations teams monitor SD-WAN tunnel health (loss, latency, jitter) against application-specific SLA thresholds, enabling proactive detection of degraded paths before voice, video, and critical applications are impacted.

## Implementation

Poll vManage API for BFD session statistics. Collect loss, latency, jitter per tunnel. Alert when SLA thresholds exceeded.

## Detailed Implementation

### Prerequisites
- Cisco Catalyst Add-on for Splunk (TA_cisco_catalyst, Splunkbase 7538) installed and configured with a vManage API account. The TA polls vManage REST APIs for BFD (Bidirectional Forwarding Detection) session statistics, which provide per-tunnel loss, latency, and jitter metrics.
- vManage API account needs read-only access to the statistics API: `/dataservice/statistics/bfd`. Configure the account in the TA's setup page with vManage host, port (8443), and credentials.
- Data lands in `index=sdwan` with `sourcetype=cisco:sdwan:bfd`. Key fields: `site_id`, `system_ip`, `local_color` (transport type: mpls, biz-internet, lte), `remote_color`, `tunnel_name`, `loss_percentage`, `latency` (ms), `jitter` (ms), `state` (up/down).
- Build a `sdwan_sites.csv` lookup: `site_id,site_name,region,tier` (e.g., `100,HQ-NYC,East,Tier1`, `200,Branch-Chicago,Central,Tier2`). This provides human-readable site names and priority tiers.
- SD-WAN tunnel SLA thresholds depend on application requirements: voice (loss < 1%, latency < 150ms, jitter < 30ms), video (loss < 0.5%, latency < 200ms, jitter < 50ms), general data (loss < 5%, latency < 300ms). Define thresholds per application class.

### Step 1 — Configure data collection
Verify BFD data arrival:
```spl
index=sdwan sourcetype="cisco:sdwan:bfd" earliest=-15m
| stats count dc(system_ip) as devices dc(tunnel_name) as tunnels by site_id
```
Each site should show its edge devices and tunnels. If empty: check vManage API connectivity from the Splunk Heavy Forwarder, verify the TA data input is enabled, and confirm the API account has statistics read permissions.

Verify key BFD fields:
```spl
index=sdwan sourcetype="cisco:sdwan:bfd" earliest=-15m
| stats avg(loss_percentage) as avg_loss avg(latency) as avg_latency avg(jitter) as avg_jitter by site_id, local_color
```

### Step 2 — Create the search and alert

**Primary search — Tunnel health with SLA evaluation:**
```spl
index=sdwan sourcetype="cisco:sdwan:bfd" earliest=-15m
| stats avg(loss_percentage) as avg_loss avg(latency) as avg_latency avg(jitter) as avg_jitter max(loss_percentage) as peak_loss max(latency) as peak_latency count as samples by site_id, system_ip, local_color, remote_color, tunnel_name
| eval voice_sla=if(avg_loss < 1 AND avg_latency < 150 AND avg_jitter < 30, "PASS", "FAIL")
| eval video_sla=if(avg_loss < 0.5 AND avg_latency < 200 AND avg_jitter < 50, "PASS", "FAIL")
| eval data_sla=if(avg_loss < 5 AND avg_latency < 300, "PASS", "FAIL")
| lookup sdwan_sites.csv site_id OUTPUT site_name region tier
| eval severity=case(data_sla="FAIL", "CRITICAL", voice_sla="FAIL", "HIGH", video_sla="FAIL", "MEDIUM", 1==1, "OK")
| where severity!="OK"
| sort severity, -avg_loss
```

#### Understanding this SPL: Evaluates every tunnel against three SLA tiers (voice, video, data). A tunnel failing the data SLA is critical — even basic applications are impacted. Voice SLA failure means call quality degradation. The `local_color` field identifies the transport type (MPLS, internet, LTE), which helps with troubleshooting — MPLS tunnels should have better SLAs than internet tunnels.

**Tunnel degradation trending:**
```spl
index=sdwan sourcetype="cisco:sdwan:bfd" earliest=-24h
| bin _time span=5m
| stats avg(loss_percentage) as loss avg(latency) as latency avg(jitter) as jitter by _time, site_id, local_color
| lookup sdwan_sites.csv site_id OUTPUT site_name
| eval site_label=if(isnotnull(site_name), site_name, "Site-".site_id)
| timechart span=5m avg(loss) as avg_loss avg(latency) as avg_latency by site_label
```

**Per-transport comparison (MPLS vs. Internet vs. LTE):**
```spl
index=sdwan sourcetype="cisco:sdwan:bfd" earliest=-1h
| stats avg(loss_percentage) as loss avg(latency) as latency avg(jitter) as jitter by local_color
| eval transport=case(local_color="mpls", "MPLS", local_color="biz-internet", "Internet", local_color="lte", "LTE", local_color="private1", "Private", 1==1, local_color)
| sort transport
```

### Step 3 — Validate
(a) In vManage: Monitor > Network > BFD. Compare loss/latency/jitter for the same tunnel and time range. Values should match within the polling interval.
(b) Run a known voice call over the WAN and correlate MOS scores with tunnel metrics during the call.
(c) Verify site mapping: spot-check 10 site_ids in the lookup against vManage's site inventory.

### Step 4 — Operationalize
Dashboard ("SD-WAN — Tunnel Health"):
- Row 1 — Single-value tiles: "Tunnels failing voice SLA", "Tunnels failing data SLA", "Worst loss (%)", "Worst latency (ms)".
- Row 2 — Site status grid: each cell = site, color = worst tunnel status (green/yellow/red).
- Row 3 — Tunnel detail table: site, tunnel, transport, loss, latency, jitter, voice SLA, video SLA.
- Row 4 — Trending: selected site's tunnel metrics over 24h.

Alerting:
- Critical (any tunnel fails data SLA sustained 10+ min): page NOC — site may be unreachable for critical apps.
- High (voice SLA failure on Tier1 site): alert — call quality impacted.
- Warning (video SLA failure): monitor and prepare for failover.

Runbook:
1. **High loss on internet tunnel**: Check ISP circuit health. If loss is from the ISP, failover to MPLS/LTE. Open a ticket with the ISP. If persistent, the SD-WAN policy should automatically route traffic away.
2. **High latency on all tunnels at a site**: Check the edge device CPU (UC-5.5.13). High CPU on the data plane causes latency on all tunnels. Also check for asymmetric routing or MTU issues.
3. **Jitter spikes on LTE**: Expected during cell tower congestion. If the site has MPLS or internet backup, traffic should already be preferring those for voice/video.

### Step 5 — Troubleshooting

- **BFD data not arriving** — Check vManage API reachability from the Heavy Forwarder. Verify the TA input configuration: vManage host, port 8443, SSL verification, and credentials. Check `_internal` for TA errors.

- **Loss shows 100% briefly then recovers** — Tunnel renegotiation during ISP maintenance or policy push. BFD detects the brief outage. If the tunnel recovers within 30 seconds, it's likely a transient event. Check vManage alarms for correlation.

- **Latency values seem too high (> 500ms) on MPLS** — MPLS latency should be < 50ms domestically. Values > 200ms suggest: misconfigured DSCP marking (BFD packets not getting QoS priority), MTU issues causing fragmentation, or a routing loop in the MPLS network.

## SPL

```spl
index=sdwan sourcetype="cisco:sdwan:bfd"
| stats avg(loss_percentage) as loss, avg(latency) as latency, avg(jitter) as jitter by site, tunnel_name
| where loss > 1 OR latency > 100 OR jitter > 30
```

## Visualization

Line chart (loss/latency/jitter per tunnel), Table, Status grid per site.

## Known False Positives

Tunnels may renegotiate during ISP maintenance, BFD timer changes, planned controller upgrades, or policy pushes; short blips may look like failures when the business path is still acceptable.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
