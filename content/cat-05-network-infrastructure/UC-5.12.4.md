<!-- AUTO-GENERATED from UC-5.12.4.json — DO NOT EDIT -->

---
id: "5.12.4"
title: "SIP Trunk Utilization"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.12.4 · SIP Trunk Utilization

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Capacity

*We help you know how full your SIP trunks to carriers or cloud are, so you can add capacity or move traffic before busy-hour busy signals.*

---

## Description

Concurrent session counts or peg counts vs. licensed trunk capacity — prevents preemptive blocking at peak.

## Value

Capacity planners and voice operations prevent call blocking by tracking real-time trunk utilization against licensed capacity and forecasting when expansion is needed.

## Implementation

Separate inbound vs. outbound if asymmetric licensing; forecast with `predict` for capacity planning.

## Detailed Implementation

### Prerequisites
- Two data sources for trunk utilization: (a) SNMP polling of the SBC via `sourcetype=snmp:sbc` — polls active session counts at regular intervals (1-5 minutes), giving point-in-time concurrent session numbers; (b) SIP wire data via `sourcetype=stream:sip` — captures individual SIP transactions, from which concurrency can be derived by counting overlapping sessions.
- For SNMP: configure SNMP polling from Splunk (Splunk Add-on for SNMP, or Splunk Connect for SNMP / SC4SNMP) targeting the SBC's session count OIDs. Common OIDs: Cisco CUBE uses vendor-specific MIBs, AudioCodes uses `acPMActiveSIPSessions`, Ribbon uses `sipSgSgSessionCount`. The polled value gives `active_calls` or `curr_sess` per trunk group.
- Build a `trunk_capacity.csv` lookup with columns: `trunk_group`, `licensed_sess` (maximum licensed concurrent sessions), `carrier_name`, `direction` (inbound/outbound/bidirectional). This is critical — without it, you cannot calculate utilization percentage.
- Index: `index=voip` for SIP/CDR data, `index=snmp` for SNMP polls.

### Step 1 — Configure data collection
For SNMP-based monitoring, configure SC4SNMP or the SNMP Modular Input to poll session counts every 60 seconds.

Verify SNMP data arrival:
```spl
index=snmp sourcetype="snmp:sbc" earliest=-15m
| stats count latest(active_calls) as latest_sessions by host, trunk_group
```
Each row should show the SBC hostname and trunk group with a recent session count.

For Stream-based concurrent session derivation (if SNMP is not available):
```spl
index=voip sourcetype="stream:sip" method="INVITE" reply_code=200 earliest=-15m
| bin _time span=1m
| stats dc(call_id) as concurrent_sessions by _time, dest
```

Upload the `trunk_capacity.csv` lookup with your SBC's licensed session limits.

### Step 2 — Create the search and alert

**Primary search — Trunk utilization (5-min poll):**
```spl
index=voip (sourcetype="stream:sip" OR sourcetype="snmp:sbc") earliest=-4h
| eval concurrent=coalesce(active_calls, curr_sess)
| bin _time span=5m
| stats max(concurrent) as peak_sess by _time, trunk_group
| lookup trunk_capacity.csv trunk_group OUTPUT licensed_sess carrier_name direction
| eval util_pct=if(isnotnull(licensed_sess) AND licensed_sess > 0, round(100*peak_sess/licensed_sess, 1), null())
| eval status=case(util_pct >= 95, "CRITICAL", util_pct >= 85, "WARNING", util_pct >= 70, "Monitor", 1==1, "Healthy")
| where util_pct >= 70
| sort -util_pct
```

#### Understanding this SPL: We use `coalesce` to handle both SNMP-sourced (`active_calls`) and Stream-sourced (`curr_sess`) fields. The 5-minute max gives peak concurrency per trunk group. Thresholds: 70% = capacity planning trigger, 85% = expand soon, 95% = imminent blocking (calls will get 503 or busy signal).

**Capacity forecasting — predict when trunk will hit capacity:**
```spl
index=voip (sourcetype="stream:sip" OR sourcetype="snmp:sbc") earliest=-30d
| eval concurrent=coalesce(active_calls, curr_sess)
| bin _time span=1h
| stats max(concurrent) as peak_hourly by _time, trunk_group
| lookup trunk_capacity.csv trunk_group OUTPUT licensed_sess
| timechart span=1d max(peak_hourly) as daily_peak by trunk_group
| predict daily_peak as predicted_peak future_timespan=30
```

