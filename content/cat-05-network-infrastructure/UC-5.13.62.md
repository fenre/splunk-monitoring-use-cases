<!-- AUTO-GENERATED from UC-5.13.62.json — DO NOT EDIT -->

---
id: "5.13.62"
title: "Wireless Channel Utilization and Interference"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.13.62 · Wireless Channel Utilization and Interference

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance &middot; **Wave:** Walk &middot; **Status:** Verified

*We measure how crowded each wireless channel is — like checking how busy a walkie-talkie frequency is. When a channel is too busy, everyone on it experiences slow connections. We find the busy channels so your wireless team can spread the traffic more evenly across available frequencies.*

---

## Description

Monitors wireless channel utilisation and interference levels per AP and frequency band, identifying congested channels, high-interference zones, and opportunities for RRM optimisation — the RF-layer diagnostics that explain why Wi-Fi is slow even when signal strength (UC-5.13.42) looks fine.

## Value

Signal strength (RSSI) tells you whether the client can hear the AP. Channel utilisation tells you whether the AP can actually *transmit*. An AP with excellent RSSI (-55 dBm) but 85% channel utilisation is like a strong radio station on a crowded frequency — you can hear it, but it can't get a word in. High utilisation means the AP is waiting for airtime, causing latency and jitter that destroy VoIP and video quality. High interference means non-Wi-Fi sources (microwaves, Bluetooth, radar on DFS channels) are corrupting the channel. This UC is the missing link between 'signal is fine' (UC-5.13.42) and 'users say Wi-Fi is slow' (UC-5.13.9).

## Implementation

Requires a custom scripted input for wireless RF data (see `docs/guides/catalyst-center.md` § Custom Scripted Inputs). Poll every 15 minutes. Place alongside UC-5.13.42 (RSSI/SNR) on the Wireless Performance dashboard.

## Detailed Implementation

### Prerequisites
- Custom scripted input for wireless RF data must be deployed. The native TA does not include an RF metrics modular input. See `docs/guides/catalyst-center.md` § Custom Scripted Inputs — Wireless RF Health for the script template.
- The Catalyst Center RF APIs may vary by version. Common endpoints: `GET /dna/intent/api/v1/wireless/rf-profile` for RF profiles, and per-AP Assurance detail endpoints for radio metrics.
- Understanding RF fundamentals: channel utilisation > 50% = congestion begins; > 80% = significant performance impact. Interference > 30% = non-Wi-Fi sources competing for airtime.

### Step 1 — Configure data collection
Deploy the RF polling script:
```ini
[script://$SPLUNK_HOME/etc/apps/TA_catalyst_rf/bin/poll_rf_health.py]
interval = 900
sourcetype = cisco:dnac:wireless:rf
index = catalyst
disabled = 0
```

The script polls per-AP radio metrics and outputs: `apName`, `band`, `channel`, `channelUtilization`, `interferencePercentage`, `noiseFloor`, `txPower`.

Verification:
```spl
index=catalyst sourcetype="cisco:dnac:wireless:rf" earliest=-30m
| stats dc(apName) as aps avg(channelUtilization) as avg_util by band
```

### Step 2 — Create the search and report
```spl
index=catalyst sourcetype="cisco:dnac:wireless:rf"
| stats latest(channelUtilization) as util latest(interferencePercentage) as interference latest(channel) as ch latest(txPower) as power by apName, band
| eval rf_quality=case(util>80,"Congested", util>50,"Busy", interference>30,"High Interference", 1==1,"Good")
| sort -util
```

Why separate `util` and `interference`: utilisation includes ALL airtime usage (your clients + neighbours + interference). Interference is specifically non-Wi-Fi sources. An AP with `util=80%, interference=5%` is congested from Wi-Fi traffic (too many clients or neighbours). An AP with `util=80%, interference=50%` has a non-Wi-Fi interference source that's consuming half the airtime.

