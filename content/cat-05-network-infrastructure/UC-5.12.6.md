<!-- AUTO-GENERATED from UC-5.12.6.json — DO NOT EDIT -->

---
id: "5.12.6"
title: "Signaling Storm Detection"
criticality: "critical"
splunkPillar: "Security"
---

# UC-5.12.6 · Signaling Storm Detection

> **Criticality:** Critical &middot; **Difficulty:** Advanced &middot; **Pillar:** Security &middot; **Type:** Availability, Security

*We help you catch a flood of SIP or Diameter messages early—often a misconfiguration, loop, or attack—before the control plane drowns in noise.*

---

## Description

Bursts of SIP OPTIONS, REGISTER, or diameter requests can indicate reflection DDoS or misconfigured endpoints — complements UC-5.10.5 with cross-layer view.

## Value

NOC teams detect cross-protocol signaling storms — SIP OPTIONS/REGISTER floods, Diameter reconnect loops, DDoS attacks — before they overwhelm control-plane infrastructure and cause cascading IMS/voice outages.

## Implementation

Whitelist health-check sources; coordinate with peer ops when storm targets upstream interconnect.

## Detailed Implementation

### Prerequisites
- SIP and/or Diameter signaling data in Splunk via: (a) Splunk App for Stream capturing `sourcetype=stream:sip` on SBC/IMS interfaces; (b) Diameter signaling capture via `sourcetype=diameter:cap` or `sourcetype=stream:diameter` on core links. This UC provides a cross-layer view of signaling storms — complementing UC-5.10.5 (SIP REGISTER only) with all SIP methods plus Diameter signaling.
- Understand what constitutes a signaling storm: bursts of SIP OPTIONS (health checks amplified), SIP REGISTER (mass re-registration), SIP INVITE retransmissions (overloaded trunk), or Diameter CER/DWR floods (peer reconnect loops). A storm overwhelms control-plane processing capacity on SBCs, P-CSCFs, and DRAs, potentially causing cascading failures across the entire voice/IMS infrastructure.
- Index: `index=signaling` (or split into `index=telecom_sip` and `index=telecom_diameter`).
- Build a whitelist lookup `signaling_healthcheck_sources.csv` listing IP addresses of load balancers and monitoring probes that legitimately generate high-volume OPTIONS or DWR messages. These must be excluded from storm detection.
- Baseline knowledge: establish normal signaling rates per method/command during peak hours. Store baselines in a summary index or lookup for stable alerting.

### Step 1 — Configure data collection
Verify signaling data from both protocols:
```spl
index=signaling (sourcetype="stream:sip" OR sourcetype="diameter:cap") earliest=-15m
| stats count by sourcetype
```
Both sourcetypes should show non-zero counts. If only one is active, the other protocol's mirror/capture may need configuration.

Establish baseline message rates per method:
```spl
index=signaling (sourcetype="stream:sip" OR sourcetype="diameter:cap") earliest=-7d
| eval msg_type=coalesce(method, cmd_code)
| bin _time span=1m
| stats count by _time, msg_type
| stats avg(count) as avg_per_min stdev(count) as stdev_per_min by msg_type
| eval storm_threshold=avg_per_min + (5 * stdev_per_min)
| table msg_type, avg_per_min, stdev_per_min, storm_threshold
```

### Step 2 — Create the search and alert

**Primary search — Cross-protocol storm detection (1-min real-time):**
```spl
index=signaling (sourcetype="stream:sip" OR sourcetype="diameter:cap") earliest=-24h
| eval msg_type=coalesce(method, cmd_code)
| lookup signaling_healthcheck_sources.csv src_ip as src OUTPUT is_healthcheck
| where isnull(is_healthcheck) OR is_healthcheck!="true"
| bin _time span=1m
| stats count dc(src) as unique_sources by _time, msg_type
| eventstats avg(count) as mu stdev(count) as s by msg_type
| eval threshold=mu + (5 * s)
| eval threshold=if(threshold < mu*3, mu*3, threshold)
| where count > threshold AND count > 100
| eval spike_factor=round(count/mu, 1)
| eval rps=round(count/60, 0)
| sort -spike_factor
```

#### Understanding this SPL: We unify SIP `method` and Diameter `cmd_code` into `msg_type` for cross-protocol analysis. Health-check sources are excluded via lookup. The 5-sigma threshold with a 3x floor prevents false positives in stable environments. The `unique_sources` count distinguishes mass events (many sources) from single-source loops. `rps` (requests per second) gives operators an immediate sense of storm intensity relative to their infrastructure's rated capacity.

