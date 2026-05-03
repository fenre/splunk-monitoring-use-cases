<!-- AUTO-GENERATED from UC-5.3.38.json — DO NOT EDIT -->

---
id: "5.3.38"
title: "Citrix SD-WAN Virtual Path Loss, Jitter, and Latency"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.3.38 · Citrix SD-WAN Virtual Path Loss, Jitter, and Latency

> **Criticality:** Critical &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance

*We read loss, jitter, and delay on the overlay path so a brown site or a noisy link is a fact on a chart, not a feeling on a call.*

---

## Description

Citrix SD-WAN virtual paths carry business traffic between sites and cloud services. Packet loss, jitter, latency, and voice-style mean opinion score (MOS) metrics reveal path quality before users open tickets. Tracking path state changes pinpoints when the fabric moved traffic or when a path stopped meeting policy for quality of experience.

## Value

Network operations teams monitor Citrix SD-WAN virtual path loss, jitter, and latency per WAN link, detecting dead paths and quality degradation that impacts real-time applications.

## Implementation

Ingest per-virtual-path telemetry on a 1–5 minute cadence. Align thresholds to site baselines and voice or video SLOs. Alert on sustained loss or latency above policy, MOS below the floor, or explicit degraded state. Correlate with carrier incidents and change windows. Document how path reselection affects latency (acceptable vs regression).

## Detailed Implementation

### Prerequisites
* Citrix SD-WAN appliance syslog or Citrix SD-WAN Orchestrator API data in `index=netscaler` with `sourcetype=citrix:sdwan:syslog` or `sourcetype=citrix:sdwan:perf`. Key fields: `virtual_path`, `site_name`, `wan_link`, `loss_pct`, `jitter_ms`, `latency_ms`, `path_state` (GOOD/BAD/DEAD).
* Citrix SD-WAN virtual paths are overlay tunnels between sites. Each virtual path uses one or more WAN links (MPLS, Internet, LTE). The SD-WAN appliance continuously measures loss, jitter, and latency per path and uses these metrics for application steering decisions.

### Step 1 — - Configure data collection
Configure syslog on Citrix SD-WAN appliance or poll Orchestrator API for virtual path stats. Verify:
```spl
index=netscaler (sourcetype="citrix:sdwan:syslog" OR sourcetype="citrix:sdwan:perf") earliest=-4h
| where isnotnull(virtual_path) OR isnotnull(loss_pct) OR isnotnull(latency_ms)
| stats count by site_name, virtual_path
```

### Step 2 — - Create the search and alert

**Primary search -- Virtual path health monitoring:**
```spl
index=netscaler (sourcetype="citrix:sdwan:syslog" OR sourcetype="citrix:sdwan:perf") earliest=-4h
| eval vpath=coalesce(virtual_path, path_name)
| eval site=coalesce(site_name, site)
| eval loss=coalesce(loss_pct, packet_loss)
| eval jitter=coalesce(jitter_ms, jitter)
| eval latency=coalesce(latency_ms, latency)
| eval wan=coalesce(wan_link, link_name)
| eval state=coalesce(path_state, path_status)
| bin _time span=5m
| stats avg(loss) as avg_loss max(loss) as max_loss avg(jitter) as avg_jitter max(jitter) as max_jitter avg(latency) as avg_latency latest(state) as path_state by _time, site, vpath, wan
| eval quality=case(match(lower(path_state), "dead"), "DEAD", max_loss > 5, "POOR", max_jitter > 30, "POOR", avg_latency > 150, "POOR", avg_loss > 1 OR avg_jitter > 15 OR avg_latency > 80, "FAIR", 1==1, "GOOD")
| where quality IN ("DEAD", "POOR")
| eval impact=case(quality="DEAD", "Path completely down -- traffic on alternate path", quality="POOR" AND max_loss > 5, "High packet loss -- voice/video degraded", quality="POOR" AND max_jitter > 30, "High jitter -- real-time apps affected", 1==1, "Performance degradation")
| sort quality, -avg_loss
```

### Step 3 — - Validate
(a) Compare path metrics with Citrix SD-WAN Orchestrator: Monitor > Virtual Paths.
(b) Introduce artificial impairment on a test WAN link and verify degradation in Splunk.
(c) Verify DEAD paths correspond to actual WAN link failures.

### Step 4 — - Operationalize
Dashboard ("Citrix SD-WAN -- Path Health"):
* Row 1 -- Single-value: "Active paths", "Dead paths", "Poor quality paths", "Avg latency (ms)".
* Row 2 -- Per-path health table with impact assessment.
* Row 3 -- Loss/jitter/latency trending timechart by site.

Alerting:
* Critical (virtual path DEAD): site connectivity impaired.
* Warning (loss > 5% or jitter > 30ms sustained > 10 min): real-time traffic affected.

### Step 5 — - Troubleshooting

* **Path DEAD** -- WAN link is completely down. Check: ISP circuit status, router interface, firewall rules for SD-WAN overlay ports (UDP 4980).

* **High loss on Internet path but MPLS is fine** -- Internet link quality degradation. Consider: ISP change, adding a second Internet link, adjusting path quality thresholds to steer traffic to MPLS.

* **Jitter spikes at specific times** -- Correlate with ISP peak hours or backup schedules consuming WAN bandwidth.

## SPL

```spl
index=sdwan sourcetype="citrix:sdwan:virtual_path" earliest=-4h
| eval loss=tonumber(loss_pct), jit=tonumber(jitter_ms), lat=tonumber(latency_ms), mos=tonumber(mos)
| bin _time span=5m
| stats avg(loss) as avg_loss, avg(jit) as avg_jit, avg(lat) as avg_lat, avg(mos) as avg_mos, latest(path_state) as path_state by _time, site_id, path_name
| where avg_loss>2 OR avg_jit>30 OR avg_lat>150 OR (isnotnull(avg_mos) AND avg_mos<3.5) OR match(lower(path_state),"(?i)down|bad|degraded")
| table _time, site_id, path_name, avg_loss, avg_jit, avg_lat, avg_mos, path_state
```

## Visualization

Timechart: loss, jitter, latency per path; line: MOS; overlay annotations for path state changes; table: worst paths in the last hour by site.

## Known False Positives

Brownouts, carrier work, and flapping remotes can move loss and jitter on one path one day and a different path the next.

## References

- [Citrix — SD-WAN paths and quality metrics](https://docs.citrix.com/en-us/citrix-sd-wan/)