Why include `channel` and `txPower`: these are the levers the wireless engineer can adjust. Knowing the current channel and power level helps plan channel changes or power reductions to alleviate co-channel interference.

For per-channel congestion analysis:
```spl
index=catalyst sourcetype="cisco:dnac:wireless:rf" band="5.0"
| stats dc(apName) as ap_count avg(channelUtilization) as avg_util by channel
| sort channel
```

Schedule: every 15 minutes as a real-time dashboard panel. Alert: `rf_quality IN ("Congested","High Interference")` for APs with > 10 connected clients.

### Step 3 — Validate
(a) Pick an AP from the results. Open **Catalyst Center > Assurance > Device 360 > [AP] > RF** and compare channel, utilisation, and interference values.
(b) Walk to the AP's location with a Wi-Fi analyser. Compare the measured channel utilisation with the Splunk value.
(c) Cross-reference congested APs with UC-5.13.42 (RSSI/SNR) and UC-5.13.12 (Client Health by SSID) — high utilisation APs should correlate with poor client health.
(d) Check 2.4 GHz vs 5 GHz utilisation patterns — 2.4 GHz is typically more congested due to fewer non-overlapping channels.

### Step 4 — Operationalize
- Wireless Performance dashboard: RF quality table alongside RSSI/SNR (UC-5.13.42).
- RRM effectiveness assessment: are auto-adjustments reducing congestion?
- Capacity planning: APs consistently above 70% utilisation need client load redistribution (add APs, enable band steering).

Runbook (owner: Wireless Engineering):
1. Identify APs with `rf_quality = Congested`.
2. Check `interference` — if > 30%, investigate non-Wi-Fi sources (spectrum analyser needed).
3. If interference is low but utilisation is high: too many clients or too many APs on the same channel. Check co-channel interference: `| stats dc(apName) by channel, band` — channels with > 3 APs have co-channel issues.
4. Solutions: change channel (manual or let RRM handle it), reduce Tx power to shrink cell size, add APs to distribute the load.
5. After changes: monitor this UC for 48 hours to confirm improvement.

### Step 5 — Troubleshooting

- **No `cisco:dnac:wireless:rf` events** — the custom scripted input is not deployed. Follow `docs/guides/catalyst-center.md` § Custom Scripted Inputs.

- **`channelUtilization` is null** — the RF API may not expose this field in your Catalyst Center version. Check `| fieldsummary` for available RF fields.

- **All APs show 0% utilisation** — the APs may not be reporting RF metrics (older models, disabled radio). Check AP radio status in Catalyst Center.

- **Utilisation is always high on 2.4 GHz** — expected in dense environments. 2.4 GHz has only 3 non-overlapping channels (1, 6, 11). Consider disabling 2.4 GHz on some APs and using band steering to push clients to 5 GHz.

- **Interference spikes at regular intervals** — a non-Wi-Fi device is operating on a schedule (microwave in a break room at noon, automated equipment). Use spectrum analysis to identify the source.

- **Channel changes frequently** — RRM is actively optimising. If the network is stable, this is normal. If it's oscillating (channel A → B → A → B), disable RRM for that AP and set channels manually.

- **RF data doesn't correlate with client complaints** — the RF data shows the AP's perspective. Clients in a different physical location may experience different RF conditions. Use UC-5.13.42 (per-client RSSI) alongside this UC.

- **Want to track RF quality over time** — use `| timechart span=1h avg(channelUtilization) by band` for fleet-level RF trending.

Additional operational context for Wireless Channel Utilization and Interference:

For month-over-month comparison:
- Export the primary search results monthly as CSV to a `catalyst_monthly_snapshots` directory. Compare current month vs previous month to identify trends, improvements, and regressions.
- Track the key metric from this UC over 90 days with `| timechart span=1w` for the quarterly operations review.

For SLA alignment:
- Define the acceptable threshold for this UC's primary metric in your SLA documentation.
- Schedule a weekly check against the SLA target. Breaches should generate tickets in your ITSM with a link to this UC's dashboard panel for investigation context.

