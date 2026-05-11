<!-- AUTO-GENERATED from UC-5.9.9.json — DO NOT EDIT -->

---
id: "5.9.9"
title: "BGP Path Change Trending"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.9.9 · BGP Path Change Trending

> **Criticality:** High &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Anomaly &middot; **Wave:** Walk &middot; **Status:** Verified

*We track how often the internet changes the route it uses to reach our addresses. A sudden burst of route changes is like seeing all the road signs on the highway flip at once — it usually means something just happened in the network, and we need to check whether it's causing problems.*

---

## Description

Trends the volume of BGP path changes observed across ThousandEyes' global BGP monitors, per prefix per hour. A sudden spike in path change count — from a baseline of 0–2 per hour to 50+ — signals routing instability that could be a BGP convergence event, a route leak, or the early stages of a BGP hijack. The trend view distinguishes transient events (single spike that returns to baseline) from sustained instability (elevated path changes for hours).

## Value

BGP path changes are the precursor to user-visible impact. When a carrier changes how it routes to your prefix, your latency changes, your traceroutes change, and in the worst case your reachability changes. By trending path change volume in Splunk alongside UC-5.9.8 (reachability), the NOC can correlate: "reachability dropped to 95% at 14:30 — and path changes spiked to 40/hour at 14:28." This causal chain turns a confusing reachability alert into an actionable diagnosis: the routing instability caused the reachability drop, and the ISP whose monitors show the most path changes is likely the source.

## Implementation

Uses the same Tests Stream — Metrics data as UC-5.9.8. No additional data collection required. The `bgp.path_changes.count` metric is reported alongside `bgp.reachability` in the same BGP test events. Schedule as a dashboard panel for continuous trending; set an alert for spikes exceeding 3× the 7-day baseline.

## Detailed Implementation

### Prerequisites
- All prerequisites from UC-5.9.8 apply — BGP tests configured in ThousandEyes, Tests Stream — Metrics input enabled, BGP data flowing to `thousandeyes_metrics`.
- **Baseline period:** Allow at least 7 days of data collection before setting alert thresholds. BGP path change rates vary significantly between prefixes based on how many upstream paths exist, how many monitors observe the prefix, and the prefix's position in the global routing table.

### Step 1 — Configure data collection
Same as UC-5.9.8. No additional configuration. The `bgp.path_changes.count` metric is reported in the same BGP test events as `bgp.reachability`.

Verify the metric is present:
```spl
index=thousandeyes_metrics thousandeyes.test.type="bgp" earliest=-1h
| stats sum(bgp.path_changes.count) as total_changes by network.prefix
```
A value of 0 is normal during stable routing — it means no path changes were observed. A non-zero value means at least one monitor saw a path change.

### Step 2 — Create the search and alert
**Trending search (for dashboard):**
```spl
`stream_index` thousandeyes.test.type="bgp"
| timechart span=1h sum(bgp.path_changes.count) as path_changes by network.prefix
```

**Alert search (for anomaly detection):**
```spl
`stream_index` thousandeyes.test.type="bgp"
| stats sum(bgp.path_changes.count) as hourly_changes by network.prefix
| where hourly_changes > 10
| sort -hourly_changes
```

**Understanding this SPL**

`timechart span=1h sum(bgp.path_changes.count)` — sums all path changes across all monitors for each prefix per hour. Why `sum` not `avg`: path changes are a count metric — you want the total volume of changes, not the average per monitor. A single monitor seeing 1 path change is different from 50 monitors all seeing path changes simultaneously (which indicates a widespread routing event).

`by network.prefix` — splits the timechart by prefix so you can see which prefix is experiencing instability. If ALL prefixes spike simultaneously, it's likely a backbone event. If only one prefix spikes, the issue is specific to that prefix's routing.

**Threshold for alerting:** The `where hourly_changes > 10` threshold is a starting point. Establish your baseline by running the trending search over 7 days: `| stats avg(path_changes) as baseline_avg stdev(path_changes) as baseline_stdev by network.prefix`. Set the alert threshold at `baseline_avg + 3 * baseline_stdev` to catch anomalies while avoiding false positives from normal routing variation.

**Per-monitor breakdown variant** (for investigation):
```spl
`stream_index` thousandeyes.test.type="bgp" network.prefix="<your-prefix>"
| stats sum(bgp.path_changes.count) as changes by thousandeyes.monitor.name, thousandeyes.monitor.location
| where changes > 0
| sort -changes
```
This shows which specific monitors/ISPs are seeing path changes, narrowing the investigation to the affected part of the internet.

**Scheduling:** For the trending dashboard: auto-refresh every 15 minutes. For the alert: cron `0 * * * *`, time range `-1h to now`, trigger on "Number of results > 0". Throttle by `network.prefix` for 4 hours.

