<!-- AUTO-GENERATED from UC-5.10.6.json — DO NOT EDIT -->

---
id: "5.10.6"
title: "SIP Post-Dial Delay Monitoring"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.10.6 · SIP Post-Dial Delay Monitoring

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance

*We measure the gap between dialing and the call really starting so when voice feels slow or dead, the team has a number to chase instead of just complaints.*

---

## Description

Measures the time between a SIP INVITE and the first ringing or answer response, directly reflecting the user experience of waiting after dialing. High post-dial delay indicates trunk congestion, routing loops, or downstream SBC issues.

## Value

Voice quality teams identify trunk-level and carrier-level PDD degradation against ITU-T E.721 SLA thresholds, enabling proactive carrier engagement before customers experience unacceptable call setup delays.

## Implementation

Configure Splunk App for Stream to capture SIP INVITE and response transactions. The `setup_delay` field measures the time from INVITE to the first non-100 response (typically 180 Ringing or 200 OK). Monitor by `dest` to identify slow destinations or trunks. ITU-T E.721 recommends post-dial delay under 3 seconds for national calls and under 5 seconds for international calls. Create tiered alerts: warning at p95 >3s, critical at p95 >5s. Trend analysis reveals degradation patterns across time of day and destination.

## Detailed Implementation

### Prerequisites
- Splunk App for Stream (Splunkbase 1809) v8.0+ with the Stream Forwarder deployed on a mirror/tap that sees SIP signaling on trunk and subscriber-facing interfaces. The `setup_delay` field is computed by Stream from the time delta between the INVITE request and the first non-100 provisional or final response — this requires bidirectional traffic capture.
- Understand post-dial delay (PDD) in SIP terms: PDD is the interval from when the caller's device sends a SIP INVITE to when the called party's network sends back a meaningful response — typically 180 Ringing (phone is ringing) or 183 Session Progress (early media/ringback tone). The callerexperiences PDD as the silence between pressing "dial" and hearing a ringtone. Stream's `setup_delay` field captures this in seconds.
- Know the ITU-T E.721 benchmarks: PDD should be under 3 seconds for national calls, under 5 seconds for international calls, and under 8 seconds for satellite-routed calls. These are industry-standard SLA thresholds used by carriers and regulators.
- Understand PDD components: PDD = SBC processing time + trunk signaling latency + downstream routing hops + destination network processing. High PDD on a specific trunk indicates that trunk's carrier or the destination network is slow. High PDD across all trunks indicates your own SBC or routing infrastructure is the bottleneck.
- Index: use `index=telecom_sip` from UC-5.10.4. The `setup_delay` field is only available for completed INVITE transactions where the response was captured.

### Step 1 — Configure data collection
Reuse the SIP stream from UC-5.10.4. Verify that `setup_delay` is being computed:
```spl
index=telecom_sip sourcetype="stream:sip" method="INVITE" earliest=-1h
| where isnotnull(setup_delay)
| stats count avg(setup_delay) as avg_setup_delay_sec
```
If `setup_delay` is null for all events, the Stream Forwarder is not seeing the response messages (only INVITE requests). Verify the mirror captures both directions. Also check that the Stream version computes `setup_delay` — this field requires Stream to correlate the INVITE request with its response, which needs the `time_taken` or `setup_delay` field to be enabled in the stream configuration.

If `setup_delay` is truly unavailable, you can compute it manually by correlating INVITE requests with responses:
```spl
index=telecom_sip sourcetype="stream:sip" (method="INVITE" OR (reply_code>=100 AND reply_code<200) OR reply_code=200) earliest=-1h
| transaction call_id maxspan=30s
| eval pdd=duration
| where isnotnull(pdd)
| stats avg(pdd) as avg_pdd_sec by dest
```
Note: `transaction` is expensive; prefer the native `setup_delay` field.

Establish your baseline PDD:
```spl
index=telecom_sip sourcetype="stream:sip" method="INVITE" reply_code=200 earliest=-7d
| where isnotnull(setup_delay)
| stats avg(setup_delay) as avg_pdd perc50(setup_delay) as p50_pdd perc95(setup_delay) as p95_pdd perc99(setup_delay) as p99_pdd by dest
| eval avg_ms=round(avg_pdd*1000,0), p50_ms=round(p50_pdd*1000,0), p95_ms=round(p95_pdd*1000,0), p99_ms=round(p99_pdd*1000,0)
| sort -p95_ms
```
Record these baselines per trunk/destination for comparison in alerting and validation.

### Step 2 — Create the search and alert

