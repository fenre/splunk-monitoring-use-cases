<!-- AUTO-GENERATED from UC-2.6.78.json — DO NOT EDIT -->

---
id: "2.6.78"
title: "Citrix Session Recording Pipeline and Storage Health"
criticality: "high"
splunkPillar: "Security"
---

# UC-2.6.78 · Citrix Session Recording Pipeline and Storage Health

## Description

Session recording is often a compliance and insider-risk control. The recording service, search index, and long-term file storage must be healthy, searchable within agreed latency, and large enough to retain evidence. Failures in any tier create a gap where activity is not provable even though policy requires recording. Monitoring capacity and playback availability closes that gap operationally and for audits.

## Value

Session recording is often a compliance and insider-risk control. The recording service, search index, and long-term file storage must be healthy, searchable within agreed latency, and large enough to retain evidence. Failures in any tier create a gap where activity is not provable even though policy requires recording. Monitoring capacity and playback availability closes that gap operationally and for audits.

## Implementation

Separate alerts: infrastructure (service down, disk, SQL), pipeline lag (ingest to searchable), and product errors on playback. Plan retention tiering: hot, warm, and archive. Test restore and playback quarterly. If storage is object-backed, add bucket health and cost monitors outside Splunk and link the dashboard here.

## Detailed Implementation

Prerequisites: Centralized Windows or platform logs and disk metrics from the Session Recording cluster; agreed max search delay (SLO) from compliance. Step 1: Configure data collection — Install forwarders on each recording node; props.conf stanzas [citrix:session:recording:server], [citrix:session:recording:storage], [citrix:session:recording:search] with EXTRACT for free_gb, index_lag_sec, and service state; tag host with site in a lookup session_recording_site_map.csv. Step 2: Create the search and alert — Severe: service down for two poll cycles; warning: free space <20% for one hour or index_lag>300s (tune to your SLO, starting stricter and relaxing after baseline). Step 3: Validate — After a controlled load test, run `index=xd (sourcetype="citrix:session:recording:*") earliest=-2h | stats max(index_lag_sec) as lag, min(free_gb) as disk by host` and compare to the SR admin console. Step 4: Operationalize — Add to the compliance control pack with owner sign-off; if evidence gaps or lag persist, escalate to Citrix Session Recording and storage administrators.

## SPL

```spl
index=xd (sourcetype="citrix:session:recording:server" OR sourcetype="citrix:session:recording:storage" OR sourcetype="citrix:session:recording:search") earliest=-24h
| eval g=tonumber(free_gb), low_disk=if((isnotnull(g) AND g<10) OR match(_raw, "(?i)low.?space|disk.?full"),1,0), lag_sec=tonumber(index_lag_sec), down=if(match(_raw, "(?i)service.?(not.?(start|run)|down|stop|fail)"),1,0)
| bin _time span=5m
| stats max(low_disk) as risk_disk, max(lag_sec) as max_lag, max(down) as down_ev by _time, host
| where risk_disk=1 OR max_lag>300 OR down_ev=1
| table _time, host, risk_disk, max_lag, down_ev
```

## Visualization

Gauges: free space and index lag; timeline: down events; table: last successful backup or archive job per site if logged.

## References

- [Citrix — Session Recording architecture and storage](https://docs.citrix.com/en-us/citrix-virtual-apps-desktops/technical-overview/session-recording.html)