### Step 3 — Validate
(a) **Cross-reference ThousandEyes UI.** The ThousandEyes BGP Route Visualization shows path change events as markers on the timeline. Compare the spike times and magnitudes in Splunk to the UI markers.

(b) **Correlation with reachability.** When path changes spike, check UC-5.9.8 reachability for the same prefix and time window. A path change spike WITH a reachability drop is a confirmed routing incident. A path change spike WITHOUT reachability impact means the routing changed but all new paths are valid (carrier optimization).

(c) **Baseline verification.** After 7 days of data, run the baseline stats query. Normal path change rates vary by prefix: a well-connected prefix may see 0–5 path changes per hour normally, while a prefix with many upstream paths may see 5–15. Set thresholds accordingly.

### Step 4 — Operationalize
**Dashboard** (add as a row in the UC-5.9.8 "BGP Prefix Health" dashboard):
- Timechart: path changes per hour per prefix over 24 hours. Add a baseline reference line (horizontal line at the 3σ threshold) to make spikes visually obvious.
- Bar chart: total path changes per monitor, top 10 — identifies the ISP vantage points seeing the most churn.
- Correlation panel: overlay path changes with reachability for the same prefix on the same timechart (dual Y-axis).

**Runbook** (owner: Network Engineering):
1. **Path change spike detected.** Check whether reachability (UC-5.9.8) is also affected.
2. **If reachability is fine:** Monitor for 1 hour. The routing is changing but all new paths are valid. May be carrier maintenance or traffic engineering.
3. **If reachability dropped:** This is an active routing incident. Follow UC-5.9.8 runbook for triage.
4. **Check which monitors are affected:** If path changes are concentrated in a few monitors from the same ISP, that ISP is changing its routing. If widespread across many ISPs, the change is happening closer to your origin network.
5. **Check UC-5.9.11 (AS Path Monitoring):** Identify which ASNs appeared or disappeared from the path. A new, unexpected ASN in the path could indicate a route leak or hijack.

### Step 5 — Troubleshooting

- **`bgp.path_changes.count` is always 0** — This is likely correct! Stable routing produces 0 path changes. Only investigate if you know a routing event occurred but Splunk didn't record path changes — in that case, check the BGP test interval (15 minutes may miss brief flaps that converge in < 15 minutes).

- **Path change counts seem unrealistically high (thousands per hour)** — Check whether multiple BGP tests are configured for the same prefix, causing double-counting. Also check whether the sum is being computed per-monitor (which is correct) vs per-event (which may overcount if events contain aggregated data).

- **All common troubleshooting** — See UC-5.9.8 and UC-5.9.1 Step 5.

## SPL

```spl
`stream_index` thousandeyes.test.type="bgp"
| timechart span=1h sum(bgp.path_changes.count) as path_changes by network.prefix
```

## Visualization

(1) Line chart: `timechart span=1h sum(bgp.path_changes.count) as path_changes by network.prefix` — shows path change volume over 24 hours per prefix. Spikes are immediately visible. (2) Single value: total path changes in the last hour (baseline comparison). (3) Bar chart: total path changes per monitor, sorted descending — identifies which monitors/ISPs are seeing the most churn. (4) Correlation panel: overlay path change timechart with reachability timechart (UC-5.9.8) for the same prefix to show cause and effect.

## Known False Positives

**Carrier peering changes and traffic engineering.** Large ISPs routinely adjust BGP policies — prepending, community changes, peer preference shifts — during maintenance windows, typically at off-peak hours. These produce bursts of path changes that are planned and benign. Distinguish by checking whether the changes occur during known ISP maintenance windows and whether reachability remains at 100%.

**Initial BGP test setup.** When a new BGP test is created, monitors need one or two collection cycles to establish a baseline path. The first few rounds may report path changes as the monitor's RIB converges. Ignore path changes in the first 30 minutes after test creation.

**Internet backbone events (submarine cable cuts, IX outages).** Major internet infrastructure events cause global BGP path changes across all monitors and prefixes simultaneously. If you see a spike across ALL prefixes and ALL monitors at the same time, it's likely a backbone event, not specific to your prefix. Check BGP event feeds (bgpstream.com, ThousandEyes Outages page) to confirm.

**AS path prepending changes by your own team.** If your network engineering team changes BGP prepending on your announcements, monitors will observe path changes as ISPs re-converge to the new best path. Correlate with your change management system.

## References

- [Cisco ThousandEyes App for Splunk (Splunkbase 7719)](https://splunkbase.splunk.com/app/7719)
- [ThousandEyes BGP Route Monitoring — Path change metrics](https://docs.thousandeyes.com/product-documentation/internet-and-wan-monitoring/tests/)
- [BGP Route Instability Analysis — RIPE RIS](https://www.ripe.net/analyse/internet-measurements/routing-information-service-ris)