**Primary search — PDD by destination with ITU-T E.721 thresholds (15-min alert):**
```spl
index=telecom_sip sourcetype="stream:sip" method="INVITE" reply_code=200 earliest=-15m
| where isnotnull(setup_delay)
| stats avg(setup_delay) as avg_pdd perc50(setup_delay) as p50_pdd perc95(setup_delay) as p95_pdd max(setup_delay) as max_pdd count as calls by dest
| eval avg_ms=round(avg_pdd*1000, 0), p50_ms=round(p50_pdd*1000, 0), p95_ms=round(p95_pdd*1000, 0), max_ms=round(max_pdd*1000, 0)
| lookup sip_trunks.csv dest_ip as dest OUTPUT carrier_name trunk_group call_type
| eval trunk_label=if(isnotnull(carrier_name), carrier_name, dest)
| eval sla_threshold=case(call_type=="international", 5000, call_type=="satellite", 8000, 1==1, 3000)
| eval sla_status=if(p95_ms > sla_threshold, "VIOLATION", "OK")
| where p95_ms > 2000 OR sla_status="VIOLATION"
| sort -p95_ms
```

#### Understanding this SPL: We filter for successful INVITE transactions (reply_code=200) because PDD is only meaningful for calls that connected. Failed calls have no meaningful delay metric. We compute avg, p50, p95, and max PDD in milliseconds per destination. The trunk lookup provides carrier name and `call_type` (national/international/satellite) which determines the applicable ITU-T E.721 SLA threshold. `sla_status` flags destinations that violate their applicable SLA. We surface any destination with p95 > 2 seconds as a monitoring candidate, and flag SLA violations for immediate attention.

**PDD distribution — histogram for a specific trunk (investigation):**
```spl
index=telecom_sip sourcetype="stream:sip" method="INVITE" reply_code=200 dest="<trunk_ip>" earliest=-4h
| where isnotnull(setup_delay)
| eval pdd_ms=round(setup_delay*1000, 0)
| eval pdd_bucket=case(pdd_ms<500, "0-500ms", pdd_ms<1000, "500ms-1s", pdd_ms<2000, "1-2s", pdd_ms<3000, "2-3s", pdd_ms<5000, "3-5s", 1==1, ">5s")
| stats count by pdd_bucket
| sort pdd_bucket
```

#### Understanding this SPL: For a flagged trunk, this shows the distribution of PDD values. A bimodal distribution (most calls fast, but a tail of slow calls) suggests intermittent routing issues. A uniformly shifted distribution (all calls slow) suggests a systematic trunk or carrier problem.

**PDD trending — degradation detection over 24h:**
```spl
index=telecom_sip sourcetype="stream:sip" method="INVITE" reply_code=200 earliest=-24h
| where isnotnull(setup_delay)
| eval pdd_ms=round(setup_delay*1000, 0)
| bin _time span=15m
| stats avg(pdd_ms) as avg_ms perc95(pdd_ms) as p95_ms count as calls by _time, dest
| lookup sip_trunks.csv dest_ip as dest OUTPUT carrier_name
| eval trunk=if(isnotnull(carrier_name), carrier_name, dest)
| where p95_ms > 1500
| timechart span=15m avg(p95_ms) by trunk
```

#### Understanding this SPL: 24-hour p95 PDD trend per trunk. Reveals time-of-day patterns (carrier congestion during business hours), gradual degradation (routing table growth, DNS resolution slowdown), or step-function increases (carrier configuration change). Compare multiple trunks — if all trunks show simultaneous degradation, the issue is local (your SBC, DNS, or network path).

Schedule as Alert: the primary search runs every 15 minutes. Trigger when `sla_status="VIOLATION"` for any trunk with `calls > 20` (minimum sample size). Throttle by `dest` for 1 hour.