#### Understanding this SPL: Uses Splunk's `predict` command (Kalman filter) to forecast peak concurrency 30 days forward. If the predicted value crosses the `licensed_sess` threshold within the forecast window, trunk expansion is needed.

**Inbound vs. outbound split:**
```spl
index=voip sourcetype="stream:sip" method="INVITE" earliest=-4h
| eval call_direction=if(match(src, "^(10\.|172\.)"), "Outbound", "Inbound")
| bin _time span=5m
| stats dc(call_id) as concurrent by _time, trunk_group, call_direction
| lookup trunk_capacity.csv trunk_group OUTPUT licensed_sess
| eval util_pct=round(100*concurrent/licensed_sess, 1)
```

Schedule as Alert: primary search runs every 5 minutes. Trigger when `util_pct >= 85`. Critical at 95%. Throttle by trunk_group for 30 minutes.

### Step 3 — Validate
(a) On the SBC management console, check the real-time concurrent session count for each trunk group. Compare to Splunk's `peak_sess`. They should match within 5%.
(b) Verify `trunk_capacity.csv` accuracy against actual SBC license page. An incorrect `licensed_sess` value makes utilization percentages meaningless.
(c) During a known peak hour, verify that Splunk shows the expected peak and that it aligns with historical patterns.
(d) Test the forecast: compare last week's prediction to actual values.

### Step 4 — Operationalize
Dashboard ("Voice - SIP Trunk Capacity"):
- Row 1 — Gauge per trunk group: current utilization with green/yellow/red zones.
- Row 2 — Timechart: peak concurrency per trunk over 7 days with licensed capacity as reference lines.
- Row 3 — Forecast chart: predicted daily peak for next 30 days per trunk.
- Row 4 — Table: trunk group, carrier, licensed sessions, current peak, utilization, status.

Alerting:
- Critical (util_pct >= 95%): page NOC — calls will be blocked. Reroute traffic immediately.
- Warning (util_pct >= 85%): ticket to capacity planning with 1-week SLA.
- Forecast (predicted to exceed 100% within 30 days): monthly report to carrier management.

Runbook (owner: Voice Operations / Carrier Management):
1. **Trunk at 95%+**: Activate overflow routing on the SBC. Contact the carrier for emergency trunk expansion.
2. **Sustained 85%+ during peak hours**: Order additional trunk capacity. Lead time is typically 2-4 weeks.

### Step 5 — Troubleshooting

- **SNMP session count is always 0** — The SNMP community string or OID may be wrong. Verify with `snmpwalk` directly against the SBC. Check that the SBC's SNMP agent is enabled and the trunk group OID is correct for your vendor.

- **Stream-derived concurrency seems too low** — Stream may not capture all calls if some traffic bypasses the mirror. Also, if BYE messages are lost, sessions appear open indefinitely. Add a max session duration cap.

- **`trunk_group` field is null** — Different data sources name this field differently. SNMP may use `ifAlias`, CDR may use `route_pattern`, Stream may use `dest`. Normalize with `eval trunk_group=coalesce(trunk_group, route_label, ifAlias)`.

- **Utilization percentage exceeds 100%** — The `licensed_sess` value in the lookup may be stale (carrier upgraded the trunk but lookup wasn't updated). Refresh the lookup from the SBC license page.

## SPL

```spl
index=voip sourcetype="stream:sip" OR sourcetype="snmp:sbc"
| eval concurrent=if(isnotnull(active_calls), active_calls, curr_sess)
| timechart span=1m max(concurrent) as peak_sess by trunk_group
| lookup trunk_capacity trunk_group OUTPUT licensed_sess
| eval util_pct=round(100*peak_sess/licensed_sess,1)
| where util_pct>85
```

## Visualization

Area chart (concurrency), Gauge (utilization %), Table (trunk groups at risk).

## Known False Positives

Rehome events, SBC restarts, and carrier maintenance can dip utilization without a customer-visible outage; use duration filters before paging.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
