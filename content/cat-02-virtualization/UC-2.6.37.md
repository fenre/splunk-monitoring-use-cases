<!-- AUTO-GENERATED from UC-2.6.37.json — DO NOT EDIT -->

---
id: "2.6.37"
title: "HDX Adaptive Transport (EDT) and Graphics Mode"
criticality: "high"
splunkPillar: "Observability"
---

# UC-2.6.37 · HDX Adaptive Transport (EDT) and Graphics Mode

## Description

HDX Adaptive Transport prefers UDP (EDT) for interactive traffic when the network is healthy, falling back to TCP when loss or delay is high. High packet loss, RTT, or constant fallback reduces perceived responsiveness and can force CPU-biased H.264/HEVC or software rendering, stressing hosts and user experience. uberAgent’s EDT and HDX remoting metrics complement Citrix VDA event strings on encoder choice and display pipeline pressure.

## Value

HDX Adaptive Transport prefers UDP (EDT) for interactive traffic when the network is healthy, falling back to TCP when loss or delay is high. High packet loss, RTT, or constant fallback reduces perceived responsiveness and can force CPU-biased H.264/HEVC or software rendering, stressing hosts and user experience. uberAgent’s EDT and HDX remoting metrics complement Citrix VDA event strings on encoder choice and display pipeline pressure.

## Implementation

Deploy uberAgent on VDAs with network and remoting data enabled. Add field extractions for your exact uberAgent 7.x/8.x field names. Side-by-side: run a VDA search for 'policy', 'H264', 'HEVC', or 'YUV' in `citrix:vda:events` for policy-driven changes. Set threshold bands by site (WAN vs LAN).

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: uberAgent UXM (Splunkbase 1448), optional VDA or broker TA for context.
• Ensure the following data sources are available: `sourcetype="uberAgent:Network:NetworkPerformanceEDT"` and remoting/graphics sourcetypes, optional `sourcetype="citrix:vda:events"`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Confirm uberAgent is licensed for network remoting. Map transport and GPU metrics to fields used in the SPL; create macros if sourcetype names include wildcards. Ingest a narrow slice of VDA log events for display stack messages.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; align field names to your uberAgent build):

```spl
index=uberagent (sourcetype="uberAgent:Network:NetworkPerformanceEDT" OR sourcetype="uberAgent:Remoting:HDX*") earliest=-1h
| eval loss_pct=coalesce(UDPPacketLossPercent, UdpPacketLoss, PacketLoss), latency_ms=coalesce(UDPRTTms, AvgRttMs, Latency), fallback=if(match(coalesce(Transport, Protocol), "(?i)tcp"),1,0)
| where loss_pct>2 OR latency_ms>150 OR fallback=1
| bin _time span=5m
| stats avg(loss_pct) as avg_loss, avg(latency_ms) as avg_rtt, sum(fallback) as fallbacks, dc(user) as users by _time, host, SessionId
| table _time, host, users, avg_loss, avg_rtt, fallbacks
```

Step 3 — Validate
Benchmark a known good LAN session and a throttled lab session. Adjust thresholds. Confirm VDA text events align on forced encoder mode.

Step 4 — Operationalize
Feed findings to the network and desktop graphics teams. Track GPU memory pressure in a companion panel if you enable GPU fields.

## SPL

```spl
index=uberagent (sourcetype="uberAgent:Network:NetworkPerformanceEDT" OR sourcetype="uberAgent:Remoting:HDX*") earliest=-1h
| eval loss_pct=coalesce(UDPPacketLossPercent, UdpPacketLoss, PacketLoss), latency_ms=coalesce(UDPRTTms, AvgRttMs, Latency), fallback=if(match(coalesce(Transport, Protocol), "(?i)tcp"),1,0)
| where loss_pct>2 OR latency_ms>150 OR fallback=1
| bin _time span=5m
| stats avg(loss_pct) as avg_loss, avg(latency_ms) as avg_rtt, sum(fallback) as fallbacks, dc(user) as users by _time, host, SessionId
| table _time, host, users, avg_loss, avg_rtt, fallbacks
```

## Visualization

Dual-axis chart (loss vs RTT), Heatmap (hosts by time), Table (top sessions with fallback).

## References

- [uberAgent documentation - HDX/EDT](https://uberagent.com/docs/)