Cross-reference with related UCs:
- When this UC flags an issue, always cross-reference with UC-5.13.1 (Device Health) and UC-5.13.16 (Network Health) to assess the broader impact.
- For compliance-related findings, connect to UC-5.13.28-33 for the compliance posture context.
- For security-related findings, connect to UC-5.13.34-39 for PSIRT advisory exposure.

Runbook integration:
- Document the response procedure for each alert from this UC in your operations runbook.
- Include: who to contact, what to check first, typical root causes, and escalation criteria.
- Review and update the runbook quarterly based on actual alert outcomes (was the runbook helpful? did it miss common scenarios?).

Additional troubleshooting:
- If the search returns unexpected results, check `| fieldsummary` on the base data to verify field names and types match the SPL.
- If data is not arriving for the expected sourcetype, verify the TA input is enabled and check `index=_internal sourcetype=splunkd component=ExecProcessor "TA_cisco_catalyst"` for errors from the modular input.
- If field values changed after a Catalyst Center upgrade, compare `| fieldsummary` from before and after the upgrade to identify renamed or restructured fields.
- If the search is slow, narrow the time range to `earliest=-20m` for a real-time snapshot, or use summary indexing for historical analysis.
- For vendor UI parity, cross-reference the Splunk results with the corresponding **Catalyst Center > Assurance** page for the same time window to confirm counts and values match.


## SPL

```spl
index=catalyst sourcetype="cisco:dnac:wireless:rf"
| stats latest(channelUtilization) as util latest(interferencePercentage) as interference latest(channel) as ch latest(txPower) as power by apName, band
| eval rf_quality=case(util>80,"Congested", util>50,"Busy", interference>30,"High Interference", 1==1,"Good")
| sort -util
```

## Visualization

(1) Table: apName, band, ch, util, interference, power, rf_quality — sorted by utilisation. (2) Heatmap: APs (rows) × bands (columns) with utilisation as colour (green < 50%, yellow 50–80%, red > 80%). (3) Histogram: channel utilisation distribution across fleet. (4) Scatter: utilisation (x) vs interference (y) — APs in top-right quadrant (high both) need channel changes.

## Known False Positives

**High channel utilisation during peak business hours.** Channel utilisation naturally increases during high-client-density periods (10 AM–3 PM). Distinguish by comparing against time-of-day baselines. Suppress by setting thresholds appropriate for peak hours (70%) vs off-hours (30%).

**DFS channel radar event causing temporary channel change.** APs on DFS channels (5 GHz channels 52–144) may vacate the channel when radar is detected, temporarily spiking utilisation on the fallback channel. Distinguish by checking for channel changes: `| streamstats last(channel) as prev_ch by apName | where channel != prev_ch`. Do not suppress — but note it's a regulatory requirement, not a network problem.

**High interference from non-Wi-Fi sources.** Microwaves, Bluetooth devices, wireless video transmitters, and medical equipment operate in the 2.4 GHz band and cause interference that's unrelated to Wi-Fi design. Distinguish by checking whether interference is concentrated in the 2.4 GHz band at specific locations (kitchen, break room, medical wing). Fix by using spectrum analysis to identify the source.

**RRM power/channel adjustments appearing as instability.** Catalyst Center's RRM engine periodically adjusts AP channels and power levels, which can cause short-term utilisation changes. Distinguish by correlating with RRM event logs. Do not suppress — but expect periodic channel shifts as normal RRM behaviour.

## References

- [Cisco Catalyst Add-on for Splunk (Splunkbase 7538)](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center RF Health APIs](https://developer.cisco.com/docs/catalyst-center/#!retrieve-rf-profiles)
- [Catalyst Center Integration Guide (this repo)](../../docs/guides/catalyst-center.md)
- [Cisco Wireless Design — RF Planning and Channel Management](https://www.cisco.com/c/en/us/solutions/design-zone/networking-design-guides/campus-wired-wireless.html)
