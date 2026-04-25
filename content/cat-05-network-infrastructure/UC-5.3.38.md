<!-- AUTO-GENERATED from UC-5.3.38.json — DO NOT EDIT -->

---
id: "5.3.38"
title: "Citrix SD-WAN Virtual Path Loss, Jitter, and Latency"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.3.38 · Citrix SD-WAN Virtual Path Loss, Jitter, and Latency

## Description

Citrix SD-WAN virtual paths carry business traffic between sites and cloud services. Packet loss, jitter, latency, and voice-style mean opinion score (MOS) metrics reveal path quality before users open tickets. Tracking path state changes pinpoints when the fabric moved traffic or when a path stopped meeting policy for quality of experience.

## Value

Citrix SD-WAN virtual paths carry business traffic between sites and cloud services. Packet loss, jitter, latency, and voice-style mean opinion score (MOS) metrics reveal path quality before users open tickets. Tracking path state changes pinpoints when the fabric moved traffic or when a path stopped meeting policy for quality of experience.

## Implementation

Ingest per-virtual-path telemetry on a 1–5 minute cadence. Align thresholds to site baselines and voice or video SLOs. Alert on sustained loss or latency above policy, MOS below the floor, or explicit degraded state. Correlate with carrier incidents and change windows. Document how path reselection affects latency (acceptable vs regression).

## Detailed Implementation

Prerequisites: citrix:sdwan:virtual_path with stable path_name, site_id, and site class baselines. Step 1: Configure data collection — Enable structured export from edges or orchestrator; props/transforms to normalize loss_pct, jitter_ms, latency_ms, mos, path_state; enforce UTC. Step 2: Create the search and alert — Primary alerts on business-critical paths; start with avg loss>2%, jitter>30ms, latency>150ms, or MOS<3.5 for voice (tune per site class and dial down if noisy). Step 3: Validate — For one gold site, compare `index=sdwan sourcetype="citrix:sdwan:virtual_path" | timechart avg(loss_pct) avg(latency_ms) by path_name` to SD-WAN UI/CLI; verify upgrades do not break path_name joins. Step 4: Operationalize — WAN health wallboard with change calendar and carrier contacts; if metrics stay breached, escalate to SD-WAN engineering and the carrier; validation: `| stats latest(path_state) by site_id, path_name`.

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

## References

- [Citrix — SD-WAN paths and quality metrics](https://docs.citrix.com/en-us/citrix-sd-wan/)
