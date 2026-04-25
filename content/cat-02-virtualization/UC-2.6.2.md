<!-- AUTO-GENERATED from UC-2.6.2.json — DO NOT EDIT -->

---
id: "2.6.2"
title: "ICA/HDX Session Latency and Quality"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-2.6.2 · ICA/HDX Session Latency and Quality

## Description

ICA Round Trip Time (RTT) is the primary measure of Citrix session responsiveness — the time from a user keystroke to the response appearing on screen. Citrix defines 0–150ms as optimal, 150–300ms as acceptable, and above 300ms as degraded. Poor ICA latency causes sluggish typing, delayed screen updates, and broken audio/video, directly impacting user productivity. Monitoring ICA RTT across the fleet detects network issues, overloaded session hosts, and endpoint problems.

## Value

ICA Round Trip Time (RTT) is the primary measure of Citrix session responsiveness — the time from a user keystroke to the response appearing on screen. Citrix defines 0–150ms as optimal, 150–300ms as acceptable, and above 300ms as degraded. Poor ICA latency causes sluggish typing, delayed screen updates, and broken audio/video, directly impacting user productivity. Monitoring ICA RTT across the fleet detects network issues, overloaded session hosts, and endpoint problems.

## Implementation

Collect ICA RTT performance counters from VDAs using the `TA-XD7-VDA` add-on (Citrix ICA Session performance object). Alternatively, poll the Monitor Service OData API `SessionMetrics` endpoint. The difference between ICA RTT and ICA Latency indicates application processing time on the session host — if ICA Latency is high but network latency is low, the VDA is overloaded. Alert on sustained p95 RTT above 300ms. Segment by delivery group and VDA host to identify whether the issue is endpoint-specific (user's network), VDA-specific (overloaded host), or site-wide (network infrastructure).

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: uberAgent UXM (Splunkbase 1448) — recommended; or Template for Citrix XenDesktop 7 (`TA-XD7-VDA`), Citrix Monitor Service OData API.
• Ensure the following data sources are available: uberAgent: `sourcetype="uberAgent:Session:SessionDetail"` (ICA RTT, ICA latency, bandwidth, protocol, session quality); or `index=xd_perfmon` `sourcetype="citrix:vda:perfmon"` fields `ica_rtt_ms`, `ica_latency_ms`, `ica_bandwidth_in`, `ica_bandwidth_out`, `session_id`, `user`, `vda_host`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Collect ICA RTT performance counters from VDAs using the `TA-XD7-VDA` add-on (Citrix ICA Session performance object). Alternatively, poll the Monitor Service OData API `SessionMetrics` endpoint. The difference between ICA RTT and ICA Latency indicates application processing time on the session host — if ICA Latency is high but network latency is low, the VDA is overloaded. Alert on sustained p95 RTT above 300ms. Segment by delivery group and VDA host to identify whether the issue is endpoint-spe…

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=xd_perfmon sourcetype="citrix:vda:perfmon" counter_name="ICA RTT"
| bin _time span=5m
| stats avg(counter_value) as avg_rtt, perc95(counter_value) as p95_rtt, max(counter_value) as max_rtt by vda_host, _time
| eval quality=case(p95_rtt<=150, "Optimal", p95_rtt<=300, "Acceptable", 1=1, "Degraded")
| where quality="Degraded"
| table _time, vda_host, avg_rtt, p95_rtt, max_rtt, quality
```

Understanding this SPL

**ICA/HDX Session Latency and Quality** — ICA Round Trip Time (RTT) is the primary measure of Citrix session responsiveness — the time from a user keystroke to the response appearing on screen. Citrix defines 0–150ms as optimal, 150–300ms as acceptable, and above 300ms as degraded. Poor ICA latency causes sluggish typing, delayed screen updates, and broken audio/video, directly impacting user productivity. Monitoring ICA RTT across the fleet detects network issues, overloaded session hosts, and endpoint problems.

Documented **Data sources**: uberAgent: `sourcetype="uberAgent:Session:SessionDetail"` (ICA RTT, ICA latency, bandwidth, protocol, session quality); or `index=xd_perfmon` `sourcetype="citrix:vda:perfmon"` fields `ica_rtt_ms`, `ica_latency_ms`, `ica_bandwidth_in`, `ica_bandwidth_out`, `session_id`, `user`, `vda_host`. **App/TA** (typical add-on context): uberAgent UXM (Splunkbase 1448) — recommended; or Template for Citrix XenDesktop 7 (`TA-XD7-VDA`), Citrix Monitor Service OData API. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: xd_perfmon; **sourcetype**: citrix:vda:perfmon. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=xd_perfmon, sourcetype="citrix:vda:perfmon". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Discretizes time or numeric ranges with `bin`/`bucket`.
• `stats` rolls up events into metrics; results are split **by vda_host, _time** so each row reflects one combination of those dimensions.
• `eval` defines or adjusts **quality** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where quality="Degraded"` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **ICA/HDX Session Latency and Quality**): table _time, vda_host, avg_rtt, p95_rtt, max_rtt, quality

Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (ICA RTT over time by VDA), Heatmap (VDA x hour), Single value (fleet average RTT with color threshold).

## SPL

```spl
index=xd_perfmon sourcetype="citrix:vda:perfmon" counter_name="ICA RTT"
| bin _time span=5m
| stats avg(counter_value) as avg_rtt, perc95(counter_value) as p95_rtt, max(counter_value) as max_rtt by vda_host, _time
| eval quality=case(p95_rtt<=150, "Optimal", p95_rtt<=300, "Acceptable", 1=1, "Degraded")
| where quality="Degraded"
| table _time, vda_host, avg_rtt, p95_rtt, max_rtt, quality
```

## Visualization

Line chart (ICA RTT over time by VDA), Heatmap (VDA x hour), Single value (fleet average RTT with color threshold).

## References

- [uberAgent UXM](https://splunkbase.splunk.com/app/1448)