### Step 3 — Validate
(a) On the SBC, pull CDR records for the same time window and compare PDD values. The SBC typically reports "Post-Dial Delay" or "Setup Time" in its CDR fields. Splunk and SBC PDD should match within 50ms — larger differences suggest the mirror is adding capture latency or the SBC measures PDD differently (e.g. from the SBC's INVITE relay to the response, excluding initial processing time).

(b) Make a test call to a known stable destination (e.g. your own IVR system on the same network) and verify the PDD in Splunk is <500ms. If it shows >1 second for a local call, there may be a systematic measurement issue.

(c) Verify `setup_delay` units: Stream may report in seconds (float) or microseconds (integer). Run `| head 5 | table setup_delay` to check. If values are in the millions, they are microseconds — divide by 1000000 instead of multiplying by 1000.

(d) Check that only INVITE→response pairs are included: if Stream reports `setup_delay` on non-INVITE methods or on retransmissions, filter appropriately. Use `| dedup call_id` if needed.

(e) Validate the `sip_trunks.csv` lookup includes the `call_type` column (national/international) so ITU-T thresholds apply correctly.

### Step 4 — Operationalize
Dashboard (recommended layout, named "Voice — Post-Dial Delay"):
- Row 1 — Single-value tiles: "Fleet p95 PDD (ms)" (gauge: green <2s, yellow 2–3s, red >3s), "Trunks violating SLA", "Total successful calls (15m)", "Worst trunk PDD (ms)".
- Row 2 — Timechart: p95 PDD per trunk over 24h with ITU-T threshold lines (3s national, 5s international).
- Row 3 — Table: trunk label, carrier, call_type, calls, avg_ms, p50_ms, p95_ms, max_ms, sla_status (color-coded). Drilldown to PDD histogram for the selected trunk.
- Row 4 — PDD distribution histogram for the selected trunk (from drill-down), showing the shape of the delay distribution.

Alerting:
- Critical (SLA violation — p95 > threshold for trunk type): page voice operations and carrier management. Include trunk name, carrier, p95 PDD, SLA threshold, and call count. This may constitute an SLA breach with financial penalties.
- Warning (p95 > 2s for any trunk): ticket to voice engineering for investigation.
- Trend (p95 increasing steadily over 7 days): weekly report to capacity planning — proactive carrier engagement needed.

Runbook (owner: Voice Operations / Carrier Management):
1. **Single trunk SLA violation**: Contact the carrier NOC with the trunk ID, time window, and p95 PDD value. Provide the PDD histogram — carriers need the distribution to diagnose (is it a few very slow calls or all calls moderately slow?). If an alternate trunk to the same destination exists, reroute traffic while the carrier investigates.
2. **All trunks degraded simultaneously**: The issue is local. Check SBC CPU utilization (high CPU adds processing delay to every call). Check DNS resolution time for SIP domains (slow DNS adds seconds to PDD). Check the SBC's routing table evaluation time (large route tables with complex regex patterns slow INVITE processing).
3. **Intermittent PDD spikes (bimodal distribution)**: Some calls route through a slow intermediate hop while others take a fast path. Check if the destination uses multiple points of presence (PoPs) with different latencies. The SBC may be load-balancing across these PoPs — investigate per-hop PDD if path data is available.
4. **PDD degradation correlated with call volume**: Peak-hour PDD increase suggests trunk capacity issues. The carrier may be queueing calls during congestion. Request trunk capacity increase or add additional carrier routes for the affected destinations.

### Step 5 — Troubleshooting

- **`setup_delay` is null for all events** — The Stream Forwarder needs both the INVITE request and the response to compute setup_delay. If the mirror only captures one direction, this field will be null. Verify bidirectional capture. Also check Stream version — older versions may not compute SIP timing fields.

- **PDD values seem unreasonably high (>30 seconds)** — Check for SIP forking: if the INVITE is forked to multiple destinations, Stream may measure the delay to the last response rather than the first. Also check for 3xx redirect responses that add additional routing hops before the final response.

- **PDD varies wildly for the same trunk** — This is often caused by DNS: if the SBC resolves the carrier's SIP domain via DNS for each call, and DNS response time varies, PDD will vary accordingly. Implement SBC-side DNS caching or static IP configuration for carrier trunks.

- **p95 PDD is high but avg is low** — A small percentage of calls are very slow while most are fast. Check for specific called number patterns (international prefixes, mobile numbers) that route through different paths. The slow calls may be going through an additional routing hop or transit carrier.

- **PDD measurement includes ringback time** — If `setup_delay` measures INVITE-to-200-OK (answer) instead of INVITE-to-180-Ringing, it includes the time the called party's phone rings before they pick up. This is not true PDD. Check the Stream documentation for your version and filter to `reply_code=180` (or 183) instead of 200 for a more accurate PDD measurement.

## SPL

```spl
sourcetype="stream:sip" method="INVITE" reply_code=200
| where isnotnull(setup_delay)
| stats avg(setup_delay) as avg_pdd, perc95(setup_delay) as p95_pdd, max(setup_delay) as max_pdd, count as calls by dest
| eval avg_pdd_ms=round(avg_pdd*1000, 0), p95_pdd_ms=round(p95_pdd*1000, 0)
| where p95_pdd_ms>3000
| sort -p95_pdd_ms
```

## Visualization

Gauge (p95 post-dial delay with thresholds: green <2s, yellow 2-3s, red >3s), Line chart (average PDD trend by dest over 24h), Table (dest, calls, avg_pdd_ms, p95_pdd_ms, max_pdd_ms — sortable), Histogram (PDD distribution across all calls).

## Known False Positives

SBC certificate rolls, number portability batches, and customer premise equipment reboots can spike SIP failures. Match trunk names to the carrier work queue.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