**Storm source analysis — identify the origin:**
```spl
index=signaling (sourcetype="stream:sip" OR sourcetype="diameter:cap") earliest=-5m
| eval msg_type=coalesce(method, cmd_code)
| stats count as msg_count dc(msg_type) as method_diversity by src
| eval msgs_per_sec=round(msg_count/300, 1)
| where msgs_per_sec > 10
| sort -msg_count
| head 20
```

#### Understanding this SPL: During an active storm, identify the top 20 source IPs by message rate. A single source sending >10 messages/second is likely misconfigured or malicious. Multiple sources at lower rates suggest a coordinated event (network recovery, firmware push).

**Cross-protocol correlation — SIP + Diameter storm timeline:**
```spl
index=signaling (sourcetype="stream:sip" OR sourcetype="diameter:cap") earliest=-6h
| eval msg_type=coalesce(method, cmd_code)
| bin _time span=1m
| chart count by _time, msg_type limit=15
```

#### Understanding this SPL: Timeline showing all signaling types side-by-side. Correlated SIP REGISTER + Diameter S6a (authentication) spikes suggest a mass device re-registration event. SIP INVITE + Diameter Gx spikes suggest a traffic burst. This cross-protocol correlation is unique to this UC and helps identify the root cause faster than monitoring each protocol in isolation.

Schedule as Alert: every 1 minute. Trigger when spike_factor > 5. Critical when spike_factor > 20 or rps > platform_rated_capacity * 0.8.

### Step 3 — Validate
(a) Compare message rates in Splunk to the SBC/DRA performance counters for the same minute. Splunk should match within 5%.
(b) Verify health-check exclusion: confirm that known monitoring probes are in the whitelist lookup and are excluded from detection.
(c) Simulate a controlled storm: restart a batch of test endpoints and verify the search detects the resulting REGISTER spike.
(d) Cross-check Diameter storms with UC-5.10.5 (SIP Registration Storm) — if both fire simultaneously, the cause is likely IMS-wide.

### Step 4 — Operationalize
Dashboard ("Signaling — Cross-Protocol Storm Detection"):
- Row 1 — Single-value tiles: "Peak signaling rate (msgs/sec)", "Spike factor", "Active storm?" (yes/no), "Unique storm sources".
- Row 2 — Timeline: message count per minute by protocol/method over 6h. Storm periods highlighted.
- Row 3 — Source analysis table: top sources during storm with msg rate, method diversity.
- Row 4 — Cross-protocol correlation chart showing SIP and Diameter side-by-side.

Alerting:
- Critical (spike_factor > 20 or rps > platform capacity * 80%): page NOC and IMS core team immediately. Cascading failure risk.
- Warning (spike_factor > 5): notify voice engineering for monitoring.

Runbook (owner: IMS / Voice Core Engineering):
1. **SIP OPTIONS flood**: Usually from a misconfigured monitoring probe or SBC health-check loop. Identify the source and either fix the configuration or block it on the firewall. OPTIONS floods are lower-risk than REGISTER/INVITE storms but waste SBC CPU.
2. **Cross-protocol storm (SIP + Diameter)**: Likely a mass device re-registration. Follow UC-5.10.5 runbook for SIP REGISTER storms. Monitor Diameter S6a interface for HSS overload.
3. **Diameter-only storm**: Check for DRA/peer reconnect loops. A Diameter peer that repeatedly connects and disconnects generates CER/CEA floods. Identify and stabilize the peer.

### Step 5 — Troubleshooting

- **Storm detection fires during planned maintenance** — Maintain a `maintenance_windows.csv` lookup and exclude those periods from alerting. SBC restarts, firmware updates, and certificate rotations all generate signaling bursts.

- **Health-check traffic dominates results** — SBC-to-SBC OPTIONS (keepalive) and Diameter DWR (watchdog) are normal but high-volume. Ensure the whitelist lookup is complete. Also filter out DWR (Diameter command 280) and SIP OPTIONS in the base search if they are not relevant to your monitoring goals.

- **`cmd_code` field is null for Diameter events** — The Diameter capture may use a different field name (e.g. `command_code`, `diameter_cmd`). Check `fieldsummary` on the Diameter sourcetype.

- **False positives at predictable times (morning, lunch)** — Business-hour patterns create predictable signaling spikes (device registration at 8 AM, SIP health-checks). Use time-of-day aware baselines or a longer lookback window (14 days) to capture weekly patterns.

## SPL

```spl
index=signaling (sourcetype="stream:sip" OR sourcetype="diameter:cap")
| bin _time span=1m
| stats count by method, cmd_code, _time
| eventstats avg(count) as mu, stdev(count) as s by method
| where count > mu+5*s
| sort -count
```

## Visualization

Timeline (spike detection), Table (method × source ASN), Single value (peak RPS).

## Known False Positives

Signaling errors from legacy phones with old firmware or NAT or SBC misalignment can spray retries; large conferences and registration refreshes can also spike counts briefly.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
